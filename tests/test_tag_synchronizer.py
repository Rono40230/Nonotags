"""
Tests unitaires pour le Module 6 - Tag Synchronizer (GROUPE 6)
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import json

# Imports du module à tester
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tag_synchronizer import (
    TagSynchronizer, 
    SynchronizationAction, 
    CoverAssociationResult,
    SynchronizationResult,
    AlbumSynchronizationResult
)


class TestTagSynchronizer:
    """Tests pour la classe TagSynchronizer."""
    
    @pytest.fixture
    def temp_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def synchronizer(self):
        """Crée une instance de TagSynchronizer pour les tests."""
        with patch('core.tag_synchronizer.AppLogger'), \
             patch('core.tag_synchronizer.ConfigManager'), \
             patch('core.tag_synchronizer.StateManager'), \
             patch('core.tag_synchronizer.MetadataValidator'), \
             patch('core.tag_synchronizer.DatabaseManager'):
            
            sync = TagSynchronizer()
            sync.logger = Mock()
            sync.config_manager = Mock()
            sync.state_manager = Mock()
            sync.validator = Mock()
            sync.db_manager = Mock()
            return sync
    
    @pytest.fixture
    def sample_cover_image(self, temp_dir):
        """Crée une image de test pour les pochettes."""
        img_path = os.path.join(temp_dir, "cover.jpg")
        img = Image.new('RGB', (500, 500), color='red')
        img.save(img_path, 'JPEG')
        return img_path
    
    @pytest.fixture
    def sample_mp3_file(self, temp_dir):
        """Crée un fichier MP3 de test."""
        mp3_path = os.path.join(temp_dir, "test.mp3")
        # Créer un fichier MP3 minimal valide
        with open(mp3_path, 'wb') as f:
            # Header MP3 minimal
            f.write(b'\xff\xfb\x90\x00')  # Sync word + layer info
            f.write(b'0' * 1000)  # Données audio factices
        return mp3_path
    
    def test_init_success(self):
        """Test de l'initialisation réussie du TagSynchronizer."""
        with patch('core.tag_synchronizer.AppLogger'), \
             patch('core.tag_synchronizer.ConfigManager'), \
             patch('core.tag_synchronizer.StateManager'), \
             patch('core.tag_synchronizer.MetadataValidator'), \
             patch('core.tag_synchronizer.DatabaseManager'):
            
            sync = TagSynchronizer()
            
            assert sync is not None
            assert hasattr(sync, 'supported_image_formats')
            assert hasattr(sync, 'min_cover_size')
            assert hasattr(sync, 'max_cover_size')
            assert hasattr(sync, 'supported_audio_formats')
    
    def test_init_with_import_error(self):
        """Test de l'initialisation avec erreur d'import."""
        with patch('core.tag_synchronizer.AppLogger', side_effect=ImportError("Module non trouvé")):
            with pytest.raises(ImportError):
                TagSynchronizer()
    
    def test_find_cover_image_priority_names(self, synchronizer, temp_dir):
        """Test de la recherche de pochette avec noms prioritaires."""
        # Créer plusieurs fichiers images
        cover_path = os.path.join(temp_dir, "cover.jpg")
        folder_path = os.path.join(temp_dir, "folder.png")
        other_path = os.path.join(temp_dir, "other.jpg")
        
        for path in [cover_path, folder_path, other_path]:
            img = Image.new('RGB', (300, 300), color='blue')
            img.save(path)
        
        # Le fichier cover.jpg doit être prioritaire
        result = synchronizer.find_cover_image(temp_dir)
        assert result == cover_path
    
    def test_find_cover_image_no_priority_names(self, synchronizer, temp_dir):
        """Test de la recherche de pochette sans noms prioritaires."""
        # Créer seulement un fichier image avec nom générique
        image_path = os.path.join(temp_dir, "album_art.jpg")
        img = Image.new('RGB', (300, 300), color='green')
        img.save(image_path)
        
        result = synchronizer.find_cover_image(temp_dir)
        assert result == image_path
    
    def test_find_cover_image_no_image(self, synchronizer, temp_dir):
        """Test de la recherche de pochette sans image disponible."""
        # Créer seulement des fichiers non-image
        text_path = os.path.join(temp_dir, "readme.txt")
        with open(text_path, 'w') as f:
            f.write("Test file")
        
        result = synchronizer.find_cover_image(temp_dir)
        assert result is None
    
    def test_find_cover_image_invalid_directory(self, synchronizer):
        """Test de la recherche de pochette avec dossier invalide."""
        result = synchronizer.find_cover_image("/dossier/inexistant")
        assert result is None
    
    def test_validate_cover_image_valid(self, synchronizer, sample_cover_image):
        """Test de validation d'une image valide."""
        is_valid, warnings = synchronizer.validate_cover_image(sample_cover_image)
        assert is_valid is True
        assert isinstance(warnings, list)
    
    def test_validate_cover_image_too_small(self, synchronizer, temp_dir):
        """Test de validation d'une image trop petite."""
        small_img_path = os.path.join(temp_dir, "small.jpg")
        img = Image.new('RGB', (100, 100), color='red')  # Plus petit que le minimum (200x200)
        img.save(small_img_path)
        
        is_valid, warnings = synchronizer.validate_cover_image(small_img_path)
        assert is_valid is False
        assert len(warnings) > 0
        assert "trop petite" in warnings[0]
    
    def test_validate_cover_image_non_square(self, synchronizer, temp_dir):
        """Test de validation d'une image non carrée."""
        rect_img_path = os.path.join(temp_dir, "rectangle.jpg")
        img = Image.new('RGB', (500, 300), color='blue')  # Image rectangulaire
        img.save(rect_img_path)
        
        is_valid, warnings = synchronizer.validate_cover_image(rect_img_path)
        assert is_valid is True  # Valide mais avec avertissement
        assert len(warnings) > 0
        assert "non carrée" in warnings[0]
    
    def test_validate_cover_image_very_large(self, synchronizer, temp_dir):
        """Test de validation d'une image très grande."""
        large_img_path = os.path.join(temp_dir, "large.jpg")
        img = Image.new('RGB', (1500, 1500), color='yellow')  # Plus grand que recommandé
        img.save(large_img_path)
        
        is_valid, warnings = synchronizer.validate_cover_image(large_img_path)
        assert is_valid is True  # Valide mais avec avertissement
        assert len(warnings) > 0
        assert "très grande" in warnings[0]
    
    def test_validate_cover_image_file_not_found(self, synchronizer):
        """Test de validation avec fichier inexistant."""
        is_valid, warnings = synchronizer.validate_cover_image("/fichier/inexistant.jpg")
        assert is_valid is False
        assert "introuvable" in warnings[0]
    
    def test_validate_cover_image_unsupported_format(self, synchronizer, temp_dir):
        """Test de validation avec format non supporté."""
        unsupported_path = os.path.join(temp_dir, "image.tiff")
        img = Image.new('RGB', (300, 300), color='purple')
        img.save(unsupported_path, 'TIFF')
        
        is_valid, warnings = synchronizer.validate_cover_image(unsupported_path)
        assert is_valid is False
        assert "non supporté" in warnings[0]
    
    def test_associate_cover_to_mp3_success(self, synchronizer, sample_mp3_file, sample_cover_image):
        """Test d'association réussie de pochette à MP3."""
        # Mock de la validation d'image (simule succès)
        synchronizer.validate_cover_image = Mock(return_value=(True, []))
        
        # Mock de mutagen avec tous les modules nécessaires
        with patch('core.tag_synchronizer.MP3') as mock_mp3, \
             patch('core.tag_synchronizer.ID3') as mock_id3, \
             patch('core.tag_synchronizer.APIC') as mock_apic, \
             patch('core.tag_synchronizer.ID3NoHeaderError') as mock_error:
            
            # Configuration du mock MP3
            mock_audio = Mock()
            mock_tags = Mock()
            mock_tags.__contains__ = Mock(return_value=False)  # Pas de APIC existant
            mock_tags.__iter__ = Mock(return_value=iter([]))  # Pas de tags existants
            mock_tags.add = Mock()
            mock_audio.tags = mock_tags
            mock_audio.save = Mock()
            mock_mp3.return_value = mock_audio
            
            # Mock APIC
            mock_apic.return_value = Mock()
            
            result = synchronizer.associate_cover_to_mp3(sample_mp3_file, sample_cover_image)
            
            assert result == CoverAssociationResult.SUCCESS
            assert mock_tags.add.called
            assert mock_audio.save.called
    
    @patch('core.tag_synchronizer.MP3')
    def test_associate_cover_to_mp3_already_exists(self, mock_mp3, synchronizer, sample_mp3_file, sample_cover_image):
        """Test d'association avec pochette déjà présente."""
        # Mock du fichier MP3 avec pochette existante
        mock_audio = Mock()
        mock_audio.tags = {'APIC:Cover': Mock()}
        mock_mp3.return_value = mock_audio
        
        result = synchronizer.associate_cover_to_mp3(sample_mp3_file, sample_cover_image)
        
        assert result == CoverAssociationResult.ALREADY_EXISTS
        assert not mock_audio.save.called
    
    def test_associate_cover_to_mp3_no_cover(self, synchronizer, sample_mp3_file):
        """Test d'association sans fichier de pochette."""
        result = synchronizer.associate_cover_to_mp3(sample_mp3_file, None)
        assert result == CoverAssociationResult.COVER_NOT_FOUND
    
    def test_associate_cover_to_mp3_invalid_image(self, synchronizer, sample_mp3_file, temp_dir):
        """Test d'association avec image invalide."""
        invalid_image = os.path.join(temp_dir, "invalid.jpg")
        with open(invalid_image, 'w') as f:
            f.write("Pas une image")
        
        result = synchronizer.associate_cover_to_mp3(sample_mp3_file, invalid_image)
        assert result == CoverAssociationResult.INVALID_FORMAT
    
    @patch('core.tag_synchronizer.MP3')
    def test_update_mp3_tags_success(self, mock_mp3, synchronizer, sample_mp3_file):
        """Test de mise à jour réussie des tags MP3."""
        # Mock du fichier MP3
        mock_audio = Mock()
        mock_audio.tags = Mock()
        mock_mp3.return_value = mock_audio
        
        metadata = {
            'TIT2': 'Test Title',
            'TPE1': 'Test Artist',
            'TALB': 'Test Album'
        }
        
        result = synchronizer.update_mp3_tags(sample_mp3_file, metadata)
        
        assert result is True
        assert mock_audio.tags.add.call_count == 3
        assert mock_audio.save.called
    
    @patch('core.tag_synchronizer.MP3')
    def test_update_mp3_tags_empty_metadata(self, mock_mp3, synchronizer, sample_mp3_file):
        """Test de mise à jour avec métadonnées vides."""
        mock_audio = Mock()
        mock_audio.tags = Mock()
        mock_mp3.return_value = mock_audio
        
        result = synchronizer.update_mp3_tags(sample_mp3_file, {})
        
        assert result is False
        assert not mock_audio.tags.add.called
        assert not mock_audio.save.called
    
    @patch('core.tag_synchronizer.MP3')
    def test_update_mp3_tags_partial_success(self, mock_mp3, synchronizer, sample_mp3_file):
        """Test de mise à jour avec succès partiel."""
        mock_audio = Mock()
        mock_audio.tags = Mock()
        
        # Simuler une erreur pour un tag spécifique
        def side_effect_add(tag):
            if hasattr(tag, 'text') and 'Bad' in str(tag.text):
                raise Exception("Tag error")
        
        mock_audio.tags.add.side_effect = side_effect_add
        mock_mp3.return_value = mock_audio
        
        metadata = {
            'TIT2': 'Good Title',
            'TPE1': 'Bad Artist'  # Celui-ci va échouer
        }
        
        result = synchronizer.update_mp3_tags(sample_mp3_file, metadata)
        
        assert result is True  # Au moins un tag a été mis à jour
        assert mock_audio.save.called
    
    def test_synchronize_file_success(self, synchronizer, sample_mp3_file):
        """Test de synchronisation réussie d'un fichier."""
        # Mock des méthodes
        synchronizer.find_cover_image = Mock(return_value="/path/to/cover.jpg")
        synchronizer.associate_cover_to_mp3 = Mock(return_value=CoverAssociationResult.SUCCESS)
        synchronizer.update_mp3_tags = Mock(return_value=True)
        
        metadata = {'TIT2': 'Test Title'}
        
        result = synchronizer.synchronize_file(sample_mp3_file, metadata)
        
        assert isinstance(result, SynchronizationResult)
        assert result.file_path == sample_mp3_file
        assert result.cover_associated is True
        assert result.tags_updated is True
        assert SynchronizationAction.ASSOCIATE_COVER in result.actions_performed
        assert SynchronizationAction.UPDATE_TAGS in result.actions_performed
        assert result.error is None
    
    def test_synchronize_file_no_cover(self, synchronizer, sample_mp3_file):
        """Test de synchronisation sans pochette disponible."""
        synchronizer.find_cover_image = Mock(return_value=None)
        synchronizer.update_mp3_tags = Mock(return_value=True)
        
        metadata = {'TIT2': 'Test Title'}
        
        result = synchronizer.synchronize_file(sample_mp3_file, metadata)
        
        assert result.cover_associated is False
        assert result.cover_result == CoverAssociationResult.COVER_NOT_FOUND
        assert "Aucune pochette trouvée dans le dossier" in result.warnings
        assert result.tags_updated is True
    
    def test_synchronize_file_error(self, synchronizer, sample_mp3_file):
        """Test de synchronisation avec erreur."""
        synchronizer.find_cover_image = Mock(side_effect=Exception("Test error"))
        
        result = synchronizer.synchronize_file(sample_mp3_file)
        
        assert result.error is not None
        assert "Test error" in result.error
        assert result.cover_associated is False
        assert result.tags_updated is False
    
    def test_synchronize_album_success(self, synchronizer, temp_dir):
        """Test de synchronisation réussie d'un album."""
        # Créer des fichiers MP3 de test
        mp3_files = []
        for i in range(3):
            mp3_path = os.path.join(temp_dir, f"track{i+1}.mp3")
            with open(mp3_path, 'wb') as f:
                f.write(b'\xff\xfb\x90\x00' + b'0' * 1000)
            mp3_files.append(mp3_path)
        
        # Mock des dépendances
        synchronizer.validator.validate_directory = Mock(return_value=Mock(is_valid=True, errors=[], warnings=[]))
        synchronizer.validator.validate_mp3_file = Mock(return_value=Mock(is_valid=True, metadata={'TIT2': 'Test'}))
        synchronizer.synchronize_file = Mock(return_value=SynchronizationResult(
            file_path="test.mp3",
            cover_associated=True,
            tags_updated=True,
            actions_performed=[SynchronizationAction.ASSOCIATE_COVER],
            cover_result=CoverAssociationResult.SUCCESS,
            warnings=[],
            processing_time=0.1
        ))
        
        result = synchronizer.synchronize_album(temp_dir, apply_metadata=True)
        
        assert isinstance(result, AlbumSynchronizationResult)
        assert result.album_path == temp_dir
        assert result.files_processed == 3
        assert result.covers_associated == 3
        assert result.tags_updated == 3
        assert len(result.file_results) == 3
        assert result.errors == []
    
    def test_synchronize_album_invalid_directory(self, synchronizer, temp_dir):
        """Test de synchronisation avec dossier invalide."""
        synchronizer.validator.validate_directory = Mock(return_value=Mock(
            is_valid=False, 
            errors=["Dossier invalide"], 
            warnings=[]
        ))
        
        result = synchronizer.synchronize_album(temp_dir)
        
        assert result.files_processed == 0
        assert len(result.errors) > 0
        assert "Dossier invalide" in result.errors[0]
    
    def test_synchronize_album_no_mp3_files(self, synchronizer, temp_dir):
        """Test de synchronisation sans fichiers MP3."""
        # Créer seulement des fichiers non-MP3
        txt_path = os.path.join(temp_dir, "readme.txt")
        with open(txt_path, 'w') as f:
            f.write("No MP3 here")
        
        synchronizer.validator.validate_directory = Mock(return_value=Mock(is_valid=True, errors=[], warnings=[]))
        
        result = synchronizer.synchronize_album(temp_dir)
        
        assert result.files_processed == 0
        assert result.total_files == 0
    
    def test_create_backup_success(self, synchronizer, sample_mp3_file):
        """Test de création réussie de sauvegarde."""
        backup_path = synchronizer.create_backup(sample_mp3_file)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert "backup" in backup_path
        
        # Nettoyer
        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)
    
    def test_create_backup_error(self, synchronizer):
        """Test de création de sauvegarde avec erreur."""
        backup_path = synchronizer.create_backup("/fichier/inexistant.mp3")
        assert backup_path is None
    
    def test_restore_from_backup_success(self, synchronizer, temp_dir):
        """Test de restauration réussie depuis sauvegarde."""
        # Créer un fichier source et une sauvegarde
        source_file = os.path.join(temp_dir, "source.mp3")
        backup_file = os.path.join(temp_dir, "backup.mp3")
        
        with open(source_file, 'wb') as f:
            f.write(b'source content')
        
        with open(backup_file, 'wb') as f:
            f.write(b'backup content')
        
        # Modifier le fichier source
        with open(source_file, 'wb') as f:
            f.write(b'modified content')
        
        # Restaurer depuis la sauvegarde
        result = synchronizer.restore_from_backup(backup_file, source_file)
        
        assert result is True
        
        # Vérifier que le contenu a été restauré
        with open(source_file, 'rb') as f:
            content = f.read()
        
        assert content == b'backup content'
    
    def test_restore_from_backup_error(self, synchronizer):
        """Test de restauration avec erreur."""
        result = synchronizer.restore_from_backup("/backup/inexistant.mp3", "/target/inexistant.mp3")
        assert result is False


