"""
Gestionnaire de fenêtre sans HeaderBar
Gère les aspects spécifiques d'une fenêtre sans barre de titre
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from typing import Optional

class WindowManager:
    """Gestionnaire pour fenêtre sans HeaderBar"""
    
    def __init__(self, app_instance):
        """
        Args:
            app_instance: Instance de NonotagsApp
        """
        self.app = app_instance
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
    def setup_headerless_window(self):
        """Configure la fenêtre pour fonctionner sans HeaderBar"""
        if not self.app.main_window:
            return
            
        # Configurer les décorations de fenêtre
        self.app.main_window.set_decorated(False)  # ✅ Supprimer complètement la barre de titre
        
        # Activer le drag de fenêtre sur toute la surface
        self._setup_window_dragging()
        
        # Configurer les raccourcis clavier
        self._setup_keyboard_shortcuts()
        
        # Optionnel: Ajouter une zone de titre discrète
        self._add_minimal_title_area()
        
    def _setup_window_dragging(self):
        """Configure le déplacement de fenêtre par glisser-déposer"""
        if not self.app.main_window:
            return
            
        # Ajouter les événements nécessaires
        self.app.main_window.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | 
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        
        # Connecter les gestionnaires d'événements
        self.app.main_window.connect("button-press-event", self._on_window_button_press)
        self.app.main_window.connect("button-release-event", self._on_window_button_release)
        self.app.main_window.connect("motion-notify-event", self._on_window_motion)
        
    def _on_window_button_press(self, widget, event):
        """Gestionnaire de clic sur la fenêtre"""
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            # Clic gauche simple - démarrer le drag
            if self._is_in_draggable_area(event):
                self.is_dragging = True
                self.drag_start_x = event.x_root - widget.get_position()[0]
                self.drag_start_y = event.y_root - widget.get_position()[1]
                return True
        elif event.button == 1 and event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            # Double-clic - toggle maximize
            if self._is_in_draggable_area(event):
                self._toggle_maximize()
                return True
        return False
        
    def _on_window_button_release(self, widget, event):
        """Gestionnaire de relâchement de clic"""
        if event.button == 1:
            self.is_dragging = False
        return False
        
    def _on_window_motion(self, widget, event):
        """Gestionnaire de mouvement de souris"""
        if self.is_dragging and event.state & Gdk.ModifierType.BUTTON1_MASK:
            new_x = int(event.x_root - self.drag_start_x)
            new_y = int(event.y_root - self.drag_start_y)
            widget.move(new_x, new_y)
            return True
        return False
        
    def _is_in_draggable_area(self, event):
        """Vérifie si le clic est dans une zone permettant le drag"""
        # Pour l'instant, toute la fenêtre est draggable
        # Plus tard, on pourra exclure certaines zones (comme les albums)
        
        # Exclure la zone des albums (approximatif)
        if hasattr(self.app, 'albums_grid') and self.app.albums_grid:
            allocation = self.app.albums_grid.get_allocation()
            if (allocation.x <= event.x <= allocation.x + allocation.width and
                allocation.y <= event.y <= allocation.y + allocation.height):
                return False
        
        # Autoriser le drag sur le reste de la fenêtre
        return True
        
    def _toggle_maximize(self):
        """Bascule entre maximisé et normal"""
        if not self.app.main_window:
            return
            
        if self.app.main_window.is_maximized():
            self.app.main_window.unmaximize()
        else:
            self.app.main_window.maximize()
            
    def _setup_keyboard_shortcuts(self):
        """Configure les raccourcis clavier pour remplacer les boutons"""
        if not self.app.main_window:
            return
            
        # Créer un accélérateur group
        accel_group = Gtk.AccelGroup()
        self.app.main_window.add_accel_group(accel_group)
        
        # Raccourcis principaux
        # Ctrl+O pour Import
        accel_group.connect(
            Gdk.keyval_from_name('o'),
            Gdk.ModifierType.CONTROL_MASK,
            0,
            lambda ag, w, kv, mod: self.app.on_import_clicked(None)
        )
        
        # Ctrl+E pour Édition groupée
        accel_group.connect(
            Gdk.keyval_from_name('e'),
            Gdk.ModifierType.CONTROL_MASK,
            0,
            lambda ag, w, kv, mod: self.app.on_edit_selection_clicked(None)
        )
        
        # F5 pour Rescan
        accel_group.connect(
            Gdk.keyval_from_name('F5'),
            0,
            0,
            lambda ag, w, kv, mod: self._rescan_current_folder()
        )
        
        # Ctrl+Q pour Quitter
        accel_group.connect(
            Gdk.keyval_from_name('q'),
            Gdk.ModifierType.CONTROL_MASK,
            0,
            lambda ag, w, kv, mod: self.app.main_window.close()
        )
        
    def _rescan_current_folder(self):
        """Rescanne le dossier actuel"""
        if hasattr(self.app, 'current_folder') and self.app.current_folder:
            self.app._scan_folder(self.app.current_folder)
            
    def _add_minimal_title_area(self):
        """Ajoute une zone de titre minimaliste (optionnel)"""
        # Pour l'instant, on garde l'interface complètement clean
        # Cette méthode peut être utilisée plus tard si nécessaire
        pass
        
    def restore_window_decorations(self):
        """Restaure les décorations de fenêtre standard"""
        if self.app.main_window:
            # Déconnecter les gestionnaires de drag
            # (GTK ne fournit pas de méthode directe pour ça)
            pass