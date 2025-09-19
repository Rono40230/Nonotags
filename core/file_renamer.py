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

# Import Mutagen pour les métadonnées
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from support.logger import AppLogger
    from support.honest_logger import HonestLogger
    from support.config_manager import ConfigManager
    from support.state_manager import StateManager
    from support.validator import MetadataValidator, ValidationResult, FileValidator
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
            self.honest_logger = HonestLogger("FileRenamer")
            self.config_manager = ConfigManager()
            self.state_manager = StateManager()
            self.file_validator = FileValidator()  # Pour validate_directory
            self.metadata_validator = MetadataValidator()  # Pour les métadonnées
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
        
        # Construction du nom de fichier AVEC extension (nécessaire pour les vrais fichiers)
        filename = f"{track_number} - {clean_title}{extension}"
        
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
            self.honest_logger.warning(f"❌ [RÈGLE 17] Année vide ou None - Pas de traitement")
            return "", []
        
        year = year.strip()
        
        # Si c'est déjà une plage formatée (ex: "1995-2000")
        if re.match(r'^\d{4}-\d{4}$', year):
            rules_applied.append(RenamingRule.HANDLE_MULTI_YEAR)
            return year, rules_applied
        
        # Extraction des années individuelles
        years = re.findall(r'\b\d{4}\b', year)
        
        if not years:
            self.honest_logger.warning(f"❌ [RÈGLE 17] Aucune année valide détectée dans: '{year}'")
            return year, []  # Retourne tel quel si pas d'années détectées
        
        # Conversion en entiers et tri
        try:
            year_ints = sorted([int(y) for y in years if 1900 <= int(y) <= 2100])
            self.honest_logger.debug(f"📊 [RÈGLE 17] Années triées: {year_ints}")
            
            if len(year_ints) == 1:
                self.honest_logger.info(f"ℹ️ [RÈGLE 17] Année unique: {year_ints[0]} - Pas de modification")
                return str(year_ints[0]), []
            elif len(year_ints) >= 2:
                # Utilise la première et dernière année pour la plage
                min_year = year_ints[0]
                max_year = year_ints[-1]
                
                if min_year != max_year:
                    rules_applied.append(RenamingRule.HANDLE_MULTI_YEAR)
                    # Format compilation : (Année la plus ancienne-2 derniers chiffres de l'année la plus récente)
                    result = f"{min_year}-{str(max_year)[-2:]}"
                    return result, rules_applied
                else:
                    return str(min_year), []
        except ValueError as e:
            self.honest_logger.error(f"❌ [RÈGLE 17] Erreur conversion années: {e}")
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
            
            # 🔧 CORRECTION : Forcer le formatage du numéro de piste avec zéro initial
            if track_number and str(track_number).isdigit():
                if len(str(track_number)) == 1:
                    track_number = f"0{track_number}"
            elif track_number and '/' in str(track_number):
                # Format "1/12" → "01/12"
                parts = str(track_number).split('/')
                if parts[0].isdigit() and len(parts[0]) == 1:
                    track_number = f"0{parts[0]}/{parts[1]}"
            
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
                self.honest_logger.error(f"❌ [RÈGLE 15] Erreur preview: {preview.error}")
                return preview
            
            if not preview.renamed:
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
                    error_msg = "Trop de fichiers avec le même nom"
                    self.honest_logger.error(f"❌ [RÈGLE 15] {error_msg}")
                    raise Exception(error_msg)
            
            # Effectuer le renommage
            if new_path != file_path:
                shutil.move(file_path, new_path)
                
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
            self.honest_logger.error(f"❌ [RÈGLE 15] {error_msg}")
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
                self.honest_logger.error(f"❌ [RÈGLE 16] Erreur preview: {preview.error}")
                return preview
            
            if not preview.renamed:
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
                    error_msg = "Trop de dossiers avec le même nom"
                    self.honest_logger.error(f"❌ [RÈGLE 16] {error_msg}")
                    raise Exception(error_msg)
            
            # Effectuer le renommage
            if new_path != folder_path:
                shutil.move(folder_path, new_path)
                
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
            self.honest_logger.error(f"❌ [RÈGLE 16] {error_msg}")
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
            validation_result = self.file_validator.validate_directory(album_path)
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
            self.state_manager.update_album_processing_status(album_path, "renaming_files")
            
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
                first_file_validation = self.file_validator.validate_mp3_file(str(mp3_files[0]))
                if first_file_validation.is_valid and first_file_validation.metadata:
                    album_metadata = first_file_validation.metadata
            
            # Prévisualisation du renommage des fichiers
            file_results = []
            files_to_rename = 0
            
            for mp3_file in mp3_files:
                # Validation basique du fichier
                file_validation = self.file_validator.validate_mp3_file(str(mp3_file))
                if file_validation.is_valid:
                    # Extraction directe des métadonnées avec Mutagen
                    metadata = {}
                    try:
                        if MUTAGEN_AVAILABLE:
                            audio_file = MP3(str(mp3_file))
                            if audio_file and audio_file.tags:
                                tags = audio_file.tags
                                # Numéro de piste
                                if 'TRCK' in tags:
                                    track = str(tags['TRCK'])
                                    if '/' in track:
                                        track = track.split('/')[0]
                                    metadata['track_number'] = track
                                # Titre
                                if 'TIT2' in tags:
                                    metadata['title'] = str(tags['TIT2'])
                    except Exception as e:
                        self.honest_logger.warning(f"Erreur extraction métadonnées {mp3_file}: {e}")
                    
                    # Utilisation des métadonnées extraites
                    if metadata:
                        result = self.preview_file_renaming(str(mp3_file), metadata)
                        file_results.append(result)
                        if result.renamed:
                            files_to_rename += 1
                    else:
                        # Pas de métadonnées, utilisation de valeurs par défaut
                        default_metadata = {
                            'track_number': '01',
                            'title': Path(mp3_file).stem
                        }
                        result = self.preview_file_renaming(str(mp3_file), default_metadata)
                        file_results.append(result)
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
        Version corrigée sans dépendance aux métadonnées des validators.
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Début du renommage de l'album : {album_path}")
            
            # Mise à jour du statut
            self.state_manager.update_album_processing_status(album_path, "renaming_files")
            
            # Validation du dossier
            validation_result = self.file_validator.validate_directory(album_path)
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
            for pattern in ['*.mp3', '*.MP3', '*.Mp3', '*.mP3']:
                mp3_files.extend(album_dir.glob(pattern))
            mp3_files = list(set(mp3_files))
            
            # Collecte des métadonnées pour l'album (analyse de tous les fichiers pour compilations)
            album_metadata = {}
            all_years = set()  # Pour collecter toutes les années uniques
            
            if mp3_files and MUTAGEN_AVAILABLE:
                # Analyse du premier fichier pour l'album et l'artiste
                try:
                    audio_file = MP3(str(mp3_files[0]))
                    if audio_file and audio_file.tags:
                        tags = audio_file.tags
                        if 'TALB' in tags:
                            album_metadata['album'] = str(tags['TALB'])
                        if 'TPE1' in tags:
                            album_metadata['artist'] = str(tags['TPE1'])
                except Exception as e:
                    self.honest_logger.warning(f"Erreur extraction métadonnées album: {e}")
                
                # Collecte de toutes les années de tous les fichiers pour détecter les compilations
                for mp3_file in mp3_files:
                    try:
                        audio_file = MP3(str(mp3_file))
                        if audio_file and audio_file.tags:
                            tags = audio_file.tags
                            year = None
                            if 'TYER' in tags:
                                year = str(tags['TYER']).strip()
                            elif 'TDRC' in tags:
                                year = str(tags['TDRC']).strip()
                            
                            if year:
                                # Extraction des années du tag (peut contenir plusieurs années)
                                import re
                                years_found = re.findall(r'\b\d{4}\b', year)
                                for y in years_found:
                                    if 1900 <= int(y) <= 2100:
                                        all_years.add(y)
                    except Exception as e:
                        self.honest_logger.debug(f"Erreur extraction année {mp3_file}: {e}")
                
                # Construction de la string d'années pour la compilation
                if all_years:
                    if len(all_years) == 1:
                        album_metadata['year'] = list(all_years)[0]
                    else:
                        # Compilation détectée : assemblage de toutes les années
                        sorted_years = sorted(all_years)
                        year_string = ', '.join(sorted_years)
                        album_metadata['year'] = year_string
                        self.honest_logger.info(f"📀 Compilation détectée: {len(all_years)} années différentes ({sorted_years[0]}-{sorted_years[-1]})")
            
            # Renommage des fichiers
            file_results = []
            files_renamed = 0
            current_album_path = album_path
            
            for mp3_file in mp3_files:
                # Validation basique
                file_validation = self.file_validator.validate_mp3_file(str(mp3_file))
                if file_validation.is_valid:
                    # Extraction métadonnées directe
                    metadata = {}
                    try:
                        if MUTAGEN_AVAILABLE:
                            audio_file = MP3(str(mp3_file))
                            if audio_file and audio_file.tags:
                                tags = audio_file.tags
                                # Numéro de piste
                                if 'TRCK' in tags:
                                    track = str(tags['TRCK'])
                                    if '/' in track:
                                        track = track.split('/')[0]
                                    metadata['track_number'] = track
                                # Titre
                                if 'TIT2' in tags:
                                    metadata['title'] = str(tags['TIT2'])
                    except Exception as e:
                        self.honest_logger.warning(f"Erreur extraction métadonnées {mp3_file}: {e}")
                    
                    # Utilisation des métadonnées ou valeurs par défaut
                    if not metadata:
                        metadata = {
                            'track_number': '01',
                            'title': Path(mp3_file).stem
                        }
                    
                    result = self.rename_file(str(mp3_file), metadata)
                    file_results.append(result)
                    if result.renamed:
                        files_renamed += 1
                else:
                    # Fichier invalide
                    result = RenamingResult(
                        original_path=str(mp3_file),
                        new_path=str(mp3_file),
                        renamed=False,
                        rules_applied=[],
                        warnings=[],
                        error="Fichier MP3 invalide"
                    )
                    file_results.append(result)
            
            # Renommage du dossier (optionnel)
            folder_result = None
            folder_renamed = False
            if album_metadata and self.config.rename_folders:
                try:
                    folder_result = self.rename_folder(current_album_path, album_metadata)
                    if folder_result.renamed:
                        folder_renamed = True
                        current_album_path = folder_result.new_path
                except Exception as e:
                    self.honest_logger.warning(f"Erreur renommage dossier: {e}")
            
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
            self.state_manager.update_album_processing_status(current_album_path, "file_renaming_completed")
            
            # Enregistrement en base
            try:
                self.db_manager.add_import_history(
                    folder_path=current_album_path,
                    import_type="file_renaming",
                    status="completed" if files_renamed > 0 else "no_changes",
                    files_processed=len(mp3_files),
                    processing_time=processing_time
                )
            except Exception as e:
                self.honest_logger.warning(f"Erreur enregistrement base: {e}")
            
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
            error_msg = f"Erreur lors du renommage de l'album {album_path} : {str(e)}"
            self.logger.error(error_msg)
            self.honest_logger.error(error_msg)
            
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
    
    def rename_album_files(self, album_path: str) -> bool:
        """
        Méthode de compatibilité pour processing_orchestrator.py.
        Renomme les fichiers d'un album.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            bool: True si le renommage a réussi, False sinon
        """
        try:
            result = self.rename_album(album_path)
            success = len(result.errors) == 0
            
            if success:
                self.logger.info(f"Renommage réussi pour : {album_path}")
            else:
                self.logger.error(f"Erreurs lors du renommage de : {album_path}")
                for error in result.errors:
                    self.logger.error(f"  - {error}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erreur critique lors du renommage de {album_path}: {str(e)}", exc_info=True)
            return False
    
    def get_mp3_metadata(self, file_path: str) -> Dict[str, str]:
        """
        Extrait les métadonnées d'un fichier MP3.
        
        Args:
            file_path: Chemin vers le fichier MP3
            
        Returns:
            Dictionnaire des métadonnées
        """
        metadata = {}
        
        if not MUTAGEN_AVAILABLE:
            return metadata
            
        try:
            audio_file = MP3(file_path)
            if audio_file is not None:
                # Extraction des métadonnées principales
                metadata['TRCK'] = str(audio_file.get('TRCK', [''])[0])
                metadata['TIT2'] = str(audio_file.get('TIT2', [''])[0])
                metadata['TALB'] = str(audio_file.get('TALB', [''])[0])
                metadata['TPE1'] = str(audio_file.get('TPE1', [''])[0])
                metadata['TDRC'] = str(audio_file.get('TDRC', [''])[0])
                
                # Nettoyage des valeurs vides
                for key in list(metadata.keys()):
                    if not metadata[key] or metadata[key] == 'None':
                        del metadata[key]
                        
        except Exception as e:
            self.logger.warning(f"Erreur extraction métadonnées {file_path}: {e}")
            
        return metadata