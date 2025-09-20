#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complet de conversion de playlists
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.playlist_manager import PlaylistManager

def test_full_conversion():
    print("🧪 Test complet de conversion de playlists")
    
    manager = PlaylistManager()
    manager.add_scan_directory("/home/rono/Nonotags")
    manager._scan_playlists()
    
    playlists = manager.get_all_playlists()
    
    # Trouver une playlist avec chemins absolus
    absolute_playlist = None
    relative_playlist = None
    
    for playlist in playlists:
        if playlist.get_path_type() == "Absolu" and not absolute_playlist:
            absolute_playlist = playlist
        elif playlist.get_path_type() == "Relatif" and not relative_playlist:
            relative_playlist = playlist
    
    # Test 1: Convertir une playlist absolue vers relative
    if absolute_playlist:
        print(f"\n📝 Test 1: Convertir '{absolute_playlist.name}' vers relatif")
        print(f"   Type avant: {absolute_playlist.get_path_type()}")
        
        # Sauvegarder l'état original
        original_file = absolute_playlist.file_path + ".backup"
        with open(absolute_playlist.file_path, 'r') as src:
            with open(original_file, 'w') as dst:
                dst.write(src.read())
        
        # Convertir
        success = manager.convert_playlist_paths(absolute_playlist, to_relative=True)
        
        if success:
            # Recharger pour vérifier
            manager._scan_playlists()
            updated_playlist = manager._find_playlist_by_path(absolute_playlist.file_path)
            if updated_playlist:
                print(f"   Type après: {updated_playlist.get_path_type()}")
                print(f"   ✅ Conversion réussie!")
                
                # Montrer quelques exemples
                for i, track in enumerate(updated_playlist.tracks[:2]):
                    print(f"     Piste {i+1}: {track.original_path}")
            else:
                print("   ❌ Erreur: playlist non trouvée après conversion")
        else:
            print("   ❌ Échec de la conversion")
        
        # Restaurer l'état original
        os.rename(original_file, absolute_playlist.file_path)
        print("   🔄 État original restauré")
    
    # Test 2: Convertir une playlist relative vers absolue
    if relative_playlist:
        print(f"\n📝 Test 2: Convertir '{relative_playlist.name}' vers absolu")
        print(f"   Type avant: {relative_playlist.get_path_type()}")
        
        # Sauvegarder l'état original
        original_file = relative_playlist.file_path + ".backup"
        with open(relative_playlist.file_path, 'r') as src:
            with open(original_file, 'w') as dst:
                dst.write(src.read())
        
        # Convertir
        success = manager.convert_playlist_paths(relative_playlist, to_relative=False)
        
        if success:
            # Recharger pour vérifier
            manager._scan_playlists()
            updated_playlist = manager._find_playlist_by_path(relative_playlist.file_path)
            if updated_playlist:
                print(f"   Type après: {updated_playlist.get_path_type()}")
                print(f"   ✅ Conversion réussie!")
                
                # Montrer quelques exemples
                for i, track in enumerate(updated_playlist.tracks[:2]):
                    print(f"     Piste {i+1}: {track.original_path}")
            else:
                print("   ❌ Erreur: playlist non trouvée après conversion")
        else:
            print("   ❌ Échec de la conversion")
        
        # Restaurer l'état original
        os.rename(original_file, relative_playlist.file_path)
        print("   🔄 État original restauré")
    
    print(f"\n✅ Tests terminés")

# Méthode manquante
def _find_playlist_by_path(self, path):
    """Trouve une playlist par son chemin"""
    for playlist in self.playlists:
        if playlist.file_path == path:
            return playlist
    return None

# Ajouter la méthode à la classe
PlaylistManager._find_playlist_by_path = _find_playlist_by_path

if __name__ == "__main__":
    test_full_conversion()
