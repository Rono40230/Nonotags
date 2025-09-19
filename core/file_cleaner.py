"""
Module 1 - Nettoyage des fichiers (GROUPE 1)

Ce module implémente les règles de nettoyage des fichiers dans les dossiers d'albums :
1. Suppression des fichiers indésirables (.DS_Store, Thumbs.db, etc.)
2. Suppression des sous-dossiers 
3. Renommage des fichie            # Vérification simple des permissions d'écriture
            if not os.access(file_path, os.W_OK):
                return CleaningResult(
                    action=CleaningAction.DELETE_FILE,
                    source_path=str(file_path),
                    success=False,
                    error_message=f"Permission d'écriture refusée : {file_path}"
                )chettes (front.jpg → cover.jpg)

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
from support.honest_logger import honest_logger, ProcessingResult


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
        # Scan AVANT nettoyage
        before_files = [f.name for f in Path(album_path).iterdir() if f.is_file()]
        before_dirs = [f.name for f in Path(album_path).iterdir() if f.is_dir()]
        
        # Validation du chemin d'album
        validation = self.validator.validate_directory(album_path)
        if not validation.is_valid:
            error_msg = f"Impossible d'accéder au dossier : {', '.join(validation.errors)}"
            honest_logger.error(error_msg)
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
            
            # Scan APRÈS nettoyage
            after_files = [f.name for f in Path(album_path).iterdir() if f.is_file()]
            after_dirs = [f.name for f in Path(album_path).iterdir() if f.is_dir()]
            
            # CONTRÔLE DE RÉALITÉ
            result = ProcessingResult(
                operation="Nettoyage fichiers",
                success=len(stats.errors) == 0,
                files_affected=stats.files_deleted + stats.files_renamed + stats.folders_deleted,
                files_expected=len(before_files) + len(before_dirs),
                errors=stats.errors,
                details={
                    'fichiers_supprimés': stats.files_deleted,
                    'dossiers_supprimés': stats.folders_deleted,
                    'fichiers_renommés': stats.files_renamed,
                    'avant_fichiers': len(before_files),
                    'après_fichiers': len(after_files),
                    'avant_dossiers': len(before_dirs),
                    'après_dossiers': len(after_dirs)
                }
            )
            
            honest_logger.reality_check("Nettoyage", result)
            honest_logger.folder_scan(album_path, before_files + before_dirs, after_files + after_dirs)
            
            # Mise à jour de l'état final
            if stats.errors:
                self.state.update_album_processing_status(album_path, "cleaning_completed_with_errors")
            else:
                self.state.update_album_processing_status(album_path, "cleaning_completed")
                
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage de {album_path} : {str(e)}"
            honest_logger.error(error_msg)
            stats.errors.append(error_msg)
            self.state.update_album_processing_status(album_path, "cleaning_failed")
        
        return stats
    
    def _clean_unwanted_files(self, album_path: str) -> List[CleaningResult]:
        """Supprime les fichiers indésirables du dossier."""
        results = []
        album_dir = Path(album_path)
        
        # Liste des types de fichiers à supprimer selon règle 1
        target_extensions = ['.DS_Store', 'Thumbs.db', '.png', '.nfo', '.txt', '.m3u', 'bs.db']
        
        unwanted_count = 0
        total_files = 0
        
        for file_path in album_dir.iterdir():
            if not file_path.is_file():
                continue
            
            total_files += 1
            
            if self._is_unwanted_file(file_path):
                unwanted_count += 1
                result = self._delete_file(file_path)
                results.append(result)
                
                if result.success:
                    honest_logger.file_operation("SUPPRESSION", str(file_path), True)
                else:
                    honest_logger.error(f"❌ RÈGLE 1 - Suppression échouée: {file_path.name} - {result.error_message}")
                    honest_logger.file_operation("SUPPRESSION", str(file_path), False, result.error_message)
        
        # Rapport final règle 1
        if unwanted_count == 0:
            honest_logger.warning(f"⚠️ RÈGLE 1 - Aucun fichier indésirable trouvé sur {total_files} fichiers")
        else:
            honest_logger.info(f"📊 RÈGLE 1 - {unwanted_count} fichiers indésirables traités sur {total_files} fichiers")
        
        return results
    
    def _clean_subfolders(self, album_path: str) -> List[CleaningResult]:
        """Supprime tous les sous-dossiers du dossier d'album."""
        results = []
        album_dir = Path(album_path)
        
        subfolder_count = 0
        total_dirs = 0
        
        for subfolder in album_dir.iterdir():
            if subfolder.is_dir():
                total_dirs += 1
                subfolder_count += 1
                
                result = self._delete_folder(subfolder)
                results.append(result)
                
                if not result.success:
                    honest_logger.error(f"❌ RÈGLE 2 - Suppression dossier échouée: {subfolder.name} - {result.error_message}")
        
        return results
    
    def _rename_cover_files(self, album_path: str) -> List[CleaningResult]:
        """Renomme les fichiers de pochettes selon les patterns configurés."""
        results = []
        album_dir = Path(album_path)
        
        # Patterns ciblés selon règle 3
        target_patterns = ['front.jpg', 'Front.jpg', 'Cover.jpg']
        honest_logger.info(f"📋 Patterns ciblés: {target_patterns} → cover.jpg")
        
        cover_count = 0
        total_files = 0
        
        for file_path in album_dir.iterdir():
            if not file_path.is_file():
                continue
            
            total_files += 1
            
            new_name = self._get_cover_rename_target(file_path)
            if new_name and new_name != file_path.name:
                cover_count += 1
                target_path = album_dir / new_name
                
                honest_logger.info(f"🖼️ RÈGLE 3 - Fichier pochette détecté: {file_path.name} → {new_name}")
                
                result = self._rename_file(file_path, target_path)
                results.append(result)
                
                if not result.success:
                    honest_logger.error(f"❌ RÈGLE 3 - Renommage échoué: {file_path.name} → {new_name} - {result.error_message}")
        
        return results
    
    def _is_unwanted_file(self, file_path: Path) -> bool:
        """Vérifie si un fichier est dans la liste des fichiers indésirables."""
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # Vérification des noms exacts
        if filename in self._unwanted_files:
            return True
        
        # Vérification des extensions indésirables
        unwanted_extensions = ['.tmp', '.temp', '.bak', '.log', '.txt', '.m3u', '.nfo', '.sfv', '.md5', '.pdf', '.doc', '.docx', '.png']
        if extension in unwanted_extensions:
            return True
        
        # Vérification des patterns système
        unwanted_patterns = ['.ds_store', 'thumbs.db', 'desktop.ini', '.fuse_hidden', '._metadata', '#recycle', 'recycle.bin']
        if any(pattern in filename for pattern in unwanted_patterns):
            return True
            
        # Vérification des fichiers images non-pochettes (GIF, BMP uniquement)
        if extension in ['.gif', '.bmp'] and not filename.startswith('cover'):
            # Fichiers images qui ne sont pas des pochettes
            if not any(word in filename for word in ['cover', 'front', 'album', 'artwork']):
                return True
        
        return False
    
    def _get_cover_rename_target(self, file_path: Path) -> Optional[str]:
        """Détermine le nouveau nom pour un fichier de pochette."""
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # Vérification que c'est bien une image (PNG exclus car supprimés)
        if extension not in ['.jpg', '.jpeg', '.bmp', '.gif']:
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
            honest_logger.info(f"🗑️ Tentative suppression: {file_path.name} ({size} bytes)")
            
            # Validation simple des permissions
            if not os.access(file_path, os.W_OK):
                error_msg = f"Permission d'écriture refusée : {file_path}"
                honest_logger.error(f"❌ SUPPRESSION ÉCHEC: {file_path.name} - {error_msg}")
                return CleaningResult(
                    action=CleaningAction.DELETE_FILE,
                    source_path=str(file_path),
                    success=False,
                    error_message=error_msg
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
            honest_logger.error(f"❌ SUPPRESSION ÉCHEC: {file_path.name} - {str(e)}")
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
            
            # Validation simple des permissions pour suppression
            if not os.access(folder_path.parent, os.W_OK):
                return CleaningResult(
                    action=CleaningAction.DELETE_FOLDER,
                    source_path=str(folder_path),
                    success=False,
                    error_message=f"Permission refusée pour supprimer le dossier : {folder_path}"
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
            if not os.access(source_path, os.W_OK):
                return CleaningResult(
                    action=CleaningAction.RENAME_FILE,
                    source_path=str(source_path),
                    target_path=str(target_path),
                    success=False,
                    error_message=f"Permission d'écriture refusée : {source_path}"
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
    
    def clean_album_metadata(self, album_directory: str) -> bool:
        """
        Méthode requise par processing_orchestrator.py.
        Nettoie un dossier d'album selon les règles du GROUPE 1.
        
        Args:
            album_directory: Chemin vers le dossier de l'album
            
        Returns:
            bool: True si le nettoyage a réussi, False sinon
        """
        try:
            stats = self.clean_album_folder(album_directory)
            success = len(stats.errors) == 0
            
            if success:
                self.logger.info(f"Nettoyage des fichiers réussi pour : {album_directory}")
            else:
                self.logger.error(f"Erreurs lors du nettoyage de : {album_directory}")
                for error in stats.errors:
                    self.logger.error(f"  - {error}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erreur critique lors du nettoyage de {album_directory}: {str(e)}", exc_info=True)
            return False