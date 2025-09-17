#!/usr/bin/env python3
"""
Test du FileCleaner sur l'album compilation complex pour voir la gestion PNG
"""
import sys
import os
sys.path.append('/home/rono/Nonotags/Nonotags')

from core.file_cleaner import FileCleaner
from support.honest_logger import HonestLogger

def test_filecleaner_png():
    print("=== TEST FILECLEANER SUR ALBUM COMPILATION COMPLEX ===")
    
    # Copions l'album test dans un dossier temporaire
    import shutil
    from pathlib import Path
    
    source_path = "/home/rono/Nonotags/Nonotags/test_albums/02_compilation_complex"
    test_path = "/tmp/test_compilation_png"
    
    # Nettoyage et copie
    if os.path.exists(test_path):
        shutil.rmtree(test_path)
    shutil.copytree(source_path, test_path)
    
    print(f"\nAlbum test copié dans: {test_path}")
    
    # Vérifions les fichiers AVANT
    print(f"\nFichiers AVANT FileCleaner:")
    for i, file in enumerate(os.listdir(test_path), 1):
        if not file.startswith('.'):
            print(f"  {i}. {file}")
    
    # Ajoutons quelques fichiers PNG pour tester
    test_files = [
        "artwork.png",
        "cover.png", 
        "some_random_image.png",
        "folder.jpg",
        "info.txt"
    ]
    
    for test_file in test_files:
        if not os.path.exists(f"{test_path}/{test_file}"):
            Path(f"{test_path}/{test_file}").touch()
            print(f"  Créé: {test_file}")
    
    print(f"\nFichiers APRÈS ajout tests:")
    for i, file in enumerate(sorted(os.listdir(test_path)), 1):
        if not file.startswith('.'):
            print(f"  {i}. {file}")
    
    # Test du FileCleaner
    print(f"\n=== EXECUTION FILECLEANER ===")
    
    honest_logger = HonestLogger("FileCleaner")
    file_cleaner = FileCleaner()
    
    result = file_cleaner.clean_album_folder(test_path)
    
    print(f"\nRésultat FileCleaner:")
    print(f"  Succès: {result.success}")
    print(f"  Fichiers supprimés: {result.files_deleted}")
    print(f"  Dossiers supprimés: {result.folders_deleted}")
    print(f"  Fichiers renommés: {result.files_renamed}")
    
    if result.operations:
        print(f"\nOpérations effectuées:")
        for i, op in enumerate(result.operations, 1):
            print(f"  {i}. {op}")
    
    print(f"\nFichiers APRÈS FileCleaner:")
    if os.path.exists(test_path):
        for i, file in enumerate(sorted(os.listdir(test_path)), 1):
            if not file.startswith('.'):
                print(f"  {i}. {file}")
                
                # Analyse de chaque fichier
                if file.endswith('.png'):
                    print(f"      🖼️ PNG conservé")
                elif file.endswith('.jpg'):
                    print(f"      📸 JPG conservé") 
                elif file.endswith('.txt'):
                    print(f"      📄 TXT (devrait être supprimé?)")
    else:
        print("  ❌ Dossier supprimé")
    
    # Nettoyage
    if os.path.exists(test_path):
        shutil.rmtree(test_path)
        print(f"\n🧹 Dossier test nettoyé")

if __name__ == "__main__":
    test_filecleaner_png()
