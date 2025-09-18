#!/bin/bash
# Script de lancement simple Nonotags
# Remplace l'ancien run_nonotags.sh complexe

cd "$(dirname "$0")"

echo "🎵 Lancement de Nonotags..."
echo "📁 Répertoire: $(pwd)"

# Lancer l'application
python3 main.py
