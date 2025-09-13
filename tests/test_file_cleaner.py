"""
Tests unitaires pour le Module 1 - FileCleaner
Phase 2 - Tests avec intégration des modules de support
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import du module à tester
from core.file_cleaner import FileCleaner, CleaningStats, CleaningAction
from support.config_manager import ConfigManager
from support.validator import ValidationResult


class TestFileCleaner:
    """Tests pour le module FileCleaner."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        self.temp_dir = tempfile.mkdtemp()
        self.album_path = Path(self.temp_dir) / "Test Album"
        self.album_path.mkdir()
        
        # Mock des modules de support pour les tests
        with patch('core.file_cleaner.AppLogger') as mock_logger:
            with patch('core.file_cleaner.ConfigManager') as mock_config:
                with patch('core.file_cleaner.StateManager') as mock_state:
                    with patch('core.file_cleaner.FileValidator') as mock_validator:
                        # Configuration des mocks
                        mock_logger_instance = MagicMock()
                        mock_logger.return_value.get_logger.return_value = mock_logger_instance
                        
                        mock_config_instance = MagicMock()
                        mock_config.return_value = mock_config_instance
                        
                        # Configuration de ProcessingConfig
                        processing_config = MagicMock()
                        processing_config.unwanted_files = [
                            '.ds_store', 'thumbs.db', 'desktop.ini'
                        ]
                        processing_config.cover_rename_patterns = {
                            'front': 'cover',
                            'folder': 'cover'
                        }
                        mock_config_instance.get_processing_config.return_value = processing_config
                        
                        mock_state_instance = MagicMock()
                        mock_state.return_value = mock_state_instance
                        
                        mock_validator_instance = MagicMock()
                        mock_validator.return_value = mock_validator_instance
                        
                        # Validation par défaut positive
                        valid_result = ValidationResult(True, [], [], {})
                        mock_validator_instance.validate_directory_access.return_value = valid_result
                        mock_validator_instance.validate_file_permissions.return_value = valid_result
                        
                        # Création de l'instance FileCleaner
                        self.file_cleaner = FileCleaner()
                        
                        # Stockage des mocks pour utilisation dans les tests
                        self.mock_logger = mock_logger_instance
                        self.mock_config = mock_config_instance
                        self.mock_state = mock_state_instance
                        self.mock_validator = mock_validator_instance
    
    def teardown_method(self):
        """Nettoyage après chaque test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test de l'initialisation du FileCleaner."""
        assert self.file_cleaner is not None
        assert hasattr(self.file_cleaner, 'logger')
        assert hasattr(self.file_cleaner, 'config')
        assert hasattr(self.file_cleaner, 'state')
        assert hasattr(self.file_cleaner, 'validator')
        
        # Vérification que les configurations sont chargées
        # Note: appelé 2 fois - une fois pour unwanted_files, une fois pour cover_rename_patterns
        assert self.mock_config.get_processing_config.call_count >= 1
    
    def test_clean_unwanted_files_success(self):
        """Test de suppression des fichiers indésirables."""
        # Création de fichiers de test
        unwanted_files = [
            self.album_path / ".DS_Store",
            self.album_path / "Thumbs.db",
            self.album_path / "normal_file.mp3"
        ]
        
        for file_path in unwanted_files:
            file_path.write_text("test content")
        
        # Test de nettoyage
        stats = self.file_cleaner.clean_album_folder(str(self.album_path))
        
        # Vérifications
        assert isinstance(stats, CleaningStats)
        assert stats.album_path == str(self.album_path)
        assert stats.files_deleted == 2  # .DS_Store et Thumbs.db
        assert stats.errors == []
        
        # Vérification que seuls les fichiers indésirables ont été supprimés
        remaining_files = list(self.album_path.iterdir())
        assert len(remaining_files) == 1
        assert remaining_files[0].name == "normal_file.mp3"
    
    def test_clean_subfolders_success(self):
        """Test de suppression des sous-dossiers."""
        # Création de sous-dossiers de test
        subfolder1 = self.album_path / "Subfolder1"
        subfolder2 = self.album_path / "Subfolder2"
        subfolder1.mkdir()
        subfolder2.mkdir()
        
        # Ajout de fichiers dans les sous-dossiers
        (subfolder1 / "file1.txt").write_text("content1")
        (subfolder2 / "file2.txt").write_text("content2")
        
        # Test de nettoyage
        stats = self.file_cleaner.clean_album_folder(str(self.album_path))
        
        # Vérifications
        assert stats.folders_deleted == 2
        assert stats.errors == []
        
        # Vérification que les sous-dossiers ont été supprimés
        remaining_items = list(self.album_path.iterdir())
        assert len(remaining_items) == 0
    
    def test_rename_cover_files_success(self):
        """Test de renommage des fichiers de pochettes."""
        # Création de fichiers de pochettes de test
        cover_files = [
            self.album_path / "front.jpg",
            self.album_path / "folder.png",
            self.album_path / "normal_image.jpg"
        ]
        
        for file_path in cover_files:
            file_path.write_text("image content")
        
        # Test de nettoyage
        stats = self.file_cleaner.clean_album_folder(str(self.album_path))
        
        # Vérifications
        assert stats.files_renamed == 2  # front.jpg et folder.png → cover.*
        assert stats.errors == []
        
        # Vérification des fichiers renommés
        remaining_files = [f.name for f in self.album_path.iterdir()]
        assert "cover.jpg" in remaining_files
        assert "cover.png" in remaining_files
        assert "normal_image.jpg" in remaining_files
        assert "front.jpg" not in remaining_files
        assert "folder.png" not in remaining_files
    
    def test_validation_error_handling(self):
        """Test de gestion des erreurs de validation."""
        # Configuration d'une validation en échec
        invalid_result = ValidationResult(False, ["Accès refusé"], [], {})
        self.mock_validator.validate_directory_access.return_value = invalid_result
        
        # Test de nettoyage
        stats = self.file_cleaner.clean_album_folder(str(self.album_path))
        
        # Vérifications
        assert len(stats.errors) == 1
        assert "Impossible d'accéder au dossier" in stats.errors[0]
        assert stats.files_deleted == 0
        assert stats.folders_deleted == 0
        assert stats.files_renamed == 0
    
    def test_get_cleaning_preview(self):
        """Test de l'aperçu de nettoyage sans exécution."""
        # Création de fichiers de test
        (self.album_path / ".DS_Store").write_text("unwanted")
        (self.album_path / "front.jpg").write_text("cover")
        subfolder = self.album_path / "Subfolder"
        subfolder.mkdir()
        
        # Test de preview
        preview = self.file_cleaner.get_cleaning_preview(str(self.album_path))
        
        # Vérifications
        assert ".DS_Store" in preview['files_to_delete']
        assert "Subfolder" in preview['folders_to_delete']
        assert any("front.jpg" in rename for rename in preview['files_to_rename'])
        
        # Vérification qu'aucun fichier n'a été modifié
        assert (self.album_path / ".DS_Store").exists()
        assert (self.album_path / "front.jpg").exists()
        assert subfolder.exists()
    
    def test_state_management_integration(self):
        """Test de l'intégration avec le gestionnaire d'état."""
        # Test de nettoyage
        stats = self.file_cleaner.clean_album_folder(str(self.album_path))
        
        # Vérification des appels au gestionnaire d'état
        self.mock_state.update_album_processing_status.assert_any_call(
            str(self.album_path), "cleaning_files"
        )
        self.mock_state.update_album_processing_status.assert_any_call(
            str(self.album_path), "cleaning_completed"
        )
    
    def test_logging_integration(self):
        """Test de l'intégration avec le système de logging."""
        # Création d'un fichier indésirable
        (self.album_path / ".DS_Store").write_text("unwanted")
        
        # Test de nettoyage
        stats = self.file_cleaner.clean_album_folder(str(self.album_path))
        
        # Vérification des logs
        self.mock_logger.info.assert_any_call(
            f"Début du nettoyage de l'album : {str(self.album_path)}"
        )
        assert self.mock_logger.info.call_count >= 2  # Au moins début et fin
    
    def test_compatibility_method(self):
        """Test de la méthode de compatibilité clean_album_directory."""
        # Test de la méthode de compatibilité
        result = self.file_cleaner.clean_album_directory(str(self.album_path))
        
        # Vérification
        assert isinstance(result, bool)
        assert result is True  # Pas d'erreurs
        
        # Vérification que la nouvelle API a été appelée
        self.mock_state.update_album_processing_status.assert_called()


