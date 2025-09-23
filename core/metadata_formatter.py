#!/usr/bin/env python3
"""
Module 4 - Formatage des métadonnées (GROUPE 4)
Système de formatage et normalisation des métadonnées MP3
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Imports des modules de support
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager
from support.validator import MetadataValidator, FileValidator, ValidationResult

# Import du gestionnaire de base de données
from database.db_manager import DatabaseManager


class FormattingRule(Enum):
    """Énumération des règles de formatage."""
    COPY_ARTIST_TO_ALBUMARTIST = "copy_artist_to_albumartist"     # Copie artiste → interprète
    FORMAT_TRACK_NUMBERS = "format_track_numbers"                 # Formatage numéros de piste
    HANDLE_COMPILATION_YEAR = "handle_compilation_year"           # Gestion année compilation
    NORMALIZE_GENRE = "normalize_genre"                           # Normalisation des genres
    FORMAT_DURATION = "format_duration"                           # Formatage durée
    VALIDATE_REQUIRED_FIELDS = "validate_required_fields"         # Validation champs requis


@dataclass
class FormattingResult:
    """Résultat d'une opération de formatage."""
    original_value: Any
    formatted_value: Any
    field_name: str
    rules_applied: List[FormattingRule]
    changed: bool
    warnings: List[str] = None


@dataclass
class AlbumFormattingResult:
    """Résultat du formatage d'un album complet."""
    album_path: str
    files_processed: int
    total_changes: int
    field_changes: Dict[str, int]
    warnings: List[str]
    errors: List[str]
    processing_time: float


