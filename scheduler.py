#!/usr/bin/env python3
# ============================================
# Scheduler - Notifications proactives Telegram
# Répétition espacée : J+1, J+3, J+7
# ============================================

import asyncio
import json
import logging
import os
from datetime import datetime

from telegram import Bot

from curriculum_tdah import get_sujet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROGRESSION_FILE = "progression.json"
REVISIONS_FILE = "revisions.json"
INTERVALLE_VERIFICATION = 3600  # secondes entre deux vérifications

# Délais de répétition espacée (en jours) après la complétion d'une leçon
RAPPELS = {"J+1": 1, "J+3": 3, "J+7": 7}


def load_env_var(key, env_path=".env"):
    """Lit une variable depuis le fichier .env (format CLE=valeur)."""
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"')
    except FileNotFoundError:
        pass
    return None


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def maj_revisions(progression, revisions):
    """Initialise/actualise l'état de révision quand un utilisateur termine une nouvelle leçon."""
    for user_id, user in progression.items():
        lecon_completee = user["lecon"] - 1
        if lecon_completee < 0 or not user["date"]:
            continue

        etat = revisions.get(user_id)
        if etat is None or etat["lecon"] != lecon_completee:
            revisions[user_id] = {
                "lecon": lecon_completee,
                "date": user["date"],
                "rappels_envoyes": [],
            }
    return revisions


async def envoyer_rappels(bot, revisions):
    maintenant = datetime.now()

    for user_id, etat in revisions.items():
        info = get_sujet(etat["lecon"])
        if info is None:
            continue
        phase, sujet, _, _ = info

        date_completion = datetime.fromisoformat(etat["date"])
        jours_ecoules = (maintenant - date_completion).days

        for label, delai in RAPPELS.items():
            if jours_ecoules >= delai and label not in etat["rappels_envoyes"]:
                texte = (
                    f"🔔 *Petite révision ({label})*\n\n"
                    f"Il y a {delai} jour(s), tu as vu : *{sujet}* "
                    f"({phase['titre']}).\n\n"
                    f"Prends 30 secondes pour te le remémorer, puis tape "
                    f"/lecon pour continuer la formation 🚀"
                )
                try:
                    await bot.send_message(
                        chat_id=int(user_id), text=texte, parse_mode="Markdown"
                    )
                    etat["rappels_envoyes"].append(label)
                    logger.info("Rappel %s envoyé à l'utilisateur %s", label, user_id)
                except Exception as e:
                    logger.error("Erreur lors de l'envoi du rappel à %s : %s", user_id, e)


async def cycle(bot):
    progression = load_json(PROGRESSION_FILE, {})
    revisions = load_json(REVISIONS_FILE, {})

    revisions = maj_revisions(progression, revisions)
    await envoyer_rappels(bot, revisions)

    save_json(REVISIONS_FILE, revisions)


async def main():
    token = load_env_var("TOKEN")
    if not token:
        logger.error("TOKEN introuvable dans .env. Lancez setup.sh d'abord.")
        return

    bot = Bot(token=token)
    logger.info("📅 Scheduler démarré (vérification toutes les %ds)", INTERVALLE_VERIFICATION)

    while True:
        try:
            await cycle(bot)
        except Exception as e:
            logger.error("Erreur pendant le cycle de vérification : %s", e)
        await asyncio.sleep(INTERVALLE_VERIFICATION)


if __name__ == "__main__":
    asyncio.run(main())
