# 🎓 Formation IA — Mentor web + Bot Telegram

Plateforme de formation en français, pensée pour un apprentissage adapté **TDAH** :
leçons courtes fondées sur les neurosciences de l'apprentissage, quiz corrigés, et
rappels de révision espacée (J+1, J+3, J+7).

Deux cibles de certification : **`claude`** (Anthropic) et **`linux`** (fondamentaux
orientés LPIC-1 / LFCS). Le mentor _entraîne_ à l'examen (il ne délivre pas le
diplôme officiel).

## Deux façons de l'utiliser

- **🌐 Mentor web (`web_app.py`)** — une page responsive (téléphone, tablette,
  ordinateur) où un mentor IA (Claude) génère des leçons sur mesure, te fait un quiz,
  et **corrige tes réponses libres comme un vrai mentor**. C'est le chemin principal.
- **🤖 Bot Telegram (`bot_telegram.py`)** — la version historique par certifications,
  avec examen final, directement dans Telegram.

## Fonctionnalités (mentor web)

- 📚 Leçons générées dynamiquement, courtes, fondées sur les neurosciences
  (récupération active, chunking, double codage, répétition espacée)
- ❓ Quiz à choix multiple corrigé immédiatement
- ✍️ Question ouverte de **rappel actif** : tu réponds de mémoire, le mentor évalue
  le fond et te donne un feedback + un conseil de mémorisation
- 📊 Progression sauvegardée par certification
- 🔔 Rappels de révision espacée sur Telegram

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
pip install -r requirements.txt
```

## Configuration

Crée un fichier `.env` à la racine (format `CLE="valeur"`) :

```env
TOKEN="ton_token_telegram"
ANTHROPIC_API_KEY="ta_cle_anthropic"
TELEGRAM_CHAT_ID="ton_chat_id"
```

> ⚠️ La `ANTHROPIC_API_KEY` est **indispensable** au mentor web (génération et
> correction des leçons). Sans elle, l'app renvoie une erreur claire.
>
> ⚠️ Le fichier `.env` contient des secrets et n'est **jamais** committé
> (il est exclu par `.gitignore`).

## Lancement

Toujours activer l'environnement virtuel d'abord :

```bash
source venv/bin/activate
```

### Mentor web

```bash
python web_app.py         # sert la page sur http://<serveur>:8000
python reminders.py       # rappels Telegram (process séparé)
```

Puis ouvre `http://<ip-du-serveur>:8000` depuis ton téléphone ou ta tablette.

> ⚠️ **Port** : le mentor écoute sur **8000** par défaut. Si ce port est déjà pris
> (par exemple par une autre app), lance `PORT=8001 python web_app.py`.

### Bot Telegram (optionnel)

```bash
python bot_telegram.py    # le bot (répond aux commandes Telegram)
python scheduler.py       # les rappels de révision (process séparé)
```

## Déploiement permanent (tmux + systemd, sans sudo)

`start.sh` lance le mentor web **et** les rappels dans une session **tmux**
persistante (`formation`), chaque process étant **relancé automatiquement** s'il
s'arrête. Un service **systemd utilisateur** le démarre à chaque boot (le *linger*
étant activé, aucun login ni sudo requis).

```bash
# Installation du service utilisateur
mkdir -p ~/.config/systemd/user
cp deploy/formation.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now formation.service

# Voir les logs en direct
tmux attach -t formation      # détacher : Ctrl-b puis d

# Gérer le service
systemctl --user status formation.service
systemctl --user restart formation.service
```

### Accès mobile via Tailscale

La VM est sur un tailnet. Après `sudo tailscale serve --bg 8000` (et l'activation
des certificats HTTPS dans la console Tailscale), l'app est joignable depuis le
téléphone/tablette sur :

```
https://ubuntu-srv.<ton-tailnet>.ts.net
```

Sans HTTPS, l'accès direct `http://<ip-tailscale>:8000` fonctionne aussi (déjà
chiffré par Tailscale).

## Utilisation du bot (commandes Telegram)

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
| `web_app.py`         | Serveur Flask du mentor web (page + API)                    |
| `static/index.html`  | Interface responsive (tél/tablette)                         |
| `mentor.py`          | Génération de leçons + évaluation via l'API Claude          |
| `curriculum.py`      | Curriculums des pistes `claude` et `linux`                  |
| `reminders.py`       | Rappels Telegram basés sur la progression web               |
| `bot_telegram.py`    | Le bot Telegram historique et ses commandes                 |
| `certifications.py`  | Contenu curé des leçons/examens (source du bot)             |
| `scheduler.py`       | Rappels de révision espacée (bot)                           |
| `web_progress.json`  | Progression du mentor web (généré, local)                   |