class MetadataFormatter:
    """
    Gestionnaire de formatage des métadonnées MP3.
    
    Fonctionnalités :
    - Copie artiste vers champ interprète (albumartist)
    - Formatage des numéros de piste (01, 02, 03...)
    - Gestion des années de compilation
    - Normalisation des genres
    - Validation des champs requis
    """
    
    def __init__(self):
        """Initialise le formateur de métadonnées."""
        # Initialisation des modules de support
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.validator = MetadataValidator()
        self.file_validator = FileValidator()  # ✅ Pour validate_directory
        self.db_manager = DatabaseManager()
        
        # Configuration du module
        self.processing_config = self.config_manager.processing
        
        # Genres prédéfinis standardisés
        self.standard_genres = self._build_standard_genres()
        
        # Configuration du formatage
        self.formatting_config = self._load_formatting_config()
        
        self.logger.info("MetadataFormatter initialisé avec succès")
    
    def format_album_metadata(self, album_path: str) -> AlbumFormattingResult:
        """
        Formate les métadonnées pour un album complet.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            Résultat du formatage de l'album
        """
        from support.honest_logger import honest_logger
        
        start_time = datetime.now()
        honest_logger.info(f"📊 GROUPE 4 - Début formatage métadonnées album : {album_path}")
        self.logger.info(f"Début formatage métadonnées album : {album_path}")
        
        # Mise à jour du statut
        self.state_manager.update_album_processing_status(album_path, "formatting_metadata")
        
        try:
            # Validation du répertoire
            validation_result = self.file_validator.validate_directory(album_path)
            if not validation_result.is_valid:
                self.logger.error(f"Répertoire invalide : {validation_result.errors}")
                return self._create_error_result(album_path, validation_result.errors)
            
            # Recherche des fichiers MP3
            mp3_files = self._find_mp3_files(album_path)
            if not mp3_files:
                self.logger.warning(f"Aucun fichier MP3 trouvé dans {album_path}")
                return self._create_empty_result(album_path)
            
            # Extraction des informations globales de l'album
            album_info = self._extract_album_info(mp3_files)
            
            # Formatage de chaque fichier
            total_changes = 0
            field_changes = {}
            warnings = []
            errors = []
            
            for mp3_file in mp3_files:
                try:
                    # Validation du fichier MP3
                    file_validation = self.validator.validate_mp3_file(mp3_file)
                    if not file_validation.is_valid:
                        self.logger.warning(f"Fichier MP3 invalide ignoré : {mp3_file}")
                        errors.append(f"Fichier invalide : {Path(mp3_file).name}")
                        continue
                    
                    # Formatage du fichier
                    file_results = self._format_file_metadata(mp3_file, album_info)
                    
                    # Compilation des résultats
                    for field_name, result in file_results.items():
                        if result.changed:
                            total_changes += 1
                            field_changes[field_name] = field_changes.get(field_name, 0) + 1
                        
                        if result.warnings:
                            warnings.extend(result.warnings)
                
                except Exception as e:
                    error_msg = f"Erreur formatage {Path(mp3_file).name}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Calcul du temps de traitement
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Création du résultat
            result = AlbumFormattingResult(
                album_path=album_path,
                files_processed=len(mp3_files) - len([e for e in errors if "invalide" in e]),
                total_changes=total_changes,
                field_changes=field_changes,
                warnings=warnings,
                errors=errors,
                processing_time=processing_time
            )
            
            # Mise à jour du statut
            self.state_manager.update_album_processing_status(album_path, "metadata_formatting_completed")
            
            # Sauvegarde en base de données
            self._save_formatting_history(result)
            
            self.logger.info(f"Formatage terminé : {result.files_processed} fichiers, {result.total_changes} changements")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors du formatage : {e}")
            self.state_manager.update_album_processing_status(album_path, "metadata_formatting_error")
            return self._create_error_result(album_path, [str(e)])
    
    def format_metadata_field(self, field_name: str, field_value: Any, metadata_context: Dict = None) -> FormattingResult:
        """
        Formate un champ de métadonnées spécifique.
        
        Args:
            field_name: Nom du champ (TIT2, TALB, TPE1, etc.)
            field_value: Valeur actuelle du champ
            metadata_context: Contexte des autres métadonnées
            
        Returns:
            Résultat du formatage du champ
        """
        if metadata_context is None:
            metadata_context = {}
        
        original_value = field_value
        formatted_value = field_value
        rules_applied = []
        warnings = []

        # Application des règles selon le type de champ
        if field_name == "TRCK":  # Numéro de piste
            self.logger.info(f"🎵 [GROUPE 4] Application RÈGLE 14 sur piste TRCK: '{field_value}'")
            formatted_value, track_rules = self._format_track_number(field_value)
            rules_applied.extend(track_rules)
            if track_rules:
                self.logger.info(f"✅ [GROUPE 4] RÈGLE 14 appliquée avec succès")
            else:
                self.logger.warning(f"⚠️ [GROUPE 4] RÈGLE 14 non appliquée")
            
        elif field_name == "TPE2":  # Artiste de l'album (interprète)
            self.logger.info(f"👤 [GROUPE 4] Application RÈGLE 13 sur albumartist TPE2: '{field_value}'")
            formatted_value, artist_rules = self._copy_artist_to_albumartist(
                field_value, metadata_context.get("TPE1")
            )
            rules_applied.extend(artist_rules)
            if artist_rules:
                self.logger.info(f"✅ [GROUPE 4] RÈGLE 13 appliquée avec succès")
            else:
                self.logger.info(f"ℹ️ [GROUPE 4] RÈGLE 13 non appliquée (conditions non remplies)")
            
        elif field_name == "TYER" or field_name == "TDRC":  # Année
            self.logger.info(f"📅 [GROUPE 4] Application RÈGLE 21 sur année {field_name}: '{field_value}'")
            formatted_value, year_rules, year_warnings = self._handle_compilation_year(
                field_value, metadata_context
            )
            rules_applied.extend(year_rules)
            warnings.extend(year_warnings)
            if year_rules:
                self.logger.info(f"✅ [GROUPE 4] RÈGLE 21 appliquée avec succès")
            else:
                self.logger.info(f"ℹ️ [GROUPE 4] RÈGLE 21 non appliquée (année standard)")
            
        elif field_name == "TCON":  # Genre
            formatted_value, genre_rules = self._normalize_genre(field_value)
            rules_applied.extend(genre_rules)
            
        elif field_name == "TLEN":  # Durée
            formatted_value, duration_rules = self._format_duration(field_value)
            rules_applied.extend(duration_rules)
        
        # Validation des champs requis
        if self._is_required_field(field_name):
            validation_rules, validation_warnings = self._validate_required_field(
                field_name, formatted_value
            )
            rules_applied.extend(validation_rules)
            warnings.extend(validation_warnings)
        
        changed = original_value != formatted_value
        
        return FormattingResult(
            original_value=original_value,
            formatted_value=formatted_value,
            field_name=field_name,
            rules_applied=rules_applied,
            changed=changed,
            warnings=warnings if warnings else None
        )
    
    def preview_formatting_changes(self, album_path: str) -> Dict[str, List[Dict]]:
        """
        Aperçu des changements de formatage sans les appliquer.
        
        Args:
            album_path: Chemin vers l'album
            
        Returns:
            Dict avec aperçu des changements par fichier
        """
        self.logger.info(f"Aperçu formatage : {album_path}")
        
        mp3_files = self._find_mp3_files(album_path)
        preview_results = {}
        
        # Extraction des informations globales
        album_info = self._extract_album_info(mp3_files)
        
        for mp3_file in mp3_files:
            file_preview = []
            
            # Simulation des métadonnées à formater
            metadata_fields = self._get_metadata_fields_for_preview(mp3_file)
            
            for field_name, field_value in metadata_fields.items():
                if field_value is not None:
                    result = self.format_metadata_field(field_name, field_value, metadata_fields)
                    
                    if result.changed or result.warnings:
                        preview_item = {
                            'field': field_name,
                            'original': result.original_value,
                            'formatted': result.formatted_value,
                            'rules': [rule.value for rule in result.rules_applied],
                            'changed': result.changed
                        }
                        
                        if result.warnings:
                            preview_item['warnings'] = result.warnings
                        
                        file_preview.append(preview_item)
            
            if file_preview:
                preview_results[mp3_file] = file_preview
        
        return preview_results
    
    def _format_track_number(self, track_value: Any) -> Tuple[str, List[FormattingRule]]:
        """Formate le numéro de piste (01, 02, 03...)."""
        
        if not track_value:
            self.logger.warning(f"❌ [RÈGLE 14] Valeur piste vide ou None - Pas de formatage")
            return track_value, []
        
        # Extraction du numéro de piste
        track_str = str(track_value)
        self.logger.debug(f"📝 [RÈGLE 14] Piste convertie en string: '{track_str}'")
        
        # Pattern pour extraire le numéro de piste (ex: "1/12" → "1")
        match = re.match(r'^(\d+)', track_str)
        if not match:
            self.logger.error(f"❌ [RÈGLE 14] Pattern numérique non trouvé dans: '{track_str}'")
            return track_value, []
        
        track_number = int(match.group(1))
        self.logger.debug(f"🔢 [RÈGLE 14] Numéro extrait: {track_number}")
        
        # Formatage avec zéro initial si nécessaire
        zero_padding = self.formatting_config.get('track_zero_padding', True)
        self.logger.debug(f"⚙️ [RÈGLE 14] Zero padding activé: {zero_padding}")
        
        if zero_padding:
            formatted_track = f"{track_number:02d}"
            self.logger.info(f"✅ [RÈGLE 14] Formatage avec zéro: '{track_str}' → '{formatted_track}'")
        else:
            formatted_track = str(track_number)
            self.logger.info(f"✅ [RÈGLE 14] Formatage simple: '{track_str}' → '{formatted_track}'")
        
        # Préservation du total si présent (ex: "01/12")
        if '/' in track_str:
            total_match = re.search(r'/(\d+)', track_str)
            if total_match:
                total_tracks = total_match.group(1)
                formatted_track += f"/{total_tracks}"
                self.logger.info(f"📊 [RÈGLE 14] Total préservé: '{formatted_track}' (total: {total_tracks})")
            else:
                self.logger.warning(f"⚠️ [RÈGLE 14] Slash détecté mais total non extrait de: '{track_str}'")
        
        return formatted_track, [FormattingRule.FORMAT_TRACK_NUMBERS]
    
    def _copy_artist_to_albumartist(self, albumartist_value: Any, artist_value: Any) -> Tuple[str, List[FormattingRule]]:
        """Copie l'artiste vers le champ interprète si vide."""
        
        if albumartist_value and albumartist_value.strip():
            # Le champ interprète existe déjà
            return albumartist_value, []
        
        if not artist_value or not artist_value.strip():
            # Pas d'artiste source
            self.logger.warning(f"❌ [RÈGLE 13] Artiste source vide ou None: '{artist_value}' - Impossible de copier")
            return albumartist_value, []
        
        # Copie de l'artiste vers interprète
        result = artist_value.strip()
        return result, [FormattingRule.COPY_ARTIST_TO_ALBUMARTIST]
    
    def _handle_compilation_year(self, year_value: Any, metadata_context: Dict) -> Tuple[Any, List[FormattingRule], List[str]]:
        """Gère les années de compilation."""
        warnings = []
        
        if not year_value:
            self.logger.warning(f"❌ [RÈGLE 21] Valeur année vide ou None - Pas de traitement")
            return year_value, [], warnings
        
        year_str = str(year_value).strip()
        self.logger.debug(f"📝 [RÈGLE 21] Année convertie: '{year_str}'")
        
        # Détection d'une compilation (plusieurs années)
        year_pattern = r'(\d{4})'
        years = re.findall(year_pattern, year_str)
        
        if len(years) > 1:
            # Compilation détectée
            min_year = min(years)
            max_year = max(years)
            
            if min_year != max_year:
                # Format compilation : "1995-2000"
                formatted_year = f"{min_year}-{max_year}"
                warning_msg = f"Compilation détectée : années {min_year} à {max_year}"
                warnings.append(warning_msg)
                return formatted_year, [FormattingRule.HANDLE_COMPILATION_YEAR], warnings
        
        elif len(years) == 1:
            # Année unique, validation de la plage
            year = int(years[0])
            current_year = datetime.now().year
            self.logger.debug(f"📅 [RÈGLE 21] Validation année unique: {year} (actuelle: {current_year})")
            
            if year < 1900 or year > current_year + 1:
                warning_msg = f"Année suspecte : {year}"
                warnings.append(warning_msg)
                self.logger.warning(f"⚠️ [RÈGLE 21] {warning_msg}")
            else:
                self.logger.info(f"✅ [RÈGLE 21] Année valide: {year}")
            
            return years[0], [], warnings
        
        # Année non détectable
        warning_msg = f"Format d'année non reconnu : {year_str}"
        warnings.append(warning_msg)
        self.logger.error(f"❌ [RÈGLE 21] {warning_msg}")
        return year_value, [], warnings
    
    def _normalize_genre(self, genre_value: Any) -> Tuple[str, List[FormattingRule]]:
        """Normalise le genre musical."""
        if not genre_value:
            return genre_value, []
        
        genre_str = str(genre_value).strip()
        
        # Suppression des parenthèses de numérotation ID3v1 (ex: "(13)" → "Pop")
        if re.match(r'^\(\d+\)$', genre_str):
            # Genre numérique ID3v1, conversion nécessaire
            genre_number = int(genre_str.strip('()'))
            if genre_number < len(self.standard_genres):
                normalized_genre = self.standard_genres[genre_number]
                return normalized_genre, [FormattingRule.NORMALIZE_GENRE]
        
        # Nettoyage du genre textuel
        genre_clean = re.sub(r'^[\(\[]?\d+[\)\]]?\s*', '', genre_str)  # Suppression numéros
        genre_clean = re.sub(r'[^\w\s&/+-]', '', genre_clean)  # Suppression caractères spéciaux (garde /, &, +, -)
        genre_clean = ' '.join(genre_clean.split())  # Normalisation espaces
        
        # Capitalisation
        if genre_clean:
            genre_clean = genre_clean.title()
            
            # Recherche dans les genres standards pour normalisation
            genre_lower = genre_clean.lower()
            for standard_genre in self.standard_genres:
                if standard_genre.lower() == genre_lower:
                    return standard_genre, [FormattingRule.NORMALIZE_GENRE]
            
            return genre_clean, [FormattingRule.NORMALIZE_GENRE] if genre_clean != genre_str else []
        
        return genre_value, []
    
    def _format_duration(self, duration_value: Any) -> Tuple[Any, List[FormattingRule]]:
        """Formate la durée (généralement pas modifiée, juste validée)."""
        if not duration_value:
            return duration_value, []
        
        # La durée est généralement en millisecondes dans TLEN
        # On la laisse telle quelle mais on peut la valider
        try:
            duration_ms = int(duration_value)
            if duration_ms < 0:
                return None, [FormattingRule.FORMAT_DURATION]  # Durée invalide
            return duration_value, []
        except (ValueError, TypeError):
            return duration_value, []
    
    def _validate_required_field(self, field_name: str, field_value: Any) -> Tuple[List[FormattingRule], List[str]]:
        """Valide les champs requis."""
        warnings = []
        
        if self._is_required_field(field_name):
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                warnings.append(f"Champ requis manquant : {field_name}")
                return [FormattingRule.VALIDATE_REQUIRED_FIELDS], warnings
        
        return [], warnings
    
    def _is_required_field(self, field_name: str) -> bool:
        """Détermine si un champ est requis."""
        required_fields = self.formatting_config.get('required_fields', [
            'TIT2',  # Titre
            'TPE1',  # Artiste
            'TALB',  # Album
            'TRCK',  # Numéro de piste
        ])
        return field_name in required_fields
    
    def _find_mp3_files(self, directory: str) -> List[str]:
        """Trouve tous les fichiers MP3 dans un répertoire."""
        mp3_files = []
        try:
            for file_path in Path(directory).glob("*.mp3"):
                mp3_files.append(str(file_path))
        except Exception as e:
            self.logger.error(f"Erreur recherche fichiers MP3 : {e}")
        return sorted(mp3_files)
    
    def _extract_album_info(self, mp3_files: List[str]) -> Dict[str, Any]:
        """Extrait les informations globales de l'album."""
        # Placeholder pour l'extraction des informations d'album
        # En réalité, on lirait les métadonnées avec mutagen
        album_info = {
            'artist': 'Sample Artist',
            'album': 'Sample Album',
            'year': '2023',
            'total_tracks': len(mp3_files),
            'is_compilation': False
        }
        return album_info
    
    def _format_file_metadata(self, mp3_file: str, album_info: Dict) -> Dict[str, FormattingResult]:
        """Formate les métadonnées d'un fichier MP3."""
        # Placeholder pour le formatage d'un fichier
        # En réalité, on utiliserait mutagen pour lire/écrire les tags
        
        # Simulation des métadonnées
        metadata_fields = {
            'TIT2': f'Sample Title {Path(mp3_file).stem}',
            'TPE1': album_info.get('artist', 'Unknown Artist'),
            'TPE2': '',  # Interprète vide à remplir
            'TALB': album_info.get('album', 'Unknown Album'),
            'TRCK': str(len(Path(mp3_file).stem.split()) % 20 + 1),  # Simulation numéro
            'TYER': album_info.get('year', ''),
            'TCON': 'Rock',
        }
        
        results = {}
        for field_name, field_value in metadata_fields.items():
            result = self.format_metadata_field(field_name, field_value, metadata_fields)
            results[field_name] = result
        
        return results
    
    def _get_metadata_fields_for_preview(self, mp3_file: str) -> Dict[str, Any]:
        """Obtient les champs métadonnées pour aperçu."""
        # Simulation - en réalité on utiliserait mutagen
        return {
            'TIT2': f'sample title {Path(mp3_file).stem}',
            'TPE1': 'sample artist',
            'TPE2': '',  # Vide pour test copie artiste
            'TALB': 'sample album',
            'TRCK': '1',  # Test formatage
            'TYER': '2023',
            'TCON': '(13)',  # Test normalisation genre
        }
    
    def _build_standard_genres(self) -> List[str]:
        """Construit la liste des genres musicaux standardisés."""
        return [
            "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk", "Grunge",
            "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other", "Pop", "R&B",
            "Rap", "Reggae", "Rock", "Techno", "Industrial", "Alternative", "Ska",
            "Death Metal", "Pranks", "Soundtrack", "Euro-Techno", "Ambient",
            "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion", "Trance", "Classical",
            "Instrumental", "Acid", "House", "Game", "Sound Clip", "Gospel",
            "Noise", "Alternative Rock", "Bass", "Soul", "Punk", "Space",
            "Meditative", "Instrumental Pop", "Instrumental Rock", "Ethnic",
            "Gothic", "Darkwave", "Techno-Industrial", "Electronic", "Pop-Folk",
            "Eurodance", "Dream", "Southern Rock", "Comedy", "Cult", "Gangsta",
            "Top 40", "Christian Rap", "Pop/Funk", "Jungle", "Native US",
            "Cabaret", "New Wave", "Psychadelic", "Rave", "Showtunes", "Trailer",
            "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz", "Polka", "Retro",
            "Musical", "Rock & Roll", "Hard Rock"
        ]
    
    def _load_formatting_config(self) -> Dict[str, Any]:
        """Charge la configuration de formatage."""
        return {
            'track_zero_padding': True,
            'required_fields': ['TIT2', 'TPE1', 'TALB', 'TRCK'],
            'copy_artist_to_albumartist': True,
            'normalize_genres': True,
            'handle_compilation_years': True
        }
    
    def _create_error_result(self, album_path: str, errors: List[str]) -> AlbumFormattingResult:
        """Crée un résultat d'erreur."""
        return AlbumFormattingResult(
            album_path=album_path,
            files_processed=0,
            total_changes=0,
            field_changes={},
            warnings=[],
            errors=errors,
            processing_time=0.0
        )
    
    def _create_empty_result(self, album_path: str) -> AlbumFormattingResult:
        """Crée un résultat vide."""
        return AlbumFormattingResult(
            album_path=album_path,
            files_processed=0,
            total_changes=0,
            field_changes={},
            warnings=["Aucun fichier MP3 trouvé"],
            errors=[],
            processing_time=0.0
        )
    
    def _save_formatting_history(self, result: AlbumFormattingResult) -> None:
        """Sauvegarde l'historique de formatage en base."""
        try:
            self.db_manager.save_import_history(
                album_path=result.album_path,
                operation_type="metadata_formatting",
                files_processed=result.files_processed,
                changes_made=result.total_changes,
                details={
                    "field_changes": result.field_changes,
                    "processing_time": result.processing_time,
                    "warnings_count": len(result.warnings),
                    "errors_count": len(result.errors)
                }
            )
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde historique : {e}")


# Alias pour compatibilité
MetadataProcessor = MetadataFormatter