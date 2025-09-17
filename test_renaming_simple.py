#!/usr/bin/env python3
"""
Test FileRenamer simplifié - contournement du problème métadonnées
"""
import sys
import os
sys.path.append('/home/rono/Nonotags/Nonotags')

from pathlib import Path
from mutagen.mp3 import MP3

def test_simple_renaming():
    """Test simple de renommage sans les validators défaillants"""
    print("=== TEST RENOMMAGE SIMPLE SANS VALIDATORS ===")
    
    album_path = "/home/rono/Téléchargements/1"
    
    if not os.path.exists(album_path):
        print(f"ERREUR: Album {album_path} n'existe pas")
        return
    
    # Liste des MP3
    album_dir = Path(album_path)
    mp3_files = []
    for pattern in ['*.mp3', '*.MP3', '*.Mp3', '*.mP3']:
        mp3_files.extend(album_dir.glob(pattern))
    
    print(f"\nTrouvé {len(mp3_files)} fichiers MP3:")
    
    renamed_count = 0
    
    for i, mp3_file in enumerate(mp3_files, 1):
        print(f"\n{i}. {mp3_file.name}")
        
        # Extraction métadonnées directe
        try:
            audio_file = MP3(str(mp3_file))
            track_number = "01"  # Par défaut
            title = "Unknown Title"
            
            if audio_file and audio_file.tags:
                tags = audio_file.tags
                
                # Numéro de piste
                if 'TRCK' in tags:
                    track = str(tags['TRCK'])
                    if '/' in track:
                        track = track.split('/')[0]
                    track_number = track.zfill(2)
                
                # Titre
                if 'TIT2' in tags:
                    title = str(tags['TIT2'])
                    
            # Nouveau nom au format "N° - Titre.mp3"
            new_name = f"{track_number} - {title}.mp3"
            
            # Nettoyage du nom
            invalid_chars = r'[<>:"/\\|?*]'
            import re
            new_name = re.sub(invalid_chars, '', new_name)
            new_name = re.sub(r'\s+', ' ', new_name).strip()
            
            print(f"   Métadonnées: Piste={track_number}, Titre={title}")
            print(f"   Nouveau nom: {new_name}")
            
            # Renommage si différent
            if mp3_file.name != new_name:
                new_path = mp3_file.parent / new_name
                try:
                    mp3_file.rename(new_path)
                    print(f"   ✅ RENOMMÉ: {mp3_file.name} → {new_name}")
                    renamed_count += 1
                except Exception as e:
                    print(f"   ❌ ERREUR renommage: {e}")
            else:
                print(f"   ⏭️ Déjà bon format")
                
        except Exception as e:
            print(f"   ❌ ERREUR métadonnées: {e}")
    
    print(f"\n=== RÉSULTAT ===")
    print(f"Fichiers renommés: {renamed_count}/{len(mp3_files)}")
    
    # Liste finale
    print(f"\nFichiers finaux:")
    final_files = list(album_dir.glob("*.mp3")) + list(album_dir.glob("*.MP3"))
    for i, file in enumerate(final_files, 1):
        print(f"  {i}. {file.name}")
        # Vérification format
        if " - " in file.name and file.name[0].isdigit():
            print(f"      ✅ Format correct")
        else:
            print(f"      ❌ Format incorrect")

if __name__ == "__main__":
    test_simple_renaming()
