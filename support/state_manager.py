"""
Module 16 - Gestionnaire d'état global de l'application
Centralise l'état de l'application et coordination entre modules.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
import time
import os
from support.logger import get_logger

class ApplicationState(Enum):
    """États possibles de l'application."""
    STARTING = "starting"
    READY = "ready"
    IMPORTING = "importing"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class ImportStatus(Enum):
    """États possibles d'un import."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"

@dataclass
class AlbumState:
    """État d'un album dans l'application."""
    id: str
    path: str
    name: str
    artist: str = ""
    track_count: int = 0
    import_status: ImportStatus = ImportStatus.PENDING
    error_message: str = ""
    selected: bool = False
    last_modified: float = field(default_factory=time.time)
    metadata_changed: bool = False

@dataclass
class ImportTask:
    """Tâche d'import en cours."""
    id: str
    album_path: str
    status: ImportStatus
    progress: float = 0.0  # 0.0 à 1.0
    current_step: str = ""
    error_message: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

class StateManager:
    """Gestionnaire centralisé de l'état global de l'application."""
    
    def __init__(self):
        """Initialise le gestionnaire d'état."""
        self.logger = get_logger()
        self._lock = Lock()
        
        # État global de l'application
        self._app_state = ApplicationState.STARTING
        self._error_message = ""
        
        # Albums importés et gérés
        self._albums: Dict[str, AlbumState] = {}
        self._selected_albums: List[str] = []
        
        # Tâches d'import en cours
        self._import_tasks: Dict[str, ImportTask] = {}
        
        # Système d'événements
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Statistiques
        self._stats = {
            'total_imports': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'total_tracks_processed': 0,
            'total_metadata_changes': 0
        }
        
        self.logger.info("State manager initialized")
    
    # === Gestion de l'état global ===
    
    def get_app_state(self) -> ApplicationState:
        """Retourne l'état actuel de l'application."""
        with self._lock:
            return self._app_state
    
    def set_app_state(self, state: ApplicationState, error_message: str = ""):
        """
        Définit l'état de l'application.
        
        Args:
            state: Nouvel état
            error_message: Message d'erreur si applicable
        """
        with self._lock:
            old_state = self._app_state
            self._app_state = state
            self._error_message = error_message
        
        self.logger.info(f"Application state changed: {old_state.value} -> {state.value}")
        if error_message:
            self.logger.error(f"Error state: {error_message}")
        
        # Émission de l'événement
        self._emit_event('app_state_changed', {
            'old_state': old_state,
            'new_state': state,
            'error_message': error_message
        })
    
    def get_error_message(self) -> str:
        """Retourne le dernier message d'erreur."""
        with self._lock:
            return self._error_message
    
    # === Gestion des albums ===
    
    def add_album(self, album: AlbumState) -> bool:
        """
        Ajoute un album à l'état.
        
        Args:
            album: Album à ajouter
            
        Returns:
            True si l'album a été ajouté, False s'il existait déjà
        """
        with self._lock:
            if album.id in self._albums:
                self.logger.warning(f"Album already exists: {album.id}")
                return False
            
            self._albums[album.id] = album
        
        self.logger.debug(f"Album added: {album.name} ({album.id})")
        self._emit_event('album_added', {'album': album})
        return True
    
    def update_album(self, album_id: str, **kwargs) -> bool:
        """
        Met à jour un album.
        
        Args:
            album_id: ID de l'album
            **kwargs: Champs à mettre à jour
            
        Returns:
            True si l'album a été mis à jour, False sinon
        """
        with self._lock:
            if album_id not in self._albums:
                self.logger.warning(f"Album not found for update: {album_id}")
                return False
            
            album = self._albums[album_id]
            old_values = {}
            
            for key, value in kwargs.items():
                if hasattr(album, key):
                    old_values[key] = getattr(album, key)
                    setattr(album, key, value)
            
            album.last_modified = time.time()
        
        self.logger.debug(f"Album updated: {album_id}")
        self._emit_event('album_updated', {
            'album_id': album_id,
            'old_values': old_values,
            'new_values': kwargs
        })
        return True
    
    def remove_album(self, album_id: str) -> bool:
        """
        Supprime un album de l'état.
        
        Args:
            album_id: ID de l'album à supprimer
            
        Returns:
            True si l'album a été supprimé, False sinon
        """
        with self._lock:
            if album_id not in self._albums:
                self.logger.warning(f"Album not found for removal: {album_id}")
                return False
            
            album = self._albums.pop(album_id)
            
            # Suppression de la sélection si nécessaire
            if album_id in self._selected_albums:
                self._selected_albums.remove(album_id)
        
        self.logger.debug(f"Album removed: {album_id}")
        self._emit_event('album_removed', {'album_id': album_id, 'album': album})
        return True
    
    def get_album(self, album_id: str) -> Optional[AlbumState]:
        """
        Retourne un album par son ID.
        
        Args:
            album_id: ID de l'album
            
        Returns:
            Album ou None si non trouvé
        """
        with self._lock:
            return self._albums.get(album_id)
    
    def get_all_albums(self) -> List[AlbumState]:
        """Retourne tous les albums."""
        with self._lock:
            return list(self._albums.values())
    
    def get_albums_by_status(self, status: ImportStatus) -> List[AlbumState]:
        """
        Retourne les albums avec un statut donné.
        
        Args:
            status: Statut recherché
            
        Returns:
            Liste des albums avec ce statut
        """
        with self._lock:
            return [album for album in self._albums.values() 
                   if album.import_status == status]
    
    # === Gestion de la sélection ===
    
    def select_album(self, album_id: str) -> bool:
        """
        Sélectionne un album.
        
        Args:
            album_id: ID de l'album à sélectionner
            
        Returns:
            True si l'album a été sélectionné, False sinon
        """
        with self._lock:
            if album_id not in self._albums:
                return False
            
            if album_id not in self._selected_albums:
                self._selected_albums.append(album_id)
                self._albums[album_id].selected = True
        
        self._emit_event('album_selected', {'album_id': album_id})
        return True
    
    def deselect_album(self, album_id: str) -> bool:
        """
        Désélectionne un album.
        
        Args:
            album_id: ID de l'album à désélectionner
            
        Returns:
            True si l'album a été désélectionné, False sinon
        """
        with self._lock:
            if album_id in self._selected_albums:
                self._selected_albums.remove(album_id)
            
            if album_id in self._albums:
                self._albums[album_id].selected = False
        
        self._emit_event('album_deselected', {'album_id': album_id})
        return True
    
    def clear_selection(self):
        """Vide la sélection."""
        with self._lock:
            for album_id in self._selected_albums:
                if album_id in self._albums:
                    self._albums[album_id].selected = False
            self._selected_albums.clear()
        
        self._emit_event('selection_cleared', {})
    
    def get_selected_albums(self) -> List[str]:
        """Retourne la liste des IDs d'albums sélectionnés."""
        with self._lock:
            return self._selected_albums.copy()
    
    # === Gestion des tâches d'import ===
    
    def start_import_task(self, task: ImportTask):
        """
        Démarre une tâche d'import.
        
        Args:
            task: Tâche d'import à démarrer
        """
        with self._lock:
            self._import_tasks[task.id] = task
        
        self.logger.info(f"Import task started: {task.id}")
        self._emit_event('import_task_started', {'task': task})
    
    def update_import_task(self, task_id: str, **kwargs):
        """
        Met à jour une tâche d'import.
        
        Args:
            task_id: ID de la tâche
            **kwargs: Champs à mettre à jour
        """
        with self._lock:
            if task_id in self._import_tasks:
                task = self._import_tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
        
        self._emit_event('import_task_updated', {'task_id': task_id, 'updates': kwargs})
    
    def finish_import_task(self, task_id: str, status: ImportStatus, error_message: str = ""):
        """
        Termine une tâche d'import.
        
        Args:
            task_id: ID de la tâche
            status: Statut final
            error_message: Message d'erreur si applicable
        """
        with self._lock:
            if task_id in self._import_tasks:
                task = self._import_tasks[task_id]
                task.status = status
                task.error_message = error_message
                task.end_time = time.time()
                
                # Mise à jour des statistiques
                if status == ImportStatus.SUCCESS:
                    self._stats['successful_imports'] += 1
                elif status == ImportStatus.ERROR:
                    self._stats['failed_imports'] += 1
        
        self.logger.info(f"Import task finished: {task_id} - {status.value}")
        self._emit_event('import_task_finished', {
            'task_id': task_id,
            'status': status,
            'error_message': error_message
        })
    
    def get_import_tasks(self) -> List[ImportTask]:
        """Retourne toutes les tâches d'import."""
        with self._lock:
            return list(self._import_tasks.values())
    
    def get_active_import_tasks(self) -> List[ImportTask]:
        """Retourne les tâches d'import en cours."""
        with self._lock:
            return [task for task in self._import_tasks.values() 
                   if task.status == ImportStatus.IN_PROGRESS]
    
    # === Système d'événements ===
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Enregistre un gestionnaire d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction gestionnaire
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        self.logger.debug(f"Event handler registered for: {event_type}")
    
    def unregister_event_handler(self, event_type: str, handler: Callable):
        """
        Désenregistre un gestionnaire d'événement.
        
        Args:
            event_type: Type d'événement
            handler: Fonction gestionnaire
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                self.logger.debug(f"Event handler unregistered for: {event_type}")
            except ValueError:
                pass
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """
        Émet un événement.
        
        Args:
            event_type: Type d'événement
            data: Données de l'événement
        """
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    # === Statistiques ===
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'application."""
        with self._lock:
            return self._stats.copy()
    
    def increment_stat(self, stat_name: str, value: int = 1):
        """
        Incrémente une statistique.
        
        Args:
            stat_name: Nom de la statistique
            value: Valeur à ajouter
        """
        with self._lock:
            if stat_name in self._stats:
                self._stats[stat_name] += value
    
    def reset_statistics(self):
        """Remet à zéro toutes les statistiques."""
        with self._lock:
            for key in self._stats:
                self._stats[key] = 0
        
        self.logger.info("Statistics reset")
        self._emit_event('statistics_reset', {})
    
    def update_album_processing_status(self, album_path: str, status: str) -> bool:
        """
        Met à jour le statut de traitement d'un album.
        
        Args:
            album_path: Chemin vers l'album
            status: Nouveau statut (cleaning_files, processing, completed, failed, etc.)
            
        Returns:
            True si mis à jour avec succès
        """
        try:
            # Trouver l'album par path ou créer une entrée temporaire
            album_id = os.path.basename(album_path)
            
            # Log du changement de statut
            self.logger.debug(f"Album {album_path} status: {status}")
            
            # Émettre un événement pour notifier l'UI
            self._emit_event('album_status_changed', {
                'album_path': album_path,
                'status': status,
                'timestamp': time.time()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour statut album {album_path}: {e}")
            return False