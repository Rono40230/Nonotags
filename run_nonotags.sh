#!/bin/bash
# Script de lancement principal Nonotags pour Fedora
# Lance l'application avec gestion d'erreurs et environnement optimal

set -e

# Configuration des couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction d'affichage avec couleurs
print_status() {
    echo -e "${BLUE}🎵 Nonotags:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ️${NC} $1"
}

# En-tête de démarrage
clear
echo -e "${PURPLE}"
echo "██████╗ ██████╗ ███████╗██████╗ ████████╗ █████╗  ██████╗ ███████╗"
echo "██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔════╝ ██╔════╝"
echo "██████╔╝██████╔╝█████╗  ██████╔╝   ██║   ███████║██║  ███╗███████╗"
echo "██╔══██╗██╔══██╗██╔══╝  ██╔══██╗   ██║   ██╔══██║██║   ██║╚════██║"
echo "██║  ██║██║  ██║███████╗██║  ██║   ██║   ██║  ██║╚██████╔╝███████║"
echo "╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
echo -e "${NC}"
echo -e "${CYAN}Gestionnaire de métadonnées MP3 moderne pour Fedora${NC}"
echo "================================================================="

# Vérification du répertoire de travail
if [ ! -f "launch_gtk3.py" ]; then
    print_error "Fichier launch_gtk3.py non trouvé!"
    print_info "Assurez-vous d'être dans le répertoire Nonotags"
    print_info "Usage: cd /chemin/vers/Nonotags && ./run_nonotags.sh"
    exit 1
fi

print_status "Vérification de l'environnement..."

# Vérification de Python3
if ! command -v python3 >/dev/null 2>&1; then
    print_error "Python3 n'est pas installé"
    print_info "Installez Python3 avec: sudo dnf install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
print_success "Python détecté: $PYTHON_VERSION"

# Vérification des modules Python requis
print_status "Vérification des modules Python..."

check_python_module() {
    local module=$1
    local package_hint=$2
    
    if python3 -c "import $module" 2>/dev/null; then
        print_success "Module $module: OK"
        return 0
    else
        print_warning "Module $module: MANQUANT"
        if [ -n "$package_hint" ]; then
            print_info "Installation suggérée: $package_hint"
        fi
        return 1
    fi
}

MISSING_MODULES=0

# Vérification des modules essentiels
if ! check_python_module "gi" "sudo dnf install python3-gobject"; then
    ((MISSING_MODULES++))
fi

if ! check_python_module "mutagen" "pip3 install --user mutagen"; then
    ((MISSING_MODULES++))
fi

# Test spécifique de GTK3
print_status "Vérification de GTK3..."
if python3 -c "
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
print('GTK3 OK')
" 2>/dev/null; then
    print_success "GTK3: OK"
else
    print_error "GTK3 non accessible"
    print_info "Installez GTK3 avec: sudo dnf install gtk3-devel python3-gobject"
    ((MISSING_MODULES++))
fi

# Si des modules manquent, proposer l'installation
if [ $MISSING_MODULES -gt 0 ]; then
    echo ""
    print_warning "$MISSING_MODULES module(s) manquant(s) détecté(s)"
    print_info "Voulez-vous exécuter le script d'installation automatique? [y/N]"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [ -f "install_deps_fedora.sh" ]; then
            print_status "Lancement de l'installation des dépendances..."
            chmod +x install_deps_fedora.sh
            ./install_deps_fedora.sh
        else
            print_error "Script d'installation non trouvé!"
            exit 1
        fi
    else
        print_info "Installation annulée. L'application peut ne pas fonctionner correctement."
    fi
fi

# Configuration de l'environnement
print_status "Configuration de l'environnement..."

# Variables d'environnement pour GTK3
export GTK_THEME=Adwaita
export GDK_SCALE=1
export GDK_DPI_SCALE=1

# Variables pour Python
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Variables pour éviter les warnings
export NO_AT_BRIDGE=1

print_success "Environnement configuré"

# Vérification de l'affichage (pour SSH/X11)
if [ -n "$SSH_CONNECTION" ] && [ -z "$DISPLAY" ]; then
    print_warning "Connexion SSH détectée sans DISPLAY"
    print_info "Pour X11 forwarding: ssh -X utilisateur@serveur"
    print_info "Ou utilisez: export DISPLAY=:0"
fi

# Test rapide des modules de l'application
print_status "Test des modules Nonotags..."
if python3 -c "
import sys
import os
sys.path.insert(0, '.')
try:
    from ui.main_app import NonotagsApp
    print('Modules OK')
except Exception as e:
    print(f'Erreur: {e}')
    exit(1)
" 2>/dev/null; then
    print_success "Modules Nonotags: OK"
else
    print_error "Erreur lors du chargement des modules Nonotags"
    print_info "Vérifiez que tous les fichiers sont présents dans ui/"
    exit 1
fi

# Lancement de l'application
echo ""
print_status "Lancement de l'application Nonotags..."
print_info "Interface moderne GTK3 avec design épuré"
print_info "Appuyez sur Ctrl+C pour quitter"
echo ""

# Log des événements
LOG_FILE="/tmp/nonotags_$(date +%Y%m%d_%H%M%S).log"
print_info "Logs disponibles dans: $LOG_FILE"

# Lancement avec gestion d'erreurs
{
    echo "=== Démarrage Nonotags $(date) ===" >> "$LOG_FILE"
    echo "Python: $PYTHON_VERSION" >> "$LOG_FILE"
    echo "Répertoire: $(pwd)" >> "$LOG_FILE"
    echo "Utilisateur: $(whoami)" >> "$LOG_FILE"
    echo "Display: ${DISPLAY:-non défini}" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Lancement effectif
    python3 launch_gtk3.py 2>&1 | tee -a "$LOG_FILE"
    
} || {
    EXIT_CODE=$?
    echo ""
    print_error "L'application s'est arrêtée avec le code: $EXIT_CODE"
    
    case $EXIT_CODE in
        1)
            print_info "Erreur générale - Consultez les logs: $LOG_FILE"
            ;;
        130)
            print_success "Arrêt demandé par l'utilisateur (Ctrl+C)"
            ;;
        *)
            print_warning "Code d'erreur inattendu: $EXIT_CODE"
            print_info "Consultez les logs: $LOG_FILE"
            ;;
    esac
    
    # Affichage des dernières lignes du log en cas d'erreur
    if [ $EXIT_CODE -ne 130 ] && [ $EXIT_CODE -ne 0 ]; then
        echo ""
        print_info "Dernières lignes du log:"
        echo "------------------------"
        tail -10 "$LOG_FILE" 2>/dev/null || echo "Pas de logs disponibles"
    fi
    
    exit $EXIT_CODE
}

print_success "Application fermée proprement"
