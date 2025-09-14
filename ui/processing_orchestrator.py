"""
Gestionnaire d'orchestration UI pour le pipeline de traitement
Connecte l'interface utilisateur aux 6 modules core de traitement
"""

import os
import threading
from enum import Enum
from typing import List, Dict, Callable, Optional
from gi.repository import GLib

# Imports des modules core
from core.file_cleaner import FileCleaner
from core.metadata_processor import MetadataProcessor  
from core.case_corrector import CaseCorrector
from core.metadata_formatter import MetadataFormatter
from core.file_renamer import FileRenamer
from core.tag_synchronizer import TagSynchronizer

# Imports des modules support
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager
from support.validator import Validator


class ProcessingState(Enum):
    """États du traitement"""
    IDLE = "idle"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ProcessingStep(Enum):
    """Étapes du pipeline de traitement"""
    FILE_CLEANING = "file_cleaning"
    METADATA_CLEANING = "metadata_cleaning"
    CASE_CORRECTION = "case_correction"
    FORMATTING = "formatting"
    RENAMING = "renaming"
    SYNCHRONIZATION = "synchronization"


class ProcessingOrchestrator:
    """Orchestrateur du pipeline de traitement pour l'interface utilisateur"""
    
    def __init__(self):
        """Initialise l'orchestrateur"""
        self.logger = AppLogger()
        self.config = ConfigManager()
        self.state_manager = StateManager()
        self.validator = Validator()
        
        # État du traitement
        self.current_state = ProcessingState.IDLE
        self.current_step = None
        self.current_progress = 0.0
        self.total_albums = 0
        self.processed_albums = 0
        
        # Modules de traitement
        self.file_cleaner = FileCleaner()
        self.metadata_processor = MetadataProcessor()
        self.case_corrector = CaseCorrector()
        self.metadata_formatter = MetadataFormatter()
        self.file_renamer = FileRenamer()
        self.tag_synchronizer = TagSynchronizer()
        
        # Thread de traitement
        self.processing_thread = None
        self.stop_requested = False
        
        # Callbacks pour l'interface
        self.on_state_changed: Optional[Callable] = None
        self.on_progress_updated: Optional[Callable] = None
        self.on_step_changed: Optional[Callable] = None
        self.on_album_processed: Optional[Callable] = None
        self.on_error_occurred: Optional[Callable] = None
        self.on_processing_completed: Optional[Callable] = None
        
        # Liste des albums à traiter
        self.albums_queue: List[Dict] = []
        
        self.logger.info("ProcessingOrchestrator initialisé")
    
    def add_albums(self, albums: List[Dict]):
        """
        Ajoute des albums à la queue de traitement
        
        Args:
            albums: Liste des albums avec métadonnées
        """
        self.albums_queue.extend(albums)
        self.total_albums = len(self.albums_queue)
        self.logger.info(f"{len(albums)} albums ajoutés à la queue (total: {self.total_albums})")
    
    def clear_queue(self):
        """Vide la queue de traitement"""
        self.albums_queue.clear()
        self.total_albums = 0
        self.processed_albums = 0
        self.logger.info("Queue de traitement vidée")
    
    def start_processing(self):
        """Démarre le traitement des albums en arrière-plan"""
        if self.current_state == ProcessingState.RUNNING:
            self.logger.warning("Traitement déjà en cours")
            return False
        
        if not self.albums_queue:
            self.logger.warning("Aucun album à traiter")
            return False
        
        self.stop_requested = False
        self.processed_albums = 0
        self._update_state(ProcessingState.RUNNING)
        
        # Lancer le traitement en arrière-plan
        self.processing_thread = threading.Thread(target=self._process_albums)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.logger.info(f"Traitement démarré pour {self.total_albums} albums")
        return True
    
    def pause_processing(self):
        """Met en pause le traitement"""
        if self.current_state == ProcessingState.RUNNING:
            self._update_state(ProcessingState.PAUSED)
            self.logger.info("Traitement mis en pause")
            return True
        return False
    
    def resume_processing(self):
        """Reprend le traitement"""
        if self.current_state == ProcessingState.PAUSED:
            self._update_state(ProcessingState.RUNNING)
            self.logger.info("Traitement repris")
            return True
        return False
    
    def stop_processing(self):
        """Arrête le traitement"""
        if self.current_state in [ProcessingState.RUNNING, ProcessingState.PAUSED]:
            self.stop_requested = True
            self._update_state(ProcessingState.CANCELLED)
            self.logger.info("Arrêt du traitement demandé")
            return True
        return False
    
    def _process_albums(self):
        """Traite tous les albums dans la queue (exécuté en arrière-plan)"""
        try:
            for i, album in enumerate(self.albums_queue):
                # Vérifier si l'arrêt est demandé
                if self.stop_requested:
                    break
                
                # Attendre si en pause
                while self.current_state == ProcessingState.PAUSED and not self.stop_requested:
                    threading.Event().wait(0.1)
                
                if self.stop_requested:
                    break
                
                # Traiter l'album
                success = self._process_single_album(album, i + 1)
                
                if success:
                    self.processed_albums += 1
                    GLib.idle_add(self._notify_album_processed, album, True)
                else:
                    GLib.idle_add(self._notify_album_processed, album, False)
                
                # Mettre à jour le progrès
                progress = (i + 1) / self.total_albums * 100
                GLib.idle_add(self._notify_progress_updated, progress)
            
            # Traitement terminé
            if not self.stop_requested:
                GLib.idle_add(self._notify_processing_completed, True)
                GLib.idle_add(self._update_state, ProcessingState.COMPLETED)
            else:
                GLib.idle_add(self._notify_processing_completed, False)
        
        except Exception as e:
            self.logger.error(f"Erreur durant le traitement: {e}")
            GLib.idle_add(self._notify_error_occurred, str(e))
            GLib.idle_add(self._update_state, ProcessingState.ERROR)
    
    def _process_single_album(self, album: Dict, album_number: int) -> bool:
        """
        Traite un album unique à travers le pipeline complet
        
        Args:
            album: Données de l'album
            album_number: Numéro de l'album en cours
        
        Returns:
            bool: True si le traitement a réussi
        """
        album_path = album.get('path')
        if not album_path or not os.path.exists(album_path):
            self.logger.error(f"Chemin album invalide: {album_path}")
            return False
        
        self.logger.info(f"Traitement album {album_number}/{self.total_albums}: {album.get('title', 'Sans titre')}")
        
        try:
            # ÉTAPE 1: Nettoyage des fichiers
            GLib.idle_add(self._notify_step_changed, ProcessingStep.FILE_CLEANING, album_number)
            
            if not self._execute_step(
                lambda: self.file_cleaner.clean_directory(album_path),
                f"Nettoyage fichiers - Album {album_number}"
            ):
                return False
            
            # ÉTAPE 2: Nettoyage des métadonnées
            GLib.idle_add(self._notify_step_changed, ProcessingStep.METADATA_CLEANING, album_number)
            
            if not self._execute_step(
                lambda: self.metadata_processor.clean_metadata(album_path),
                f"Nettoyage métadonnées - Album {album_number}"
            ):
                return False
            
            # ÉTAPE 3: Correction de casse
            GLib.idle_add(self._notify_step_changed, ProcessingStep.CASE_CORRECTION, album_number)
            
            if not self._execute_step(
                lambda: self.rules_engine.apply_case_rules(album_path),
                f"Correction casse - Album {album_number}"
            ):
                return False
            
            # ÉTAPE 4: Formatage
            GLib.idle_add(self._notify_step_changed, ProcessingStep.FORMATTING, album_number)
            
            if not self._execute_step(
                lambda: self.rules_engine.apply_formatting_rules(album_path),
                f"Formatage - Album {album_number}"
            ):
                return False
            
            # ÉTAPE 5: Renommage
            GLib.idle_add(self._notify_step_changed, ProcessingStep.RENAMING, album_number)
            
            if not self._execute_step(
                lambda: self.rules_engine.apply_renaming_rules(album_path),
                f"Renommage - Album {album_number}"
            ):
                return False
            
            # ÉTAPE 6: Synchronisation
            GLib.idle_add(self._notify_step_changed, ProcessingStep.SYNCHRONIZATION, album_number)
            
            if not self._execute_step(
                lambda: self.sync_manager.synchronize_album(album_path),
                f"Synchronisation - Album {album_number}"
            ):
                return False
            
            self.logger.info(f"Album {album_number} traité avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur traitement album {album_number}: {e}")
            GLib.idle_add(self._notify_error_occurred, f"Album {album_number}: {str(e)}")
            return False
    
    def _execute_step(self, step_function: Callable, step_description: str) -> bool:
        """
        Exécute une étape du pipeline avec gestion d'erreurs
        
        Args:
            step_function: Fonction à exécuter
            step_description: Description de l'étape
        
        Returns:
            bool: True si l'étape a réussi
        """
        try:
            # Vérifier si l'arrêt est demandé
            if self.stop_requested:
                return False
            
            # Attendre si en pause
            while self.current_state == ProcessingState.PAUSED and not self.stop_requested:
                threading.Event().wait(0.1)
            
            if self.stop_requested:
                return False
            
            # Exécuter l'étape
            result = step_function()
            
            # Vérifier le résultat
            if hasattr(result, 'success') and not result.success:
                self.logger.warning(f"Étape échouée: {step_description}")
                return False
            
            self.logger.debug(f"Étape réussie: {step_description}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur étape {step_description}: {e}")
            return False
    
    def _update_state(self, new_state: ProcessingState):
        """Met à jour l'état et notifie l'interface"""
        old_state = self.current_state
        self.current_state = new_state
        
        if self.on_state_changed:
            self.on_state_changed(old_state, new_state)
        
        self.logger.debug(f"État changé: {old_state} → {new_state}")
    
    def _notify_progress_updated(self, progress: float):
        """Notifie la mise à jour du progrès"""
        self.current_progress = progress
        if self.on_progress_updated:
            self.on_progress_updated(progress, self.processed_albums, self.total_albums)
        return False  # Pour GLib.idle_add
    
    def _notify_step_changed(self, step: ProcessingStep, album_number: int):
        """Notifie le changement d'étape"""
        self.current_step = step
        if self.on_step_changed:
            self.on_step_changed(step, album_number)
        return False  # Pour GLib.idle_add
    
    def _notify_album_processed(self, album: Dict, success: bool):
        """Notifie qu'un album a été traité"""
        if self.on_album_processed:
            self.on_album_processed(album, success)
        return False  # Pour GLib.idle_add
    
    def _notify_error_occurred(self, error_message: str):
        """Notifie qu'une erreur s'est produite"""
        if self.on_error_occurred:
            self.on_error_occurred(error_message)
        return False  # Pour GLib.idle_add
    
    def _notify_processing_completed(self, success: bool):
        """Notifie que le traitement est terminé"""
        if self.on_processing_completed:
            self.on_processing_completed(success, self.processed_albums, self.total_albums)
        return False  # Pour GLib.idle_add
    
    def get_status(self) -> Dict:
        """Retourne l'état actuel du traitement"""
        return {
            'state': self.current_state,
            'step': self.current_step,
            'progress': self.current_progress,
            'processed_albums': self.processed_albums,
            'total_albums': self.total_albums,
            'queue_size': len(self.albums_queue)
        }
    
    def get_processing_steps(self) -> List[ProcessingStep]:
        """Retourne la liste des étapes de traitement"""
        return list(ProcessingStep)
    
    def get_step_description(self, step: ProcessingStep) -> str:
        """Retourne la description d'une étape"""
        descriptions = {
            ProcessingStep.FILE_CLEANING: "Nettoyage des fichiers",
            ProcessingStep.METADATA_CLEANING: "Nettoyage des métadonnées", 
            ProcessingStep.CASE_CORRECTION: "Correction de la casse",
            ProcessingStep.FORMATTING: "Formatage des champs",
            ProcessingStep.RENAMING: "Renommage des fichiers",
            ProcessingStep.SYNCHRONIZATION: "Synchronisation finale"
        }
        return descriptions.get(step, "Étape inconnue")
