"""
Gestionnaire d'événements pour les métadonnées
Système d'observateur pour notifier automatiquement les cards des changements
"""

from typing import Dict, List, Callable, Set
import os


class MetadataEventManager:
    """Gestionnaire centralisé des événements de modification de métadonnées"""
    
    _instance = None  # Singleton
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Dictionnaire : album_path -> set(callbacks)
        self._observers: Dict[str, Set[Callable]] = {}
        print("📡 MetadataEventManager initialisé")
    
    def register_observer(self, album_path: str, callback: Callable):
        """Enregistre un observateur pour un album spécifique
        
        Args:
            album_path: Chemin de l'album à observer
            callback: Fonction à appeler lors des changements
        """
        if album_path not in self._observers:
            self._observers[album_path] = set()
        
        self._observers[album_path].add(callback)
        print(f"📝 Observateur enregistré pour: {os.path.basename(album_path)}")
    
    def unregister_observer(self, album_path: str, callback: Callable):
        """Désenregistre un observateur
        
        Args:
            album_path: Chemin de l'album
            callback: Fonction à retirer
        """
        if album_path in self._observers:
            self._observers[album_path].discard(callback)
            if not self._observers[album_path]:
                del self._observers[album_path]
            print(f"📝 Observateur désenregistré pour: {os.path.basename(album_path)}")
    
    def notify_metadata_changed(self, album_paths: List[str], updated_metadata: Dict = None):
        """Notifie tous les observateurs des albums modifiés
        
        Args:
            album_paths: Liste des chemins d'albums modifiés
            updated_metadata: Métadonnées mises à jour (optionnel)
        """
        if not album_paths:
            return
        
        notifications_sent = 0
        
        for album_path in album_paths:
            if album_path in self._observers:
                observers = self._observers[album_path].copy()  # Copie pour éviter les modifications concurrentes
                for callback in observers:
                    try:
                        # Appeler le callback avec les nouvelles métadonnées si disponibles
                        if updated_metadata and album_path in updated_metadata:
                            callback(updated_metadata[album_path])
                        else:
                            callback()
                        notifications_sent += 1
                    except Exception as e:
                        print(f"❌ Erreur notification observateur pour {os.path.basename(album_path)}: {e}")
        
        print(f"📡 {notifications_sent} notifications envoyées pour {len(album_paths)} albums modifiés")
    
    def notify_single_album(self, album_path: str, updated_metadata: Dict = None):
        """Notifie les observateurs d'un seul album
        
        Args:
            album_path: Chemin de l'album modifié
            updated_metadata: Métadonnées mises à jour (optionnel)
        """
        self.notify_metadata_changed([album_path], {album_path: updated_metadata} if updated_metadata else None)
    
    def get_observer_count(self) -> int:
        """Retourne le nombre total d'observateurs enregistrés"""
        return sum(len(observers) for observers in self._observers.values())
    
    def get_observed_albums(self) -> List[str]:
        """Retourne la liste des albums actuellement observés"""
        return list(self._observers.keys())
    
    def clear_all_observers(self):
        """Supprime tous les observateurs (pour nettoyage)"""
        count = self.get_observer_count()
        self._observers.clear()
        print(f"🧹 {count} observateurs supprimés")


# Instance globale pour accès facile
metadata_event_manager = MetadataEventManager()