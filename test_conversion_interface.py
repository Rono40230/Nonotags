#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'interface de conversion de playlists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ui.views.playlist_manager_window import PlaylistManagerWindow

def test_conversion_interface():
    print("🧪 Test de l'interface de conversion de playlists")
    
    # Créer la fenêtre
    window = PlaylistManagerWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    
    print("✅ Interface lancée")
    print("📋 Fonctionnalités disponibles :")
    print("   1. Sélectionnez une playlist dans le tableau")
    print("   2. Visualisez l'état actuel dans 'État actuel'")
    print("   3. Cliquez sur 'Convertir en chemins relatifs/absolus'")
    print("   4. Vérifiez l'aperçu dans 'Aperçu après conversion'")
    print("   5. Cliquez sur 'Appliquer la conversion' pour sauvegarder")
    print("   📌 Utilisez Ctrl+C pour fermer")
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\n👋 Fermeture de l'interface")

if __name__ == "__main__":
    test_conversion_interface()
