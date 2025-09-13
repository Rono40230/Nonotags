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
from ui.main_window import MainWindow

def main():
    """Point d'entrée principal de l'application."""
    # Initialisation des modules de support
    logger = AppLogger()
    config = ConfigManager()
    state = StateManager()
    
    logger.info("Démarrage de l'application Nonotags")
    
    try:
        # Lancement de l'interface graphique
        app = MainWindow(config, state, logger)
        app.run()
        
    except Exception as e:
        logger.error(f"Erreur fatale dans l'application: {e}")
        sys.exit(1)
    
    logger.info("Arrêt de l'application Nonotags")

if __name__ == "__main__":
    main()
