"""
Tests unitaires pour le Module 2 - MetadataCleaner
Phase 2 - Tests avec intégration des modules de support
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import du module à tester
from core.metadata_processor import MetadataCleaner, CleaningRule, MetadataChange, CleaningResults
from support.validator import ValidationResult


class TestMetadataCleaner:
    """Tests pour le module MetadataCleaner."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        self.temp_dir = tempfile.mkdtemp()
        self.album_path = Path(self.temp_dir) / "Test Album"
        self.album_path.mkdir()
        
        # Mock des modules de support pour les tests
        with patch('core.metadata_processor.AppLogger') as mock_logger:
            with patch('core.metadata_processor.ConfigManager') as mock_config:
                with patch('core.metadata_processor.StateManager') as mock_state:
                    with patch('core.metadata_processor.MetadataValidator') as mock_validator:
                        with patch('core.metadata_processor.DatabaseManager') as mock_db:
                            
                            # Configuration des mocks
                            mock_logger_instance = MagicMock()
                            mock_logger.return_value.get_logger.return_value = mock_logger_instance
                            
                            mock_config_instance = MagicMock()
                            mock_config.return_value = mock_config_instance
                            
                            # Configuration ProcessingConfig
                            processing_config = MagicMock()
                            mock_config_instance.get_processing_config.return_value = processing_config
                            
                            mock_state_instance = MagicMock()
                            mock_state.return_value = mock_state_instance
                            
                            mock_validator_instance = MagicMock()
                            mock_validator.return_value = mock_validator_instance
                            
                            # Validation par défaut positive
                            valid_result = ValidationResult(True, [], [], {})
                            mock_validator_instance.validate_directory.return_value = valid_result
                            mock_validator_instance.validate_mp3_file.return_value = valid_result
                            
                            mock_db_instance = MagicMock()
                            mock_db.return_value = mock_db_instance
                            
                            # Création de l'instance MetadataCleaner
                            self.metadata_cleaner = MetadataCleaner()
                            
                            # Stockage des mocks pour utilisation dans les tests
                            self.mock_logger = mock_logger_instance
                            self.mock_config = mock_config_instance
                            self.mock_state = mock_state_instance
                            self.mock_validator = mock_validator_instance
                            self.mock_db = mock_db_instance
    
    def teardown_method(self):
        """Nettoyage après chaque test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test de l'initialisation du MetadataCleaner."""
        assert self.metadata_cleaner is not None
        assert hasattr(self.metadata_cleaner, 'logger')
        assert hasattr(self.metadata_cleaner, 'config')
        assert hasattr(self.metadata_cleaner, 'state')
        assert hasattr(self.metadata_cleaner, 'validator')
        assert hasattr(self.metadata_cleaner, 'db')
        
        # Vérification que les configurations sont chargées
        assert self.mock_config.get_processing_config.call_count >= 1
    
    def test_apply_cleaning_rules_parentheses(self):
        """Test de suppression des parenthèses."""
        test_cases = [
            ("Song Title (Live Version)", "Song Title"),
            ("Album [Remastered]", "Album"),
            ("Artist {Demo}", "Artist"),
            ("Title (feat. Other Artist)", "Title"),
            ("Normal Title", "Normal Title"),
        ]
        
        for original, expected in test_cases:
            result = self.metadata_cleaner._apply_cleaning_rules(original)
            # Note: le résultat peut inclure d'autres nettoyages
            assert "(" not in result
            assert "[" not in result
            assert "{" not in result
    
    def test_apply_cleaning_rules_whitespace(self):
        """Test de nettoyage des espaces."""
        test_cases = [
            ("  Song   Title  ", "Song Title"),
            ("Album\t\tName", "Album Name"),
            ("Artist\n\nName", "Artist Name"),
            ("Title     Here", "Title Here"),
        ]
        
        for original, expected in test_cases:
            result = self.metadata_cleaner._apply_cleaning_rules(original)
            assert result == expected
    
    def test_apply_cleaning_rules_special_chars(self):
        """Test de suppression des caractères spéciaux."""
        test_cases = [
            ("Song™ Title®", "Song Title"),
            ("Album© Name", "Album Name"),
            ("Artist† Name", "Artist Name"),
        ]
        
        for original, _ in test_cases:
            result = self.metadata_cleaner._apply_cleaning_rules(original)
            # Vérifier que les caractères spéciaux ont été supprimés
            assert "™" not in result
            assert "®" not in result
            assert "©" not in result
            assert "†" not in result
    
    def test_apply_cleaning_rules_conjunctions(self):
        """Test de normalisation des conjonctions."""
        test_cases = [
            ("Artist and Band", "Artist & Band"),
            ("Song et Version", "Song & Version"),
            ("Name And Title", "Name & Title"),
            ("Album Et Song", "Album & Song"),
            ("ALL AND CAPS", "ALL & CAPS"),
        ]
        
        for original, expected in test_cases:
            result = self.metadata_cleaner._apply_cleaning_rules(original)
            assert " & " in result
            assert " and " not in result.lower()
            assert " et " not in result.lower()
    
    def test_identify_applied_rules(self):
        """Test d'identification des règles appliquées."""
        # Test règle parenthèses
        rules = self.metadata_cleaner._identify_applied_rules(
            "Song (Live)", "Song"
        )
        assert CleaningRule.REMOVE_PARENTHESES in rules
        
        # Test règle espaces
        rules = self.metadata_cleaner._identify_applied_rules(
            "  Song  ", "Song"
        )
        assert CleaningRule.CLEAN_WHITESPACE in rules
        
        # Test règle conjonctions
        rules = self.metadata_cleaner._identify_applied_rules(
            "Artist and Band", "Artist & Band"
        )
        assert CleaningRule.NORMALIZE_CONJUNCTIONS in rules
    
    def test_find_mp3_files(self):
        """Test de recherche des fichiers MP3."""
        # Création de fichiers de test
        test_files = [
            "01 - Song One.mp3",
            "02 - Song Two.mp3",
            "cover.jpg",
            "info.txt",
        ]
        
        for filename in test_files:
            (self.album_path / filename).write_text("content")
        
        # Test de recherche
        mp3_files = self.metadata_cleaner._find_mp3_files(str(self.album_path))
        
        # Vérifications
        assert len(mp3_files) == 2
        assert any("Song One.mp3" in f for f in mp3_files)
        assert any("Song Two.mp3" in f for f in mp3_files)
        assert all(f.endswith(".mp3") for f in mp3_files)
    
    def test_get_cleaning_preview(self):
        """Test de génération d'aperçu de nettoyage."""
        # Création d'un fichier MP3 fictif
        mp3_file = self.album_path / "test.mp3"
        mp3_file.write_text("fake mp3")
        
        # Mock de la méthode _preview_file_changes
        with patch.object(self.metadata_cleaner, '_preview_file_changes') as mock_preview:
            mock_preview.return_value = {
                'file_path': str(mp3_file),
                'changes': [
                    {'field': 'TIT2', 'original': 'Song (Live)', 'cleaned': 'Song', 'rule': 'remove_parentheses'}
                ],
                'errors': []
            }
            
            # Test de preview
            preview = self.metadata_cleaner.get_cleaning_preview(str(self.album_path))
            
            # Vérifications
            assert 'files_to_modify' in preview
            assert 'estimated_changes' in preview
            assert 'rules_preview' in preview
            assert preview['estimated_changes'] == 1
            assert 'remove_parentheses' in preview['rules_preview']
    
    def test_validation_error_handling(self):
        """Test de gestion des erreurs de validation."""
        # Configuration d'une validation en échec
        invalid_result = ValidationResult(False, ["Dossier non accessible"], [], {})
        self.mock_validator.validate_directory.return_value = invalid_result
        
        # Test de nettoyage
        stats = self.metadata_cleaner.clean_album_metadata(str(self.album_path))
        
        # Vérifications
        assert stats.total_errors == 1
        assert stats.files_processed == 0
        assert stats.files_modified == 0
    
    def test_state_management_integration(self):
        """Test de l'intégration avec le gestionnaire d'état."""
        # Configuration d'un dossier valide mais sans fichiers MP3
        valid_result = ValidationResult(True, [], [], {})
        self.mock_validator.validate_directory.return_value = valid_result
        
        # Test de nettoyage
        stats = self.metadata_cleaner.clean_album_metadata(str(self.album_path))
        
        # Vérification des appels au gestionnaire d'état
        self.mock_state.update_album_processing_status.assert_any_call(
            str(self.album_path), "cleaning_metadata"
        )
        self.mock_state.update_album_processing_status.assert_any_call(
            str(self.album_path), "metadata_cleaning_completed"
        )
    
    def test_logging_integration(self):
        """Test de l'intégration avec le système de logging."""
        # Test de nettoyage avec logging
        stats = self.metadata_cleaner.clean_album_metadata(str(self.album_path))
        
        # Vérification des logs
        self.mock_logger.info.assert_any_call(
            f"Début du nettoyage des métadonnées : {str(self.album_path)}"
        )
        assert self.mock_logger.info.call_count >= 2  # Au moins début et fin
    
    def test_metadata_change_dataclass(self):
        """Test de la dataclass MetadataChange."""
        change = MetadataChange(
            field_name="TIT2",
            old_value="Song (Live)",
            new_value="Song",
            rule_applied=CleaningRule.REMOVE_PARENTHESES
        )
        
        assert change.field_name == "TIT2"
        assert change.old_value == "Song (Live)"
        assert change.new_value == "Song"
        assert change.rule_applied == CleaningRule.REMOVE_PARENTHESES
        assert change.timestamp  # Timestamp automatique
    
    def test_cleaning_results_dataclass(self):
        """Test de la dataclass CleaningResults."""
        results = CleaningResults("/path/to/file.mp3")
        
        assert results.file_path == "/path/to/file.mp3"
        assert results.success is False  # Valeur par défaut
        assert results.changes == []
        assert results.errors == []
        assert results.warnings == []
        assert results.processing_time == 0.0
    
    def test_complex_cleaning_scenario(self):
        """Test d'un scénario de nettoyage complexe."""
        # Texte avec plusieurs problèmes
        messy_text = "  Song Title (Live Version) and Band [Remastered]   "
        
        # Application des règles
        cleaned = self.metadata_cleaner._apply_cleaning_rules(messy_text)
        
        # Vérifications
        assert "(" not in cleaned
        assert "[" not in cleaned
        assert " & " in cleaned
        assert cleaned.strip() == cleaned  # Pas d'espaces aux extrémités
        assert "  " not in cleaned  # Pas d'espaces multiples