class TestEnumsAndDataClasses:
    """Tests pour les énumérations et classes de données."""
    
    def test_synchronization_action_enum(self):
        """Test de l'énumération SynchronizationAction."""
        assert SynchronizationAction.ASSOCIATE_COVER.value == "associate_cover"
        assert SynchronizationAction.UPDATE_TAGS.value == "update_tags"
        assert SynchronizationAction.VALIDATE_CONSISTENCY.value == "validate_consistency"
        assert SynchronizationAction.BACKUP_ORIGINAL.value == "backup_original"
        assert SynchronizationAction.RESTORE_FROM_BACKUP.value == "restore_from_backup"
    
    def test_cover_association_result_enum(self):
        """Test de l'énumération CoverAssociationResult."""
        assert CoverAssociationResult.SUCCESS.value == "success"
        assert CoverAssociationResult.COVER_NOT_FOUND.value == "cover_not_found"
        assert CoverAssociationResult.INVALID_FORMAT.value == "invalid_format"
        assert CoverAssociationResult.SIZE_TOO_SMALL.value == "size_too_small"
        assert CoverAssociationResult.ALREADY_EXISTS.value == "already_exists"
        assert CoverAssociationResult.ERROR.value == "error"
    
    def test_synchronization_result_dataclass(self):
        """Test de la classe SynchronizationResult."""
        result = SynchronizationResult(
            file_path="/test/file.mp3",
            cover_associated=True,
            tags_updated=False,
            actions_performed=[SynchronizationAction.ASSOCIATE_COVER],
            cover_result=CoverAssociationResult.SUCCESS,
            warnings=["Test warning"],
            error=None,
            processing_time=1.5
        )
        
        assert result.file_path == "/test/file.mp3"
        assert result.cover_associated is True
        assert result.tags_updated is False
        assert len(result.actions_performed) == 1
        assert result.cover_result == CoverAssociationResult.SUCCESS
        assert len(result.warnings) == 1
        assert result.error is None
        assert result.processing_time == 1.5
    
    def test_album_synchronization_result_dataclass(self):
        """Test de la classe AlbumSynchronizationResult."""
        file_result = SynchronizationResult(
            file_path="/test/file.mp3",
            cover_associated=True,
            tags_updated=True,
            actions_performed=[],
            cover_result=CoverAssociationResult.SUCCESS,
            warnings=[]
        )
        
        album_result = AlbumSynchronizationResult(
            album_path="/test/album",
            files_processed=5,
            covers_associated=3,
            tags_updated=4,
            total_files=5,
            file_results=[file_result],
            processing_time=10.0,
            errors=[],
            warnings=["Test warning"]
        )
        
        assert album_result.album_path == "/test/album"
        assert album_result.files_processed == 5
        assert album_result.covers_associated == 3
        assert album_result.tags_updated == 4
        assert album_result.total_files == 5
        assert len(album_result.file_results) == 1
        assert album_result.processing_time == 10.0
        assert len(album_result.errors) == 0
        assert len(album_result.warnings) == 1


if __name__ == "__main__":
    pytest.main([__file__])
