#!/usr/bin/env python3
# ============================================
# Rappels Telegram pour la web app "Mentor IA"
# Répétition espacée (J+1, J+3, J+7) fondée sur les neurosciences :
# on révise juste avant l'oubli pour consolider la mémoire à long terme.
# ============================================

import asyncio
import json
import logging
import os
from datetime import datetime

from telegram import Bot

import curriculum
from mentor import load_env_var

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROGRESS_FILE = "web_progress.json"
STATE_FILE = "reminders_state.json"
INTERVALLE = 3600  # secondes entre deux vérifications
RAPPELS = {"J+1": 1, "J+3": 3, "J+7": 7}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def envoyer(bot, chat_id):
    progression = load_json(PROGRESS_FILE, {})
    etat = load_json(STATE_FILE, {})
    maintenant = datetime.now()

    for cert_id, prog in progression.items():
        cert = curriculum.get_cert(cert_id)
        if not cert:
            continue
        for c in prog.get("completed", []):
            info = curriculum.get_sujet(cert_id, c["index"])
            if info is None:
                continue
            _, module, sujet, _, _ = info
            cle = f"{cert_id}:{c['index']}"
            envoyes = etat.get(cle, [])
            jours = (maintenant - datetime.fromisoformat(c["ts"])).days

            for label, delai in RAPPELS.items():
                if jours >= delai and label not in envoyes:
                    texte = (
                        f"🔔 *Révision ({label})*\n\n"
                        f"Il y a {delai} jour(s), tu as vu :\n"
                        f"*{sujet}*\n_({cert['titre']} · {module['titre']})_\n\n"
                        "Prends 30 secondes pour te le remémorer de mémoire, "
                        "puis reprends la formation 🚀"
                    )
                    try:
                        await bot.send_message(
                            chat_id=int(chat_id), text=texte, parse_mode="Markdown"
                        )
                        envoyes.append(label)
                        etat[cle] = envoyes
                        logger.info("Rappel %s envoyé pour %s", label, cle)
                    except Exception as e:
                        logger.error("Échec envoi rappel %s : %s", cle, e)

    save_json(STATE_FILE, etat)


async def main():
    token = load_env_var("TOKEN")
    chat_id = load_env_var("TELEGRAM_CHAT_ID")
    if not token:
        logger.error("TOKEN introuvable dans .env.")
        return
    if not chat_id:
        logger.error(
            "TELEGRAM_CHAT_ID introuvable dans .env. "
            'Ajoutez TELEGRAM_CHAT_ID="votre_id" (ex. 8681010418).'
        )
        return

    bot = Bot(token=token)
    logger.info("📅 Rappels Mentor IA démarrés (toutes les %ds)", INTERVALLE)
    while True:
        try:
            await envoyer(bot, chat_id)
        except Exception as e:
            logger.error("Erreur cycle rappels : %s", e)
        await asyncio.sleep(INTERVALLE)


if __name__ == "__main__":
    asyncio.run(main())
