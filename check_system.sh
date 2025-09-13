#!/bin/bash
# Script de diagnostic rapide pour Nonotags sur Fedora
# Vérifie l'état du système et des dépendances

echo "🔍 Diagnostic Nonotags pour Fedora"
echo "=================================="

# Informations système
echo "📋 Informations système:"
echo "  OS: $(cat /etc/fedora-release 2>/dev/null || echo 'Non-Fedora détecté')"
echo "  Kernel: $(uname -r)"
echo "  Architecture: $(uname -m)"
echo "  Utilisateur: $(whoami)"
echo "  Répertoire: $(pwd)"
echo ""

# Vérification Python
echo "🐍 Python:"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  ✅ $PYTHON_VERSION"
    echo "  📍 Emplacement: $(which python3)"
    
    # Version pip
    if command -v pip3 >/dev/null 2>&1; then
        PIP_VERSION=$(pip3 --version 2>&1 | head -1)
        echo "  ✅ $PIP_VERSION"
    else
        echo "  ❌ pip3 non trouvé"
    fi
else
    echo "  ❌ Python3 non trouvé"
fi
echo ""

# Vérification des modules Python
echo "📦 Modules Python:"
check_module() {
    if python3 -c "import $1" 2>/dev/null; then
        VERSION=$(python3 -c "import $1; print(getattr($1, '__version__', 'version inconnue'))" 2>/dev/null)
        echo "  ✅ $1 ($VERSION)"
    else
        echo "  ❌ $1 manquant"
    fi
}

check_module "gi"
check_module "mutagen"
check_module "cairo"

# Test GTK3 spécifique
echo ""
echo "🎨 GTK3:"
if python3 -c "
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
print('Version GTK:', Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
" 2>/dev/null; then
    echo "  ✅ GTK3 accessible"
else
    echo "  ❌ GTK3 non accessible"
fi
echo ""

# Vérification des fichiers Nonotags
echo "📁 Fichiers Nonotags:"
check_file() {
    if [ -f "$1" ]; then
        SIZE=$(ls -lh "$1" | awk '{print $5}')
        echo "  ✅ $1 ($SIZE)"
    else
        echo "  ❌ $1 manquant"
    fi
}

check_file "launch_gtk3.py"
check_file "ui/simple_gtk3_app.py"
check_file "requirements.txt"
check_file "run_nonotags.sh"
check_file "install_deps_fedora.sh"

# Vérification des permissions
echo ""
echo "🔐 Permissions:"
if [ -x "run_nonotags.sh" ]; then
    echo "  ✅ run_nonotags.sh exécutable"
else
    echo "  ⚠️  run_nonotags.sh non exécutable (chmod +x run_nonotags.sh)"
fi

if [ -x "install_deps_fedora.sh" ]; then
    echo "  ✅ install_deps_fedora.sh exécutable"
else
    echo "  ⚠️  install_deps_fedora.sh non exécutable (chmod +x install_deps_fedora.sh)"
fi

# Variables d'environnement importantes
echo ""
echo "🌍 Variables d'environnement:"
echo "  DISPLAY: ${DISPLAY:-non défini}"
echo "  PYTHONPATH: ${PYTHONPATH:-non défini}"
echo "  GTK_THEME: ${GTK_THEME:-non défini}"
echo "  XDG_CURRENT_DESKTOP: ${XDG_CURRENT_DESKTOP:-non défini}"

# Test de connectivité X11 (si DISPLAY défini)
if [ -n "$DISPLAY" ]; then
    echo ""
    echo "🖥️  Test X11:"
    if command -v xset >/dev/null 2>&1; then
        if xset q >/dev/null 2>&1; then
            echo "  ✅ Connexion X11 active"
        else
            echo "  ❌ Problème de connexion X11"
        fi
    else
        echo "  ⚠️  xset non disponible pour tester X11"
    fi
fi

# Packages système Fedora recommandés
echo ""
echo "📦 Packages Fedora recommandés:"
PACKAGES=("python3" "python3-pip" "python3-gobject" "gtk3-devel" "cairo-gobject-devel")

for pkg in "${PACKAGES[@]}"; do
    if rpm -q "$pkg" >/dev/null 2>&1; then
        VERSION=$(rpm -q "$pkg" --qf '%{VERSION}')
        echo "  ✅ $pkg ($VERSION)"
    else
        echo "  ❌ $pkg non installé"
    fi
done

# Résumé et recommandations
echo ""
echo "📝 Résumé:"

# Compter les problèmes
PROBLEMS=0
if ! command -v python3 >/dev/null 2>&1; then ((PROBLEMS++)); fi
if ! python3 -c "import gi" 2>/dev/null; then ((PROBLEMS++)); fi
if ! python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then ((PROBLEMS++)); fi
if [ ! -f "launch_gtk3.py" ]; then ((PROBLEMS++)); fi

if [ $PROBLEMS -eq 0 ]; then
    echo "  🎉 Système prêt pour Nonotags!"
    echo "  🚀 Lancez avec: ./run_nonotags.sh"
elif [ $PROBLEMS -le 2 ]; then
    echo "  ⚠️  $PROBLEMS problème(s) mineur(s) détecté(s)"
    echo "  🔧 Lancez: ./install_deps_fedora.sh"
else
    echo "  ❌ $PROBLEMS problème(s) majeur(s) détecté(s)"
    echo "  📖 Consultez la documentation d'installation"
fi

echo ""
echo "🛠️  Commandes utiles:"
echo "  Installation dépendances: ./install_deps_fedora.sh"
echo "  Lancement application:    ./run_nonotags.sh"
echo "  Permissions exécution:    chmod +x *.sh"
echo "  Logs en temps réel:       tail -f /tmp/nonotags_*.log"
