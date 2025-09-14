"""
Module 5 - File Renamer (GROUPE 5)
Renommage standardisé des fichiers et dossiers MP3
"""

import os
import re
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import time

try:
    from support.logger import AppLogger
    from support.config_manager import ConfigManager
    from support.state_manager import StateManager
    from support.validator import MetadataValidator, ValidationResult
    from database.db_manager import DatabaseManager
except ImportError as e:
    print(f"Erreur d'import des modules de support : {e}")


class RenamingRule(Enum):
    """Énumération des règles de renommage appliquées."""
    FORMAT_TRACK_FILENAME = "format_track_filename"
    FORMAT_ALBUM_FOLDER = "format_album_folder"
    HANDLE_MULTI_YEAR = "handle_multi_year"
    SANITIZE_FILENAME = "sanitize_filename"
    HANDLE_DUPLICATE_NAME = "handle_duplicate_name"
    PRESERVE_EXTENSION = "preserve_extension"


@dataclass
class RenamingResult:
    """Résultat du renommage d'un fichier ou dossier."""
    original_path: str
    new_path: str
    renamed: bool
    rules_applied: List[RenamingRule]
    warnings: List[str]
    error: Optional[str] = None


@dataclass
class AlbumRenamingResult:
    """Résultat du renommage complet d'un album."""
    album_path: str
    files_renamed: int
    folder_renamed: bool
    total_files: int
    file_results: List[RenamingResult]
    folder_result: Optional[RenamingResult]
    processing_time: float
    errors: List[str]
    warnings: List[str]


