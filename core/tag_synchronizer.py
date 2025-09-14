"""
Module 6 - Tag Synchronizer (GROUPE 6)
Finalisation et synchronisation des métadonnées MP3
"""

import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Union
from enum import Enum
import time
from PIL import Image
import tempfile

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TYER, TCON, TRCK, TPE2, TLEN
    from mutagen.id3._util import ID3NoHeaderError
    from support.logger import get_logger
    from support.config_manager import ConfigManager
    from support.state_manager import StateManager
    from support.validator import MetadataValidator, ValidationResult
    from database.db_manager import DatabaseManager
except ImportError as e:
    print(f"Erreur d'import des modules de support : {e}")


class SynchronizationAction(Enum):
    """Énumération des actions de synchronisation."""
    ASSOCIATE_COVER = "associate_cover"
    UPDATE_TAGS = "update_tags"
    VALIDATE_CONSISTENCY = "validate_consistency"
    BACKUP_ORIGINAL = "backup_original"
    RESTORE_FROM_BACKUP = "restore_from_backup"


class CoverAssociationResult(Enum):
    """Résultats possibles de l'association de pochette."""
    SUCCESS = "success"
    COVER_NOT_FOUND = "cover_not_found"
    INVALID_FORMAT = "invalid_format"
    SIZE_TOO_SMALL = "size_too_small"
    ALREADY_EXISTS = "already_exists"
    ERROR = "error"


@dataclass
class SynchronizationResult:
    """Résultat de la synchronisation d'un fichier."""
    file_path: str
    cover_associated: bool
    tags_updated: bool
    actions_performed: List[SynchronizationAction]
    cover_result: Optional[CoverAssociationResult]
    warnings: List[str]
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class AlbumSynchronizationResult:
    """Résultat de la synchronisation complète d'un album."""
    album_path: str
    files_processed: int
    covers_associated: int
    tags_updated: int
    total_files: int
    file_results: List[SynchronizationResult]
    processing_time: float
    errors: List[str]
    warnings: List[str]


