"""
Tests unitaires pour le Module 5 - FileRenamer
Tests du renommage des fichiers et dossiers MP3
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.file_renamer import FileRenamer, RenamingRule, RenamingResult, AlbumRenamingResult
from support.validator import ValidationResult


class TestFileRenamer(unittest.TestCase):
    """Tests pour le module FileRenamer."""
    
    def setUp(self):
        """Configuration des tests."""
        # Création d'un dossier temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        
        # Configuration des mocks
        with patch('core.file_renamer.AppLogger') as mock_logger:
            with patch('core.file_renamer.ConfigManager') as mock_config:
                with patch('core.file_renamer.StateManager') as mock_state:
                    with patch('core.file_renamer.MetadataValidator') as mock_validator:
                        with patch('core.file_renamer.DatabaseManager') as mock_db:
                            
                            # Configuration minimale des mocks
                            mock_logger.return_value.get_logger.return_value = MagicMock()
                            mock_config.return_value.get_processing_config.return_value = {}
                            mock_state.return_value = MagicMock()
                            mock_validator.return_value = MagicMock()
                            mock_db.return_value = MagicMock()
                            
                            self.renamer = FileRenamer()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_sanitize_filename_basic(self):
        """Test du nettoyage basique des noms de fichiers."""
        # Test des caractères interdits
        result, rules = self.renamer.sanitize_filename('Test<>:"/\\|?*Song')
        self.assertEqual(result, "Test()-'---Song")
        self.assertIn(RenamingRule.SANITIZE_FILENAME, rules)
        
        # Test des espaces multiples
        result, rules = self.renamer.sanitize_filename('Song   Title    Here')
        self.assertEqual(result, "Song Title Here")
        self.assertIn(RenamingRule.SANITIZE_FILENAME, rules)
        
        # Test sans changement nécessaire
        result, rules = self.renamer.sanitize_filename('Normal Song Title')
        self.assertEqual(result, "Normal Song Title")
        self.assertEqual(rules, [])
    
    def test_sanitize_filename_length_limit(self):
        """Test de la limitation de longueur des noms de fichiers."""
        long_name = "A" * 250
        result, rules = self.renamer.sanitize_filename(long_name)
        self.assertTrue(len(result) <= 200)
        self.assertIn(RenamingRule.SANITIZE_FILENAME, rules)
    
    def test_format_track_filename_basic(self):
        """Test du formatage basique des noms de fichiers de piste."""
        # Test avec numéro simple
        result, rules = self.renamer.format_track_filename("1", "Song Title", ".mp3")
        self.assertEqual(result, "(01) - Song Title.mp3")
        self.assertIn(RenamingRule.FORMAT_TRACK_FILENAME, rules)
        self.assertIn(RenamingRule.PRESERVE_EXTENSION, rules)
        
        # Test avec numéro déjà formaté
        result, rules = self.renamer.format_track_filename("05", "Another Song", ".mp3")
        self.assertEqual(result, "(05) - Another Song.mp3")
        
        # Test avec numéro à deux chiffres
        result, rules = self.renamer.format_track_filename("12", "Track Twelve", ".mp3")
        self.assertEqual(result, "(12) - Track Twelve.mp3")
    
    def test_format_track_filename_with_total(self):
        """Test du formatage avec numéro de piste incluant le total."""
        # Test avec format "5/20"
        result, rules = self.renamer.format_track_filename("5/20", "Track Five", ".mp3")
        self.assertEqual(result, "(05) - Track Five.mp3")
        self.assertIn(RenamingRule.FORMAT_TRACK_FILENAME, rules)
        
        # Test avec format "01/12"
        result, rules = self.renamer.format_track_filename("01/12", "First Track", ".mp3")
        self.assertEqual(result, "(01) - First Track.mp3")
    
    def test_format_track_filename_special_characters(self):
        """Test du formatage avec caractères spéciaux dans le titre."""
        result, rules = self.renamer.format_track_filename("3", "Song: The Title?", ".mp3")
        self.assertEqual(result, "(03) - Song- The Title.mp3")
        self.assertIn(RenamingRule.FORMAT_TRACK_FILENAME, rules)
        self.assertIn(RenamingRule.SANITIZE_FILENAME, rules)
    
    def test_format_album_folder_basic(self):
        """Test du formatage basique des noms de dossiers d'album."""
        # Test avec année simple
        result, rules = self.renamer.format_album_folder("2023", "Album Title")
        self.assertEqual(result, "(2023) Album Title")
        self.assertIn(RenamingRule.FORMAT_ALBUM_FOLDER, rules)
        
        # Test sans année
        result, rules = self.renamer.format_album_folder("", "Album Title")
        self.assertEqual(result, "Album Title")
        self.assertIn(RenamingRule.FORMAT_ALBUM_FOLDER, rules)
    
    def test_format_album_folder_multi_year(self):
        """Test du formatage avec années multiples (compilations)."""
        # Test avec plage déjà formatée
        result, rules = self.renamer.format_album_folder("1995-2000", "Best Of Collection")
        self.assertEqual(result, "(1995-2000) Best Of Collection")
        self.assertIn(RenamingRule.HANDLE_MULTI_YEAR, rules)
        
        # Test avec années multiples à formater
        result, rules = self.renamer.format_album_folder("1995, 1996, 2000", "Greatest Hits")
        self.assertEqual(result, "(1995-2000) Greatest Hits")
        self.assertIn(RenamingRule.HANDLE_MULTI_YEAR, rules)
        
        # Test avec années non séquentielles
        result, rules = self.renamer.format_album_folder("1980, 1985, 1990, 1995", "Decades Collection")
        self.assertEqual(result, "(1980-1995) Decades Collection")
        self.assertIn(RenamingRule.HANDLE_MULTI_YEAR, rules)
    
    def test_handle_multi_year_folder_edge_cases(self):
        """Test de la gestion des cas limites pour les années multiples."""
        # Test avec une seule année
        result, rules = self.renamer._handle_multi_year_folder("2023")
        self.assertEqual(result, "2023")
        self.assertEqual(rules, [])
        
        # Test avec années invalides
        result, rules = self.renamer._handle_multi_year_folder("abc")
        self.assertEqual(result, "abc")
        self.assertEqual(rules, [])
        
        # Test avec chaîne vide
        result, rules = self.renamer._handle_multi_year_folder("")
        self.assertEqual(result, "")
        self.assertEqual(rules, [])
        
        # Test avec années hors plage acceptable
        result, rules = self.renamer._handle_multi_year_folder("1800, 2200")
        self.assertEqual(result, "1800, 2200")
        self.assertEqual(rules, [])
    
    def test_preview_file_renaming(self):
        """Test de la prévisualisation du renommage de fichiers."""
        # Création d'un fichier de test
        test_file = Path(self.test_dir) / "old_name.mp3"
        test_file.write_text("fake mp3")
        
        # Métadonnées de test
        metadata = {
            'TRCK': '5',
            'TIT2': 'Test Song'
        }
        
        # Test de prévisualisation
        result = self.renamer.preview_file_renaming(str(test_file), metadata)
        
        self.assertIsInstance(result, RenamingResult)
        self.assertEqual(result.original_path, str(test_file))
        self.assertTrue(result.new_path.endswith("(05) - Test Song.mp3"))
        self.assertTrue(result.renamed)
        self.assertIn(RenamingRule.FORMAT_TRACK_FILENAME, result.rules_applied)
        self.assertIsNone(result.error)
    
    def test_preview_folder_renaming(self):
        """Test de la prévisualisation du renommage de dossiers."""
        # Création d'un dossier de test
        test_folder = Path(self.test_dir) / "old_album_name"
        test_folder.mkdir()
        
        # Métadonnées d'album de test
        album_metadata = {
            'TYER': '2023',
            'TALB': 'Test Album'
        }
        
        # Test de prévisualisation
        result = self.renamer.preview_folder_renaming(str(test_folder), album_metadata)
        
        self.assertIsInstance(result, RenamingResult)
        self.assertEqual(result.original_path, str(test_folder))
        self.assertTrue(result.new_path.endswith("(2023) Test Album"))
        self.assertTrue(result.renamed)
        self.assertIn(RenamingRule.FORMAT_ALBUM_FOLDER, result.rules_applied)
        self.assertIsNone(result.error)
    
    def test_rename_file_actual_renaming(self):
        """Test du renommage effectif d'un fichier."""
        # Création d'un fichier de test
        test_file = Path(self.test_dir) / "original.mp3"
        test_file.write_text("fake mp3")
        
        # Métadonnées de test
        metadata = {
            'TRCK': '3',
            'TIT2': 'New Title'
        }
        
        # Test de renommage
        result = self.renamer.rename_file(str(test_file), metadata)
        
        self.assertTrue(result.renamed)
        self.assertFalse(test_file.exists())  # Ancien fichier n'existe plus
        self.assertTrue(Path(result.new_path).exists())  # Nouveau fichier existe
        self.assertTrue(result.new_path.endswith("(03) - New Title.mp3"))
        self.assertIsNone(result.error)
    
    def test_rename_file_conflict_resolution(self):
        """Test de la résolution des conflits lors du renommage."""
        # Création de deux fichiers avec des noms qui vont entrer en conflit
        test_file1 = Path(self.test_dir) / "song1.mp3"
        test_file2 = Path(self.test_dir) / "song2.mp3"
        conflict_file = Path(self.test_dir) / "(01) - Same Title.mp3"
        
        test_file1.write_text("fake mp3 1")
        test_file2.write_text("fake mp3 2")
        conflict_file.write_text("existing file")
        
        # Métadonnées identiques pour créer un conflit
        metadata = {
            'TRCK': '1',
            'TIT2': 'Same Title'
        }
        
        # Renommage du premier fichier (devrait créer un conflit)
        result = self.renamer.rename_file(str(test_file1), metadata)
        
        self.assertTrue(result.renamed)
        self.assertTrue(result.new_path.endswith("(01) - Same Title (1).mp3"))
        self.assertIn(RenamingRule.HANDLE_DUPLICATE_NAME, result.rules_applied)
        self.assertIsNone(result.error)
    
    def test_rename_folder_actual_renaming(self):
        """Test du renommage effectif d'un dossier."""
        # Création d'un dossier de test
        test_folder = Path(self.test_dir) / "original_album"
        test_folder.mkdir()
        
        # Métadonnées d'album de test
        album_metadata = {
            'TYER': '2020',
            'TALB': 'Renamed Album'
        }
        
        # Test de renommage
        result = self.renamer.rename_folder(str(test_folder), album_metadata)
        
        self.assertTrue(result.renamed)
        self.assertFalse(test_folder.exists())  # Ancien dossier n'existe plus
        self.assertTrue(Path(result.new_path).exists())  # Nouveau dossier existe
        self.assertTrue(result.new_path.endswith("(2020) Renamed Album"))
        self.assertIsNone(result.error)
    
    def test_preview_album_renaming(self):
        """Test de la prévisualisation du renommage complet d'un album."""
        # Configuration du validator existant du renamer
        self.renamer.validator.validate_directory.return_value = ValidationResult(True, [], [], {})
        
        # Validation des fichiers MP3 réussie avec métadonnées
        metadata = {
            'TRCK': '1',
            'TIT2': 'Track One',
            'TYER': '2023',
            'TALB': 'Test Album'
        }
        self.renamer.validator.validate_mp3_file.return_value = ValidationResult(True, [], [], metadata)
        
        # Création d'un album de test
        album_dir = Path(self.test_dir) / "test_album"
        album_dir.mkdir()
        
        # Test de prévisualisation (même sans fichiers MP3)
        result = self.renamer.preview_album_renaming(str(album_dir))
        
        self.assertIsInstance(result, AlbumRenamingResult)
        # Test que le traitement se fait sans erreurs
        self.assertEqual(len(result.errors), 0)
        # Test que processing_time est défini
        self.assertGreaterEqual(result.processing_time, 0)
        # Test que l'album_path est correct
        self.assertEqual(result.album_path, str(album_dir))
    
    def test_rename_album_complete(self):
        """Test du renommage complet d'un album."""
        # Configuration du validator existant du renamer
        self.renamer.validator.validate_directory.return_value = ValidationResult(True, [], [], {})
        
        # Métadonnées de test pour les fichiers
        metadata = {
            'TRCK': '1',
            'TIT2': 'Test Track',
            'TYER': '2023',
            'TALB': 'Test Album'
        }
        self.renamer.validator.validate_mp3_file.return_value = ValidationResult(True, [], [], metadata)
        
        # Création d'un album de test
        album_dir = Path(self.test_dir) / "original_album"
        album_dir.mkdir()
        
        # Test de renommage complet (même sans fichiers MP3)
        result = self.renamer.rename_album(str(album_dir))
        
        self.assertIsInstance(result, AlbumRenamingResult)
        # Test que le traitement se fait sans erreurs
        self.assertEqual(len(result.errors), 0)
        # Test que processing_time est défini
        self.assertGreaterEqual(result.processing_time, 0)
        # Test que l'album_path est correct ou a été mis à jour
        self.assertIsNotNone(result.album_path)
    
    def test_error_handling_invalid_file_path(self):
        """Test de la gestion d'erreurs avec un chemin de fichier invalide."""
        metadata = {'TRCK': '1', 'TIT2': 'Test'}
        
        result = self.renamer.preview_file_renaming("/nonexistent/file.mp3", metadata)
        
        self.assertIsInstance(result, RenamingResult)
        # La prévisualisation peut fonctionner même avec un fichier inexistant
        # (elle ne fait que calculer le nouveau nom)
        self.assertTrue(result.renamed)
        self.assertTrue(result.new_path.endswith("(01) - Test.mp3"))
    
    def test_error_handling_missing_metadata(self):
        """Test de la gestion d'erreurs avec des métadonnées manquantes."""
        test_file = Path(self.test_dir) / "test.mp3"
        test_file.write_text("fake mp3")
        
        # Métadonnées vides
        result = self.renamer.preview_file_renaming(str(test_file), {})
        
        # Devrait utiliser des valeurs par défaut
        self.assertTrue(result.new_path.endswith("(01) - Unknown Title.mp3"))
        self.assertTrue(result.renamed)
    
    def test_filename_edge_cases(self):
        """Test des cas limites pour les noms de fichiers."""
        # Test avec titre vide
        result, rules = self.renamer.format_track_filename("1", "", ".mp3")
        self.assertEqual(result, "(01) - .mp3")
        
        # Test avec extension différente
        result, rules = self.renamer.format_track_filename("5", "Song", ".flac")
        self.assertEqual(result, "(05) - Song.flac")
        
        # Test avec numéro de piste non numérique
        result, rules = self.renamer.format_track_filename("A", "Track A", ".mp3")
        self.assertEqual(result, "(A) - Track A.mp3")


if __name__ == '__main__':
    unittest.main()
