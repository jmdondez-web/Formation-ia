#!/usr/bin/env python3
# ============================================
# Agent Mistral - Génération de leçons dynamiques
# adaptées TDAH (courtes, variées, engageantes)
# (Fichier historique nommé agent_claude.py ; chemin
#  expérimental, non branché au bot Telegram.)
# ============================================

import json
import logging
import random

from mistralai import Mistral

from curriculum_tdah import get_sujet

logger = logging.getLogger(__name__)

MODEL = "mistral-large-latest"

ANGLES = [
    "une analogie de la vie quotidienne",
    "une mini-histoire ou un scénario concret",
    "une comparaison avant/après ou un tableau simple",
    "un exemple de code commenté étape par étape",
    "un fait surprenant suivi d'une explication",
    "une métaphore visuelle facile à imaginer",
]

SYSTEM_PROMPT = (
    "Tu es un formateur IA spécialisé dans l'enseignement à des personnes TDAH. "
    "Tes leçons doivent être : courtes (150 à 200 mots maximum pour le contenu), "
    "structurées avec des emojis et des puces pour ancrer l'attention visuelle, "
    "concrètes (toujours un exemple ou un exercice rapide), "
    "et écrites dans un ton dynamique et encourageant, en français. "
    "Varie systématiquement le format d'une leçon à l'autre pour éviter la routine. "
    "Le format Markdown utilisé doit être compatible Telegram (gras avec *texte*, "
    "blocs de code avec ```)."
    "\n\n"
    "Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans texte autour, "
    "respectant exactement ce schéma :\n"
    '{"titre": "...", "contenu": "...", "quiz": {"question": "...", '
    '"choix": ["A) ...", "B) ...", "C) ...", "D) ..."], "reponse": "A"}}'
)


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


def _client():
    api_key = load_env_var("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MISTRAL_API_KEY introuvable dans .env. "
            'Ajoutez MISTRAL_API_KEY="votre_cle" dans le fichier .env.'
        )
    return Mistral(api_key=api_key)


def _extraire_json(texte):
    """Extrait un objet JSON même s'il est entouré de ```json ... ```."""
    texte = texte.strip()
    if texte.startswith("```"):
        texte = texte.split("```")[1]
        if texte.startswith("json"):
            texte = texte[4:]
    return json.loads(texte.strip())


def generer_lecon(lecon_id):
    """
    Génère dynamiquement une leçon (titre, contenu, quiz) pour l'index global
    `lecon_id` du curriculum, via l'API Mistral.

    Retourne None si le curriculum est terminé.
    """
    info = get_sujet(lecon_id)
    if info is None:
        return None

    phase, sujet, position, total = info
    angle = random.choice(ANGLES)

    prompt = (
        f"Crée la leçon n°{position + 1}/{total} de la formation.\n\n"
        f"Module : {phase['titre']} - {phase['description']}\n"
        f"Sujet précis de cette leçon : {sujet}\n\n"
        f"Présente ce sujet en utilisant {angle}.\n"
        "Termine par un quiz à choix multiple (4 propositions A/B/C/D, une seule "
        "bonne réponse) qui vérifie la compréhension du point clé de la leçon."
    )

    client = _client()
    response = client.chat.complete(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    texte = response.choices[0].message.content
    try:
        lecon = _extraire_json(texte)
    except (json.JSONDecodeError, IndexError) as e:
        logger.error("Réponse Mistral non parsable en JSON : %s\n%s", e, texte)
        raise

    return lecon


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lecon = generer_lecon(0)
    print(json.dumps(lecon, indent=2, ensure_ascii=False))
