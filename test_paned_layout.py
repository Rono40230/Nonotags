#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du nouveau layout avec réglage de hauteur pour le gestionnaire de playlists
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from ui.views.playlist_manager_window import PlaylistManagerWindow

def main():
    """Teste l'interface de gestion des playlists avec le réglage de hauteur"""
    
    # Créer l'application
    app = Gtk.Application()
    
    # Créer la fenêtre de gestion des playlists
    playlist_window = PlaylistManagerWindow()
    
    # Connecter la fermeture de la fenêtre
    playlist_window.connect("delete-event", Gtk.main_quit)
    
    print("🎵 Gestionnaire de playlists avec réglage de hauteur lancé")
    print("📏 Vous pouvez maintenant faire glisser la barre de séparation")
    print("   pour ajuster la répartition entre les blocs 'Playlists trouvées'")
    print("   et 'Détails de la playlist'")
    print("❌ Fermez la fenêtre pour arrêter le test")
    
    # Lancer la boucle principale
    Gtk.main()

if __name__ == "__main__":
    main()
