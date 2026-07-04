# 🎓 Formation IA — Bot Telegram

Bot Telegram de formation à l'IA en français, pensé pour un apprentissage adapté
**TDAH** : leçons courtes, quiz à choix multiple, et rappels de révision espacée
(J+1, J+3, J+7).

L'apprentissage est organisé par **certifications**. La première, `claude`, prépare à
la certification Anthropic : le bot t'_entraîne_ à l'examen (il ne délivre pas le
diplôme officiel).

## Fonctionnalités

- 📚 Leçons progressives regroupées en modules
- ❓ Quiz à choix multiple après chaque leçon
- 📝 Examen final avec seuil de réussite
- 📊 Suivi de progression et de score par utilisateur
- 🔔 Rappels de révision automatiques (répétition espacée)

## Prérequis

- Ubuntu / Linux avec Python 3
- Un **token de bot Telegram** (créé via [@BotFather](https://t.me/BotFather))
- Une **clé API Anthropic** (seulement pour la génération dynamique de leçons)

## Installation

### Option A — Script automatique (Ubuntu)

```bash
git clone git@github.com:jmdondez-web/Formation-ia.git
cd Formation-ia
./setup.sh
```

Le script installe Python et les dépendances, crée l'environnement virtuel, et te
demande ton token Telegram (enregistré dans `.env`).

### Option B — Manuelle

```bash
git clone git@github.com:jmdondez-web/Formation-ia.git
cd Formation-ia

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install python-telegram-bot==20.7 anthropic numpy pandas
```

## Configuration

Crée un fichier `.env` à la racine (format `CLE="valeur"`) :

```env
TOKEN="ton_token_telegram"
ANTHROPIC_API_KEY="ta_cle_anthropic"
```

> ⚠️ Le fichier `.env` contient des secrets et n'est **jamais** committé
> (il est exclu par `.gitignore`).

## Lancement

Toujours activer l'environnement virtuel d'abord :

```bash
source venv/bin/activate
```

Le bot et les rappels sont deux processus indépendants :

```bash
python bot_telegram.py    # le bot (répond aux commandes Telegram)
python scheduler.py       # les rappels de révision (process séparé)
```

## Utilisation (commandes Telegram)

| Commande          | Action                                             |
| ----------------- | -------------------------------------------------- |
| `/start`          | Démarrer et voir l'aide                            |
| `/certifications` | Lister les certifications disponibles              |
| `/commencer`      | Démarrer (ou reprendre) une certification          |
| `/lecon`          | Recevoir la prochaine leçon                        |
| `/quiz <réponse>` | Répondre au quiz / à l'examen (ex : `/quiz B`)     |
| `/examen`         | Passer l'examen final de la certification          |
| `/progression`    | Voir son avancement                                |
| `/reset`          | Recommencer la certification                       |

## Structure du projet

| Fichier              | Rôle                                                        |
| -------------------- | ----------------------------------------------------------- |
| `bot_telegram.py`    | Le bot Telegram et ses commandes                            |
| `certifications.py`  | Contenu des leçons, quiz et examens (source du bot)         |
| `scheduler.py`       | Rappels de révision espacée                                 |
| `agent_claude.py`    | Génération dynamique de leçons via l'API Claude             |
| `curriculum_tdah.py` | Curriculum utilisé par la génération dynamique              |
| `progression.json`   | Progression des utilisateurs (généré, local)                |
