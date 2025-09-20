#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du gestionnaire de playlists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_playlist_manager():
    print("🧪 Test du gestionnaire de playlists")
    
    # Créer le gestionnaire
    manager = PlaylistManager()
    
    # Ajouter le répertoire actuel pour le scan
    current_dir = os.getcwd()
    manager.add_scan_directory(current_dir)
    print(f"📁 Répertoire ajouté: {current_dir}")
    
    # Scanner les playlists
    print("🔍 Scan des playlists...")
    manager._scan_playlists()  # Version synchrone pour le test
    
    # Afficher les résultats
    playlists = manager.get_all_playlists()
    print(f"📋 {len(playlists)} playlist(s) trouvée(s):")
    
    for playlist in playlists:
        print(f"  📝 {playlist.name}")
        print(f"     📁 {os.path.dirname(playlist.file_path)}")
        print(f"     🎶 {len(playlist.tracks)} pistes ({playlist.valid_tracks} valides, {playlist.invalid_tracks} manquantes)")
        print(f"     ⏱️ {playlist.get_formatted_duration()}")
        print()
        
        # Détails des pistes
        for i, track in enumerate(playlist.tracks[:3]):  # Limiter à 3 pour l'affichage
            status = "✅" if track.exists else "❌"
            print(f"       {i+1}. {status} {track}")
        
        if len(playlist.tracks) > 3:
            print(f"       ... et {len(playlist.tracks) - 3} autre(s)")
        print()
    
    # Statistiques
    stats = manager.get_playlist_statistics()
    print("📊 Statistiques:")
    print(f"  🎵 Total playlists: {stats['total_playlists']}")
    print(f"  🎶 Total pistes: {stats['total_tracks']}")
    print(f"  ✅ Pistes valides: {stats['valid_tracks']}")
    print(f"  ❌ Pistes manquantes: {stats['invalid_tracks']}")
    print(f"  ⏱️ Durée totale: {stats['total_duration'] // 60}m{stats['total_duration'] % 60:02d}s")

if __name__ == "__main__":
    test_playlist_manager()
