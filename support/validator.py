"""
Module 13 - Système de validation centralisé
Valide toutes les données d'entrée, formats et intégrité.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from PIL import Image
from support.logger import get_logger

@dataclass
class ValidationResult:
    """Résultat d'une validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]

class FileValidator:
    """Validateur pour les fichiers et chemins."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def validate_mp3_file(self, file_path: str) -> ValidationResult:
        """
        Valide un fichier MP3.
        
        Args:
            file_path: Chemin du fichier MP3
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            path = Path(file_path)
            
            # Vérification de l'existence
            if not path.exists():
                errors.append(f"File does not exist: {file_path}")
                return ValidationResult(False, errors, warnings, details)
            
            # Vérification de l'extension
            if path.suffix.lower() != '.mp3':
                errors.append(f"Not an MP3 file: {file_path}")
            
            # Vérification des permissions
            if not os.access(file_path, os.R_OK):
                errors.append(f"File not readable: {file_path}")
            
            if not os.access(file_path, os.W_OK):
                warnings.append(f"File not writable: {file_path}")
            
            # Validation avec mutagen
            try:
                audio_file = MP3(file_path)
                if audio_file is None:
                    errors.append(f"Invalid MP3 file: {file_path}")
                else:
                    # Détails du fichier
                    details['duration'] = getattr(audio_file.info, 'length', 0)
                    details['bitrate'] = getattr(audio_file.info, 'bitrate', 0)
                    details['channels'] = getattr(audio_file.info, 'channels', 0)
                    details['sample_rate'] = getattr(audio_file.info, 'sample_rate', 0)
                    
                    # Vérifications de qualité
                    if details['bitrate'] < 128:
                        warnings.append(f"Low bitrate ({details['bitrate']} kbps): {file_path}")
                    
                    if details['duration'] < 10:
                        warnings.append(f"Very short track ({details['duration']:.1f}s): {file_path}")
                    
            except Exception as e:
                errors.append(f"Error reading MP3 metadata: {e}")
            
        except Exception as e:
            errors.append(f"Unexpected error validating MP3: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_directory(self, dir_path: str) -> ValidationResult:
        """
        Valide un répertoire d'album.
        
        Args:
            dir_path: Chemin du répertoire
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            path = Path(dir_path)
            
            # Vérification de l'existence
            if not path.exists():
                errors.append(f"Directory does not exist: {dir_path}")
                return ValidationResult(False, errors, warnings, details)
            
            if not path.is_dir():
                errors.append(f"Path is not a directory: {dir_path}")
                return ValidationResult(False, errors, warnings, details)
            
            # Vérification des permissions
            if not os.access(dir_path, os.R_OK):
                errors.append(f"Directory not readable: {dir_path}")
            
            if not os.access(dir_path, os.W_OK):
                warnings.append(f"Directory not writable: {dir_path}")
            
            # Analyse du contenu
            mp3_files = list(path.glob("*.mp3"))
            cover_files = list(path.glob("*.jpg")) + list(path.glob("*.jpeg")) + list(path.glob("*.png"))
            
            details['mp3_count'] = len(mp3_files)
            details['cover_count'] = len(cover_files)
            details['total_size'] = sum(f.stat().st_size for f in path.iterdir() if f.is_file())
            
            # Validations
            if len(mp3_files) == 0:
                errors.append(f"No MP3 files found in directory: {dir_path}")
            
            if len(cover_files) == 0:
                warnings.append(f"No cover image found in directory: {dir_path}")
            
            # Vérification des fichiers indésirables
            unwanted_files = ['.DS_Store', 'Thumbs.db', '.db']
            found_unwanted = []
            for file in path.iterdir():
                if file.name in unwanted_files or file.name.endswith('.db'):
                    found_unwanted.append(file.name)
            
            if found_unwanted:
                details['unwanted_files'] = found_unwanted
                warnings.append(f"Unwanted files found: {', '.join(found_unwanted)}")
            
        except Exception as e:
            errors.append(f"Error validating directory: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_image_file(self, image_path: str, min_size: Tuple[int, int] = (250, 250)) -> ValidationResult:
        """
        Valide un fichier image de pochette.
        
        Args:
            image_path: Chemin de l'image
            min_size: Taille minimale (largeur, hauteur)
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            path = Path(image_path)
            
            # Vérification de l'existence
            if not path.exists():
                errors.append(f"Image file does not exist: {image_path}")
                return ValidationResult(False, errors, warnings, details)
            
            # Vérification de l'extension
            valid_extensions = ['.jpg', '.jpeg', '.png']
            if path.suffix.lower() not in valid_extensions:
                errors.append(f"Invalid image format: {path.suffix}")
            
            # Validation avec PIL
            try:
                with Image.open(image_path) as img:
                    details['width'] = img.width
                    details['height'] = img.height
                    details['format'] = img.format
                    details['mode'] = img.mode
                    
                    # Vérification de la taille minimale
                    if img.width < min_size[0] or img.height < min_size[1]:
                        errors.append(
                            f"Image too small: {img.width}x{img.height}, "
                            f"minimum required: {min_size[0]}x{min_size[1]}"
                        )
                    
                    # Vérifications de qualité
                    if img.width != img.height:
                        warnings.append(f"Image is not square: {img.width}x{img.height}")
                    
                    if img.width > 1500 or img.height > 1500:
                        warnings.append(f"Image very large: {img.width}x{img.height}")
                    
            except Exception as e:
                errors.append(f"Error reading image file: {e}")
            
        except Exception as e:
            errors.append(f"Error validating image: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)

class MetadataValidator:
    """Validateur pour les métadonnées."""
    
    def __init__(self):
        self.logger = get_logger()
        
        # Expressions régulières pour validation
        self.year_pattern = re.compile(r'^\d{4}$')
        self.track_pattern = re.compile(r'^\d{1,3}$')
        
        # Caractères interdits dans les noms de fichiers
        self.forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    def validate_metadata_field(self, field_name: str, value: str) -> ValidationResult:
        """
        Valide un champ de métadonnées.
        
        Args:
            field_name: Nom du champ
            value: Valeur à valider
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {'field': field_name, 'value': value}
        
        try:
            if not isinstance(value, str):
                value = str(value) if value is not None else ""
            
            # Validation générale
            if len(value.strip()) == 0:
                warnings.append(f"Empty {field_name}")
            
            # Validation spécifique par champ
            if field_name.lower() == 'year':
                if value and not self.year_pattern.match(value.strip()):
                    errors.append(f"Invalid year format: {value}")
                elif value:
                    year = int(value)
                    if year < 1900 or year > 2030:
                        warnings.append(f"Unusual year: {year}")
            
            elif field_name.lower() in ['track', 'tracknumber']:
                if value and not self.track_pattern.match(value.strip()):
                    errors.append(f"Invalid track number format: {value}")
            
            elif field_name.lower() in ['title', 'album', 'artist', 'albumartist']:
                # Vérification des caractères interdits pour les noms de fichiers
                forbidden_found = [char for char in self.forbidden_chars if char in value]
                if forbidden_found:
                    warnings.append(f"Forbidden characters in {field_name}: {', '.join(forbidden_found)}")
                
                # Vérification de la longueur
                if len(value) > 255:
                    errors.append(f"{field_name} too long: {len(value)} characters")
                
                # Vérification des caractères de contrôle
                if any(ord(char) < 32 for char in value):
                    warnings.append(f"Control characters found in {field_name}")
            
        except Exception as e:
            errors.append(f"Error validating {field_name}: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_complete_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Valide un ensemble complet de métadonnées.
        
        Args:
            metadata: Dictionnaire des métadonnées
            
        Returns:
            Résultat de validation combiné
        """
        all_errors = []
        all_warnings = []
        details = {'fields_validated': []}
        
        # Champs requis
        required_fields = ['title', 'artist', 'album']
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                all_errors.append(f"Missing required field: {field}")
        
        # Validation de chaque champ
        for field, value in metadata.items():
            result = self.validate_metadata_field(field, value)
            details['fields_validated'].append(field)
            
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        # Validations croisées
        if 'artist' in metadata and 'albumartist' in metadata:
            if metadata['artist'] and metadata['albumartist']:
                if metadata['artist'] != metadata['albumartist']:
                    all_warnings.append("Artist and AlbumArtist are different")
        
        is_valid = len(all_errors) == 0
        return ValidationResult(is_valid, all_errors, all_warnings, details)

class UserInputValidator:
    """Validateur pour les saisies utilisateur."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def validate_exception_word(self, word: str) -> ValidationResult:
        """
        Valide un mot d'exception de casse.
        
        Args:
            word: Mot à valider
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {'word': word}
        
        try:
            if not word or len(word.strip()) == 0:
                errors.append("Exception word cannot be empty")
                return ValidationResult(False, errors, warnings, details)
            
            word = word.strip()
            
            # Vérifications de base
            if len(word) > 100:
                errors.append("Exception word too long (max 100 characters)")
            
            if any(char.isdigit() for char in word):
                warnings.append("Exception word contains numbers")
            
            # Vérification des caractères spéciaux autorisés
            allowed_special = ['-', "'", '/', '&', '.', ' ']
            special_chars = [char for char in word if not char.isalnum() and char not in allowed_special]
            
            if special_chars:
                warnings.append(f"Unusual special characters: {', '.join(set(special_chars))}")
            
        except Exception as e:
            errors.append(f"Error validating exception word: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def validate_file_path_input(self, path: str, must_exist: bool = True) -> ValidationResult:
        """
        Valide un chemin de fichier saisi par l'utilisateur.
        
        Args:
            path: Chemin à valider
            must_exist: Si True, le chemin doit exister
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {'path': path}
        
        try:
            if not path or len(path.strip()) == 0:
                errors.append("Path cannot be empty")
                return ValidationResult(False, errors, warnings, details)
            
            path = path.strip()
            path_obj = Path(path)
            
            # Vérification de l'existence si requis
            if must_exist and not path_obj.exists():
                errors.append(f"Path does not exist: {path}")
            
            # Vérification de la validité du chemin
            try:
                # Test de création du Path (validation de la syntaxe)
                Path(path).resolve()
            except Exception:
                errors.append(f"Invalid path format: {path}")
            
            # Vérifications de sécurité
            if '..' in path:
                warnings.append("Path contains parent directory references")
            
            if len(path) > 260:  # Limite Windows
                warnings.append("Path very long (may cause issues on some systems)")
            
        except Exception as e:
            errors.append(f"Error validating path: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)

class Validator:
    """Validateur principal regroupant tous les types de validation."""
    
    def __init__(self):
        self.logger = get_logger()
        self.file_validator = FileValidator()
        self.metadata_validator = MetadataValidator()
        self.input_validator = UserInputValidator()
        
        self.logger.info("Validator initialized")
    
    def validate_album_import(self, album_path: str) -> ValidationResult:
        """
        Validation complète pour l'import d'un album.
        
        Args:
            album_path: Chemin du dossier album
            
        Returns:
            Résultat de validation combiné
        """
        all_errors = []
        all_warnings = []
        details = {'album_path': album_path}
        
        # Validation du répertoire
        dir_result = self.file_validator.validate_directory(album_path)
        all_errors.extend(dir_result.errors)
        all_warnings.extend(dir_result.warnings)
        details.update(dir_result.details)
        
        if dir_result.is_valid:
            # Validation des fichiers MP3
            mp3_files = list(Path(album_path).glob("*.mp3"))
            mp3_results = []
            
            for mp3_file in mp3_files[:10]:  # Limite pour éviter la surcharge
                result = self.file_validator.validate_mp3_file(str(mp3_file))
                mp3_results.append(result)
                
                if not result.is_valid:
                    all_errors.extend([f"MP3 {mp3_file.name}: {error}" for error in result.errors])
                all_warnings.extend([f"MP3 {mp3_file.name}: {warning}" for warning in result.warnings])
            
            details['mp3_validation_count'] = len(mp3_results)
            details['valid_mp3_count'] = sum(1 for r in mp3_results if r.is_valid)
        
        is_valid = len(all_errors) == 0
        return ValidationResult(is_valid, all_errors, all_warnings, details)
    
    def validate_directory_for_deletion(self, dir_path: str) -> ValidationResult:
        """
        Valide un répertoire pour suppression (pas besoin de MP3).
        
        Args:
            dir_path: Chemin du répertoire à supprimer
            
        Returns:
            Résultat de validation
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            path = Path(dir_path)
            
            # Vérification de l'existence
            if not path.exists():
                warnings.append(f"Directory already deleted: {dir_path}")
                return ValidationResult(True, errors, warnings, details)  # OK si déjà supprimé
            
            if not path.is_dir():
                errors.append(f"Path is not a directory: {dir_path}")
                return ValidationResult(False, errors, warnings, details)
            
            # Vérification des permissions de suppression
            parent_dir = path.parent
            if not os.access(parent_dir, os.W_OK):
                errors.append(f"Cannot delete directory - parent not writable: {dir_path}")
            
            # Calcul de la taille pour statistiques
            try:
                total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                details['total_size'] = total_size
                details['file_count'] = len([f for f in path.rglob('*') if f.is_file()])
                details['dir_count'] = len([f for f in path.rglob('*') if f.is_dir()])
            except Exception as e:
                warnings.append(f"Could not calculate directory size: {e}")
                details['total_size'] = 0
                
        except Exception as e:
            errors.append(f"Error validating directory for deletion: {e}")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, details)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé des capacités de validation.
        
        Returns:
            Dictionnaire des informations de validation
        """
        return {
            'supported_audio_formats': ['.mp3'],
            'supported_image_formats': ['.jpg', '.jpeg', '.png'],
            'min_image_size': (250, 250),
            'max_metadata_length': 255,
            'required_metadata_fields': ['title', 'artist', 'album'],
            'validation_categories': [
                'file_validation',
                'metadata_validation', 
                'user_input_validation',
                'album_import_validation'
            ]
        }