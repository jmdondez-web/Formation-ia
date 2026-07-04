# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Bot Telegram de formation IA en français, pensé pour un apprentissage adapté TDAH
(leçons courtes, quiz, répétition espacée). L'utilisateur progresse par
**certifications** : la première, `claude`, prépare à la certification Anthropic.
Le bot _entraîne_ à l'examen, il ne délivre pas de diplôme officiel. Tout le texte
utilisateur est en français.

## Commandes

```bash
source venv/bin/activate            # toujours activer le venv d'abord
python bot_telegram.py              # lance le bot (polling Telegram)
python scheduler.py                 # lance les rappels de révision (process séparé)
python agent_claude.py              # teste la génération dynamique d'une leçon (appel API)
./setup.sh                          # install système + venv + saisie du token (Ubuntu)
```

Il n'y a ni tests, ni linter, ni build configurés. `setup.sh` installe les
dépendances via `pip install` direct (pas de `requirements.txt`) : `python-telegram-bot==20.7`,
`anthropic`, `numpy`, `pandas`. Le bot et le scheduler sont deux processus longue durée
indépendants qu'il faut lancer séparément.

## Configuration

`.env` (format `CLE="valeur"`, **jamais** committé) contient :
- `TOKEN` — token du bot Telegram (@BotFather)
- `ANTHROPIC_API_KEY` — clé API pour `agent_claude.py`

Le `.env` est lu à la main, ligne par ligne (pas de `python-dotenv`) — voir
`load_env_var()`, dupliquée dans `agent_claude.py` et `scheduler.py`, et le parsing
inline dans `bot_telegram.py`.

## Architecture

Deux systèmes de contenu coexistent, et c'est le point le plus important à comprendre :

1. **Contenu curé (actif)** — `certifications.py` : leçons, quiz et examens écrits en
   dur dans le dict `CERTIFICATIONS[cert_id]`. C'est **ce qu'utilise réellement le bot**.
   Structure : `cert → modules[] → lecons[] {titre, contenu, quiz}` plus un `examen
   {seuil, questions[]}`. API d'accès : `list_certifications`, `get_certification`,
   `total_lecons(cert_id)`, `get_lecon(cert_id, index)`, `get_examen(cert_id)`. Les
   leçons sont indexées par un **index global** à plat sur tous les modules.

2. **Contenu dynamique (non branché)** — `agent_claude.py` + `curriculum_tdah.py` :
   génère les leçons à la volée via l'API Claude à partir du curriculum `CURRICULUM`
   (LLMs → Agents → Python avancé → RAG → Fine-tuning). `agent_claude.generer_lecon`
   demande à Claude un JSON strict `{titre, contenu, quiz}` et le parse. **Ce chemin
   n'est pas appelé par `bot_telegram.py`** ; seul `scheduler.py` réutilise
   `curriculum_tdah.get_sujet` pour libeller ses rappels. Traiter ces deux modules
   comme un système parallèle/expérimental, pas comme la source du bot.

### Flux du bot (`bot_telegram.py`)

Handlers de commandes python-telegram-bot v20 (API async). Commandes :
`/start /certifications /commencer /lecon /quiz /examen /progression /reset`.
Une machine à états par utilisateur via le champ `mode` (`"lecon"` vs `"examen"`) :
`/quiz` route vers `_quiz_lecon` ou `_quiz_examen` selon le mode. L'examen n'est
débloqué qu'une fois **toutes** les leçons faites (`lecon >= total_lecons`) et réussi
si `ratio >= examen["seuil"]`.

### Persistance

`progression.json` — dict `{user_id: {cert, lecon, score, mode, exam_idx, exam_ok,
certifie, meilleur, date}}`, écrit à chaque action. `_default_user()` définit le schéma ;
`get_user()` fait une **migration douce** en remplissant les clés manquantes des vieux
enregistrements via `setdefault` — donc en ajoutant un champ utilisateur, l'ajouter là.
`scheduler.py` maintient en plus `revisions.json` (répétition espacée J+1/J+3/J+7,
vérifiée toutes les heures).

### Conventions

- Tout message utilisateur passe par `send_md()` : envoi Markdown avec **fallback texte
  brut** si Telegram rejette le Markdown (`BadRequest`). Le Markdown doit rester
  compatible Telegram (`*gras*`, blocs ` ``` `).
- Les ids de modèles Claude sont cités par **id exact** (ex. `claude-opus-4-8`,
  `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-fable-5`) — c'est aussi le contenu
  enseigné, ne pas inventer de suffixes de date.