def test_file_cleaner_integration():
    """Test d'intégration complet du FileCleaner."""
    with tempfile.TemporaryDirectory() as temp_dir:
        album_dir = Path(temp_dir) / "Test Album"
        album_dir.mkdir()
        
        # Création d'un scénario complexe
        files_to_create = [
            # Fichiers indésirables
            album_dir / ".DS_Store",
            album_dir / "Thumbs.db",
            # Fichiers de pochettes à renommer  
            album_dir / "front.jpg",
            album_dir / "folder.png",
            # Fichiers normaux à conserver
            album_dir / "01 - Track One.mp3",
            album_dir / "02 - Track Two.mp3",
        ]
        
        for file_path in files_to_create:
            file_path.write_text("content")
        
        # Création d'un sous-dossier à supprimer
        subfolder = album_dir / "extra_folder"
        subfolder.mkdir()
        (subfolder / "extra_file.txt").write_text("extra")
        
        # Test avec les vraies dépendances (en mode mock partiel)
        with patch('core.file_cleaner.AppLogger') as mock_logger:
            with patch('core.file_cleaner.ConfigManager') as mock_config:
                with patch('core.file_cleaner.StateManager') as mock_state:
                    with patch('core.file_cleaner.FileValidator') as mock_validator:
                        
                        # Configuration minimale des mocks
                        mock_logger.return_value.get_logger.return_value = MagicMock()
                        
                        config_instance = MagicMock()
                        processing_config = MagicMock()
                        processing_config.unwanted_files = ['.ds_store', 'thumbs.db']
                        processing_config.cover_rename_patterns = {'front': 'cover', 'folder': 'cover'}
                        config_instance.get_processing_config.return_value = processing_config
                        mock_config.return_value = config_instance
                        
                        mock_state.return_value = MagicMock()
                        
                        validator_instance = MagicMock()
                        validator_instance.validate_directory_access.return_value = ValidationResult(True, [], [], {})
                        validator_instance.validate_file_permissions.return_value = ValidationResult(True, [], [], {})
                        mock_validator.return_value = validator_instance
                        
                        # Test
                        cleaner = FileCleaner()
                        preview = cleaner.get_cleaning_preview(str(album_dir))
                        
                        # Vérifications du preview
                        assert len(preview['files_to_delete']) == 2  # .DS_Store, Thumbs.db
                        assert len(preview['folders_to_delete']) == 1  # extra_folder
                        assert len(preview['files_to_rename']) == 2  # front.jpg, folder.png


if __name__ == "__main__":
    # Exécution des tests
    pytest.main([__file__, "-v"])
