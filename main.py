#!/usr/bin/env python3
"""
Application Nonotags - Gestionnaire de métadonnées MP3
Point d'entrée principal de l'application.
"""

import sys
import os

# Ajout du répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager
from ui.views.main_window import NonotagsApp

# Configuration GTK3 avec CSS moderne
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

def setup_gtk3_css():
    """Configure le CSS moderne pour GTK3"""
    css_provider = Gtk.CssProvider()
    css_data = """
    .title-label {
        font-size: 24px;
        font-weight: bold;
        color: #2563eb;
    }

    .subtitle-label {
        font-size: 14px;
        color: #64748b;
    }

    .album-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin: 8px;
        padding: 16px;
    }

    .album-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .modern-button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
    }

    .modern-button:hover {
        background: #1d4ed8;
    }
    """

    css_provider.load_from_data(css_data.encode())
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

def main():
    """Point d'entrée principal de l'application."""
    # Configuration GTK3
    setup_gtk3_css()
    
    # Initialisation des modules de support
    logger = AppLogger()
    config = ConfigManager()
    state = StateManager()
    
    logger.info("Démarrage de l'application Nonotags")
    
    try:
        # Lancement de l'interface graphique
        app = NonotagsApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Erreur fatale dans l'application: {e}")
        sys.exit(1)
    
    logger.info("Arrêt de l'application Nonotags")

if __name__ == "__main__":
    main()