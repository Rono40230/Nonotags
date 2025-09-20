#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'interface de conversion de playlists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_conversion_methods():
    print("🧪 Test des méthodes de conversion")
    
    manager = PlaylistManager()
    manager.add_scan_directory("/home/rono/Nonotags")
    manager._scan_playlists()
    
    playlists = manager.get_all_playlists()
    print(f"📋 {len(playlists)} playlist(s) trouvée(s)")
    
    for playlist in playlists:
        print(f"\n📝 Playlist: {playlist.name}")
        print(f"   🔗 Type actuel: {playlist.get_path_type()}")
        print(f"   📁 Fichier: {playlist.file_path}")
        
        # Simuler une conversion vers relatif
        playlist_dir = os.path.dirname(playlist.file_path)
        print(f"   📁 Répertoire playlist: {playlist_dir}")
        
        print("   Conversion vers relatif:")
        for i, track in enumerate(playlist.tracks[:2]):  # Premier 2 pistes
            try:
                if os.path.isabs(track.original_path):
                    relative_path = os.path.relpath(track.file_path, playlist_dir)
                    print(f"     Piste {i+1}: {track.original_path} -> {relative_path}")
                else:
                    print(f"     Piste {i+1}: {track.original_path} (déjà relatif)")
            except ValueError as e:
                print(f"     Piste {i+1}: {track.original_path} (impossible: {e})")

if __name__ == "__main__":
    test_conversion_methods()