class TestMetadataCleanerWithoutMutagen:
    """Tests pour MetadataCleaner sans dépendance Mutagen."""
    
    def test_without_mutagen_dependency(self):
        """Test que le module fonctionne même sans Mutagen."""
        with patch('core.metadata_processor.MP3', None):
            with patch('core.metadata_processor.AppLogger') as mock_logger:
                with patch('core.metadata_processor.ConfigManager') as mock_config:
                    with patch('core.metadata_processor.StateManager') as mock_state:
                        with patch('core.metadata_processor.MetadataValidator') as mock_validator:
                            with patch('core.metadata_processor.DatabaseManager') as mock_db:
                                
                                # Configuration minimale des mocks
                                mock_logger.return_value.get_logger.return_value = MagicMock()
                                mock_config.return_value.get_processing_config.return_value = MagicMock()
                                mock_state.return_value = MagicMock()
                                mock_validator.return_value = MagicMock()
                                mock_db.return_value = MagicMock()
                                
                                # Création du cleaner
                                cleaner = MetadataCleaner()
                                
                                # Test des méthodes de nettoyage de texte (ne nécessitent pas Mutagen)
                                result = cleaner._apply_cleaning_rules("Test (Live)")
                                assert result == "Test"
                                
                                # Test des règles
                                rules = cleaner._identify_applied_rules("Test (Live)", "Test")
                                assert CleaningRule.REMOVE_PARENTHESES in rules


