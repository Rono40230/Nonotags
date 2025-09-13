#!/usr/bin/env python3
"""
Tests pour le Module 3 - CaseCorrector
Tests du système de correction de la casse des métadonnées MP3
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import du module à tester
from core.case_corrector import CaseCorrector, CaseCorrectionRule, CaseException, CaseCorrectionResult


class TestCaseCorrector:
    """Tests pour la classe CaseCorrector."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        # Patch des modules de support pour éviter les dépendances réelles
        self.mock_logger = Mock()
        self.mock_config = Mock()
        self.mock_state = Mock()
        self.mock_validator = Mock()
        self.mock_db = Mock()
        
        # Configuration des mocks avec return_value appropriés
        with patch('core.case_corrector.AppLogger') as mock_logger_class:
            with patch('core.case_corrector.ConfigManager') as mock_config_class:
                with patch('core.case_corrector.StateManager') as mock_state_class:
                    with patch('core.case_corrector.MetadataValidator') as mock_validator_class:
                        with patch('core.case_corrector.DatabaseManager') as mock_db_class:
                            
                            # Configuration des retours de mock
                            mock_logger_class.return_value.get_logger.return_value = self.mock_logger
                            mock_config_class.return_value = self.mock_config
                            mock_state_class.return_value = self.mock_state
                            mock_validator_class.return_value = self.mock_validator
                            mock_db_class.return_value = self.mock_db
                            
                            self.mock_config.get_processing_config.return_value = {}
                            self.mock_db.get_case_exceptions.return_value = []
                            
                            # Création du CaseCorrector
                            self.corrector = CaseCorrector()
    
    def test_initialization(self):
        """Teste l'initialisation du CaseCorrector."""
        assert self.corrector is not None
        assert hasattr(self.corrector, 'logger')
        assert hasattr(self.corrector, 'config_manager')
        assert hasattr(self.corrector, 'state_manager')
        assert hasattr(self.corrector, 'validator')
        assert hasattr(self.corrector, 'db_manager')
        
        # Vérification des ensembles de règles
        assert len(self.corrector.roman_numerals) > 0
        assert len(self.corrector.prepositions) > 0
        assert len(self.corrector.abbreviations) > 0
    
    def test_correct_text_case_basic_title_case(self):
        """Teste la correction de casse de base (Title Case)."""
        test_cases = [
            ("hello world", "Hello World"),
            ("song title", "Song Title"),
            ("THE GREAT SONG", "The Great Song"),
            ("song and band", "Song and Band"),  # "and" est une préposition
            ("album et version", "Album et Version"),  # "et" est une préposition
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.corrected == expected
            assert CaseCorrectionRule.TITLE_CASE in result.rules_applied
            assert result.changed == (input_text != expected)
    
    def test_protect_roman_numerals(self):
        """Teste la protection des chiffres romains."""
        test_cases = [
            ("album ii", "Album II"),
            ("part iii of the story", "Part III of the Story"),
            ("world war ii", "World War II"),
            ("star wars episode iv", "Star Wars Episode IV"),
            ("chapter v", "Chapter V"),
            ("volume x", "Volume X"),
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.corrected == expected
            assert CaseCorrectionRule.PROTECT_ROMAN_NUMERALS in result.rules_applied
    
    def test_protect_single_i(self):
        """Teste la protection du 'I' isolé."""
        test_cases = [
            ("i love music", "I Love Music"),
            ("when i was young", "When I Was Young"),
            ("i and you", "I and You"),  # "and" est une préposition
            ("music i like", "Music I Like"),
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.corrected == expected
            assert CaseCorrectionRule.PROTECT_SINGLE_I in result.rules_applied
    
    def test_handle_prepositions(self):
        """Teste la gestion des prépositions."""
        test_cases = [
            ("song of the year", "Song of the Year"),
            ("music in the air", "Music in the Air"),
            ("band and the music", "Band and the Music"),
            ("up on the roof", "Up on the Roof"),
            ("chanson de la vie", "Chanson de la Vie"),
            ("musique dans le vent", "Musique dans le Vent"),
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.corrected == expected
            assert CaseCorrectionRule.HANDLE_PREPOSITIONS in result.rules_applied
    
    def test_protect_abbreviations(self):
        """Teste la protection des abréviations."""
        test_cases = [
            ("dj set", "DJ Set"),
            ("live on bbc", "Live on BBC"),
            ("music from usa", "Music from USA"),
            ("tv show theme", "TV Show Theme"),
            ("nyc nights", "NYC Nights"),
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.corrected == expected
            assert CaseCorrectionRule.PROTECT_ABBREVIATIONS in result.rules_applied
    
    def test_protect_artist_in_album(self):
        """Teste la protection du nom d'artiste dans le titre d'album."""
        artist_name = "John Doe"
        test_cases = [
            ("the best of john doe", "The Best of John Doe"),
            ("john doe greatest hits", "John Doe Greatest Hits"),
            ("JOHN DOE live album", "John Doe Live Album"),
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "album", artist_name)
            assert result.corrected == expected
            assert CaseCorrectionRule.PROTECT_ARTIST_IN_ALBUM in result.rules_applied
    
    def test_complex_case_correction(self):
        """Teste la correction de casse avec règles multiples."""
        test_cases = [
            {
                'input': "the best of john smith vol. ii",
                'artist': "John Smith",
                'expected': "The Best of John Smith Vol. II",
                'expected_rules': [
                    CaseCorrectionRule.TITLE_CASE,
                    CaseCorrectionRule.PROTECT_ROMAN_NUMERALS,
                    CaseCorrectionRule.PROTECT_SINGLE_I,
                    CaseCorrectionRule.HANDLE_PREPOSITIONS,
                    CaseCorrectionRule.PROTECT_ABBREVIATIONS,
                    CaseCorrectionRule.PROTECT_ARTIST_IN_ALBUM
                ]
            },
            {
                'input': "i love music and bands from usa",
                'artist': None,
                'expected': "I Love Music and Bands from USA",
                'expected_rules': [
                    CaseCorrectionRule.TITLE_CASE,
                    CaseCorrectionRule.PROTECT_SINGLE_I,
                    CaseCorrectionRule.HANDLE_PREPOSITIONS,
                    CaseCorrectionRule.PROTECT_ABBREVIATIONS
                ]
            }
        ]
        
        for test_case in test_cases:
            result = self.corrector.correct_text_case(
                test_case['input'], 
                "album", 
                test_case['artist']
            )
            assert result.corrected == test_case['expected']
            # Vérifier que les règles importantes sont appliquées
            for rule in test_case['expected_rules']:
                if rule != CaseCorrectionRule.PROTECT_ARTIST_IN_ALBUM or test_case['artist']:
                    assert rule in result.rules_applied
    
    def test_case_exceptions_handling(self):
        """Teste la gestion des exceptions de casse personnalisées."""
        # Configuration d'exceptions de test
        test_exceptions = [
            CaseException("iphone", "iPhone", "custom", False),  # Insensible à la casse
            CaseException("mccartney", "McCartney", "custom", False),  # Insensible à la casse
            CaseException("paris", "Paris", "city", False),
        ]
        
        # Configuration du mock pour retourner des exceptions
        self.corrector.case_exceptions = test_exceptions
        
        test_cases = [
            ("iphone music", "iPhone Music"),
            ("mccartney songs", "McCartney Songs"),
            ("PARIS nights", "Paris Nights"),
        ]
        
        for input_text, expected in test_cases:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.corrected == expected
            assert len(result.exceptions_used) > 0
    
    def test_empty_and_none_inputs(self):
        """Teste la gestion des entrées vides ou None."""
        test_inputs = ["", "   ", None]
        
        for input_text in test_inputs:
            result = self.corrector.correct_text_case(input_text, "title")
            assert result.original == input_text
            assert result.corrected == input_text
            assert not result.changed
            assert len(result.rules_applied) == 0
    
    def test_preview_case_corrections(self):
        """Teste l'aperçu des corrections de casse."""
        # Création d'un répertoire temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            album_path = Path(temp_dir) / "Test Album"
            album_path.mkdir()
            
            # Création de fichiers MP3 factices
            (album_path / "01 - test song.mp3").write_text("fake mp3")
            (album_path / "02 - another song.mp3").write_text("fake mp3")
            
            # Configuration des mocks
            from support.validator import ValidationResult
            self.mock_validator.validate_directory.return_value = ValidationResult(True, [], [], {})
            
            # Test de l'aperçu
            preview = self.corrector.preview_case_corrections(str(album_path), "Test Artist")
            
            # Vérifications
            assert isinstance(preview, dict)
            # En mode test, l'aperçu devrait contenir des corrections simulées
    
    def test_add_case_exception(self):
        """Teste l'ajout d'exceptions de casse."""
        # Configuration du mock pour simuler un ajout réussi
        self.mock_db.add_case_exception.return_value = True
        self.mock_db.get_case_exceptions.return_value = [
            {'original': 'test', 'corrected': 'TEST', 'type': 'custom', 'case_sensitive': True}
        ]
        
        # Test d'ajout d'exception
        result = self.corrector.add_case_exception("test", "TEST", "custom")
        assert result is True
        
        # Vérification que la méthode de la base a été appelée
        self.mock_db.add_case_exception.assert_called_once_with("test", "TEST", "custom")
    
    def test_add_case_exception_invalid_input(self):
        """Teste l'ajout d'exceptions avec des entrées invalides."""
        invalid_cases = [
            ("", "TEST"),
            ("test", ""),
            (None, "TEST"),
            ("test", None),
        ]
        
        for original, corrected in invalid_cases:
            result = self.corrector.add_case_exception(original, corrected)
            assert result is False
    
    def test_roman_numerals_set(self):
        """Teste l'ensemble des chiffres romains."""
        roman_numerals = self.corrector.roman_numerals
        
        # Vérification de quelques chiffres romains importants
        expected_romans = ['I', 'II', 'III', 'IV', 'V', 'X', 'XX', 'L', 'C', 'M']
        for roman in expected_romans:
            assert roman in roman_numerals
    
    def test_prepositions_set(self):
        """Teste l'ensemble des prépositions."""
        prepositions = self.corrector.prepositions
        
        # Vérification de quelques prépositions importantes
        expected_prepositions = ['the', 'and', 'of', 'in', 'on', 'with', 'for', 'et', 'de', 'dans']
        for prep in expected_prepositions:
            assert prep in prepositions
    
    def test_abbreviations_set(self):
        """Teste l'ensemble des abréviations."""
        abbreviations = self.corrector.abbreviations
        
        # Vérification de quelques abréviations importantes
        expected_abbrevs = ['USA', 'UK', 'DJ', 'TV', 'BBC', 'NYC', 'LA']
        for abbrev in expected_abbrevs:
            assert abbrev in abbreviations
    
    def test_get_text_type_from_field(self):
        """Teste la détermination du type de texte selon le champ."""
        test_cases = [
            ('TIT2', 'title'),    # Titre
            ('TALB', 'album'),    # Album
            ('TPE1', 'artist'),   # Artiste
            ('TPE2', 'artist'),   # Artiste de l'album
            ('UNKNOWN', 'title'), # Champ inconnu → titre par défaut
        ]
        
        for field_name, expected_type in test_cases:
            result = self.corrector._get_text_type_from_field(field_name)
            assert result == expected_type
    
    def test_case_correction_result_dataclass(self):
        """Teste la dataclass CaseCorrectionResult."""
        result = CaseCorrectionResult(
            original="test input",
            corrected="Test Input",
            rules_applied=[CaseCorrectionRule.TITLE_CASE],
            exceptions_used=[],
            changed=True
        )
        
        assert result.original == "test input"
        assert result.corrected == "Test Input"
        assert len(result.rules_applied) == 1
        assert result.rules_applied[0] == CaseCorrectionRule.TITLE_CASE
        assert result.changed is True
    
    def test_case_exception_dataclass(self):
        """Teste la dataclass CaseException."""
        exception = CaseException(
            original="iphone",
            corrected="iPhone",
            type="custom",
            case_sensitive=True
        )
        
        assert exception.original == "iphone"
        assert exception.corrected == "iPhone"
        assert exception.type == "custom"
        assert exception.case_sensitive is True
    
    def test_find_mp3_files(self):
        """Teste la recherche de fichiers MP3."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            
            # Création de fichiers de test
            (test_dir / "song1.mp3").write_text("fake mp3")
            (test_dir / "song2.mp3").write_text("fake mp3")
            (test_dir / "not_music.txt").write_text("text file")
            (test_dir / "cover.jpg").write_text("image file")
            
            mp3_files = self.corrector._find_mp3_files(str(test_dir))
            
            assert len(mp3_files) == 2
            assert all(file.endswith('.mp3') for file in mp3_files)
            assert str(test_dir / "song1.mp3") in mp3_files
            assert str(test_dir / "song2.mp3") in mp3_files
    
    def test_correct_album_case_integration(self):
        """Teste la correction complète d'un album (test d'intégration)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            album_path = Path(temp_dir) / "test album"
            album_path.mkdir()
            
            # Création de fichiers MP3 de test
            (album_path / "01 - song title.mp3").write_text("fake mp3")
            (album_path / "02 - another song.mp3").write_text("fake mp3")
            
            # Configuration des mocks
            from support.validator import ValidationResult
            self.mock_validator.validate_directory.return_value = ValidationResult(True, [], [], {})
            self.mock_validator.validate_mp3_file.return_value = ValidationResult(True, [], [], {})
            
            # Test de correction d'album
            results = self.corrector.correct_album_case(str(album_path), "Test Artist")
            
            # Vérifications
            assert isinstance(results, dict)
            # Le mock devrait avoir été appelé pour la mise à jour du statut
            self.mock_state.update_status.assert_called()


if __name__ == "__main__":
    # Exécution des tests si le script est lancé directement
    pytest.main([__file__, "-v"])
