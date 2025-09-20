#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test avec des données réelles pour debug
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_debug_playlist():
    print("🔍 Debug du gestionnaire de playlists")
    
    manager = PlaylistManager()
    
    # Ajouter le répertoire actuel pour scanner nos playlists de test
    manager.add_scan_directory("/home/rono/Nonotags")
    
    # Scanner
    manager._scan_playlists()
    
    playlists = manager.get_all_playlists()
    print(f"📋 {len(playlists)} playlist(s) trouvée(s)")
    
    for playlist in playlists:
        print(f"\n📝 Playlist: {playlist.name}")
        print(f"   Fichier: {playlist.file_path}")
        print(f"   Pistes: {len(playlist.tracks)}")
        
        for i, track in enumerate(playlist.tracks):
            print(f"   Piste {i+1}:")
            print(f"     📁 Fichier: {os.path.basename(track.file_path)}")
            print(f"     🎤 Artiste: '{track.artist}' (len={len(track.artist)})")
            print(f"     📝 Titre: '{track.title}' (len={len(track.title)})")
            print(f"     ⏱️ Durée: {track.duration}s")
            print(f"     ✅ Existe: {track.exists}")
            
            # Debug pour voir les données brutes
            print(f"     🔍 Type artiste: {type(track.artist)}")
            print(f"     🔍 Repr artiste: {repr(track.artist)}")

if __name__ == "__main__":
    test_debug_playlist()