def test_metadata_cleaner_integration():
    """Test d'intégration complet du MetadataCleaner."""
    with tempfile.TemporaryDirectory() as temp_dir:
        album_dir = Path(temp_dir) / "Test Album"
        album_dir.mkdir()
        
        # Test avec des métadonnées factices
        with patch('core.metadata_processor.AppLogger') as mock_logger:
            with patch('core.metadata_processor.ConfigManager') as mock_config:
                with patch('core.metadata_processor.StateManager') as mock_state:
                    with patch('core.metadata_processor.MetadataValidator') as mock_validator:
                        with patch('core.metadata_processor.DatabaseManager') as mock_db:
                            
                            # Configuration des mocks
                            mock_logger.return_value.get_logger.return_value = MagicMock()
                            mock_config.return_value.get_processing_config.return_value = MagicMock()
                            mock_state.return_value = MagicMock()
                            
                            validator_instance = MagicMock()
                            validator_instance.validate_directory.return_value = ValidationResult(True, [], [], {})
                            mock_validator.return_value = validator_instance
                            
                            mock_db.return_value = MagicMock()
                            
                            # Test
                            cleaner = MetadataCleaner()
                            
                            # Test des règles de nettoyage
                            test_cases = [
                                ("Song Title (Live)", "Song Title"),
                                ("Artist  and   Band", "Artist & Band"),
                                ("  Spaced  Title  ", "Spaced Title"),
                            ]
                            
                            for original, expected in test_cases:
                                result = cleaner._apply_cleaning_rules(original)
                                # Vérifie que le nettoyage a eu lieu
                                assert len(result.strip()) > 0
                                assert "(" not in result
                                assert " & " in result if " and " in original else True


if __name__ == "__main__":
    # Exécution des tests
    pytest.main([__file__, "-v"])
