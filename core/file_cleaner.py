"""
Module 1 - Nettoyage des fichiers (GROUPE 1)

Ce module implémente les règles de nettoyage des fichiers dans les dossiers d'albums :
1. Suppression des fichiers indésirables (.DS_Store, Thumbs.db, etc.)
2. Suppression des sous-dossiers 
3. Renommage des fichiers de pochettes (front.jpg → cover.jpg)

Intégration complète avec les modules de support :
- Module 13 : Validation des permissions et formats
- Module 14 : Logging des opérations de nettoyage
- Module 15 : Configuration des règles
- Module 16 : Gestion d'état
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import des modules de support
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager
from support.validator import FileValidator, ValidationResult


class CleaningAction(Enum):
    """Types d'actions de nettoyage possibles."""
    DELETE_FILE = "delete_file"
    DELETE_FOLDER = "delete_folder"
    RENAME_FILE = "rename_file"
    SKIP = "skip"


@dataclass
class CleaningResult:
    """Résultat d'une opération de nettoyage."""
    action: CleaningAction
    source_path: str
    target_path: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None
    size_freed: int = 0  # Taille libérée en bytes


@dataclass
class CleaningStats:
    """Statistiques de nettoyage d'un album."""
    album_path: str
    files_deleted: int = 0
    folders_deleted: int = 0
    files_renamed: int = 0
    total_size_freed: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class FileCleaner:
    """
    Module 1 - Nettoyage des fichiers (GROUPE 1)
    
    Nettoie les dossiers d'albums en supprimant les fichiers indésirables,
    les sous-dossiers et en renommant les fichiers de pochettes.
    """
    
    def __init__(self):
        """Initialise le nettoyeur de fichiers avec les modules de support."""
        # Intégration modules de support
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.config = ConfigManager()
        self.state = StateManager()
        self.validator = FileValidator()
        
        # Configuration des fichiers indésirables (personnalisable)
        self._unwanted_files = self.config.processing.unwanted_files
        self._cover_rename_patterns = self.config.processing.cover_rename_patterns
        
        self.logger.info("FileCleaner initialisé avec succès")
    
    def clean_album_folder(self, album_path: str) -> CleaningStats:
        """
        Nettoie un dossier d'album complet.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            CleaningStats: Statistiques du nettoyage
        """
        self.logger.info(f"Début du nettoyage de l'album : {album_path}")
        
        # Validation du chemin d'album
        validation = self.validator.validate_directory_access(album_path)
        if not validation.is_valid:
            error_msg = f"Impossible d'accéder au dossier : {', '.join(validation.errors)}"
            self.logger.error(error_msg)
            stats = CleaningStats(album_path)
            stats.errors.append(error_msg)
            return stats
        
        stats = CleaningStats(album_path)
        
        try:
            # Mise à jour de l'état
            self.state.update_album_processing_status(album_path, "cleaning_files")
            
            # 1. Nettoyage des fichiers indésirables
            file_results = self._clean_unwanted_files(album_path)
            self._update_stats_from_results(stats, file_results)
            
            # 2. Suppression des sous-dossiers
            folder_results = self._clean_subfolders(album_path)
            self._update_stats_from_results(stats, folder_results)
            
            # 3. Renommage des fichiers de pochettes
            rename_results = self._rename_cover_files(album_path)
            self._update_stats_from_results(stats, rename_results)
            
            # Logging des résultats
            self.logger.info(
                f"Nettoyage terminé pour {album_path} : "
                f"{stats.files_deleted} fichiers supprimés, "
                f"{stats.folders_deleted} dossiers supprimés, "
                f"{stats.files_renamed} fichiers renommés, "
                f"{stats.total_size_freed} bytes libérés"
            )
            
            # Mise à jour de l'état
            if stats.errors:
                self.state.update_album_processing_status(album_path, "cleaning_completed_with_errors")
                self.logger.warning(f"Nettoyage terminé avec {len(stats.errors)} erreurs")
            else:
                self.state.update_album_processing_status(album_path, "cleaning_completed")
            
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage de {album_path} : {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            stats.errors.append(error_msg)
            self.state.update_album_processing_status(album_path, "cleaning_failed")
        
        return stats
    
    def _clean_unwanted_files(self, album_path: str) -> List[CleaningResult]:
        """Supprime les fichiers indésirables du dossier."""
        results = []
        album_dir = Path(album_path)
        
        self.logger.debug(f"Recherche des fichiers indésirables dans {album_path}")
        
        for file_path in album_dir.iterdir():
            if not file_path.is_file():
                continue
            
            if self._is_unwanted_file(file_path):
                result = self._delete_file(file_path)
                results.append(result)
                
                if result.success:
                    self.logger.debug(f"Fichier indésirable supprimé : {file_path.name}")
                else:
                    self.logger.warning(f"Échec suppression fichier : {result.error_message}")
        
        return results
    
    def _clean_subfolders(self, album_path: str) -> List[CleaningResult]:
        """Supprime tous les sous-dossiers du dossier d'album."""
        results = []
        album_dir = Path(album_path)
        
        self.logger.debug(f"Recherche des sous-dossiers dans {album_path}")
        
        for subfolder in album_dir.iterdir():
            if subfolder.is_dir():
                result = self._delete_folder(subfolder)
                results.append(result)
                
                if result.success:
                    self.logger.debug(f"Sous-dossier supprimé : {subfolder.name}")
                else:
                    self.logger.warning(f"Échec suppression dossier : {result.error_message}")
        
        return results
    
    def _rename_cover_files(self, album_path: str) -> List[CleaningResult]:
        """Renomme les fichiers de pochettes selon les patterns configurés."""
        results = []
        album_dir = Path(album_path)
        
        self.logger.debug(f"Recherche des fichiers de pochettes dans {album_path}")
        
        for file_path in album_dir.iterdir():
            if not file_path.is_file():
                continue
            
            new_name = self._get_cover_rename_target(file_path)
            if new_name and new_name != file_path.name:
                target_path = album_dir / new_name
                result = self._rename_file(file_path, target_path)
                results.append(result)
                
                if result.success:
                    self.logger.debug(f"Fichier de pochette renommé : {file_path.name} → {new_name}")
                else:
                    self.logger.warning(f"Échec renommage pochette : {result.error_message}")
        
        return results
    
    def _is_unwanted_file(self, file_path: Path) -> bool:
        """Vérifie si un fichier est dans la liste des fichiers indésirables."""
        filename = file_path.name.lower()
        
        # Vérification des noms exacts
        if filename in self._unwanted_files:
            return True
        
        # Vérification des extensions
        if file_path.suffix.lower() in ['.tmp', '.temp', '.bak', '.log']:
            return True
        
        # Vérification des patterns
        unwanted_patterns = ['.ds_store', 'thumbs.db', 'desktop.ini', '.fuse_hidden']
        return any(pattern in filename for pattern in unwanted_patterns)
    
    def _get_cover_rename_target(self, file_path: Path) -> Optional[str]:
        """Détermine le nouveau nom pour un fichier de pochette."""
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # Vérification que c'est bien une image
        if extension not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            return None
        
        # Recherche dans les patterns de renommage
        for pattern, target in self._cover_rename_patterns.items():
            if pattern.lower() in filename:
                return target + extension
        
        return None
    
    def _delete_file(self, file_path: Path) -> CleaningResult:
        """Supprime un fichier et retourne le résultat."""
        try:
            # Récupération de la taille avant suppression
            size = file_path.stat().st_size
            
            # Validation des permissions
            validation = self.validator.validate_file_permissions(str(file_path), 'write')
            if not validation.is_valid:
                return CleaningResult(
                    action=CleaningAction.DELETE_FILE,
                    source_path=str(file_path),
                    success=False,
                    error_message=f"Permissions insuffisantes : {', '.join(validation.errors)}"
                )
            
            # Suppression
            file_path.unlink()
            
            return CleaningResult(
                action=CleaningAction.DELETE_FILE,
                source_path=str(file_path),
                success=True,
                size_freed=size
            )
            
        except Exception as e:
            return CleaningResult(
                action=CleaningAction.DELETE_FILE,
                source_path=str(file_path),
                success=False,
                error_message=str(e)
            )
    
    def _delete_folder(self, folder_path: Path) -> CleaningResult:
        """Supprime un dossier et son contenu, retourne le résultat."""
        try:
            # Calcul de la taille totale avant suppression
            total_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
            
            # Validation des permissions
            validation = self.validator.validate_directory_access(str(folder_path))
            if not validation.is_valid:
                return CleaningResult(
                    action=CleaningAction.DELETE_FOLDER,
                    source_path=str(folder_path),
                    success=False,
                    error_message=f"Accès refusé au dossier : {', '.join(validation.errors)}"
                )
            
            # Suppression récursive
            shutil.rmtree(folder_path)
            
            return CleaningResult(
                action=CleaningAction.DELETE_FOLDER,
                source_path=str(folder_path),
                success=True,
                size_freed=total_size
            )
            
        except Exception as e:
            return CleaningResult(
                action=CleaningAction.DELETE_FOLDER,
                source_path=str(folder_path),
                success=False,
                error_message=str(e)
            )
    
    def _rename_file(self, source_path: Path, target_path: Path) -> CleaningResult:
        """Renomme un fichier et retourne le résultat."""
        try:
            # Vérification que le fichier cible n'existe pas déjà
            if target_path.exists():
                return CleaningResult(
                    action=CleaningAction.RENAME_FILE,
                    source_path=str(source_path),
                    target_path=str(target_path),
                    success=False,
                    error_message=f"Le fichier cible existe déjà : {target_path.name}"
                )
            
            # Validation des permissions
            validation = self.validator.validate_file_permissions(str(source_path), 'write')
            if not validation.is_valid:
                return CleaningResult(
                    action=CleaningAction.RENAME_FILE,
                    source_path=str(source_path),
                    target_path=str(target_path),
                    success=False,
                    error_message=f"Permissions insuffisantes : {', '.join(validation.errors)}"
                )
            
            # Renommage
            source_path.rename(target_path)
            
            return CleaningResult(
                action=CleaningAction.RENAME_FILE,
                source_path=str(source_path),
                target_path=str(target_path),
                success=True
            )
            
        except Exception as e:
            return CleaningResult(
                action=CleaningAction.RENAME_FILE,
                source_path=str(source_path),
                target_path=str(target_path),
                success=False,
                error_message=str(e)
            )
    
    def _update_stats_from_results(self, stats: CleaningStats, results: List[CleaningResult]):
        """Met à jour les statistiques avec les résultats d'opérations."""
        for result in results:
            if result.success:
                if result.action == CleaningAction.DELETE_FILE:
                    stats.files_deleted += 1
                elif result.action == CleaningAction.DELETE_FOLDER:
                    stats.folders_deleted += 1
                elif result.action == CleaningAction.RENAME_FILE:
                    stats.files_renamed += 1
                
                stats.total_size_freed += result.size_freed
            else:
                stats.errors.append(f"{result.action.value}: {result.error_message}")
    
    def get_cleaning_preview(self, album_path: str) -> Dict[str, List[str]]:
        """
        Génère un aperçu des actions de nettoyage sans les exécuter.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            Dict contenant les listes des actions prévues
        """
        preview = {
            'files_to_delete': [],
            'folders_to_delete': [],
            'files_to_rename': []
        }
        
        try:
            album_dir = Path(album_path)
            
            if not album_dir.exists() or not album_dir.is_dir():
                return preview
            
            # Fichiers à supprimer
            for file_path in album_dir.iterdir():
                if file_path.is_file() and self._is_unwanted_file(file_path):
                    preview['files_to_delete'].append(file_path.name)
            
            # Dossiers à supprimer
            for subfolder in album_dir.iterdir():
                if subfolder.is_dir():
                    preview['folders_to_delete'].append(subfolder.name)
            
            # Fichiers à renommer
            for file_path in album_dir.iterdir():
                if file_path.is_file():
                    new_name = self._get_cover_rename_target(file_path)
                    if new_name and new_name != file_path.name:
                        preview['files_to_rename'].append(f"{file_path.name} → {new_name}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de l'aperçu : {str(e)}")
        
        return preview
    
    # Méthode de compatibilité avec l'ancienne API
    def clean_album_directory(self, album_path: str) -> bool:
        """
        Méthode de compatibilité - utilise la nouvelle API.
        
        Args:
            album_path: Chemin du répertoire album
            
        Returns:
            True si le nettoyage a réussi
        """
        stats = self.clean_album_folder(album_path)
        return len(stats.errors) == 0
