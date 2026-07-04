#!/usr/bin/env bash
# ============================================
# Lance le mentor web + les rappels Telegram dans une session tmux
# persistante, avec redémarrage automatique de chaque process s'il s'arrête.
# Idempotent : si la session existe déjà, on ne fait rien.
# Démarrage auto au boot via crontab (@reboot).
# ============================================

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$DIR/venv/bin/python"
SESSION="formation"
PORT="${PORT:-8000}"

# Déjà lancé ? on sort.
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session tmux '$SESSION' déjà active."
  exit 0
fi

# Fenêtre 1 : web app (relance auto toutes les 3s si le process meurt)
tmux new-session -d -s "$SESSION" -c "$DIR" -n web \
  "while true; do PORT=$PORT '$PY' web_app.py; echo '[web_app arrêté — relance dans 3s]'; sleep 3; done"

# Fenêtre 2 : rappels Telegram (idem)
tmux new-window -t "$SESSION" -c "$DIR" -n rappels \
  "while true; do '$PY' reminders.py; echo '[reminders arrêté — relance dans 3s]'; sleep 3; done"

echo "Session tmux '$SESSION' démarrée (web sur le port $PORT + rappels)."
echo "Voir les logs :  tmux attach -t $SESSION   (détacher : Ctrl-b puis d)"
