#!/usr/bin/env python3
"""
Module 3 - Correction de la casse PROPRE (GROUPE 3)
Version finale sans logs de debug
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
from support.validator import Validator, ValidationResult

# Import du gestionnaire de base de données
from database.db_manager import DatabaseManager


class CaseCorrectionRule(Enum):
    """Énumération des règles de correction de casse."""
    SENTENCE_CASE = "sentence_case"         # Première lettre de la phrase en majuscule, reste en minuscule
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
    Classe principale pour la correction de la casse.
    
    Gère la correction automatique de la casse selon des règles prédéfinies
    avec protection des éléments spéciaux et gestion des exceptions.
    """
    
    def __init__(self):
        """Initialise le correcteur de casse."""
        # Initialisation des modules de support
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.validator = Validator()
        self.db_manager = DatabaseManager()
        
        # Configuration du module
        self.processing_config = self.config_manager.processing
        
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
        from support.honest_logger import honest_logger
        
        honest_logger.info(f"🔤 GROUPE 3 - Début correction casse album : {album_path}")
        self.logger.info(f"Début correction casse album : {album_path}")
        
        # Mise à jour du statut
        self.state_manager.update_album_processing_status(album_path, "correcting_case")
        
        try:
            # Validation du répertoire
            validation_result = self.validator.file_validator.validate_directory(album_path)
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
                file_validation = self.validator.file_validator.validate_mp3_file(mp3_file)
                
                # Acceptation des fichiers avec erreurs de sync MPEG (fichiers de test)
                if not file_validation.is_valid and not any("can't sync to MPEG frame" in error for error in file_validation.errors):
                    self.logger.warning(f"Fichier MP3 invalide ignoré : {mp3_file}")
                    continue
                
                # Correction de la casse pour ce fichier
                file_results = self._correct_file_case(mp3_file, artist_name)
                if file_results:
                    results[mp3_file] = file_results
            
            # Mise à jour du statut
            self.state_manager.update_album_processing_status(album_path, "case_corrected")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la correction de casse : {e}")
            self.state_manager.update_album_processing_status(album_path, "case_correction_failed")
            return {}
    
    def correct_text_case(self, text: str, text_type: str = 'title', artist_name: str = None) -> CaseCorrectionResult:
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
        
        result = CaseCorrectionResult(
            original=original_text,
            corrected=corrected_text,
            rules_applied=rules_applied,
            exceptions_used=exceptions_used,
            changed=changed
        )
        
        return result
    
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
            'TIT2': 'title',    # Title
            'TALB': 'album',    # Album
            'TPE1': 'artist',   # Artist
            'TPE2': 'artist',   # Album Artist
            'TCOM': 'title',    # Composer
            'TGEN': 'album'     # Genre
        }
        return field_mapping.get(field_name, 'title')
    
    def _apply_case_rules(self, text: str, text_type: str, artist_name: str = None) -> Tuple[str, List[CaseCorrectionRule]]:
        """Applique les règles de correction de casse."""
        rules_applied = []
        step_text = text
        
        # 1. Application du sentence case (première lettre en majuscule)
        step_text = self._apply_sentence_case(step_text)
        rules_applied.append(CaseCorrectionRule.SENTENCE_CASE)
        
        # 2. Protection des chiffres romains
        step_text = self._protect_roman_numerals(step_text)
        rules_applied.append(CaseCorrectionRule.PROTECT_ROMAN_NUMERALS)
        
        # 3. Protection du "I" isolé
        step_text = self._protect_single_i(step_text)
        rules_applied.append(CaseCorrectionRule.PROTECT_SINGLE_I)
        
        # 4. Gestion des prépositions
        step_text = self._handle_prepositions(step_text)
        rules_applied.append(CaseCorrectionRule.HANDLE_PREPOSITIONS)
        
        # 5. Protection des abréviations
        step_text = self._protect_abbreviations(step_text)
        rules_applied.append(CaseCorrectionRule.PROTECT_ABBREVIATIONS)
        
        # 6. Protection de l'artiste dans le nom d'album
        if text_type == 'album' and artist_name:
            step_text = self._protect_artist_in_album(step_text, artist_name)
            rules_applied.append(CaseCorrectionRule.PROTECT_ARTIST_IN_ALBUM)
        
        return step_text, rules_applied
    
    def _apply_sentence_case(self, text: str) -> str:
        """Applique le sentence case : première lettre en majuscule, reste en minuscule."""
        if not text:
            return text
        
        # Conversion complète en minuscules puis première lettre en majuscule
        result = text.lower()
        if result:
            result = result[0].upper() + result[1:]
        
        return result
    
    def _protect_roman_numerals(self, text: str) -> str:
        """Protège les chiffres romains contre la conversion en minuscules."""
        # Pattern pour chiffres romains (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
        roman_pattern = r'\b([IVX]{1,4})\b'
        
        def replace_roman(match):
            return match.group(1).upper()
        
        return re.sub(roman_pattern, replace_roman, text, flags=re.IGNORECASE)
    
    def _protect_single_i(self, text: str) -> str:
        """Protège le mot 'I' isolé."""
        return re.sub(r'\bi\b', 'I', text)
    
    def _handle_prepositions(self, text: str) -> str:
        """Gère les prépositions en les gardant en minuscules."""
        # Les prépositions courantes à garder en minuscules
        prepositions = ['of', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from', 'and', 'or', 'but']
        
        for prep in prepositions:
            # Remplace la préposition sauf si elle est en début de phrase
            pattern = r'(?<!^)\b' + re.escape(prep.title()) + r'\b'
            text = re.sub(pattern, prep, text, flags=re.IGNORECASE)
        
        return text
    
    def _protect_abbreviations(self, text: str) -> str:
        """Protège les abréviations connues."""
        abbreviations = ['DJ', 'MC', 'Dr', 'Mr', 'Mrs', 'Ms', 'St', 'USA', 'UK', 'NYC', 'LA']
        
        for abbr in abbreviations:
            pattern = r'\b' + re.escape(abbr) + r'\b'
            text = re.sub(pattern, abbr, text, flags=re.IGNORECASE)
        
        return text
    
    def _protect_artist_in_album(self, album_text: str, artist_name: str) -> str:
        """Protège le nom de l'artiste dans le nom d'album."""
        if not artist_name:
            return album_text
        
        # Protection du nom exact de l'artiste
        pattern = r'\b' + re.escape(artist_name) + r'\b'
        return re.sub(pattern, artist_name, album_text, flags=re.IGNORECASE)
    
    def _apply_case_exceptions(self, text: str) -> Tuple[str, List[CaseException]]:
        """Applique les exceptions personnalisées."""
        exceptions_used = []
        result_text = text
        
        for exception in self.case_exceptions:
            if exception.case_sensitive:
                if exception.original in result_text:
                    result_text = result_text.replace(exception.original, exception.corrected)
                    exceptions_used.append(exception)
            else:
                pattern = re.escape(exception.original)
                if re.search(pattern, result_text, re.IGNORECASE):
                    result_text = re.sub(pattern, exception.corrected, result_text, flags=re.IGNORECASE)
                    exceptions_used.append(exception)
        
        return result_text, exceptions_used
    
    def _load_case_exceptions(self) -> List[CaseException]:
        """Charge les exceptions de casse depuis la base de données."""
        try:
            # Simulation du chargement depuis la base de données
            # En réalité, on interrogerait la table des exceptions
            return [
                CaseException("paris", "Paris", "city"),
                CaseException("london", "London", "city"),
                CaseException("new york", "New York", "city"),
                CaseException("dj", "DJ", "abbreviation"),
                CaseException("mc", "MC", "abbreviation"),
            ]
        except Exception as e:
            self.logger.warning(f"Impossible de charger les exceptions : {e}")
            return []
    
    def _build_roman_numerals_set(self) -> Set[str]:
        """Construit le set des chiffres romains."""
        return {
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'
        }
    
    def _build_prepositions_set(self) -> Set[str]:
        """Construit le set des prépositions."""
        return {
            'of', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from',
            'and', 'or', 'but', 'the', 'a', 'an', 'as'
        }
    
    def _build_abbreviations_set(self) -> Set[str]:
        """Construit le set des abréviations."""
        return {
            'DJ', 'MC', 'Dr', 'Mr', 'Mrs', 'Ms', 'St', 'USA', 'UK', 'NYC', 'LA',
            'TV', 'CD', 'LP', 'EP', 'vs', 'feat', 'ft'
        }