class FileRenamer:
    """
    Module de renommage des fichiers et dossiers MP3.
    
    Fonctionnalités :
    - Renommage fichiers : "(N° piste) - Titre.mp3"
    - Renommage dossiers : "(Année) Album"
    - Gestion multi-années : "(année1-année2) Album"
    - Nettoyage des noms de fichiers
    - Gestion des doublons
    """
    
    def __init__(self):
        """Initialise le module de renommage."""
        try:
            # Initialisation des modules de support
            from support.logger import get_logger
            self.logger = get_logger().main_logger
            self.config_manager = ConfigManager()
            self.state_manager = StateManager()
            self.validator = MetadataValidator()
            self.db_manager = DatabaseManager()
            
            # Configuration du module
            self.config = self.config_manager.processing
            
            # Caractères interdits dans les noms de fichiers
            self.invalid_chars = r'[<>:"/\\|?*]'
            
            # Extensions de fichiers supportées
            self.supported_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav'}
            
            self.logger.info("FileRenamer initialisé avec succès")
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de FileRenamer : {e}")
            raise
    
    def sanitize_filename(self, filename: str) -> Tuple[str, List[RenamingRule]]:
        """
        Nettoie un nom de fichier en supprimant les caractères interdits.
        
        Args:
            filename: Nom de fichier à nettoyer
            
        Returns:
            Tuple[str, List[RenamingRule]]: Nom nettoyé et règles appliquées
        """
        original = filename
        rules_applied = []
        
        # Remplacement des caractères interdits par des alternatives
        replacements = {
            '<': '(',
            '>': ')',
            ':': '-',
            '"': "'",
            '/': '-',
            '\\': '-',
            '|': '-',
            '?': '',
            '*': ''
        }
        
        for char, replacement in replacements.items():
            if char in filename:
                filename = filename.replace(char, replacement)
        
        # Nettoyage des espaces multiples
        filename = re.sub(r'\s+', ' ', filename)
        
        # Suppression des espaces en début/fin
        filename = filename.strip()
        
        # Limitation de la longueur (255 caractères max pour la plupart des systèmes)
        if len(filename) > 200:  # Garde de la marge pour l'extension
            filename = filename[:200].strip()
        
        if original != filename:
            rules_applied.append(RenamingRule.SANITIZE_FILENAME)
        
        return filename, rules_applied
    
    def format_track_filename(self, track_number: str, title: str, extension: str = '.mp3') -> Tuple[str, List[RenamingRule]]:
        """
        Formate le nom d'un fichier de piste selon le pattern "(N° piste) - Titre.ext".
        
        Args:
            track_number: Numéro de piste (déjà formaté avec zéro initial)
            title: Titre de la piste
            extension: Extension du fichier
            
        Returns:
            Tuple[str, List[RenamingRule]]: Nom formaté et règles appliquées
        """
        rules_applied = []
        
        # Nettoyage du numéro de piste (garder seulement la partie avant le "/")
        if '/' in track_number:
            track_number = track_number.split('/')[0]
        
        # Formatage avec zéro initial si nécessaire
        if track_number.isdigit() and len(track_number) == 1:
            track_number = f"0{track_number}"
        
        # Nettoyage du titre
        clean_title, title_rules = self.sanitize_filename(title)
        rules_applied.extend(title_rules)
        
        # Construction du nom de fichier
        filename = f"({track_number}) - {clean_title}{extension}"
        
        rules_applied.append(RenamingRule.FORMAT_TRACK_FILENAME)
        rules_applied.append(RenamingRule.PRESERVE_EXTENSION)
        
        return filename, rules_applied
    
    def format_album_folder(self, year: str, album: str) -> Tuple[str, List[RenamingRule]]:
        """
        Formate le nom d'un dossier d'album selon le pattern "(Année) Album".
        
        Args:
            year: Année de l'album
            album: Nom de l'album
            
        Returns:
            Tuple[str, List[RenamingRule]]: Nom formaté et règles appliquées
        """
        rules_applied = []
        
        # Gestion des années multiples (compilations)
        formatted_year, year_rules = self._handle_multi_year_folder(year)
        rules_applied.extend(year_rules)
        
        # Nettoyage du nom d'album
        clean_album, album_rules = self.sanitize_filename(album)
        rules_applied.extend(album_rules)
        
        # Construction du nom de dossier
        if formatted_year:
            folder_name = f"({formatted_year}) {clean_album}"
        else:
            folder_name = clean_album
            self.logger.warning(f"Pas d'année disponible pour l'album : {album}")
        
        rules_applied.append(RenamingRule.FORMAT_ALBUM_FOLDER)
        
        return folder_name, rules_applied
    
    def _handle_multi_year_folder(self, year: str) -> Tuple[str, List[RenamingRule]]:
        """
        Gère les années multiples pour les dossiers de compilation.
        
        Args:
            year: Année ou plage d'années
            
        Returns:
            Tuple[str, List[RenamingRule]]: Année formatée et règles appliquées
        """
        rules_applied = []
        
        if not year or not year.strip():
            return "", []
        
        year = year.strip()
        
        # Si c'est déjà une plage formatée (ex: "1995-2000")
        if re.match(r'^\d{4}-\d{4}$', year):
            rules_applied.append(RenamingRule.HANDLE_MULTI_YEAR)
            return year, rules_applied
        
        # Extraction des années individuelles
        years = re.findall(r'\b\d{4}\b', year)
        
        if not years:
            return year, []  # Retourne tel quel si pas d'années détectées
        
        # Conversion en entiers et tri
        try:
            year_ints = sorted([int(y) for y in years if 1900 <= int(y) <= 2100])
            
            if len(year_ints) == 1:
                return str(year_ints[0]), []
            elif len(year_ints) >= 2:
                # Utilise la première et dernière année pour la plage
                min_year = year_ints[0]
                max_year = year_ints[-1]
                
                if min_year != max_year:
                    rules_applied.append(RenamingRule.HANDLE_MULTI_YEAR)
                    return f"{min_year}-{max_year}", rules_applied
                else:
                    return str(min_year), []
        except ValueError:
            pass
        
        return year, []
    
    def preview_file_renaming(self, file_path: str, metadata: Dict[str, str]) -> RenamingResult:
        """
        Prévisualise le renommage d'un fichier sans l'effectuer.
        
        Args:
            file_path: Chemin du fichier
            metadata: Métadonnées du fichier
            
        Returns:
            RenamingResult: Résultat de la prévisualisation
        """
        try:
            path_obj = Path(file_path)
            original_name = path_obj.name
            extension = path_obj.suffix
            
            # Récupération des métadonnées nécessaires
            track_number = metadata.get('TRCK', metadata.get('track_number', '1'))
            title = metadata.get('TIT2', metadata.get('title', 'Unknown Title'))
            
            # Formatage du nouveau nom
            new_name, rules = self.format_track_filename(track_number, title, extension)
            
            # Construction du nouveau chemin
            new_path = str(path_obj.parent / new_name)
            
            # Vérification si renommage nécessaire
            renamed = (original_name != new_name)
            
            warnings = []
            
            # Vérification de l'existence du fichier cible
            if renamed and Path(new_path).exists():
                warnings.append(f"Le fichier cible existe déjà : {new_name}")
            
            return RenamingResult(
                original_path=file_path,
                new_path=new_path,
                renamed=renamed,
                rules_applied=rules,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la prévisualisation de {file_path} : {e}")
            return RenamingResult(
                original_path=file_path,
                new_path=file_path,
                renamed=False,
                rules_applied=[],
                warnings=[],
                error=str(e)
            )
    
    def preview_folder_renaming(self, folder_path: str, album_metadata: Dict[str, str]) -> RenamingResult:
        """
        Prévisualise le renommage d'un dossier d'album sans l'effectuer.
        
        Args:
            folder_path: Chemin du dossier
            album_metadata: Métadonnées de l'album
            
        Returns:
            RenamingResult: Résultat de la prévisualisation
        """
        try:
            path_obj = Path(folder_path)
            original_name = path_obj.name
            
            # Récupération des métadonnées nécessaires
            year = album_metadata.get('TYER', album_metadata.get('year', ''))
            album = album_metadata.get('TALB', album_metadata.get('album', 'Unknown Album'))
            
            # Formatage du nouveau nom
            new_name, rules = self.format_album_folder(year, album)
            
            # Construction du nouveau chemin
            new_path = str(path_obj.parent / new_name)
            
            # Vérification si renommage nécessaire
            renamed = (original_name != new_name)
            
            warnings = []
            
            # Vérification de l'existence du dossier cible
            if renamed and Path(new_path).exists():
                warnings.append(f"Le dossier cible existe déjà : {new_name}")
            
            return RenamingResult(
                original_path=folder_path,
                new_path=new_path,
                renamed=renamed,
                rules_applied=rules,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la prévisualisation de {folder_path} : {e}")
            return RenamingResult(
                original_path=folder_path,
                new_path=folder_path,
                renamed=False,
                rules_applied=[],
                warnings=[],
                error=str(e)
            )
    
    def rename_file(self, file_path: str, metadata: Dict[str, str]) -> RenamingResult:
        """
        Renomme un fichier selon les règles définies.
        
        Args:
            file_path: Chemin du fichier à renommer
            metadata: Métadonnées du fichier
            
        Returns:
            RenamingResult: Résultat du renommage
        """
        try:
            # Prévisualisation pour obtenir le nouveau nom
            preview = self.preview_file_renaming(file_path, metadata)
            
            if preview.error:
                return preview
            
            if not preview.renamed:
                self.logger.debug(f"Pas de renommage nécessaire pour : {file_path}")
                return preview
            
            # Gestion des conflits de noms
            new_path = preview.new_path
            counter = 1
            original_new_path = new_path
            
            while Path(new_path).exists() and new_path != file_path:
                # Ajout d'un suffixe numérique
                path_obj = Path(original_new_path)
                stem = path_obj.stem
                suffix = path_obj.suffix
                new_path = str(path_obj.parent / f"{stem} ({counter}){suffix}")
                counter += 1
                
                if counter > 100:  # Protection contre boucle infinie
                    raise Exception("Trop de fichiers avec le même nom")
            
            # Effectuer le renommage
            if new_path != file_path:
                shutil.move(file_path, new_path)
                self.logger.info(f"Fichier renommé : {Path(file_path).name} → {Path(new_path).name}")
                
                # Mise à jour des règles si conflit résolu
                rules = preview.rules_applied.copy()
                if new_path != original_new_path:
                    rules.append(RenamingRule.HANDLE_DUPLICATE_NAME)
                
                return RenamingResult(
                    original_path=file_path,
                    new_path=new_path,
                    renamed=True,
                    rules_applied=rules,
                    warnings=preview.warnings
                )
            
            return preview
            
        except Exception as e:
            error_msg = f"Erreur lors du renommage de {file_path} : {e}"
            self.logger.error(error_msg)
            return RenamingResult(
                original_path=file_path,
                new_path=file_path,
                renamed=False,
                rules_applied=[],
                warnings=[],
                error=error_msg
            )
    
    def rename_folder(self, folder_path: str, album_metadata: Dict[str, str]) -> RenamingResult:
        """
        Renomme un dossier d'album selon les règles définies.
        
        Args:
            folder_path: Chemin du dossier à renommer
            album_metadata: Métadonnées de l'album
            
        Returns:
            RenamingResult: Résultat du renommage
        """
        try:
            # Prévisualisation pour obtenir le nouveau nom
            preview = self.preview_folder_renaming(folder_path, album_metadata)
            
            if preview.error:
                return preview
            
            if not preview.renamed:
                self.logger.debug(f"Pas de renommage nécessaire pour : {folder_path}")
                return preview
            
            # Gestion des conflits de noms
            new_path = preview.new_path
            counter = 1
            original_new_path = new_path
            
            while Path(new_path).exists() and new_path != folder_path:
                # Ajout d'un suffixe numérique
                path_obj = Path(original_new_path)
                new_path = str(path_obj.parent / f"{path_obj.name} ({counter})")
                counter += 1
                
                if counter > 100:  # Protection contre boucle infinie
                    raise Exception("Trop de dossiers avec le même nom")
            
            # Effectuer le renommage
            if new_path != folder_path:
                shutil.move(folder_path, new_path)
                self.logger.info(f"Dossier renommé : {Path(folder_path).name} → {Path(new_path).name}")
                
                # Mise à jour des règles si conflit résolu
                rules = preview.rules_applied.copy()
                if new_path != original_new_path:
                    rules.append(RenamingRule.HANDLE_DUPLICATE_NAME)
                
                return RenamingResult(
                    original_path=folder_path,
                    new_path=new_path,
                    renamed=True,
                    rules_applied=rules,
                    warnings=preview.warnings
                )
            
            return preview
            
        except Exception as e:
            error_msg = f"Erreur lors du renommage de {folder_path} : {e}"
            self.logger.error(error_msg)
            return RenamingResult(
                original_path=folder_path,
                new_path=folder_path,
                renamed=False,
                rules_applied=[],
                warnings=[],
                error=error_msg
            )
    
    def preview_album_renaming(self, album_path: str) -> AlbumRenamingResult:
        """
        Prévisualise le renommage complet d'un album sans l'effectuer.
        
        Args:
            album_path: Chemin du dossier d'album
            
        Returns:
            AlbumRenamingResult: Résultat de la prévisualisation
        """
        start_time = time.time()
        
        try:
            # Validation du dossier
            validation_result = self.validator.validate_directory(album_path)
            if not validation_result.is_valid:
                return AlbumRenamingResult(
                    album_path=album_path,
                    files_renamed=0,
                    folder_renamed=False,
                    total_files=0,
                    file_results=[],
                    folder_result=None,
                    processing_time=time.time() - start_time,
                    errors=[f"Dossier invalide : {', '.join(validation_result.errors)}"],
                    warnings=validation_result.warnings
                )
            
            # Mise à jour du statut
            self.state_manager.set_status("renaming_files")
            
            # Recherche des fichiers MP3
            album_dir = Path(album_path)
            mp3_files = []
            # Recherche avec différentes casses pour l'extension
            for pattern in ['*.mp3', '*.MP3', '*.Mp3', '*.mP3']:
                mp3_files.extend(album_dir.glob(pattern))
            # Supprime les doublons potentiels
            mp3_files = list(set(mp3_files))
            
            # Collecte des métadonnées pour l'album (du premier fichier)
            album_metadata = {}
            if mp3_files:
                first_file_validation = self.validator.validate_mp3_file(str(mp3_files[0]))
                if first_file_validation.is_valid and first_file_validation.metadata:
                    album_metadata = first_file_validation.metadata
            
            # Prévisualisation du renommage des fichiers
            file_results = []
            files_to_rename = 0
            
            for mp3_file in mp3_files:
                file_validation = self.validator.validate_mp3_file(str(mp3_file))
                if file_validation.is_valid and file_validation.metadata:
                    result = self.preview_file_renaming(str(mp3_file), file_validation.metadata)
                    file_results.append(result)
                    if result.renamed:
                        files_to_rename += 1
                else:
                    # Fichier invalide, mais on l'inclut dans les résultats
                    result = RenamingResult(
                        original_path=str(mp3_file),
                        new_path=str(mp3_file),
                        renamed=False,
                        rules_applied=[],
                        warnings=[],
                        error="Fichier MP3 invalide ou métadonnées manquantes"
                    )
                    file_results.append(result)
            
            # Prévisualisation du renommage du dossier
            folder_result = None
            folder_renamed = False
            if album_metadata:
                folder_result = self.preview_folder_renaming(album_path, album_metadata)
                folder_renamed = folder_result.renamed
            
            processing_time = time.time() - start_time
            
            # Collecte des erreurs et avertissements
            errors = []
            warnings = []
            
            for result in file_results:
                if result.error:
                    errors.append(result.error)
                warnings.extend(result.warnings)
            
            if folder_result and folder_result.error:
                errors.append(folder_result.error)
            if folder_result:
                warnings.extend(folder_result.warnings)
            
            return AlbumRenamingResult(
                album_path=album_path,
                files_renamed=files_to_rename,
                folder_renamed=folder_renamed,
                total_files=len(mp3_files),
                file_results=file_results,
                folder_result=folder_result,
                processing_time=processing_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la prévisualisation de l'album {album_path} : {e}"
            self.logger.error(error_msg)
            return AlbumRenamingResult(
                album_path=album_path,
                files_renamed=0,
                folder_renamed=False,
                total_files=0,
                file_results=[],
                folder_result=None,
                processing_time=time.time() - start_time,
                errors=[error_msg],
                warnings=[]
            )
    
    def rename_album(self, album_path: str) -> AlbumRenamingResult:
        """
        Renomme tous les fichiers et le dossier d'un album.
        
        Args:
            album_path: Chemin du dossier d'album
            
        Returns:
            AlbumRenamingResult: Résultat du renommage complet
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Début du renommage de l'album : {album_path}")
            
            # Mise à jour du statut
            self.state_manager.set_status("renaming_files")
            
            # Validation du dossier
            validation_result = self.validator.validate_directory(album_path)
            if not validation_result.is_valid:
                return AlbumRenamingResult(
                    album_path=album_path,
                    files_renamed=0,
                    folder_renamed=False,
                    total_files=0,
                    file_results=[],
                    folder_result=None,
                    processing_time=time.time() - start_time,
                    errors=[f"Dossier invalide : {', '.join(validation_result.errors)}"],
                    warnings=validation_result.warnings
                )
            
            # Recherche des fichiers MP3
            album_dir = Path(album_path)
            mp3_files = []
            # Recherche avec différentes casses pour l'extension
            for pattern in ['*.mp3', '*.MP3', '*.Mp3', '*.mP3']:
                mp3_files.extend(album_dir.glob(pattern))
            # Supprime les doublons potentiels
            mp3_files = list(set(mp3_files))
            
            # Collecte des métadonnées pour l'album (du premier fichier)
            album_metadata = {}
            if mp3_files:
                first_file_validation = self.validator.validate_mp3_file(str(mp3_files[0]))
                if first_file_validation.is_valid and first_file_validation.metadata:
                    album_metadata = first_file_validation.metadata
            
            # Renommage des fichiers
            file_results = []
            files_renamed = 0
            current_album_path = album_path  # Peut changer si le dossier est renommé
            
            for mp3_file in mp3_files:
                file_validation = self.validator.validate_mp3_file(str(mp3_file))
                if file_validation.is_valid and file_validation.metadata:
                    result = self.rename_file(str(mp3_file), file_validation.metadata)
                    file_results.append(result)
                    if result.renamed:
                        files_renamed += 1
                else:
                    # Fichier invalide, mais on l'inclut dans les résultats
                    result = RenamingResult(
                        original_path=str(mp3_file),
                        new_path=str(mp3_file),
                        renamed=False,
                        rules_applied=[],
                        warnings=[],
                        error="Fichier MP3 invalide ou métadonnées manquantes"
                    )
                    file_results.append(result)
            
            # Renommage du dossier (après les fichiers pour éviter les problèmes de chemins)
            folder_result = None
            folder_renamed = False
            
            if album_metadata:
                folder_result = self.rename_folder(current_album_path, album_metadata)
                folder_renamed = folder_result.renamed
                if folder_renamed:
                    current_album_path = folder_result.new_path
            
            processing_time = time.time() - start_time
            
            # Collecte des erreurs et avertissements
            errors = []
            warnings = []
            
            for result in file_results:
                if result.error:
                    errors.append(result.error)
                warnings.extend(result.warnings)
            
            if folder_result and folder_result.error:
                errors.append(folder_result.error)
            if folder_result:
                warnings.extend(folder_result.warnings)
            
            # Logging du résultat
            self.logger.info(
                f"Renommage terminé pour {album_path}: "
                f"{files_renamed}/{len(mp3_files)} fichiers, "
                f"dossier: {'Oui' if folder_renamed else 'Non'}"
            )
            
            # Mise à jour du statut
            self.state_manager.set_status("file_renaming_completed")
            
            # Enregistrement en base
            try:
                self.db_manager.add_import_history(
                    folder_path=current_album_path,
                    action="rename_album",
                    details={
                        "files_renamed": files_renamed,
                        "folder_renamed": folder_renamed,
                        "total_files": len(mp3_files),
                        "processing_time": processing_time
                    }
                )
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'enregistrement en base : {e}")
            
            return AlbumRenamingResult(
                album_path=current_album_path,
                files_renamed=files_renamed,
                folder_renamed=folder_renamed,
                total_files=len(mp3_files),
                file_results=file_results,
                folder_result=folder_result,
                processing_time=processing_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Erreur lors du renommage de l'album {album_path} : {e}"
            self.logger.error(error_msg)
            return AlbumRenamingResult(
                album_path=album_path,
                files_renamed=0,
                folder_renamed=False,
                total_files=0,
                file_results=[],
                folder_result=None,
                processing_time=time.time() - start_time,
                errors=[error_msg],
                warnings=[]
            )
