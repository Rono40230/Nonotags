#!/usr/bin/env python3
"""
Script de vérification du mode contextuel
"""
import sys
sys.path.insert(0, '/home/rono/Nonotags')

from support.config_manager import ConfigManager

def main():
    config_manager = ConfigManager()
    mode = "Contextuel (SANS HeaderBar)" if not config_manager.ui.use_headerbar else "HeaderBar (AVEC boutons)"
    
    print(f"🔍 Mode actuel de l'interface : {mode}")
    
    if not config_manager.ui.use_headerbar:
        print("✅ L'application utilise les menus contextuels (clic droit)")
        print("⌨️  Raccourcis disponibles :")
        print("   • Ctrl+O : Importer albums")  
        print("   • Ctrl+E : Éditer sélection")
        print("   • F5     : Rescanner")
        print("   • Ctrl+Q : Quitter")
        print("🖱️  Clic droit sur l'interface pour le menu contextuel")
    else:
        print("⚠️  L'application utilise encore les boutons d'en-tête")
        
if __name__ == "__main__":
    main()