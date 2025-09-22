"""
Module de rafraîchissement centralisé pour Nonotags
Assure l'effet miroir entre métadonnées et interface utilisateur
"""

import threading
from gi.repository import GLib
from typing import List, Set, Callable, Optional
import weakref
import os


class RefreshManager:
    """
    Gestionnaire centralisé de rafraîchissement d'interface
    Pattern Singleton pour coordination globale
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Registry des composants d'affichage (WeakReferences pour éviter les fuites mémoire)
        self._display_components = weakref.WeakSet()
        
        # Cache des albums modifiés (pour éviter les rafraîchissements redondants)
        self._pending_refreshes: Set[str] = set()
        
        # Timer pour regrouper les notifications
        self._refresh_timer = None
        self._refresh_delay_ms = 100  # 100ms de délai pour regrouper les notifications
    
    @classmethod
    def get_instance(cls):
        """Récupère l'instance singleton"""
        return cls()
    
    def register_display_component(self, component):
        """
        Enregistre un composant d'affichage pour les notifications
        
        Args:
            component: Objet avec une méthode de rafraîchissement (_refresh_albums_display, _update_display, etc.)
        """
        if component is None:
            return
            
        self._display_components.add(component)
    
    def unregister_display_component(self, component):
        """
        Désenregistre un composant d'affichage
        
        Args:
            component: Composant à supprimer du registry
        """
        if component in self._display_components:
            self._display_components.discard(component)
    
    def notify_metadata_changed(self, album_paths: List[str] = None, immediate: bool = False):
        """
        Notifie que des métadonnées ont changé
        
        Args:
            album_paths: Liste des chemins d'albums modifiés (None = tout rafraîchir)
            immediate: Si True, rafraîchit immédiatement sans délai
        """
        if album_paths:
            # Normaliser les chemins d'albums
            normalized_paths = []
            for path in album_paths:
                if os.path.isfile(path):
                    # Si c'est un fichier, prendre le dossier parent
                    album_path = os.path.dirname(path)
                else:
                    album_path = path
                normalized_paths.append(album_path)
            
            self._pending_refreshes.update(normalized_paths)
        else:
            # Rafraîchissement global
            self._pending_refreshes.clear()
        
        if immediate:
            self._execute_refresh()
        else:
            self._schedule_refresh()
    
    def _schedule_refresh(self):
        """Programme un rafraîchissement avec délai pour regrouper les notifications"""
        if self._refresh_timer:
            GLib.source_remove(self._refresh_timer)
        
        self._refresh_timer = GLib.timeout_add(self._refresh_delay_ms, self._execute_refresh)
    
    def _execute_refresh(self):
        """Exécute le rafraîchissement des composants enregistrés"""
        try:
            if not self._display_components:
                print("⚠️ Aucun composant d'affichage enregistré")
                return False
            
            albums_to_refresh = list(self._pending_refreshes) if self._pending_refreshes else None
            
            # Parcourir tous les composants enregistrés
            refreshed_count = 0
            for component in list(self._display_components):  # Copie pour éviter les modifications concurrentes
                if self._refresh_component(component, albums_to_refresh):
                    refreshed_count += 1
            
            # Nettoyer les rafraîchissements en attente
            self._pending_refreshes.clear()
            self._refresh_timer = None
            
        except Exception as e:
            print(f"❌ Erreur lors du rafraîchissement: {e}")
            self._refresh_timer = None
        
        return False  # Ne pas répéter le timer
    
    def _refresh_component(self, component, albums_to_refresh: Optional[List[str]] = None):
        """
        Rafraîchit un composant spécifique en mettant à jour directement ses cartes
        
        Args:
            component: Composant à rafraîchir (doit être NonotagsApp)
            albums_to_refresh: Liste des albums à rafraîchir (None = tous)
            
        Returns:
            bool: True si le rafraîchissement a réussi
        """
        try:
            component_type = type(component).__name__
            
            # Traitement spécial pour NonotagsApp
            if component_type == "NonotagsApp":
                return self._refresh_nonotags_app_cards(component, albums_to_refresh)
            
            # Fallback vers les méthodes existantes pour autres composants
            refresh_method = None
            
            if hasattr(component, '_refresh_albums_display'):
                refresh_method = component._refresh_albums_display
            elif hasattr(component, '_update_display'):
                refresh_method = component._update_display
            elif hasattr(component, 'refresh'):
                refresh_method = component.refresh
            elif hasattr(component, 'update'):
                refresh_method = component.update
            
            if refresh_method:
                # Programmer le rafraîchissement dans le thread principal GTK
                GLib.idle_add(refresh_method)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"  ❌ Erreur rafraîchissement {type(component).__name__}: {e}")
            return False
    
    def _refresh_nonotags_app_cards(self, app, albums_to_refresh: Optional[List[str]] = None):
        """
        Met à jour directement les cartes dans NonotagsApp sans rescan complet
        
        Args:
            app: Instance de NonotagsApp
            albums_to_refresh: Liste des dossiers d'albums à rafraîchir
            
        Returns:
            bool: True si le rafraîchissement a réussi
        """
        try:
            if not hasattr(app, 'albums_grid'):
                return False
            
            # Fonction à exécuter dans le thread principal GTK
            def update_cards():
                try:
                    updated_count = 0
                    
                    # Parcourir toutes les cartes dans albums_grid
                    children = app.albums_grid.get_children()
                    
                    for child in children:
                        child_type = type(child).__name__
                        
                        # Si c'est un FlowBoxChild, récupérer la vraie carte à l'intérieur
                        actual_card = child
                        if child_type == "FlowBoxChild":
                            # FlowBoxChild contient la vraie carte d'album
                            actual_card = child.get_child()
                        
                        if hasattr(actual_card, '_update_display'):
                            # Si albums_to_refresh est spécifié, vérifier si cette carte correspond
                            if albums_to_refresh:
                                card_path = getattr(actual_card, 'album_path', None)
                                if card_path and card_path not in albums_to_refresh:
                                    continue
                            
                            # Mettre à jour la carte
                            actual_card._update_display()
                            updated_count += 1
                    
                    return False  # Ne pas répéter le timer
                    
                except Exception as e:
                    print(f"  ❌ Erreur mise à jour cartes: {e}")
                    return False
            
            # Programmer la mise à jour dans le thread principal
            GLib.idle_add(update_cards)
            return True
            
        except Exception as e:
            print(f"  ❌ Erreur _refresh_nonotags_app_cards: {e}")
            return False
    
    def force_refresh_all(self):
        """Force un rafraîchissement immédiat de tous les composants"""
        self._pending_refreshes.clear()
        self._execute_refresh()
    
    def get_status(self):
        """Retourne le statut du gestionnaire pour debug"""
        return {
            "components_count": len(self._display_components),
            "pending_refreshes": len(self._pending_refreshes),
            "pending_albums": list(self._pending_refreshes),
            "timer_active": self._refresh_timer is not None
        }


# Instance globale pour faciliter l'accès
refresh_manager = RefreshManager.get_instance()