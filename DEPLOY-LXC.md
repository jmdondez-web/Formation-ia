# Déploiement du Mentor IA dans le LXC 103 (Proxmox VE)

Configuration validée le 12/11/2026 : LXC unprivileged, IP fixe **192.168.0.103**
sur **vmbr0**, 1 Go RAM / 1 vCPU, port 8000. Tailscale tourne sur l'hôte (pas de
/dev/net/tun en LXC unprivileged) ; services systemd root dans le LXC (remplacent
tmux).

## 1. Créer le conteneur (sur l'hôte Proxmox)

```bash
pveam list local   # vérifier le template Debian 12 disponible (ex. debian-12-standard_12.12-1_amd64.tar.zst)
pct create 103 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname mentor-ia --memory 1024 --cores 1 --rootfs local-lvm:8 --net0 name=eth0,bridge=vmbr0,ip=192.168.0.103/24,gw=192.168.0.1 --unprivileged 1 --features nesting=1 --start 1
pct enter 103
```

Adapter le nom du template et le stockage selon l'hôte (`pveam list local`,
`pvesm status`).

## 2. Installer (dans le LXC, en root)

```bash
apt update && apt install -y python3-venv git
mkdir -p /opt/mentor-ia && cd /opt/mentor-ia
git clone https://github.com/jmdondez-web/Formation-ia.git repo
python3 -m venv venv
venv/bin/pip install -r repo/requirements.txt
```

Figer ensuite les versions exactes : `venv/bin/pip freeze | grep -Ei 'mistral|flask|telegram'`
puis remplacer les bornes de `requirements.txt` par ces versions exactes.

## 3. Fichier `.env` (jamais committé)

```
TOKEN="<token bot Telegram>"
MISTRAL_API_KEY="<clé Mistral, console.mistral.ai>"
TELEGRAM_CHAT_ID="<chat_id des rappels>"
MENTOR_API_KEY="<clé d'accès aléatoire, ex. openssl rand -hex 32>"
```

`MENTOR_API_KEY` est optionnelle mais recommandée : sans elle, toute requête venant
du tailnet peut réécrire la progression et déclencher des appels API payants.

## 4. Services systemd (remplacent tmux + session utilisateur)

```bash
cd /opt/mentor-ia/repo
cp deploy/mentor-web.service deploy/mentor-rappels.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now mentor-web mentor-rappels
systemctl status mentor-web mentor-rappels
curl -s http://127.0.0.1:8000/api/certs | head -c 200
```

## 5. Accès depuis l'extérieur (Tailscale via l'hôte)

Sur l'hôte (Tailscale y tourne déjà) :

```bash
tailscale serve --https=443 http://192.168.0.103:8000
```

Puis ouvrir `https://<nom-du-noeud-tailscale>.<tailnet>.ts.net` depuis le téléphone.

## 6. Mise à jour du code plus tard

```bash
cd /opt/mentor-ia/repo && git pull
systemctl restart mentor-web mentor-rappels
```

## Points d'attention

- Ne pas réutiliser le port 8080 (carnet alimentaire) — mentor = 8000.
- `web_progress.json` et `lessons_cache.json` vivent dans `/opt/mentor-ia/repo`
  (WorkingDirectory des services). Sauvegarder ce répertoire suffit.
- La clé MENTOR_API_KEY est injectée dans la page servie ; elle n'apparaît jamais
  dans le repo. La régénérer invalide juste les navigateurs ouverts.
