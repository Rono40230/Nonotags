#!/usr/bin/env python3
"""
Test du FileRenamer avec la correction StateManager
"""
import sys
import os
sys.path.append('/home/rono/Nonotags/Nonotags')

from core.file_renamer import FileRenamer
from support.state_manager import StateManager
from support.config_manager import ConfigManager
from support.honest_logger import HonestLogger
from support.validator import FileValidator
from database.db_manager import DatabaseManager

def test_filerenamer():
    print("=== TEST FILERENAMER AVEC CORRECTION ===")
    
    # Initialisation (FileRenamer s'initialise tout seul)
    file_renamer = FileRenamer()
    
    # Test sur le vrai album
    album_path = "/home/rono/Téléchargements/1"
    
    print(f"\n1. Test sur album réel: {album_path}")
    
    # Vérification de l'existence
    if not os.path.exists(album_path):
        print(f"ERREUR: Album {album_path} n'existe pas")
        return
    
    # Liste des fichiers avant
    print("\nFichiers AVANT renommage:")
    for i, file in enumerate(os.listdir(album_path), 1):
        if file.endswith(('.mp3', '.MP3')):
            print(f"  {i}. {file}")
    
    # Test du renommage
    print(f"\n2. Renommage de l'album...")
    try:
        result = file_renamer.rename_album(album_path)
        
        print(f"\nRésultat:")
        print(f"  Succès: {len(result.errors) == 0}")
        print(f"  Fichiers renommés: {result.files_renamed}")
        print(f"  Total fichiers: {result.total_files}")
        print(f"  Dossier renommé: {result.folder_renamed}")
        
        if result.errors:
            print(f"  Erreurs: {result.errors}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
            
        # Le nouveau chemin est dans folder_result si le dossier a été renommé
        new_path = result.folder_result.new_path if result.folder_result and result.folder_renamed else album_path
        if os.path.exists(new_path):
            print(f"\nFichiers APRÈS renommage (dans {new_path}):")
            mp3_files = [f for f in os.listdir(new_path) if f.endswith(('.mp3', '.MP3'))]
            for i, file in enumerate(mp3_files, 1):
                print(f"  {i}. {file}")
                # Vérification du format "N° - Titre"
                if " - " in file and file[0].isdigit():
                    print(f"      ✅ Format correct: N° - Titre")
                else:
                    print(f"      ❌ Format incorrect")
        
    except Exception as e:
        print(f"ERREUR lors du renommage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_filerenamer()
