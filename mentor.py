#!/usr/bin/env python3
# ============================================
# Mentor IA — génération de leçons + évaluation
# Fondé sur les neurosciences de l'apprentissage,
# adapté TDAH. Utilise l'API Claude (Anthropic).
# ============================================

import json
import logging

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Modèle le plus capable. Passer à "claude-sonnet-5" pour réduire les coûts.
MODEL = "claude-opus-4-8"


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
    api_key = load_env_var("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY introuvable dans .env. "
            'Ajoutez ANTHROPIC_API_KEY="votre_cle" dans le fichier .env.'
        )
    return Anthropic(api_key=api_key)


# --------------------------------------------------
# Prompts fondés sur les neurosciences de l'apprentissage
# --------------------------------------------------
NEURO_SYSTEM = (
    "Tu es un mentor expert qui enseigne à un adulte motivé, avec un TDAH, "
    "en français. Tu conçois chaque leçon selon les données probantes des "
    "neurosciences de l'apprentissage :\n"
    "• RÉCUPÉRATION ACTIVE (testing effect) : la leçon prépare le terrain d'un "
    "rappel actif, elle ne fait pas que présenter.\n"
    "• CHUNKING : découper en 2-4 idées maximum, une seule notion centrale.\n"
    "• DOUBLE CODAGE : associer le texte à une image mentale, une analogie ou un "
    "mini-schéma en mots.\n"
    "• ÉLABORATION : relier la notion à quelque chose de connu et expliquer le "
    "POURQUOI, pas seulement le QUOI.\n"
    "• DIFFICULTÉ DÉSIRABLE : un exemple concret puis une question qui force la "
    "réflexion, sans surcharge.\n"
    "• SAILLANCE / ATTENTION (TDAH) : court (120-180 mots), rythmé, emojis pour "
    "ancrer visuellement, ton dynamique et encourageant, format varié d'une "
    "leçon à l'autre pour éviter l'habituation.\n\n"
    "Le contenu est en Markdown simple (gras avec **texte**, listes avec -, "
    "blocs de code avec ```)."
)

EVAL_SYSTEM = (
    "Tu es un mentor bienveillant et exigeant qui corrige la réponse d'un "
    "apprenant TDAH, en français. Principes :\n"
    "• Évalue le FOND, pas la formulation exacte : une bonne intuition mal "
    "rédigée reste correcte.\n"
    "• Feedback immédiat, spécifique et actionnable (les corrections vagues "
    "n'ancrent rien).\n"
    "• Renforce d'abord ce qui est juste (encodage positif), puis corrige "
    "précisément ce qui manque.\n"
    "• Termine par UN conseil de mémorisation concret (analogie, moyen "
    "mnémotechnique, ou point à revoir).\n"
    "• Ton chaleureux et motivant, jamais culpabilisant. Court."
)

LESSON_SCHEMA = {
    "type": "object",
    "properties": {
        "titre": {"type": "string"},
        "contenu": {"type": "string"},
        "points_cles": {"type": "array", "items": {"type": "string"}},
        "quiz": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "choix": {"type": "array", "items": {"type": "string"}},
                "reponse": {"type": "string", "enum": ["A", "B", "C", "D"]},
                "explication": {"type": "string"},
            },
            "required": ["question", "choix", "reponse", "explication"],
            "additionalProperties": False,
        },
        "question_ouverte": {"type": "string"},
    },
    "required": ["titre", "contenu", "points_cles", "quiz", "question_ouverte"],
    "additionalProperties": False,
}

EVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "boolean"},
        "score": {"type": "number"},
        "feedback": {"type": "string"},
        "conseil": {"type": "string"},
    },
    "required": ["correct", "score", "feedback", "conseil"],
    "additionalProperties": False,
}


def _texte(response):
    """Extrait le premier bloc texte d'une réponse (ignore les blocs thinking)."""
    return next((b.text for b in response.content if b.type == "text"), "")


def generer_lecon(cert_titre, module_titre, sujet, position, total):
    """
    Génère une leçon structurée (titre, contenu, points clés, quiz QCM,
    question ouverte de rappel) pour un sujet donné.
    """
    prompt = (
        f"Certification visée : {cert_titre}\n"
        f"Module : {module_titre}\n"
        f"Sujet précis de cette leçon (n°{position + 1}/{total}) : {sujet}\n\n"
        "Rédige la leçon. Le champ `contenu` fait 120-180 mots en Markdown. "
        "`points_cles` liste 3 idées à retenir. `quiz` teste le point clé "
        "(4 choix A/B/C/D préfixés, ex. 'A) ...', une seule bonne réponse, "
        "plus une brève explication). `question_ouverte` est une question de "
        "RAPPEL ACTIF à laquelle l'apprenant répond de mémoire, avec ses mots."
    )
    client = _client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=NEURO_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": LESSON_SCHEMA}},
    )
    return json.loads(_texte(response))


def evaluer_reponse(sujet, question, reponse_attendue, reponse_user):
    """
    Évalue la réponse libre de l'apprenant comme un mentor : correct/score +
    feedback détaillé + conseil de mémorisation.
    """
    prompt = (
        f"Sujet : {sujet}\n"
        f"Question posée : {question}\n"
        f"Éléments attendus dans une bonne réponse : {reponse_attendue}\n\n"
        f"Réponse de l'apprenant : \"{reponse_user}\"\n\n"
        "Évalue le fond. `score` entre 0 et 1 (0=hors sujet, 1=maîtrisé). "
        "`correct` vrai si score >= 0.6. `feedback` reconnaît le juste puis "
        "corrige le manque. `conseil` donne un moyen concret de mieux retenir."
    )
    client = _client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=EVAL_SYSTEM,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": EVAL_SCHEMA}},
    )
    return json.loads(_texte(response))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lecon = generer_lecon(
        "Certification Claude (Anthropic)",
        "Les modèles Claude",
        "La famille de modèles Claude : Opus, Sonnet, Haiku",
        0,
        6,
    )
    print(json.dumps(lecon, indent=2, ensure_ascii=False))
