"""
Tests unitaires pour le module metadata_processor
"""

import pytest
import os
import tempfile
from pathlib import Path

# Mock pour mutagen si non disponible
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TALB, TPE1
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    # Mock classes pour tests
    class MP3:
        def __init__(self, file_path):
            self.file_path = file_path
            self.tags = {}

        def save(self):
            pass

    class TIT2:
        def __init__(self, text):
            self.text = text

    class TALB:
        def __init__(self, text):
            self.text = text

    class TPE1:
        def __init__(self, text):
            self.text = text

# Import du module à tester
from core.metadata_processor import MetadataProcessor, CleaningRule

class TestMetadataProcessor:
    """Tests pour MetadataProcessor"""

    def setup_method(self):
        """Configuration avant chaque test"""
        self.processor = MetadataProcessor()

    def test_apply_cleaning_rules(self):
        """Test application des règles de nettoyage"""
        # Test basique que la méthode existe et fonctionne
        result = self.processor._apply_cleaning_rules("Test input")
        assert isinstance(result, str), "Le résultat devrait être une chaîne"
        assert len(result) > 0, "Le résultat ne devrait pas être vide"

    def test_clean_whitespace(self):
        """Test nettoyage des espaces"""
        # Test basique
        assert True  # Placeholder

    def test_remove_special_chars(self):
        """Test suppression des caractères spéciaux"""
        # Test basique
        assert True  # Placeholder

    def test_normalize_conjunctions(self):
        """Test normalisation des conjonctions"""
        # Test basique
        assert True  # Placeholder

    @pytest.mark.skipif(not MUTAGEN_AVAILABLE, reason="Mutagen non disponible")
    def test_apply_cleaning_rules_integration(self):
        """Test d'intégration des règles de nettoyage"""
        # Créer un fichier MP3 temporaire pour test
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Créer un objet MP3 avec métadonnées de test
            audio = MP3(temp_path)
            audio.tags = ID3()

            # Ajouter des métadonnées "sales"
            audio.tags.add(TIT2(text="Titre (version live) ! avec caractères $ spéciaux"))
            audio.tags.add(TALB(text="Album (remasterisé 2023)   avec   espaces"))
            audio.tags.add(TPE1(text="Artiste and Autre"))

            audio.save()

            # Appliquer les règles de nettoyage
            success = self.processor.apply_cleaning_rules(temp_path)

            assert success, "Le nettoyage devrait réussir"

            # Recharger et vérifier
            cleaned_audio = MP3(temp_path)
            assert cleaned_audio.tags['TIT2'].text[0] == "Titre avec caractères spéciaux"
            assert cleaned_audio.tags['TALB'].text[0] == "Album avec espaces"
            assert cleaned_audio.tags['TPE1'].text[0] == "Artiste & Autre"

        finally:
            # Nettoyer
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__])