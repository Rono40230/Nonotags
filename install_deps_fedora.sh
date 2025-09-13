#!/bin/bash
# Script d'installation des dépendances Nonotags pour Fedora
# Installe GTK3, Python et les dépendances nécessaires

set -e

echo "🚀 Installation des dépendances Nonotags pour Fedora"
echo "=================================================="

# Fonction pour vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Fonction pour installer les packages avec dnf ou yum
install_packages() {
    if command_exists dnf; then
        PKG_MANAGER="dnf"
    elif command_exists yum; then
        PKG_MANAGER="yum"
    else
        echo "❌ Erreur: Ni dnf ni yum trouvés. Ce script est conçu pour Fedora/RHEL."
        exit 1
    fi
    
    echo "📦 Installation des packages système avec $PKG_MANAGER..."
    sudo $PKG_MANAGER install -y "$@"
}

# Vérification des privilèges sudo
if ! command_exists sudo; then
    echo "❌ Erreur: sudo n'est pas installé. Installez sudo ou exécutez en tant que root."
    exit 1
fi

echo "🔍 Vérification des dépendances..."

# Liste des packages requis pour Fedora
REQUIRED_PACKAGES=(
    "python3"
    "python3-pip"
    "python3-devel"
    "gtk3-devel"
    "gobject-introspection-devel"
    "python3-gobject"
    "python3-cairo"
    "cairo-gobject-devel"
    "pkg-config"
    "gcc"
    "redhat-rpm-config"
)

# Packages optionnels pour une meilleure expérience
OPTIONAL_PACKAGES=(
    "gtk3-immodule-xim"
    "gstreamer1-plugins-base"
    "gstreamer1-plugins-good"
    "python3-mutagen"
)

echo "📋 Installation des packages requis..."
install_packages "${REQUIRED_PACKAGES[@]}"

echo "📋 Installation des packages optionnels..."
install_packages "${OPTIONAL_PACKAGES[@]}" || echo "⚠️  Certains packages optionnels n'ont pas pu être installés"

# Vérification de Python et pip
echo "🐍 Vérification de Python..."
if ! command_exists python3; then
    echo "❌ Python3 n'est pas installé correctement"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ $PYTHON_VERSION détecté"

if ! command_exists pip3; then
    echo "❌ pip3 n'est pas installé correctement"
    exit 1
fi

echo "✅ pip3 détecté"

# Installation des dépendances Python
echo "🐍 Installation des dépendances Python..."
if [ -f "requirements.txt" ]; then
    pip3 install --user -r requirements.txt
else
    echo "📦 Installation des dépendances principales..."
    pip3 install --user mutagen PyGObject pycairo requests Pillow
fi

# Vérification de GTK3
echo "🎨 Vérification de GTK3..."
python3 -c "
import gi
try:
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    print('✅ GTK3 disponible')
except Exception as e:
    print(f'❌ Erreur GTK3: {e}')
    exit(1)
" || {
    echo "❌ GTK3 n'est pas accessible depuis Python"
    echo "💡 Essayez: sudo dnf install python3-gobject gtk3-devel"
    exit 1
}

# Test de l'application
echo "🧪 Test de l'application..."
if [ -f "launch_gtk3.py" ]; then
    echo "✅ Script de lancement trouvé"
    # Test rapide sans interface graphique
    python3 -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('launch_gtk3.py')))
try:
    from ui.simple_gtk3_app import SimpleNonotagsApp
    print('✅ Modules Nonotags importés avec succès')
except Exception as e:
    print(f'❌ Erreur d\\'import: {e}')
    exit(1)
    "
else
    echo "⚠️  Script launch_gtk3.py non trouvé"
fi

echo ""
echo "🎉 Installation terminée avec succès!"
echo "=================================================="
echo "🚀 Pour lancer l'application:"
echo "   ./run_nonotags.sh"
echo ""
echo "📱 Ou directement:"
echo "   python3 launch_gtk3.py"
echo ""
echo "🔧 En cas de problème:"
echo "   - Vérifiez que vous êtes dans le bon répertoire"
echo "   - Redémarrez votre session pour les variables d'environnement"
echo "   - Consultez les logs avec: journalctl --user"
