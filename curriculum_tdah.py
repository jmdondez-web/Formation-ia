#!/usr/bin/env python3
# ============================================
# Curriculum de formation IA - adapté TDAH
# Progression : LLMs -> Agents -> Python avancé -> RAG -> Fine-tuning
# ============================================

CURRICULUM = [
    {
        "id": "llms",
        "titre": "🧠 Les LLMs",
        "description": "Comprendre les grands modèles de langage",
        "sujets": [
            "Qu'est-ce qu'un LLM et comment il génère du texte (tokens, prédiction du mot suivant)",
            "Le prompt engineering : comment bien formuler ses instructions",
            "Les paramètres clés d'un modèle : température, top_p, max_tokens",
            "La fenêtre de contexte : ce qu'un LLM peut 'retenir' pendant une conversation",
            "Les limites des LLMs : hallucinations, biais, connaissances figées",
            "Comparer les modèles (Claude, GPT, Gemini, Llama) : forces et cas d'usage",
        ],
    },
    {
        "id": "agents",
        "titre": "🤖 Les Agents",
        "description": "Donner de l'autonomie et des outils à un LLM",
        "sujets": [
            "Qu'est-ce qu'un agent IA ? Différence avec un simple chatbot",
            "Le tool use / function calling : donner des outils à un LLM",
            "Les boucles agentiques : raisonner, agir, observer (ReAct)",
            "La mémoire des agents : court terme vs long terme",
            "Orchestrer plusieurs agents ensemble : quand et pourquoi",
            "Sécurité des agents : sandboxing, permissions, garde-fous",
        ],
    },
    {
        "id": "python_avance",
        "titre": "🐍 Python avancé",
        "description": "Les briques techniques pour construire des outils IA",
        "sujets": [
            "Programmation asynchrone (async/await) pour les agents",
            "Décorateurs et closures expliqués simplement",
            "Gestion des exceptions et logging propre",
            "Manipuler des données avec Pandas",
            "Appeler des APIs REST avec requests / httpx",
            "Tester son code avec pytest",
        ],
    },
    {
        "id": "rag",
        "titre": "📚 Le RAG",
        "description": "Connecter un LLM à ses propres connaissances",
        "sujets": [
            "Qu'est-ce que le RAG (Retrieval-Augmented Generation) et pourquoi c'est utile",
            "Les embeddings : transformer du texte en vecteurs",
            "Les bases de données vectorielles (Chroma, FAISS, Pinecone)",
            "Le chunking : découper ses documents intelligemment",
            "Construire un pipeline RAG complet : indexer, chercher, générer",
            "Évaluer et améliorer la qualité d'un système RAG",
        ],
    },
    {
        "id": "fine_tuning",
        "titre": "🛠️ Le Fine-tuning",
        "description": "Spécialiser un modèle pour ses besoins",
        "sujets": [
            "Fine-tuning vs prompt engineering vs RAG : quand choisir quoi",
            "Préparer un dataset de fine-tuning",
            "LoRA et QLoRA : fine-tuner un modèle à moindre coût",
            "Fine-tuner un modèle avec Hugging Face : les bases",
            "Évaluer un modèle fine-tuné",
            "Déployer son modèle personnalisé",
        ],
    },
]


def total_lecons():
    """Nombre total de leçons dans le curriculum."""
    return sum(len(phase["sujets"]) for phase in CURRICULUM)


def get_sujet(lecon_id):
    """
    Retourne les infos de la leçon correspondant à un index global (0-based) :
    (phase, sujet, position_globale, total_lecons)
    Renvoie None si l'index dépasse le curriculum.
    """
    position = 0
    for phase in CURRICULUM:
        for sujet in phase["sujets"]:
            if position == lecon_id:
                return phase, sujet, position, total_lecons()
            position += 1
    return None
