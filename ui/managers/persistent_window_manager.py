"""
Gestionnaire de fenêtres persistantes (PersistentWindowManager)
Gère les fenêtres qui restent ouvertes jusqu'à fermeture manuelle par l'utilisateur
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Dict, List, Optional, Type, Any
from enum import Enum
import weakref
import traceback

class WindowType(Enum):
    """Types de fenêtres gérées"""
    ALBUM_EDIT = "album_edit"
    CASE_EXCEPTIONS = "case_exceptions" 
    PLAYLIST_MANAGER = "playlist_manager"
    AUDIO_CONVERTER = "audio_converter"

class WindowInstance:
    """Représentation d'une instance de fenêtre persistante"""
    
    def __init__(self, window_type: WindowType, window_obj: Gtk.Window, 
                 identifier: str = None, data: Any = None):
        self.window_type = window_type
        self.window_ref = weakref.ref(window_obj, self._on_window_destroyed)
        self.identifier = identifier or f"{window_type.value}_{id(window_obj)}"
        self.data = data
        self.is_active = True
        
        # Connecter le signal de fermeture pour nettoyage automatique
        window_obj.connect("destroy", self._on_destroy)
        
    def _on_window_destroyed(self, ref):
        """Callback quand la fenêtre est détruite"""
        self.is_active = False
        
    def _on_destroy(self, widget):
        """Handler de destruction de fenêtre"""
        self.is_active = False
        
    def get_window(self) -> Optional[Gtk.Window]:
        """Récupère la fenêtre si elle existe encore"""
        if self.window_ref:
            return self.window_ref()
        return None
        
    def is_alive(self) -> bool:
        """Vérifie si la fenêtre existe encore"""
        return self.is_active and self.get_window() is not None

