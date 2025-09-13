#!/usr/bin/env python3
"""
Tests pour le Module 4 - MetadataFormatter
Tests du système de formatage des métadonnées MP3
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import du module à tester
from core.metadata_formatter import (
    MetadataFormatter, FormattingRule, FormattingResult, 
    AlbumFormattingResult
)


class TestMetadataFormatter:
    """Tests pour la classe MetadataFormatter."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        # Patch des modules de support pour éviter les dépendances réelles
        self.mock_logger = Mock()
        self.mock_config = Mock()
        self.mock_state = Mock()
        self.mock_validator = Mock()
        self.mock_db = Mock()
        
        # Configuration des mocks avec return_value appropriés
        with patch('core.metadata_formatter.AppLogger') as mock_logger_class:
            with patch('core.metadata_formatter.ConfigManager') as mock_config_class:
                with patch('core.metadata_formatter.StateManager') as mock_state_class:
                    with patch('core.metadata_formatter.MetadataValidator') as mock_validator_class:
                        with patch('core.metadata_formatter.DatabaseManager') as mock_db_class:
                            
                            # Configuration des retours de mock
                            mock_logger_class.return_value.get_logger.return_value = self.mock_logger
                            mock_config_class.return_value = self.mock_config
                            mock_state_class.return_value = self.mock_state
                            mock_validator_class.return_value = self.mock_validator
                            mock_db_class.return_value = self.mock_db
                            
                            self.mock_config.get_processing_config.return_value = {}
                            
                            # Création du MetadataFormatter
                            self.formatter = MetadataFormatter()
    
    def test_initialization(self):
        """Teste l'initialisation du MetadataFormatter."""
        assert self.formatter is not None
        assert hasattr(self.formatter, 'logger')
        assert hasattr(self.formatter, 'config_manager')
        assert hasattr(self.formatter, 'state_manager')
        assert hasattr(self.formatter, 'validator')
        assert hasattr(self.formatter, 'db_manager')
        
        # Vérification des configurations
        assert len(self.formatter.standard_genres) > 0
        assert isinstance(self.formatter.formatting_config, dict)
    
    def test_format_track_number_basic(self):
        """Teste le formatage de base des numéros de piste."""
        test_cases = [
            ("1", "01"),
            ("5", "05"),
            ("10", "10"),
            ("01", "01"),  # Déjà formaté
            ("1/12", "01/12"),  # Avec total
            ("5/20", "05/20"),
        ]
        
        for input_track, expected in test_cases:
            formatted, rules = self.formatter._format_track_number(input_track)
            assert formatted == expected
            if input_track != expected:
                assert FormattingRule.FORMAT_TRACK_NUMBERS in rules
    
    def test_format_track_number_edge_cases(self):
        """Teste les cas limites pour le formatage des numéros de piste."""
        test_cases = [
            ("", ""),  # Vide
            (None, None),  # None
            ("abc", "abc"),  # Non numérique
            ("0", "00"),  # Zéro
            ("99", "99"),  # Nombre élevé
        ]
        
        for input_track, expected in test_cases:
            formatted, rules = self.formatter._format_track_number(input_track)
            assert formatted == expected
    
    def test_copy_artist_to_albumartist(self):
        """Teste la copie artiste vers interprète."""
        test_cases = [
            # (albumartist_actuel, artiste_source, résultat_attendu, changement_attendu)
            ("", "John Doe", "John Doe", True),
            (None, "Jane Smith", "Jane Smith", True),
            ("  ", "Artist Name", "Artist Name", True),
            ("Existing Artist", "Source Artist", "Existing Artist", False),
            ("", "", "", False),
            ("", None, "", False),
        ]
        
        for albumartist, artist, expected, should_change in test_cases:
            result, rules = self.formatter._copy_artist_to_albumartist(albumartist, artist)
            assert result == expected
            if should_change:
                assert FormattingRule.COPY_ARTIST_TO_ALBUMARTIST in rules
            else:
                assert FormattingRule.COPY_ARTIST_TO_ALBUMARTIST not in rules
    
    def test_handle_compilation_year(self):
        """Teste la gestion des années de compilation."""
        test_cases = [
            ("2023", "2023", [], 0),  # Année simple
            ("1995-2000", "1995-2000", [FormattingRule.HANDLE_COMPILATION_YEAR], 1),  # Déjà formaté
            ("1995, 1996, 2000", "1995-2000", [FormattingRule.HANDLE_COMPILATION_YEAR], 1),  # Multiple
            ("", "", [], 0),  # Vide
            ("abc", "abc", [], 1),  # Non numérique - warning
            ("1800", "1800", [], 1),  # Année suspecte - warning
        ]
        
        for input_year, expected_year, expected_rules, expected_warnings in test_cases:
            result, rules, warnings = self.formatter._handle_compilation_year(input_year, {})
            assert result == expected_year
            assert rules == expected_rules
            assert len(warnings) == expected_warnings
    
    def test_normalize_genre(self):
        """Teste la normalisation des genres."""
        test_cases = [
            ("Rock", "Rock"),
            ("(13)", "Pop"),  # Genre numérique ID3v1
            ("rock", "Rock"),
            ("  electronic  ", "Electronic"),
            ("pop/rock", "Pop/Rock"),
            ("", ""),
        ]
        
        for input_genre, expected in test_cases:
            result, rules = self.formatter._normalize_genre(input_genre)
            assert result == expected
            if input_genre != expected and expected:
                assert FormattingRule.NORMALIZE_GENRE in rules
    
    def test_format_duration(self):
        """Teste le formatage de la durée."""
        test_cases = [
            ("180000", "180000"),  # 3 minutes en ms
            ("0", "0"),
            ("-1", None),  # Durée invalide
            ("abc", "abc"),  # Non numérique
            ("", ""),  # Vide
        ]
        
        for input_duration, expected in test_cases:
            result, rules = self.formatter._format_duration(input_duration)
            assert result == expected
            if result is None:
                assert FormattingRule.FORMAT_DURATION in rules
    
    def test_validate_required_field(self):
        """Teste la validation des champs requis."""
        # Configuration des champs requis
        self.formatter.formatting_config['required_fields'] = ['TIT2', 'TPE1']
        
        test_cases = [
            ("TIT2", "Song Title", [], 0),  # Champ requis valide
            ("TIT2", "", [FormattingRule.VALIDATE_REQUIRED_FIELDS], 1),  # Champ requis vide
            ("TIT2", "   ", [FormattingRule.VALIDATE_REQUIRED_FIELDS], 1),  # Champ requis espaces
            ("TCON", "", [], 0),  # Champ non requis vide
        ]
        
        for field_name, field_value, expected_rules, expected_warnings in test_cases:
            rules, warnings = self.formatter._validate_required_field(field_name, field_value)
            assert rules == expected_rules
            assert len(warnings) == expected_warnings
    
    def test_format_metadata_field_track_number(self):
        """Teste le formatage complet d'un champ numéro de piste."""
        result = self.formatter.format_metadata_field("TRCK", "5", {})
        
        assert result.field_name == "TRCK"
        assert result.original_value == "5"
        assert result.formatted_value == "05"
        assert result.changed is True
        assert FormattingRule.FORMAT_TRACK_NUMBERS in result.rules_applied
    
    def test_format_metadata_field_albumartist(self):
        """Teste le formatage complet d'un champ interprète."""
        metadata_context = {"TPE1": "John Doe"}
        result = self.formatter.format_metadata_field("TPE2", "", metadata_context)
        
        assert result.field_name == "TPE2"
        assert result.original_value == ""
        assert result.formatted_value == "John Doe"
        assert result.changed is True
        assert FormattingRule.COPY_ARTIST_TO_ALBUMARTIST in result.rules_applied
    
    def test_format_metadata_field_year(self):
        """Teste le formatage complet d'un champ année."""
        result = self.formatter.format_metadata_field("TYER", "1995, 2000", {})
        
        assert result.field_name == "TYER"
        assert result.original_value == "1995, 2000"
        assert result.formatted_value == "1995-2000"
        assert result.changed is True
        assert FormattingRule.HANDLE_COMPILATION_YEAR in result.rules_applied
        assert result.warnings is not None
    
    def test_format_metadata_field_genre(self):
        """Teste le formatage complet d'un champ genre."""
        result = self.formatter.format_metadata_field("TCON", "(13)", {})
        
        assert result.field_name == "TCON"
        assert result.original_value == "(13)"
        assert result.formatted_value == "Pop"
        assert result.changed is True
        assert FormattingRule.NORMALIZE_GENRE in result.rules_applied
    
    def test_format_metadata_field_no_change(self):
        """Teste le formatage d'un champ qui ne change pas."""
        result = self.formatter.format_metadata_field("TIT2", "Song Title", {})
        
        assert result.field_name == "TIT2"
        assert result.original_value == "Song Title"
        assert result.formatted_value == "Song Title"
        assert result.changed is False
        assert len(result.rules_applied) == 0
    
    def test_is_required_field(self):
        """Teste la détermination des champs requis."""
        # Configuration des champs requis
        self.formatter.formatting_config['required_fields'] = ['TIT2', 'TPE1', 'TALB', 'TRCK']
        
        assert self.formatter._is_required_field('TIT2') is True
        assert self.formatter._is_required_field('TPE1') is True
        assert self.formatter._is_required_field('TCON') is False
        assert self.formatter._is_required_field('UNKNOWN') is False
    
    def test_find_mp3_files(self):
        """Teste la recherche de fichiers MP3."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)
            
            # Création de fichiers de test
            (test_dir / "song1.mp3").write_text("fake mp3")
            (test_dir / "song2.mp3").write_text("fake mp3")
            (test_dir / "not_music.txt").write_text("text file")
            (test_dir / "cover.jpg").write_text("image file")
            
            mp3_files = self.formatter._find_mp3_files(str(test_dir))
            
            assert len(mp3_files) == 2
            assert all(file.endswith('.mp3') for file in mp3_files)
            assert str(test_dir / "song1.mp3") in mp3_files
            assert str(test_dir / "song2.mp3") in mp3_files
    
    def test_extract_album_info(self):
        """Teste l'extraction des informations d'album."""
        mp3_files = ["/path/to/song1.mp3", "/path/to/song2.mp3", "/path/to/song3.mp3"]
        album_info = self.formatter._extract_album_info(mp3_files)
        
        assert isinstance(album_info, dict)
        assert 'total_tracks' in album_info
        assert album_info['total_tracks'] == 3
        assert 'artist' in album_info
        assert 'album' in album_info
    
    def test_build_standard_genres(self):
        """Teste la construction de la liste des genres standards."""
        genres = self.formatter._build_standard_genres()
        
        assert isinstance(genres, list)
        assert len(genres) > 50  # Beaucoup de genres
        assert "Rock" in genres
        assert "Pop" in genres
        assert "Jazz" in genres
        assert "Classical" in genres
    
    def test_load_formatting_config(self):
        """Teste le chargement de la configuration de formatage."""
        config = self.formatter._load_formatting_config()
        
        assert isinstance(config, dict)
        assert 'track_zero_padding' in config
        assert 'required_fields' in config
        assert 'copy_artist_to_albumartist' in config
        assert isinstance(config['required_fields'], list)
    
    def test_preview_formatting_changes(self):
        """Teste l'aperçu des changements de formatage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            album_path = Path(temp_dir) / "test_album"
            album_path.mkdir()
            
            # Création de fichiers MP3 de test
            (album_path / "01 - song.mp3").write_text("fake mp3")
            (album_path / "02 - another.mp3").write_text("fake mp3")
            
            preview = self.formatter.preview_formatting_changes(str(album_path))
            
            assert isinstance(preview, dict)
            # Le preview devrait contenir des changements pour les fichiers de test
    
    def test_format_album_metadata_integration(self):
        """Teste le formatage complet d'un album (test d'intégration)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            album_path = Path(temp_dir) / "test_album"
            album_path.mkdir()
            
            # Création de fichiers MP3 de test
            (album_path / "01 - song.mp3").write_text("fake mp3")
            (album_path / "02 - another.mp3").write_text("fake mp3")
            
            # Configuration des mocks
            from support.validator import ValidationResult
            self.mock_validator.validate_directory.return_value = ValidationResult(True, [], [], {})
            self.mock_validator.validate_mp3_file.return_value = ValidationResult(True, [], [], {})
            
            # Test de formatage d'album
            result = self.formatter.format_album_metadata(str(album_path))
            
            # Vérifications
            assert isinstance(result, AlbumFormattingResult)
            assert result.album_path == str(album_path)
            assert result.files_processed >= 0
            assert result.processing_time >= 0
            
            # Le mock devrait avoir été appelé pour la mise à jour du statut
            self.mock_state.update_status.assert_called()
    
    def test_create_error_result(self):
        """Teste la création d'un résultat d'erreur."""
        errors = ["Erreur test 1", "Erreur test 2"]
        result = self.formatter._create_error_result("/path/to/album", errors)
        
        assert isinstance(result, AlbumFormattingResult)
        assert result.album_path == "/path/to/album"
        assert result.files_processed == 0
        assert result.total_changes == 0
        assert result.errors == errors
        assert result.processing_time == 0.0
    
    def test_create_empty_result(self):
        """Teste la création d'un résultat vide."""
        result = self.formatter._create_empty_result("/path/to/album")
        
        assert isinstance(result, AlbumFormattingResult)
        assert result.album_path == "/path/to/album"
        assert result.files_processed == 0
        assert result.total_changes == 0
        assert len(result.warnings) > 0
        assert "Aucun fichier MP3 trouvé" in result.warnings[0]
    
    def test_formatting_result_dataclass(self):
        """Teste la dataclass FormattingResult."""
        result = FormattingResult(
            original_value="1",
            formatted_value="01",
            field_name="TRCK",
            rules_applied=[FormattingRule.FORMAT_TRACK_NUMBERS],
            changed=True,
            warnings=["Test warning"]
        )
        
        assert result.original_value == "1"
        assert result.formatted_value == "01"
        assert result.field_name == "TRCK"
        assert len(result.rules_applied) == 1
        assert result.changed is True
        assert result.warnings == ["Test warning"]
    
    def test_album_formatting_result_dataclass(self):
        """Teste la dataclass AlbumFormattingResult."""
        result = AlbumFormattingResult(
            album_path="/path/to/album",
            files_processed=5,
            total_changes=10,
            field_changes={"TRCK": 5, "TPE2": 3},
            warnings=["Warning 1"],
            errors=["Error 1"],
            processing_time=1.5
        )
        
        assert result.album_path == "/path/to/album"
        assert result.files_processed == 5
        assert result.total_changes == 10
        assert result.field_changes["TRCK"] == 5
        assert len(result.warnings) == 1
        assert len(result.errors) == 1
        assert result.processing_time == 1.5
    
    def test_formatting_rules_enum(self):
        """Teste l'énumération FormattingRule."""
        # Vérification que toutes les règles attendues existent
        expected_rules = [
            "copy_artist_to_albumartist",
            "format_track_numbers", 
            "handle_compilation_year",
            "normalize_genre",
            "format_duration",
            "validate_required_fields"
        ]
        
        for rule_value in expected_rules:
            # Vérification que la règle existe
            rule_found = any(rule.value == rule_value for rule in FormattingRule)
            assert rule_found, f"Règle manquante : {rule_value}"


if __name__ == "__main__":
    # Exécution des tests si le script est lancé directement
    pytest.main([__file__, "-v"])
