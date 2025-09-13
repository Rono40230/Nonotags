#!/usr/bin/env python3
"""
Script de démonstration du Module 1 - FileCleaner
Teste le nettoyage de fichiers sur un album d'exemple
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import du module
from core.file_cleaner import FileCleaner
from support.validator import ValidationResult


def create_test_album():
    """Crée un album de test avec différents types de fichiers."""
    temp_dir = tempfile.mkdtemp()
    album_dir = Path(temp_dir) / "Test Album - (2023) Test Artist"
    album_dir.mkdir()
    
    print(f"📁 Création de l'album de test : {album_dir}")
    
    # Fichiers MP3 normaux
    mp3_files = [
        "01 - Premier Titre.mp3",
        "02 - Deuxième Titre.mp3", 
        "03 - Troisième Titre.mp3"
    ]
    
    for mp3_file in mp3_files:
        (album_dir / mp3_file).write_text("fake mp3 content")
    
    # Fichiers indésirables
    unwanted_files = [
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
        ".fuse_hidden0001",
        "folder.jpg"  # Fichier de pochette système
    ]
    
    for unwanted_file in unwanted_files:
        (album_dir / unwanted_file).write_text("unwanted content")
    
    # Fichiers de pochettes à renommer
    cover_files = [
        "front.jpg",
        "folder.png",
        "album.jpeg"
    ]
    
    for cover_file in cover_files:
        (album_dir / cover_file).write_text("cover image content")
    
    # Sous-dossiers à supprimer
    subfolders = [
        "CD Booklet",
        "Extras",
        "Hi-Res"
    ]
    
    for subfolder in subfolders:
        subfolder_path = album_dir / subfolder
        subfolder_path.mkdir()
        (subfolder_path / "extra_file.txt").write_text("extra content")
    
    print(f"✅ Album de test créé avec :")
    print(f"   • {len(mp3_files)} fichiers MP3")
    print(f"   • {len(unwanted_files)} fichiers indésirables")
    print(f"   • {len(cover_files)} fichiers de pochettes à renommer")
    print(f"   • {len(subfolders)} sous-dossiers à supprimer")
    
    return str(album_dir), temp_dir


def demo_file_cleaner():
    """Démontre le fonctionnement du FileCleaner."""
    print("🚀 DÉMONSTRATION MODULE 1 - FILECLEANER")
    print("=" * 50)
    
    # Création de l'album de test
    album_path, temp_dir = create_test_album()
    
    try:
        # Configuration des mocks pour la démo
        with patch('core.file_cleaner.AppLogger') as mock_logger:
            with patch('core.file_cleaner.ConfigManager') as mock_config:
                with patch('core.file_cleaner.StateManager') as mock_state:
                    with patch('core.file_cleaner.FileValidator') as mock_validator:
                        
                        # Configuration des mocks
                        logger_instance = MagicMock()
                        mock_logger.return_value.get_logger.return_value = logger_instance
                        
                        config_instance = MagicMock()
                        processing_config = MagicMock()
                        processing_config.unwanted_files = [
                            '.ds_store', 'thumbs.db', 'desktop.ini', 
                            '.fuse_hidden', 'folder.jpg'
                        ]
                        processing_config.cover_rename_patterns = {
                            'front': 'cover',
                            'folder': 'cover',
                            'album': 'cover'
                        }
                        config_instance.get_processing_config.return_value = processing_config
                        mock_config.return_value = config_instance
                        
                        mock_state.return_value = MagicMock()
                        
                        validator_instance = MagicMock()
                        validator_instance.validate_directory_access.return_value = ValidationResult(True, [], [], {})
                        validator_instance.validate_file_permissions.return_value = ValidationResult(True, [], [], {})
                        mock_validator.return_value = validator_instance
                        
                        # Initialisation du FileCleaner
                        print("\n🔧 Initialisation du FileCleaner...")
                        cleaner = FileCleaner()
                        
                        # Affichage du contenu avant nettoyage
                        print(f"\n📋 CONTENU AVANT NETTOYAGE :")
                        album_dir = Path(album_path)
                        for item in sorted(album_dir.iterdir()):
                            if item.is_dir():
                                print(f"   📁 {item.name}/")
                                for subitem in item.iterdir():
                                    print(f"      📄 {subitem.name}")
                            else:
                                print(f"   📄 {item.name}")
                        
                        # Aperçu du nettoyage
                        print(f"\n🔍 APERÇU DU NETTOYAGE :")
                        preview = cleaner.get_cleaning_preview(album_path)
                        
                        if preview['files_to_delete']:
                            print(f"   🗑️  Fichiers à supprimer ({len(preview['files_to_delete'])}) :")
                            for file in preview['files_to_delete']:
                                print(f"      • {file}")
                        
                        if preview['folders_to_delete']:
                            print(f"   📁 Dossiers à supprimer ({len(preview['folders_to_delete'])}) :")
                            for folder in preview['folders_to_delete']:
                                print(f"      • {folder}/")
                        
                        if preview['files_to_rename']:
                            print(f"   🔄 Fichiers à renommer ({len(preview['files_to_rename'])}) :")
                            for rename in preview['files_to_rename']:
                                print(f"      • {rename}")
                        
                        # Exécution du nettoyage
                        print(f"\n🧹 EXÉCUTION DU NETTOYAGE...")
                        stats = cleaner.clean_album_folder(album_path)
                        
                        # Affichage des résultats
                        print(f"\n📊 RÉSULTATS DU NETTOYAGE :")
                        print(f"   ✅ Fichiers supprimés : {stats.files_deleted}")
                        print(f"   ✅ Dossiers supprimés : {stats.folders_deleted}")
                        print(f"   ✅ Fichiers renommés : {stats.files_renamed}")
                        print(f"   💾 Espace libéré : {stats.total_size_freed} bytes")
                        
                        if stats.errors:
                            print(f"   ⚠️  Erreurs ({len(stats.errors)}) :")
                            for error in stats.errors:
                                print(f"      • {error}")
                        else:
                            print(f"   ✅ Aucune erreur")
                        
                        # Affichage du contenu après nettoyage
                        print(f"\n📋 CONTENU APRÈS NETTOYAGE :")
                        remaining_items = list(album_dir.iterdir())
                        if remaining_items:
                            for item in sorted(remaining_items):
                                if item.is_dir():
                                    print(f"   📁 {item.name}/")
                                    for subitem in item.iterdir():
                                        print(f"      📄 {subitem.name}")
                                else:
                                    print(f"   📄 {item.name}")
                        else:
                            print("   (Dossier vide)")
                        
                        # Vérification de l'intégration avec les modules de support
                        print(f"\n🔗 INTÉGRATION MODULES DE SUPPORT :")
                        print(f"   📝 Logger : {logger_instance.info.call_count} messages d'info")
                        print(f"   ⚙️  Config : {config_instance.get_processing_config.call_count} accès config")
                        print(f"   🔍 Validator : {validator_instance.validate_directory_access.call_count} validations dossier")
                        print(f"   📊 State : Statut mis à jour via StateManager")
                        
    finally:
        # Nettoyage
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧽 Dossier temporaire nettoyé")
    
    print(f"\n✨ DÉMONSTRATION TERMINÉE AVEC SUCCÈS !")


if __name__ == "__main__":
    demo_file_cleaner()
