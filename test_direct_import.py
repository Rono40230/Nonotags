#!/usr/bin/env python3
"""
Test direct de l'import avec l'application tournante
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def trigger_import():
    """Simule un clic sur le bouton d'import"""
    print("🚀 Test direct de l'import...")
    
    # Créer une nouvelle instance pour tester
    from ui.main_app import NonotagsApp
    app = NonotagsApp()
    app.create_main_window()
    
    # Test direct du scan
    test_folder = "/home/rono/.local/share/Trash/files/(1987) Madonna"
    if os.path.exists(test_folder):
        print(f"📂 Test avec le dossier: {test_folder}")
        app._scan_folder(test_folder)
    else:
        print("❌ Dossier de test non trouvé")
    
    # Attendre un peu puis fermer
    def close_test():
        print("✅ Test terminé")
        if app.main_window:
            app.main_window.destroy()
        Gtk.main_quit()
        return False
    
    GLib.timeout_add(5000, close_test)  # Fermer après 5 secondes
    
    app.main_window.show_all()
    Gtk.main()

if __name__ == "__main__":
    trigger_import()
