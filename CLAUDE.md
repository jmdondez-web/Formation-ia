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

# --- Web app "Mentor IA" (chemin principal) ---
python web_app.py                   # sert la page responsive + API (défaut PORT=8000)
PORT=8001 python web_app.py         # changer de port si besoin
python reminders.py                 # rappels Telegram basés sur la progression web
python mentor.py                    # teste la génération d'une leçon (appel API)

# --- Bot Telegram historique (autre chemin) ---
python bot_telegram.py              # le bot par certifications (polling Telegram)
python scheduler.py                 # rappels de révision du bot

./setup.sh                          # install système + venv + saisie du token (Ubuntu)
pip install -r requirements.txt     # dépendances : anthropic, flask, python-telegram-bot
```

Il n'y a ni tests, ni linter, ni build configurés. Chaque service est un processus
longue durée indépendant.

> ⚠️ **Ports** : le **carnet alimentaire** de l'utilisateur (autre projet) tourne sur
> **8080**. La web app mentor utilise **8000** par défaut — ne pas réutiliser 8080.
> Vérifier les ports libres avec `ss -tlnp` avant de lancer.

### Déploiement (production locale, en place)

Le mentor tourne **en permanence** via `start.sh` → session **tmux** `formation`
(2 fenêtres : `web`, `rappels`), chaque process ayant une boucle de **relance auto**.
Un **service systemd utilisateur** (`~/.config/systemd/user/formation.service`, copie
de référence dans `deploy/`) le démarre au boot — `Linger=yes` étant activé pour
`worff`, aucun sudo ni login n'est requis. Gérer avec
`systemctl --user {status,restart,stop} formation.service` (préfixer d'un
`export XDG_RUNTIME_DIR=/run/user/1000` dans un shell non-interactif).

**Accès mobile** : Tailscale Serve expose la VM en HTTPS sur
`https://ubuntu-srv.tail45201a.ts.net` (→ `127.0.0.1:8000`). Config serve persistante,
restaurée au boot par tailscaled. `sudo tailscale serve …` nécessite un vrai terminal
(le préfixe `!` de Claude Code n'a pas de TTY pour le mot de passe).

## Configuration

`.env` (format `CLE="valeur"`, **jamais** committé) contient :
- `TOKEN` — token du bot Telegram (@BotFather)
- `ANTHROPIC_API_KEY` — clé API pour `agent_claude.py`

Le `.env` est lu à la main, ligne par ligne (pas de `python-dotenv`) — voir
`load_env_var()`, dupliquée dans `agent_claude.py` et `scheduler.py`, et le parsing
inline dans `bot_telegram.py`.

## Architecture

### Web app "Mentor IA" (chemin principal, actuel)

Application Flask responsive (tél/tablette) où l'utilisateur suit des leçons et se
fait corriger « comme un vrai mentor », avec des rappels Telegram. Vise deux
certifications : **`claude`** (Anthropic) et **`linux`** (fondamentaux LPIC-1/LFCS).

- `web_app.py` — serveur Flask. Sert `static/index.html` et expose l'API JSON :
  `/api/certs`, `/api/lesson`, `/api/answer` (QCM), `/api/evaluate` (réponse libre),
  `/api/progress`.
- `mentor.py` — cœur IA. `generer_lecon()` et `evaluer_reponse()` appellent l'API
  Claude (`claude-opus-4-8`) avec un **system prompt fondé sur les neurosciences**
  (récupération active, chunking, double codage, élaboration, répétition espacée,
  format TDAH). Sorties JSON **garanties** via `output_config.format` (json_schema).
  `evaluer_reponse` utilise `thinking: adaptive` pour un vrai jugement de mentor.
- `curriculum.py` — `CURRICULA[cert_id] → modules[] → sujets[]`. Les leçons sont
  **générées dynamiquement** par le mentor (pas de contenu en dur), puis **mises en
  cache** dans `lessons_cache.json` (stable pour la révision espacée). Indexation par
  index global à plat, comme le reste du projet.
- `static/index.html` — SPA mobile-first, JS vanilla, thème clair/sombre, rendu
  Markdown minimal maison. Flux : choix de piste → leçon + points clés → QCM corrigé
  → question ouverte de rappel actif évaluée par le mentor → suivante.
- `reminders.py` — rappels Telegram (J+1/J+3/J+7) lus depuis `web_progress.json`,
  envoyés à `TELEGRAM_CHAT_ID`, état dans `reminders_state.json`.

**Clé requise** : `ANTHROPIC_API_KEY` dans `.env` (sinon `/api/lesson` renvoie 502
avec un message clair — c'est le seul point qui bloque le fonctionnement complet).

**Persistance web** : `web_progress.json` = `{cert_id: {index, completed[], last_ts}}`,
écrit à chaque action.

### Bot Telegram historique (chemin parallèle)

Deux systèmes de contenu coexistent côté bot, et c'est le point le plus important à
comprendre :

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
