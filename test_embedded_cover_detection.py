#!/usr/bin/env python3
"""
Test de détection des pochettes intégrées dans les tags
"""

import os
import sys

# Ajouter le chemin du projet
sys.path.append('/home/rono/Nonotags/Nonotags')

from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC

def test_embedded_cover_detection(file_path):
    """Test de la fonction de détection de pochettes intégrées"""
    print(f"\n🔍 Test pochette intégrée: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier inexistant: {file_path}")
        return False
    
    try:
        if file_path.lower().endswith('.mp3'):
            # Essayer plusieurs méthodes de lecture MP3
            try:
                audio = MP3(file_path, ID3=ID3)
            except:
                # Fallback sans ID3 forcé
                audio = MP3(file_path)
            
            if audio.tags:
                # Chercher toutes les tags APIC (Attached Picture)
                apic_tags = []
                for key in audio.tags.keys():
                    if key.startswith('APIC:'):
                        apic_tags.append(key)
                
                if apic_tags:
                    print(f"✅ MP3 - Pochettes trouvées: {apic_tags}")
                    return True
                else:
                    print(f"❌ MP3 - Aucune pochette intégrée")
                    print(f"   Tags disponibles: {list(audio.tags.keys())[:5]}...")  # Limiter l'affichage
                    return False
            else:
                print(f"❌ MP3 - Aucun tag ID3")
                return False
                
        elif file_path.lower().endswith('.flac'):
            audio = FLAC(file_path)
            if len(audio.pictures) > 0:
                print(f"✅ FLAC - {len(audio.pictures)} pochettes trouvées")
                return True
            else:
                print(f"❌ FLAC - Aucune pochette intégrée")
                return False
                
        elif file_path.lower().endswith(('.m4a', '.mp4')):
            audio = MP4(file_path)
            if audio.tags and 'covr' in audio.tags:
                print(f"✅ MP4/M4A - Pochette trouvée")
                return True
            else:
                print(f"❌ MP4/M4A - Aucune pochette intégrée")
                return False
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    print(f"❌ Format non supporté")
    return False

def main():
    print("🧪 TEST DÉTECTION POCHETTES INTÉGRÉES")
    print("=" * 50)
    
    # Tester sur l'album 01_album_standard
    test_folder = "/home/rono/Nonotags/Nonotags/test_albums/01_album_standard"
    
    if not os.path.exists(test_folder):
        print(f"❌ Dossier de test inexistant: {test_folder}")
        return
    
    # Trouver tous les fichiers audio
    audio_files = []
    for file in os.listdir(test_folder):
        if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg')):
            audio_files.append(os.path.join(test_folder, file))
    
    if not audio_files:
        print(f"❌ Aucun fichier audio trouvé dans {test_folder}")
        return
    
    print(f"📁 Dossier testé: {test_folder}")
    print(f"🎵 {len(audio_files)} fichiers audio trouvés")
    
    covers_found = 0
    total_files = len(audio_files)
    
    for audio_file in sorted(audio_files):
        has_cover = test_embedded_cover_detection(audio_file)
        if has_cover:
            covers_found += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSUMÉ:")
    print(f"   Total fichiers: {total_files}")
    print(f"   Avec pochettes: {covers_found}")
    print(f"   Sans pochettes: {total_files - covers_found}")
    print(f"   Pourcentage: {(covers_found/total_files)*100:.1f}%")

if __name__ == "__main__":
    main()
