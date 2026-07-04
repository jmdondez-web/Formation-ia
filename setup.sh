#!/bin/bash
# ============================================
# Setup formation IA - Ubuntu
# Auteur : Votre assistant DeepSeek
# ============================================

echo "🚀 Démarrage de l'installation..."

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Python et pip
sudo apt install -y python3 python3-pip python3-venv git curl

# Création environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation bibliothèques de base
pip install --upgrade pip
pip install python-telegram-bot==20.7 numpy pandas matplotlib scikit-learn jupyter

echo ""
echo "✅ Environnement Python prêt."
echo ""

# Demander le token Telegram
read -p "📱 Collez votre token Telegram (donné par @BotFather) : " TOKEN
echo "TOKEN=\"$TOKEN\"" > .env

echo ""
echo "✅ Token enregistré dans .env"
echo ""
echo "📌 Pour activer l'environnement plus tard :"
echo "   cd ~/formation-ia && source venv/bin/activate"
echo ""
echo "🔜 Prochain fichier à créer : bot_telegram.py"