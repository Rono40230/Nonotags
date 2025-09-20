#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple du gestionnaire de playlists avec GTK+
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ui.views.playlist_manager_window import PlaylistManagerWindow

def test_playlist_interface():
    print("🧪 Test de l'interface gestionnaire de playlists")
    
    # Créer la fenêtre
    window = PlaylistManagerWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    
    print("✅ Interface lancée - Vérifiez la colonne 'Type' dans le tableau")
    print("   Utilisez Ctrl+C pour fermer")
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\n👋 Fermeture de l'interface")

if __name__ == "__main__":
    test_playlist_interface()
