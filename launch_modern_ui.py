#!/usr/bin/env python3
"""
Script de lancement de l'UI moderne Nonotags
Démonstration de l'interface utilisateur épurée et intuitive
"""

import sys
import os

# Ajoute le chemin du projet
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configuration de l'environnement
os.environ['GTK_THEME'] = 'Adwaita'  # Thème moderne par défaut

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from ui.app_controller import NonotagsApp

def main():
    """Point d'entrée principal pour l'UI moderne"""
    
    print("🚀 Lancement de Nonotags UI moderne...")
    print("📱 Interface épurée et intuitive")
    print("🎨 Design moderne avec GTK4 + Libadwaita")
    print()
    
    # Initialise Libadwaita pour un look moderne
    Adw.init()
    
    # Crée et lance l'application
    app = NonotagsApp()
    
    try:
        exit_code = app.run(sys.argv)
        print(f"\n✅ Application fermée avec le code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt demandé par l'utilisateur")
        return 0
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
