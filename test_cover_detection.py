#!/usr/bin/env python3
"""
Test des cartes d'album avec affichage de pochettes
"""

import sys
import os
sys.path.append('.')

# Vérifie qu'il y a des images de pochette dans les albums de test
def check_cover_files():
    """Vérifier la présence de fichiers de pochette"""
    test_albums_dir = "test_albums"
    
    if not os.path.exists(test_albums_dir):
        print("❌ Dossier test_albums introuvable")
        return
    
    print("🔍 RECHERCHE FICHIERS DE POCHETTE")
    print("=" * 40)
    
    for album_dir in os.listdir(test_albums_dir):
        album_path = os.path.join(test_albums_dir, album_dir)
        if os.path.isdir(album_path):
            print(f"\n📁 Album: {album_dir}")
            
            cover_files = []
            cover_names = ['cover.jpg', 'cover.png', 'folder.jpg', 'folder.png', 
                          'front.jpg', 'front.png', 'album.jpg', 'album.png',
                          'artwork.jpg', 'artwork.png']
            
            for file in os.listdir(album_path):
                if file.lower() in [name.lower() for name in cover_names]:
                    cover_files.append(file)
                elif file.lower().endswith(('.jpg', '.jpeg', '.png')) and 'cover' in file.lower():
                    cover_files.append(file)
            
            if cover_files:
                print(f"   ✅ Pochettes trouvées: {', '.join(cover_files)}")
            else:
                print(f"   ❌ Aucune pochette détectée")
                print(f"   📋 Fichiers présents: {', '.join(os.listdir(album_path))}")

if __name__ == "__main__":
    check_cover_files()
