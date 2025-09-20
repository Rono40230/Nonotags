#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la colonne Type dans le gestionnaire de playlists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_path_type():
    print("🧪 Test de la méthode get_path_type()")
    
    manager = PlaylistManager()
    manager.add_scan_directory("/home/rono/Nonotags")
    manager._scan_playlists()
    
    playlists = manager.get_all_playlists()
    print(f"📋 {len(playlists)} playlist(s) trouvée(s)")
    
    for playlist in playlists:
        print(f"\n📝 Playlist: {playlist.name}")
        print(f"   🔗 Type de chemin: {playlist.get_path_type()}")
        print(f"   📁 Fichier: {playlist.file_path}")
        print(f"   🎶 Pistes: {len(playlist.tracks)}")
        
        # Afficher quelques exemples de chemins
        for i, track in enumerate(playlist.tracks[:3]):  # Première 3 pistes
            original_abs_rel = "Absolu" if track.is_original_path_absolute() else "Relatif"
            resolved_abs_rel = "Absolu" if os.path.isabs(track.file_path) else "Relatif"
            print(f"     Piste {i+1}: Original={original_abs_rel} Résolu={resolved_abs_rel}")
            print(f"       Original: {track.original_path}")
            print(f"       Résolu:   {track.file_path}")

if __name__ == "__main__":
    test_path_type()
