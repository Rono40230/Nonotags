#!/usr/bin/env python3
"""
Script de test pour basculer vers le mode contextuel (sans HeaderBar)
Usage: python test_contextual_mode.py
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, '/home/rono/Nonotags')

from support.config_manager import ConfigManager

def main():
    """Bascule temporairement vers le mode contextuel"""
    print("🔧 Configuration du mode contextuel (sans HeaderBar)...")
    
    config_manager = ConfigManager()
    
    # Sauvegarder l'état actuel
    current_mode = config_manager.ui.use_headerbar
    print(f"Mode actuel: {'HeaderBar' if current_mode else 'Contextuel'}")
    
    # Basculer vers le mode contextuel
    config_manager.ui.use_headerbar = False
    config_manager.save()
    
    print("✅ Mode contextuel activé")
    print("📱 L'application utilisera maintenant les menus contextuels (clic droit)")
    print("⌨️  Raccourcis clavier disponibles:")
    print("   Ctrl+O : Importer des albums")
    print("   Ctrl+E : Éditer la sélection")
    print("   F5     : Rescanner le dossier")
    print("   Ctrl+Q : Quitter")
    print("\n🔙 Pour revenir au mode HeaderBar, relancez ce script")
    
    # Demander confirmation pour restaurer
    try:
        input("\n👉 Appuyez sur Entrée pour lancer l'application en mode contextuel...")
        
        # Lancer l'application
        import subprocess
        subprocess.run([sys.executable, "/home/rono/Nonotags/main.py"])
        
    except KeyboardInterrupt:
        print("\n❌ Annulé par l'utilisateur")
    
    # Restaurer le mode original après fermeture
    config_manager.ui.use_headerbar = current_mode
    config_manager.save()
    print(f"✅ Mode restauré: {'HeaderBar' if current_mode else 'Contextuel'}")

if __name__ == "__main__":
    main()