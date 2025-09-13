#!/usr/bin/env python3
"""
Module 3 - Correction de la casse (GROUPE 3)
Système de correction de la casse pour les métadonnées MP3
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

# Imports des modules de support
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager
from support.validator import MetadataValidator, ValidationResult

# Import du gestionnaire de base de données
from database.db_manager import DatabaseManager


class CaseCorrectionRule(Enum):
    """Énumération des règles de correction de casse."""
    TITLE_CASE = "title_case"              # Première lettre de chaque mot en majuscule
    PROTECT_ROMAN_NUMERALS = "protect_roman_numerals"  # Protection des chiffres romains
    PROTECT_SINGLE_I = "protect_single_i"  # Protection du "I" isolé
    PROTECT_ARTIST_IN_ALBUM = "protect_artist_in_album"  # Protection nom artiste dans album
    HANDLE_EXCEPTIONS = "handle_exceptions"  # Gestion des exceptions personnalisées
    PROTECT_ABBREVIATIONS = "protect_abbreviations"  # Protection des abréviations
    HANDLE_PREPOSITIONS = "handle_prepositions"  # Gestion des prépositions


@dataclass
class CaseException:
    """Représente une exception de casse."""
    original: str
    corrected: str
    type: str  # 'city', 'roman', 'abbreviation', 'custom'
    case_sensitive: bool = True


@dataclass
class CaseCorrectionResult:
    """Résultat d'une correction de casse."""
    original: str
    corrected: str
    rules_applied: List[CaseCorrectionRule]
    exceptions_used: List[CaseException]
    changed: bool


