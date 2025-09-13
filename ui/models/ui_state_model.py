"""
Modèle d'état de l'interface utilisateur
Gère l'état global de l'UI moderne
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

class ViewMode(Enum):
    """Modes d'affichage de l'interface"""
    GRID = "grid"        # Vue en grille (défaut)
    LIST = "list"        # Vue en liste
    DETAILS = "details"  # Vue détaillée

class SortField(Enum):
    """Champs de tri disponibles"""
    TITLE = "title"
    ARTIST = "artist"
    YEAR = "year"
    GENRE = "genre"
    STATUS = "status"
    TRACK_COUNT = "track_count"

class SortOrder(Enum):
    """Ordre de tri"""
    ASC = "asc"   # Croissant
    DESC = "desc" # Décroissant

@dataclass
class FilterState:
    """État des filtres de l'interface"""
    search_text: str = ""
    selected_genres: List[str] = field(default_factory=list)
    selected_years: List[str] = field(default_factory=list)
    selected_statuses: List[str] = field(default_factory=list)
    show_only_selected: bool = False
    show_only_with_issues: bool = False

@dataclass
class UIStateModel:
    """
    Modèle d'état global de l'interface utilisateur moderne
    Centralise l'état de l'UI pour cohérence et réactivité
    """
    
    # Mode d'affichage
    view_mode: ViewMode = ViewMode.GRID
    
    # Tri
    sort_field: SortField = SortField.TITLE
    sort_order: SortOrder = SortOrder.ASC
    
    # Filtres
    filters: FilterState = field(default_factory=FilterState)
    
    # Sélection
    selected_album_ids: List[str] = field(default_factory=list)
    last_selected_id: Optional[str] = None
    
    # Interface
    sidebar_visible: bool = True
    search_bar_visible: bool = False
    status_bar_visible: bool = True
    
    # Progression et statut
    is_processing: bool = False
    processing_progress: float = 0.0
    status_message: str = "Prêt"
    
    # Dimensions et layout
    window_width: int = 1200
    window_height: int = 800
    sidebar_width: int = 300
    
    # Préférences d'affichage
    card_size: int = 250  # Taille des cards d'album
    show_covers: bool = True
    show_metadata: bool = True
    
    # Callbacks pour réactivité
    _callbacks: Dict[str, List[Callable]] = field(default_factory=dict)
    
    def add_callback(self, event: str, callback: Callable):
        """Ajoute un callback pour un événement"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable):
        """Retire un callback"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def emit_event(self, event: str, *args, **kwargs):
        """Déclenche tous les callbacks d'un événement"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Erreur dans callback {event}: {e}")
    
    # === MÉTHODES DE GESTION D'ÉTAT ===
    
    def set_view_mode(self, mode: ViewMode):
        """Change le mode d'affichage"""
        if self.view_mode != mode:
            self.view_mode = mode
            self.emit_event("view_mode_changed", mode)
    
    def set_sort(self, field: SortField, order: SortOrder = None):
        """Change le tri"""
        if order is None:
            # Toggle l'ordre si même champ
            if self.sort_field == field:
                order = SortOrder.DESC if self.sort_order == SortOrder.ASC else SortOrder.ASC
            else:
                order = SortOrder.ASC
        
        self.sort_field = field
        self.sort_order = order
        self.emit_event("sort_changed", field, order)
    
    def update_search(self, text: str):
        """Met à jour la recherche"""
        if self.filters.search_text != text:
            self.filters.search_text = text
            self.emit_event("search_changed", text)
    
    def toggle_search_bar(self):
        """Affiche/cache la barre de recherche"""
        self.search_bar_visible = not self.search_bar_visible
        self.emit_event("search_bar_toggled", self.search_bar_visible)
    
    def select_album(self, album_id: str, add_to_selection: bool = False):
        """Sélectionne un album"""
        if add_to_selection:
            if album_id not in self.selected_album_ids:
                self.selected_album_ids.append(album_id)
        else:
            self.selected_album_ids = [album_id]
        
        self.last_selected_id = album_id
        self.emit_event("selection_changed", self.selected_album_ids)
    
    def deselect_album(self, album_id: str):
        """Désélectionne un album"""
        if album_id in self.selected_album_ids:
            self.selected_album_ids.remove(album_id)
            self.emit_event("selection_changed", self.selected_album_ids)
    
    def select_all_albums(self, album_ids: List[str]):
        """Sélectionne tous les albums"""
        self.selected_album_ids = album_ids.copy()
        self.emit_event("selection_changed", self.selected_album_ids)
    
    def clear_selection(self):
        """Efface la sélection"""
        if self.selected_album_ids:
            self.selected_album_ids.clear()
            self.last_selected_id = None
            self.emit_event("selection_changed", self.selected_album_ids)
    
    def set_processing(self, is_processing: bool, progress: float = 0.0, message: str = ""):
        """Met à jour l'état de traitement"""
        self.is_processing = is_processing
        self.processing_progress = progress
        if message:
            self.status_message = message
        
        self.emit_event("processing_changed", is_processing, progress, message)
    
    def update_status(self, message: str):
        """Met à jour le message de statut"""
        self.status_message = message
        self.emit_event("status_changed", message)
    
    def set_window_size(self, width: int, height: int):
        """Met à jour la taille de la fenêtre"""
        self.window_width = width
        self.window_height = height
        self.emit_event("window_resized", width, height)
    
    # === PROPRIÉTÉS CALCULÉES ===
    
    @property
    def has_selection(self) -> bool:
        """Vérifie s'il y a une sélection"""
        return len(self.selected_album_ids) > 0
    
    @property
    def selection_count(self) -> int:
        """Nombre d'éléments sélectionnés"""
        return len(self.selected_album_ids)
    
    @property
    def has_filters(self) -> bool:
        """Vérifie s'il y a des filtres actifs"""
        return (
            bool(self.filters.search_text) or
            bool(self.filters.selected_genres) or
            bool(self.filters.selected_years) or
            bool(self.filters.selected_statuses) or
            self.filters.show_only_selected or
            self.filters.show_only_with_issues
        )
    
    def is_selected(self, album_id: str) -> bool:
        """Vérifie si un album est sélectionné"""
        return album_id in self.selected_album_ids
    
    # === SERIALISATION ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sauvegarde"""
        return {
            'view_mode': self.view_mode.value,
            'sort_field': self.sort_field.value,
            'sort_order': self.sort_order.value,
            'sidebar_visible': self.sidebar_visible,
            'status_bar_visible': self.status_bar_visible,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'sidebar_width': self.sidebar_width,
            'card_size': self.card_size,
            'show_covers': self.show_covers,
            'show_metadata': self.show_metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIStateModel':
        """Crée une instance depuis un dictionnaire"""
        state = cls()
        
        # Met à jour les valeurs depuis le dictionnaire
        if 'view_mode' in data:
            state.view_mode = ViewMode(data['view_mode'])
        if 'sort_field' in data:
            state.sort_field = SortField(data['sort_field'])
        if 'sort_order' in data:
            state.sort_order = SortOrder(data['sort_order'])
        
        # Autres propriétés
        for key, value in data.items():
            if hasattr(state, key) and not key.startswith('_'):
                setattr(state, key, value)
        
        return state
    
    def __repr__(self) -> str:
        """Représentation pour debug"""
        return (
            f"UIStateModel(view_mode={self.view_mode}, "
            f"selection_count={self.selection_count}, "
            f"processing={self.is_processing})"
        )
