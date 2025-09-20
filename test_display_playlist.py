#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du détail de l'affichage des playlists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager, PlaylistTrack, Playlist

def test_playlist_display():
    print("🧪 Test de l'affichage des détails de playlist")
    
    # Créer une playlist factice avec des données
    playlist = Playlist("/tmp/test.m3u")
    
    # Ajouter des pistes avec des métadonnées différentes
    track1 = PlaylistTrack(
        file_path="/tmp/song1.mp3",
        title="Chanson 1",
        artist="Artiste A",
        duration=180
    )
    
    track2 = PlaylistTrack(
        file_path="/tmp/song2.mp3", 
        title="Chanson 2",
        artist="Artiste B",
        duration=210
    )
    
    track3 = PlaylistTrack(
        file_path="/tmp/song3.mp3",
        title="",  # Pas de titre
        artist="",  # Pas d'artiste
        duration=0
    )
    
    playlist.add_track(track1)
    playlist.add_track(track2)
    playlist.add_track(track3)
    
    print(f"📋 Playlist: {playlist.name}")
    print(f"🎶 {len(playlist.tracks)} pistes")
    
    for i, track in enumerate(playlist.tracks):
        print(f"  {i+1}. Fichier: {os.path.basename(track.file_path)}")
        print(f"     Artiste: '{track.artist}'")
        print(f"     Titre: '{track.title}'")
        print(f"     Durée: {track.duration}s")
        print()

if __name__ == "__main__":
    test_playlist_display()
