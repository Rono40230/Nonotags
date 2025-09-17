#!/usr/bin/env python3
"""
Test FileCleaner avec suppression systématique des PNG
"""
import sys
import os
sys.path.append('/home/rono/Nonotags/Nonotags')

from core.file_cleaner import FileCleaner
from support.honest_logger import HonestLogger
from support.config_manager import ConfigManager
from support.validator import FileValidator
from database.db_manager import DatabaseManager

def test_png_removal():
    print("=== TEST SUPPRESSION SYSTEMATIQUE PNG ===")
    
    # Créer un dossier de test avec des PNG
    test_dir = "/tmp/test_png_removal"
    os.makedirs(test_dir, exist_ok=True)
    
    # Créer des fichiers de test
    test_files = [
        "01 - Song.mp3",
        "cover.png",      # Pochette PNG
        "artwork.png",    # Artwork PNG  
        "random.png",     # PNG quelconque
        "folder.jpg",     # Image JPG à garder
        "info.txt"        # Fichier texte à supprimer
    ]
    
    for file in test_files:
        with open(os.path.join(test_dir, file), 'w') as f:
            f.write("test content")
    
    print(f"\nFichiers AVANT nettoyage:")
    for i, file in enumerate(os.listdir(test_dir), 1):
        print(f"  {i}. {file}")
    
    # Initialiser FileCleaner
    config_manager = ConfigManager()
    honest_logger = HonestLogger("FileCleaner") 
    validator = FileValidator()
    db_manager = DatabaseManager()
    
    file_cleaner = FileCleaner()
    
    # Test de nettoyage
    print(f"\n=== NETTOYAGE ===")
    result = file_cleaner.clean_album_folder(test_dir)
    
    print(f"\nRésultat nettoyage:")
    print(f"  Succès: {result.success}")
    print(f"  Fichiers supprimés: {result.files_deleted}")
    print(f"  Dossiers supprimés: {result.folders_deleted}")
    print(f"  Pochettes renommées: {result.covers_renamed}")
    
    if result.errors:
        print(f"  Erreurs: {result.errors}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")
    
    print(f"\nFichiers APRÈS nettoyage:")
    remaining_files = os.listdir(test_dir)
    for i, file in enumerate(remaining_files, 1):
        print(f"  {i}. {file}")
    
    # Vérification
    png_files = [f for f in remaining_files if f.endswith('.png')]
    if png_files:
        print(f"\n❌ ÉCHEC: Fichiers PNG restants: {png_files}")
    else:
        print(f"\n✅ SUCCÈS: Tous les fichiers PNG ont été supprimés")
    
    # Nettoyage
    import shutil
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_png_removal()