class PersistentWindowManager:
    """
    Gestionnaire de fenêtres persistantes
    Permet d'avoir plusieurs fenêtres du même type ouvertes simultanément
    """
    
    def __init__(self):
        # Registre des fenêtres ouvertes par type
        self._windows: Dict[WindowType, List[WindowInstance]] = {
            window_type: [] for window_type in WindowType
        }
        
        # Factories pour créer chaque type de fenêtre
        self._window_factories: Dict[WindowType, callable] = {}
        
        # Callbacks pour synchronisation des données
        self._sync_callbacks: Dict[WindowType, List[callable]] = {
            window_type: [] for window_type in WindowType
        }
        
        # Timer de nettoyage automatique
        self._cleanup_timer = GLib.timeout_add_seconds(30, self._cleanup_dead_windows)
        
    def register_window_factory(self, window_type: WindowType, factory: callable):
        """
        Enregistre une factory pour créer un type de fenêtre
        
        Args:
            window_type: Type de fenêtre
            factory: Fonction qui crée la fenêtre (signature: factory(*args, **kwargs) -> Gtk.Window)
        """
        self._window_factories[window_type] = factory
        
    def register_sync_callback(self, window_type: WindowType, callback: callable):
        """
        Enregistre un callback de synchronisation pour un type de fenêtre
        
        Args:
            window_type: Type de fenêtre
            callback: Fonction appelée lors de changements (signature: callback(window_instances, data))
        """
        if callback not in self._sync_callbacks[window_type]:
            self._sync_callbacks[window_type].append(callback)
            
    def create_or_focus_window(self, window_type: WindowType, 
                              identifier: str = None, 
                              focus_existing: bool = True,
                              *args, **kwargs) -> Optional[Gtk.Window]:
        """
        Crée une nouvelle fenêtre ou focus sur une existante
        
        Args:
            window_type: Type de fenêtre à créer
            identifier: Identifiant unique (pour fenêtres uniques comme playlist manager)
            focus_existing: Si True, focus sur existante au lieu de créer nouvelle
            *args, **kwargs: Arguments pour la factory
            
        Returns:
            Instance de la fenêtre ou None si erreur
        """
        try:
            # Nettoyer les fenêtres mortes d'abord
            self._cleanup_dead_windows()
            
            # Si identifier fourni et focus_existing=True, chercher fenêtre existante
            if identifier and focus_existing:
                existing_window = self._find_window_by_identifier(window_type, identifier)
                if existing_window:
                    window = existing_window.get_window()
                    if window:
                        window.present()  # Mettre au premier plan
                        print(f"🔄 Focus sur fenêtre existante: {window_type.value} [{identifier}]")
                        return window
                        
            # Créer nouvelle fenêtre si factory disponible
            if window_type not in self._window_factories:
                print(f"❌ Pas de factory enregistrée pour {window_type.value}")
                return None
                
            factory = self._window_factories[window_type]
            window = factory(*args, **kwargs)
            
            if not window or not isinstance(window, Gtk.Window):
                print(f"❌ Factory a retourné un objet invalide pour {window_type.value}")
                return None
                
            # Configurer fenêtre comme non-modale et persistante
            self._setup_persistent_window(window)
            
            # Enregistrer la fenêtre
            window_instance = WindowInstance(
                window_type=window_type,
                window_obj=window,
                identifier=identifier,
                data=kwargs.get('data')
            )
            
            self._windows[window_type].append(window_instance)
            
            print(f"✅ Nouvelle fenêtre créée: {window_type.value} [{identifier or 'auto'}]")
            print(f"📊 Total fenêtres {window_type.value}: {len(self._windows[window_type])}")
            
            # Notifier les callbacks de synchronisation
            self._notify_sync_callbacks(window_type)
            
            return window
            
        except Exception as e:
            print(f"❌ Erreur création fenêtre {window_type.value}: {e}")
            traceback.print_exc()
            return None
            
    def _setup_persistent_window(self, window: Gtk.Window):
        """Configure une fenêtre pour être persistante"""
        # Fenêtre non-modale
        window.set_modal(False)
        
        # Reste au-dessus mais pas toujours
        window.set_keep_above(False)
        
        # Position par défaut
        window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        
        # Redimensionnable
        window.set_resizable(True)
        
        # Icône et titre si pas définis
        if not window.get_title():
            window.set_title("Nonotags")
            
    def _find_window_by_identifier(self, window_type: WindowType, 
                                  identifier: str) -> Optional[WindowInstance]:
        """Trouve une fenêtre par son identifiant"""
        for window_instance in self._windows[window_type]:
            if (window_instance.identifier == identifier and 
                window_instance.is_alive()):
                return window_instance
        return None
        
    def get_windows(self, window_type: WindowType) -> List[Gtk.Window]:
        """Récupère toutes les fenêtres vivantes d'un type"""
        windows = []
        for window_instance in self._windows[window_type]:
            if window_instance.is_alive():
                window = window_instance.get_window()
                if window:
                    windows.append(window)
        return windows
        
    def get_window_count(self, window_type: WindowType) -> int:
        """Compte le nombre de fenêtres ouvertes d'un type"""
        return len([w for w in self._windows[window_type] if w.is_alive()])
        
    def close_all_windows(self, window_type: WindowType = None):
        """Ferme toutes les fenêtres d'un type ou tous types"""
        window_types = [window_type] if window_type else list(WindowType)
        
        for wtype in window_types:
            for window_instance in self._windows[wtype][:]:  # Copie pour éviter modification pendant itération
                if window_instance.is_alive():
                    window = window_instance.get_window()
                    if window:
                        window.destroy()
                        
    def broadcast_data_change(self, window_type: WindowType, data: Any):
        """Diffuse un changement de données à toutes les fenêtres d'un type"""
        self._notify_sync_callbacks(window_type, data)
        
    def _notify_sync_callbacks(self, window_type: WindowType, data: Any = None):
        """Notifie les callbacks de synchronisation"""
        window_instances = [w for w in self._windows[window_type] if w.is_alive()]
        
        for callback in self._sync_callbacks[window_type]:
            try:
                callback(window_instances, data)
            except Exception as e:
                print(f"⚠️ Erreur callback sync {window_type.value}: {e}")
                
    def _cleanup_dead_windows(self) -> bool:
        """Nettoie les références vers des fenêtres détruites"""
        cleaned_count = 0
        
        for window_type in WindowType:
            alive_windows = []
            for window_instance in self._windows[window_type]:
                if window_instance.is_alive():
                    alive_windows.append(window_instance)
                else:
                    cleaned_count += 1
                    
            self._windows[window_type] = alive_windows
            
        if cleaned_count > 0:
            print(f"🧹 Nettoyage: {cleaned_count} références de fenêtres supprimées")
            
        return True  # Continuer le timer
        
    def get_stats(self) -> Dict[str, int]:
        """Statistiques des fenêtres ouvertes"""
        stats = {}
        for window_type in WindowType:
            stats[window_type.value] = self.get_window_count(window_type)
        return stats
        
    def shutdown(self):
        """Nettoyage à la fermeture de l'application"""
        if self._cleanup_timer:
            GLib.source_remove(self._cleanup_timer)
            self._cleanup_timer = None
            
        # Fermer toutes les fenêtres
        self.close_all_windows()
        
        print("🔚 PersistentWindowManager arrêté")

# Instance globale
persistent_window_manager = PersistentWindowManager()