#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complet du gestionnaire de playlists avec création
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_playlist_creation():
    print("🧪 Test de création de playlist")
    
    # Créer un répertoire temporaire avec des fichiers de test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Répertoire temporaire: {temp_dir}")
        
        # Créer quelques fichiers "audio" de test (vides mais avec bonnes extensions)
        test_files = [
            "01 - Artiste - Chanson1.mp3",
            "02 - Artiste - Chanson2.mp3", 
            "03 - Autre - Chanson3.flac",
            "readme.txt"  # Fichier non-audio à ignorer
        ]
        
        for filename in test_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write("")  # Fichier vide
        
        print(f"📄 Fichiers créés: {test_files}")
        
        # Tester le gestionnaire
        manager = PlaylistManager()
        
        # Créer une playlist depuis le répertoire
        playlist = manager.create_playlist_from_directory(
            temp_dir, 
            "Ma Playlist Test", 
            recursive=False
        )
        
        if playlist:
            print(f"✅ Playlist créée: {playlist.name}")
            print(f"   📁 Chemin: {playlist.file_path}")
            print(f"   🎶 {len(playlist.tracks)} pistes")
            print(f"   📄 Fichier existe: {os.path.exists(playlist.file_path)}")
            
            # Lire le contenu du fichier M3U créé
            if os.path.exists(playlist.file_path):
                print("\n📋 Contenu du fichier M3U:")
                with open(playlist.file_path, 'r') as f:
                    content = f.read()
                    print(content)
            
            # Tester le scan de la playlist créée
            print("\n🔍 Test du scan de la playlist créée:")
            manager.add_scan_directory(temp_dir)
            manager._scan_playlists()
            
            found_playlists = manager.get_all_playlists()
            print(f"📋 {len(found_playlists)} playlist(s) trouvée(s)")
            
            for p in found_playlists:
                print(f"  📝 {p.name}: {len(p.tracks)} pistes")
        else:
            print("❌ Échec de création de la playlist")

if __name__ == "__main__":
    test_playlist_creation()