class CaseCorrector:
    """
    Gestionnaire de correction de la casse des métadonnées.
    
    Fonctionnalités :
    - Correction de la casse selon les règles de l'anglais
    - Gestion des exceptions (villes, chiffres romains, etc.)
    - Protection des noms d'artistes dans les titres d'albums
    - Intégration avec les modules de support
    """
    
    def __init__(self):
        """Initialise le correcteur de casse."""
        # Initialisation des modules de support
        self.logger = AppLogger().get_logger(__name__)
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.validator = MetadataValidator()
        self.db_manager = DatabaseManager()
        
        # Configuration du module
        self.processing_config = self.config_manager.get_processing_config()
        
        # Chargement des exceptions depuis la base de données
        self.case_exceptions = self._load_case_exceptions()
        
        # Règles prédéfinies
        self.roman_numerals = self._build_roman_numerals_set()
        self.prepositions = self._build_prepositions_set()
        self.abbreviations = self._build_abbreviations_set()
        
        self.logger.info("CaseCorrector initialisé avec succès")
    
    def correct_album_case(self, album_path: str, artist_name: str = None) -> Dict[str, CaseCorrectionResult]:
        """
        Corrige la casse des métadonnées pour un album complet.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            artist_name: Nom de l'artiste (pour protection dans les titres)
            
        Returns:
            Dict avec les résultats de correction pour chaque fichier
        """
        self.logger.info(f"Début correction casse album : {album_path}")
        
        # Mise à jour du statut
        self.state_manager.update_status("correcting_case")
        
        try:
            # Validation du répertoire
            validation_result = self.validator.validate_directory(album_path)
            if not validation_result.is_valid:
                self.logger.error(f"Répertoire invalide : {validation_result.errors}")
                return {}
            
            # Recherche des fichiers MP3
            mp3_files = self._find_mp3_files(album_path)
            if not mp3_files:
                self.logger.warning(f"Aucun fichier MP3 trouvé dans {album_path}")
                return {}
            
            results = {}
            
            for mp3_file in mp3_files:
                # Validation du fichier MP3
                file_validation = self.validator.validate_mp3_file(mp3_file)
                if not file_validation.is_valid:
                    self.logger.warning(f"Fichier MP3 invalide ignoré : {mp3_file}")
                    continue
                
                # Correction de la casse pour ce fichier
                file_results = self._correct_file_case(mp3_file, artist_name)
                if file_results:
                    results[mp3_file] = file_results
            
            # Mise à jour du statut
            self.state_manager.update_status("case_correction_completed")
            
            # Sauvegarde en base de données
            self._save_correction_history(album_path, results)
            
            self.logger.info(f"Correction casse terminée : {len(results)} fichiers traités")
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la correction casse : {e}")
            self.state_manager.update_status("case_correction_error")
            return {}
    
    def correct_text_case(self, text: str, text_type: str = "title", artist_name: str = None) -> CaseCorrectionResult:
        """
        Corrige la casse d'un texte selon les règles définies.
        
        Args:
            text: Texte à corriger
            text_type: Type de texte ('title', 'album', 'artist')
            artist_name: Nom de l'artiste (pour protection)
            
        Returns:
            Résultat de la correction avec détails
        """
        if not text or not text.strip():
            return CaseCorrectionResult(
                original=text,
                corrected=text,
                rules_applied=[],
                exceptions_used=[],
                changed=False
            )
        
        original_text = text
        corrected_text = text
        rules_applied = []
        exceptions_used = []
        
        # Application des règles de correction
        corrected_text, rule_results = self._apply_case_rules(
            corrected_text, text_type, artist_name
        )
        rules_applied.extend(rule_results)
        
        # Gestion des exceptions (après les règles de base)
        corrected_text, exception_results = self._apply_case_exceptions(corrected_text)
        exceptions_used.extend(exception_results)
        
        changed = original_text != corrected_text
        
        return CaseCorrectionResult(
            original=original_text,
            corrected=corrected_text,
            rules_applied=rules_applied,
            exceptions_used=exceptions_used,
            changed=changed
        )
    
    def preview_case_corrections(self, album_path: str, artist_name: str = None) -> Dict[str, List[Dict]]:
        """
        Aperçu des corrections de casse sans les appliquer.
        
        Args:
            album_path: Chemin vers l'album
            artist_name: Nom de l'artiste
            
        Returns:
            Dict avec aperçu des changements par fichier
        """
        self.logger.info(f"Aperçu corrections casse : {album_path}")
        
        mp3_files = self._find_mp3_files(album_path)
        preview_results = {}
        
        for mp3_file in mp3_files:
            file_preview = []
            
            # Simulation des métadonnées à corriger
            # En réalité, on lirait les métadonnées avec mutagen
            metadata_fields = self._get_metadata_fields_for_preview(mp3_file)
            
            for field_name, field_value in metadata_fields.items():
                if field_value:
                    text_type = self._get_text_type_from_field(field_name)
                    result = self.correct_text_case(field_value, text_type, artist_name)
                    
                    if result.changed:
                        file_preview.append({
                            'field': field_name,
                            'original': result.original,
                            'corrected': result.corrected,
                            'rules': [rule.value for rule in result.rules_applied],
                            'exceptions': [ex.original for ex in result.exceptions_used]
                        })
            
            if file_preview:
                preview_results[mp3_file] = file_preview
        
        return preview_results
    
    def add_case_exception(self, original: str, corrected: str, exception_type: str = "custom") -> bool:
        """
        Ajoute une exception de casse personnalisée.
        
        Args:
            original: Texte original
            corrected: Texte corrigé
            exception_type: Type d'exception
            
        Returns:
            True si ajouté avec succès
        """
        try:
            # Validation de l'exception
            if not original or not corrected:
                self.logger.error("Exception invalide : texte vide")
                return False
            
            # Ajout en base de données
            self.db_manager.add_case_exception(original, corrected, exception_type)
            
            # Rechargement des exceptions
            self.case_exceptions = self._load_case_exceptions()
            
            self.logger.info(f"Exception ajoutée : '{original}' → '{corrected}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur ajout exception : {e}")
            return False
    
    def _apply_case_rules(self, text: str, text_type: str, artist_name: str = None) -> Tuple[str, List[CaseCorrectionRule]]:
        """Applique les règles de correction de casse."""
        rules_applied = []
        result_text = text
        
        # Règle 1 : Title Case de base
        result_text = self._apply_title_case(result_text)
        rules_applied.append(CaseCorrectionRule.TITLE_CASE)
        
        # Règle 2 : Gestion des prépositions (après title case)
        result_text = self._handle_prepositions(result_text)
        rules_applied.append(CaseCorrectionRule.HANDLE_PREPOSITIONS)
        
        # Règle 3 : Protection des chiffres romains
        result_text = self._protect_roman_numerals(result_text)
        rules_applied.append(CaseCorrectionRule.PROTECT_ROMAN_NUMERALS)
        
        # Règle 4 : Protection du "I" isolé
        result_text = self._protect_single_i(result_text)
        rules_applied.append(CaseCorrectionRule.PROTECT_SINGLE_I)
        
        # Règle 5 : Protection des abréviations
        result_text = self._protect_abbreviations(result_text)
        rules_applied.append(CaseCorrectionRule.PROTECT_ABBREVIATIONS)
        
        # Règle 6 : Protection artiste dans album (si applicable)
        if text_type == "album" and artist_name:
            result_text = self._protect_artist_in_album(result_text, artist_name)
            rules_applied.append(CaseCorrectionRule.PROTECT_ARTIST_IN_ALBUM)
        
        return result_text, rules_applied
    
    def _apply_title_case(self, text: str) -> str:
        """Applique le Title Case de base."""
        return ' '.join(word.capitalize() for word in text.split())
    
    def _protect_roman_numerals(self, text: str) -> str:
        """Protège les chiffres romains."""
        words = text.split()
        for i, word in enumerate(words):
            if word.upper() in self.roman_numerals:
                words[i] = word.upper()
        return ' '.join(words)
    
    def _protect_single_i(self, text: str) -> str:
        """Protège le "I" isolé."""
        return re.sub(r'\bi\b', 'I', text)
    
    def _handle_prepositions(self, text: str) -> str:
        """Gère les prépositions (minuscules sauf en début)."""
        words = text.split()
        for i, word in enumerate(words):
            # Ne pas traiter le premier mot
            if i > 0:
                # Extraire le mot principal sans ponctuation
                word_clean = re.sub(r'[^\w]', '', word)
                if word_clean.lower() in self.prepositions:
                    # Remplacer en conservant la ponctuation, en minuscules
                    words[i] = re.sub(r'\w+', word_clean.lower(), word)
        return ' '.join(words)
    
    def _protect_abbreviations(self, text: str) -> str:
        """Protège les abréviations connues, mais pas les prépositions."""
        words = text.split()
        for i, word in enumerate(words):
            # Extraire le mot sans ponctuation pour comparaison
            word_clean = re.sub(r'[^\w]', '', word).upper()
            # Ne pas traiter si c'est une préposition déjà en minuscules (sauf première position)
            if i > 0 and word.lower() in self.prepositions:
                continue
            # Protéger les abréviations
            if word_clean in self.abbreviations:
                # Remplacer le mot en préservant la ponctuation
                words[i] = re.sub(r'\w+', word_clean, word)
        return ' '.join(words)
    
    def _protect_artist_in_album(self, album_title: str, artist_name: str) -> str:
        """Protège le nom de l'artiste dans le titre de l'album."""
        if artist_name and artist_name.lower() in album_title.lower():
            # Remplacement en préservant la casse de l'artiste
            pattern = re.compile(re.escape(artist_name), re.IGNORECASE)
            return pattern.sub(artist_name, album_title)
        return album_title
    
    def _apply_case_exceptions(self, text: str) -> Tuple[str, List[CaseException]]:
        """Applique les exceptions de casse personnalisées."""
        exceptions_used = []
        result_text = text
        
        for exception in self.case_exceptions:
            if exception.case_sensitive:
                # Recherche sensible à la casse
                if exception.original in result_text:
                    result_text = result_text.replace(exception.original, exception.corrected)
                    exceptions_used.append(exception)
            else:
                # Recherche insensible à la casse
                pattern = re.compile(re.escape(exception.original), re.IGNORECASE)
                if pattern.search(result_text):
                    result_text = pattern.sub(exception.corrected, result_text)
                    exceptions_used.append(exception)
        
        return result_text, exceptions_used
    
    def _find_mp3_files(self, directory: str) -> List[str]:
        """Trouve tous les fichiers MP3 dans un répertoire."""
        mp3_files = []
        try:
            for file_path in Path(directory).glob("*.mp3"):
                mp3_files.append(str(file_path))
        except Exception as e:
            self.logger.error(f"Erreur recherche fichiers MP3 : {e}")
        return sorted(mp3_files)
    
    def _correct_file_case(self, mp3_file: str, artist_name: str = None) -> Dict[str, CaseCorrectionResult]:
        """Corrige la casse des métadonnées d'un fichier."""
        # Placeholder pour l'intégration avec mutagen
        # En réalité, on lirait et modifierait les tags ID3
        results = {}
        
        # Simulation des champs métadonnées
        metadata_fields = {
            'TIT2': f"sample title from {Path(mp3_file).stem}",
            'TALB': f"sample album name",
            'TPE1': f"sample artist name"
        }
        
        for field_name, field_value in metadata_fields.items():
            if field_value:
                text_type = self._get_text_type_from_field(field_name)
                result = self.correct_text_case(field_value, text_type, artist_name)
                results[field_name] = result
        
        return results
    
    def _get_text_type_from_field(self, field_name: str) -> str:
        """Détermine le type de texte selon le champ métadonnée."""
        field_mapping = {
            'TIT2': 'title',    # Titre
            'TALB': 'album',    # Album
            'TPE1': 'artist',   # Artiste
            'TPE2': 'artist',   # Artiste de l'album
        }
        return field_mapping.get(field_name, 'title')
    
    def _get_metadata_fields_for_preview(self, mp3_file: str) -> Dict[str, str]:
        """Obtient les champs métadonnées pour aperçu."""
        # Simulation - en réalité on utiliserait mutagen
        return {
            'TIT2': f"sample title from {Path(mp3_file).stem}",
            'TALB': f"sample album name",
            'TPE1': f"sample artist name"
        }
    
    def _load_case_exceptions(self) -> List[CaseException]:
        """Charge les exceptions de casse depuis la base de données."""
        try:
            exceptions_data = self.db_manager.get_case_exceptions()
            exceptions = []
            
            for exception_data in exceptions_data:
                exception = CaseException(
                    original=exception_data['original'],
                    corrected=exception_data['corrected'],
                    type=exception_data.get('type', 'custom'),
                    case_sensitive=exception_data.get('case_sensitive', True)
                )
                exceptions.append(exception)
            
            self.logger.info(f"Chargé {len(exceptions)} exceptions de casse")
            return exceptions
            
        except Exception as e:
            self.logger.error(f"Erreur chargement exceptions : {e}")
            return []
    
    def _build_roman_numerals_set(self) -> Set[str]:
        """Construit l'ensemble des chiffres romains."""
        return {
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX',
            'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV', 'XXX', 'XL', 'L', 'LX', 'LXX',
            'LXXX', 'XC', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM', 'M'
        }
    
    def _build_prepositions_set(self) -> Set[str]:
        """Construit l'ensemble des prépositions."""
        return {
            'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'of', 'on', 
            'or', 'the', 'to', 'up', 'via', 'with', 'from', 'into', 'over', 'under',
            'et', 'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'dans', 'sur',
            'avec', 'pour', 'par', 'sans', 'sous', 'vers', 'chez'
        }
    
    def _build_abbreviations_set(self) -> Set[str]:
        """Construit l'ensemble des abréviations."""
        return {
            'USA', 'UK', 'US', 'DJ', 'MC', 'NYC', 'LA', 'SF', 'DC', 'CD', 'DVD',
            'TV', 'FM', 'AM', 'PM', 'BC', 'AD', 'CEO', 'FBI', 'CIA', 'NASA',
            'BBC', 'CNN', 'ESPN', 'MTV', 'VHS', 'GPS', 'WWW', 'HTTP', 'FTP'
        }
    
    def _save_correction_history(self, album_path: str, results: Dict) -> None:
        """Sauvegarde l'historique des corrections en base."""
        try:
            # Comptage des changements
            total_changes = sum(
                len([r for r in file_results.values() if r.changed])
                for file_results in results.values()
            )
            
            # Sauvegarde en base
            self.db_manager.save_import_history(
                album_path=album_path,
                operation_type="case_correction",
                files_processed=len(results),
                changes_made=total_changes,
                details={"corrections": len(results)}
            )
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde historique : {e}")


# Alias pour compatibilité
MetadataCaseCorrector = CaseCorrector