class TagSynchronizer:
    """
    Module de finalisation et synchronisation des métadonnées MP3.
    
    Fonctionnalités :
    - Association automatique des pochettes cover.jpg
    - Synchronisation temps réel des tags physiques
    - Validation de cohérence des métadonnées
    - Sauvegarde et restauration des originaux
    """
    
    def __init__(self):
        """Initialise le module de synchronisation."""
        try:
            # Initialisation des modules de support
            self.logger = get_logger().main_logger
            self.config_manager = ConfigManager()
            self.state_manager = StateManager()
            self.validator = MetadataValidator()
            self.db_manager = DatabaseManager()
            
            # Configuration du module
            self.config = self.config_manager.processing
            
            # Formats d'images supportés pour les pochettes
            self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
            
            # Taille minimale pour les pochettes (pixels)
            self.min_cover_size = (200, 200)
            
            # Taille maximale recommandée (pour éviter des fichiers trop volumineux)
            self.max_cover_size = (1000, 1000)
            
            # Extensions audio supportées
            self.supported_audio_formats = {'.mp3', '.flac', '.m4a', '.ogg', '.wav'}
            
            self.logger.info("TagSynchronizer initialisé avec succès")
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de TagSynchronizer : {e}")
            raise
    
    def find_cover_image(self, directory: str) -> Optional[str]:
        """
        Recherche un fichier de pochette dans le dossier.
        
        Args:
            directory: Chemin du dossier à analyser
            
        Returns:
            Optional[str]: Chemin vers le fichier de pochette trouvé
        """
        try:
            dir_path = Path(directory)
            
            # Noms de fichiers prioritaires pour les pochettes
            priority_names = [
                'cover.jpg', 'cover.jpeg', 'cover.png',
                'folder.jpg', 'folder.jpeg', 'folder.png',
                'front.jpg', 'front.jpeg', 'front.png',
                'album.jpg', 'album.jpeg', 'album.png'
            ]
            
            # Recherche prioritaire
            for name in priority_names:
                cover_file = dir_path / name
                if cover_file.exists() and cover_file.suffix.lower() in self.supported_image_formats:
                    return str(cover_file)
            
            # Recherche élargie de tous les fichiers images
            for file_path in dir_path.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.supported_image_formats):
                    return str(file_path)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de pochette dans {directory} : {e}")
            return None
    
    def validate_cover_image(self, image_path: str) -> Tuple[bool, List[str]]:
        """
        Valide un fichier image pour l'utilisation comme pochette.
        
        Args:
            image_path: Chemin vers le fichier image
            
        Returns:
            Tuple[bool, List[str]]: (Validité, Liste des avertissements)
        """
        warnings = []
        
        try:
            if not Path(image_path).exists():
                return False, ["Fichier image introuvable"]
            
            # Validation du format
            if not Path(image_path).suffix.lower() in self.supported_image_formats:
                return False, ["Format d'image non supporté"]
            
            # Validation avec PIL
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Vérification de la taille minimale
                if width < self.min_cover_size[0] or height < self.min_cover_size[1]:
                    return False, [f"Image trop petite : {width}x{height} pixels (minimum : {self.min_cover_size[0]}x{self.min_cover_size[1]})"]
                
                # Avertissement pour les images non carrées
                if abs(width - height) > min(width, height) * 0.1:
                    warnings.append(f"Image non carrée : {width}x{height}")
                
                # Avertissement pour les très grandes images
                if width > self.max_cover_size[0] or height > self.max_cover_size[1]:
                    warnings.append(f"Image très grande : {width}x{height} pixels (recommandé : max {self.max_cover_size[0]}x{self.max_cover_size[1]})")
                
                # Validation du mode couleur
                if img.mode not in ('RGB', 'RGBA', 'L'):
                    warnings.append(f"Mode couleur inhabituel : {img.mode}")
            
            return True, warnings
            
        except Exception as e:
            return False, [f"Erreur lors de la validation de l'image : {e}"]
    
    def associate_cover_to_mp3(self, mp3_path: str, cover_path: str) -> CoverAssociationResult:
        """
        Associe une pochette à un fichier MP3.
        
        Args:
            mp3_path: Chemin vers le fichier MP3
            cover_path: Chemin vers l'image de pochette
            
        Returns:
            CoverAssociationResult: Résultat de l'association
        """
        try:
            if not cover_path:
                return CoverAssociationResult.COVER_NOT_FOUND
            
            # Validation de l'image
            is_valid, warnings = self.validate_cover_image(cover_path)
            if not is_valid:
                self.logger.warning(f"Image invalide {cover_path} : {warnings}")
                return CoverAssociationResult.INVALID_FORMAT
            
            # Chargement du fichier MP3
            try:
                audio_file = MP3(mp3_path, ID3=ID3)
            except ID3NoHeaderError:
                # Création d'un nouveau header ID3 si absent
                audio_file = MP3(mp3_path)
                audio_file.add_tags()
            
            # Vérification si une pochette existe déjà
            if audio_file.tags:
                for key in audio_file.tags:
                    if key.startswith('APIC'):
                        self.logger.debug(f"Pochette existante trouvée dans {mp3_path}")
                        return CoverAssociationResult.ALREADY_EXISTS
            
            # Lecture de l'image
            with open(cover_path, 'rb') as img_file:
                img_data = img_file.read()
            
            # Détermination du type MIME
            cover_ext = Path(cover_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.bmp': 'image/bmp',
                '.gif': 'image/gif'
            }
            mime_type = mime_types.get(cover_ext, 'image/jpeg')
            
            # Ajout de la pochette
            audio_file.tags.add(
                APIC(
                    encoding=3,  # UTF-8
                    mime=mime_type,
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=img_data
                )
            )
            
            # Sauvegarde
            audio_file.save()
            
            self.logger.info(f"Pochette associée avec succès : {mp3_path}")
            return CoverAssociationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'association de pochette à {mp3_path} : {e}")
            return CoverAssociationResult.ERROR
    
    def update_mp3_tags(self, mp3_path: str, metadata: Dict[str, str]) -> bool:
        """
        Met à jour les tags d'un fichier MP3 avec les métadonnées fournies.
        
        Args:
            mp3_path: Chemin vers le fichier MP3
            metadata: Dictionnaire des métadonnées à appliquer
            
        Returns:
            bool: Succès de la mise à jour
        """
        try:
            # Chargement du fichier MP3
            try:
                audio_file = MP3(mp3_path, ID3=ID3)
            except ID3NoHeaderError:
                # Création d'un nouveau header ID3 si absent
                audio_file = MP3(mp3_path)
                audio_file.add_tags()
            
            # Mise à jour des tags selon les métadonnées fournies
            tag_mapping = {
                'TIT2': lambda v: TIT2(encoding=3, text=v),  # Titre
                'TPE1': lambda v: TPE1(encoding=3, text=v),  # Artiste
                'TALB': lambda v: TALB(encoding=3, text=v),  # Album
                'TYER': lambda v: TYER(encoding=3, text=v),  # Année
                'TCON': lambda v: TCON(encoding=3, text=v),  # Genre
                'TRCK': lambda v: TRCK(encoding=3, text=v),  # Numéro de piste
                'TPE2': lambda v: TPE2(encoding=3, text=v),  # Interprète
                'TLEN': lambda v: TLEN(encoding=3, text=v),  # Durée
            }
            
            updated_tags = []
            
            for tag_name, value in metadata.items():
                if tag_name in tag_mapping and value:
                    try:
                        tag_obj = tag_mapping[tag_name](str(value))
                        audio_file.tags.add(tag_obj)
                        updated_tags.append(tag_name)
                    except Exception as e:
                        self.logger.warning(f"Erreur lors de la mise à jour du tag {tag_name} : {e}")
            
            # Sauvegarde si des tags ont été mis à jour
            if updated_tags:
                audio_file.save()
                self.logger.info(f"Tags mis à jour dans {mp3_path} : {', '.join(updated_tags)}")
                return True
            else:
                self.logger.debug(f"Aucun tag à mettre à jour dans {mp3_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour des tags de {mp3_path} : {e}")
            return False
    
    def synchronize_file(self, mp3_path: str, metadata: Optional[Dict[str, str]] = None) -> SynchronizationResult:
        """
        Synchronise un fichier MP3 (pochette + tags).
        
        Args:
            mp3_path: Chemin vers le fichier MP3
            metadata: Métadonnées optionnelles à appliquer
            
        Returns:
            SynchronizationResult: Résultat de la synchronisation
        """
        start_time = time.time()
        
        try:
            file_path = Path(mp3_path)
            directory = file_path.parent
            
            actions_performed = []
            warnings = []
            cover_associated = False
            tags_updated = False
            cover_result = None
            
            # 1. Association de la pochette
            cover_path = self.find_cover_image(str(directory))
            if cover_path:
                cover_result = self.associate_cover_to_mp3(mp3_path, cover_path)
                if cover_result == CoverAssociationResult.SUCCESS:
                    cover_associated = True
                    actions_performed.append(SynchronizationAction.ASSOCIATE_COVER)
                elif cover_result == CoverAssociationResult.ALREADY_EXISTS:
                    warnings.append("Pochette déjà présente")
                else:
                    warnings.append(f"Association de pochette échouée : {cover_result.value}")
            else:
                cover_result = CoverAssociationResult.COVER_NOT_FOUND
                warnings.append("Aucune pochette trouvée dans le dossier")
            
            # 2. Mise à jour des tags
            if metadata:
                tags_updated = self.update_mp3_tags(mp3_path, metadata)
                if tags_updated:
                    actions_performed.append(SynchronizationAction.UPDATE_TAGS)
            
            processing_time = time.time() - start_time
            
            return SynchronizationResult(
                file_path=mp3_path,
                cover_associated=cover_associated,
                tags_updated=tags_updated,
                actions_performed=actions_performed,
                cover_result=cover_result,
                warnings=warnings,
                processing_time=processing_time
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la synchronisation de {mp3_path} : {e}"
            self.logger.error(error_msg)
            
            return SynchronizationResult(
                file_path=mp3_path,
                cover_associated=False,
                tags_updated=False,
                actions_performed=[],
                cover_result=CoverAssociationResult.ERROR,
                warnings=[],
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    def synchronize_album(self, album_path: str, apply_metadata: bool = True) -> AlbumSynchronizationResult:
        """
        Synchronise tous les fichiers MP3 d'un album.
        
        Args:
            album_path: Chemin du dossier d'album
            apply_metadata: Si True, applique les métadonnées depuis les fichiers
            
        Returns:
            AlbumSynchronizationResult: Résultat de la synchronisation complète
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Début de la synchronisation de l'album : {album_path}")
            
            # Mise à jour du statut
            self.state_manager.set_status("synchronizing_tags")
            
            # Validation du dossier
            validation_result = self.validator.validate_directory(album_path)
            if not validation_result.is_valid:
                return AlbumSynchronizationResult(
                    album_path=album_path,
                    files_processed=0,
                    covers_associated=0,
                    tags_updated=0,
                    total_files=0,
                    file_results=[],
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
            
            # Traitement de chaque fichier
            file_results = []
            covers_associated = 0
            tags_updated = 0
            
            for mp3_file in mp3_files:
                # Récupération des métadonnées existantes si demandé
                metadata = None
                if apply_metadata:
                    file_validation = self.validator.validate_mp3_file(str(mp3_file))
                    if file_validation.is_valid and file_validation.metadata:
                        metadata = file_validation.metadata
                
                # Synchronisation du fichier
                result = self.synchronize_file(str(mp3_file), metadata)
                file_results.append(result)
                
                if result.cover_associated:
                    covers_associated += 1
                if result.tags_updated:
                    tags_updated += 1
            
            processing_time = time.time() - start_time
            
            # Collecte des erreurs et avertissements
            errors = []
            warnings = []
            
            for result in file_results:
                if result.error:
                    errors.append(result.error)
                warnings.extend(result.warnings)
            
            # Logging du résultat
            self.logger.info(
                f"Synchronisation terminée pour {album_path}: "
                f"{len(file_results)}/{len(mp3_files)} fichiers traités, "
                f"{covers_associated} pochettes associées, "
                f"{tags_updated} mises à jour de tags"
            )
            
            # Mise à jour du statut
            self.state_manager.set_status("tag_synchronization_completed")
            
            # Enregistrement en base
            try:
                self.db_manager.add_import_history(
                    folder_path=album_path,
                    action="synchronize_album",
                    details={
                        "files_processed": len(file_results),
                        "covers_associated": covers_associated,
                        "tags_updated": tags_updated,
                        "total_files": len(mp3_files),
                        "processing_time": processing_time
                    }
                )
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'enregistrement en base : {e}")
            
            return AlbumSynchronizationResult(
                album_path=album_path,
                files_processed=len(file_results),
                covers_associated=covers_associated,
                tags_updated=tags_updated,
                total_files=len(mp3_files),
                file_results=file_results,
                processing_time=processing_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la synchronisation de l'album {album_path} : {e}"
            self.logger.error(error_msg)
            return AlbumSynchronizationResult(
                album_path=album_path,
                files_processed=0,
                covers_associated=0,
                tags_updated=0,
                total_files=0,
                file_results=[],
                processing_time=time.time() - start_time,
                errors=[error_msg],
                warnings=[]
            )
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Crée une sauvegarde d'un fichier MP3 avant modification.
        
        Args:
            file_path: Chemin vers le fichier à sauvegarder
            
        Returns:
            Optional[str]: Chemin vers le fichier de sauvegarde
        """
        try:
            source_path = Path(file_path)
            backup_dir = source_path.parent / ".nonotags_backup"
            backup_dir.mkdir(exist_ok=True)
            
            backup_name = f"{source_path.stem}_backup_{int(time.time())}{source_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Sauvegarde créée : {backup_path}")
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de sauvegarde pour {file_path} : {e}")
            return None
    
    def restore_from_backup(self, backup_path: str, target_path: str) -> bool:
        """
        Restaure un fichier depuis une sauvegarde.
        
        Args:
            backup_path: Chemin vers la sauvegarde
            target_path: Chemin de destination
            
        Returns:
            bool: Succès de la restauration
        """
        try:
            shutil.copy2(backup_path, target_path)
            self.logger.info(f"Fichier restauré depuis {backup_path} vers {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la restauration de {backup_path} : {e}")
            return False
