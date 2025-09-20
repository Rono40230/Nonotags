#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du parsing d'une vraie playlist
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_real_playlist_parsing():
    print("🧪 Test du parsing d'une vraie playlist")
    
    manager = PlaylistManager()
    
    # Parser directement le fichier test_playlist.m3u
    playlist_path = "/home/rono/Nonotags/test_playlist.m3u"
    playlist = manager._parse_playlist(playlist_path)
    
    if playlist:
        print(f"✅ Playlist parsée: {playlist.name}")
        print(f"🎶 {len(playlist.tracks)} pistes")
        
        for i, track in enumerate(playlist.tracks):
            print(f"  {i+1}. Fichier: {os.path.basename(track.file_path)}")
            print(f"     Artiste: '{track.artist}'")
            print(f"     Titre: '{track.title}'")
            print(f"     Durée: {track.duration}s")
            print(f"     Existe: {track.exists}")
            print()
    else:
        print("❌ Échec du parsing de la playlist")

if __name__ == "__main__":
    test_real_playlist_parsing()
