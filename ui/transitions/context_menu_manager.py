"""
Gestionnaire de menus contextuels
Remplace les boutons du HeaderBar par des menus contextuels
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from typing import Optional

class ContextMenuManager:
    """Gestionnaire de menus contextuels pour remplacer le HeaderBar"""
    
    def __init__(self, app_instance):
        """
        Args:
            app_instance: Instance de NonotagsApp
        """
        self.app = app_instance
        self.main_menu = None
        self.album_grid_menu = None
        
    def activate_context_menus(self):
        """Active tous les menus contextuels"""
        self._create_main_context_menu()
        self._setup_album_grid_context_menu()
        self._setup_window_context_menu()
        
    def _create_main_context_menu(self):
        """Crée le menu contextuel principal"""
        self.main_menu = Gtk.Menu()
        
        # Section Import
        import_item = Gtk.MenuItem.new_with_label("📁 Importer des albums...")
        import_item.connect("activate", lambda w: self.app.on_import_clicked(None))
        self.main_menu.append(import_item)
        
        # Séparateur
        separator1 = Gtk.SeparatorMenuItem()
        self.main_menu.append(separator1)
        
        # Section Édition
        edit_selection_item = Gtk.MenuItem.new_with_label("✏️ Éditer les albums sélectionnés")
        edit_selection_item.connect("activate", lambda w: self.app.on_edit_selection_clicked(None))
        self.main_menu.append(edit_selection_item)
        
        exceptions_item = Gtk.MenuItem.new_with_label("⚙️ Exceptions de casse...")
        exceptions_item.connect("activate", lambda w: self.app.on_exceptions_clicked(None))
        self.main_menu.append(exceptions_item)
        
        # Séparateur
        separator2 = Gtk.SeparatorMenuItem()
        self.main_menu.append(separator2)
        
        # Section Outils
        playlists_item = Gtk.MenuItem.new_with_label("🎵 Gestionnaire de playlists...")
        playlists_item.connect("activate", lambda w: self.app.on_playlists_clicked(None))
        self.main_menu.append(playlists_item)
        
        converter_item = Gtk.MenuItem.new_with_label("🔄 Convertir les formats...")
        converter_item.connect("activate", lambda w: self.app.on_converter_clicked(None))
        self.main_menu.append(converter_item)
        
        # Séparateur
        separator3 = Gtk.SeparatorMenuItem()
        self.main_menu.append(separator3)
        
        # Quitter
        quit_item = Gtk.MenuItem.new_with_label("❌ Quitter")
        quit_item.connect("activate", self._on_quit_clicked)
        self.main_menu.append(quit_item)
        
        self.main_menu.show_all()
        
    def _setup_album_grid_context_menu(self):
        """Configure le menu contextuel pour la grille d'albums"""
        if self.app.albums_grid:
            self.app.albums_grid.connect("button-press-event", self._on_grid_button_press)
            
    def _setup_window_context_menu(self):
        """Configure le menu contextuel pour la fenêtre principale"""
        if self.app.main_window:
            # Ajouter le clic droit sur la fenêtre principale
            self.app.main_window.connect("button-press-event", self._on_window_button_press)
            # S'assurer que la fenêtre peut recevoir les événements
            self.app.main_window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            
    def _on_grid_button_press(self, widget, event):
        """Gestionnaire de clic sur la grille d'albums"""
        if event.button == 3:  # Clic droit
            self._show_context_menu(event)
            return True
        return False
        
    def _on_window_button_press(self, widget, event):
        """Gestionnaire de clic sur la fenêtre"""
        if event.button == 3:  # Clic droit
            self._show_context_menu(event)
            return True
        return False
        
    def _show_context_menu(self, event):
        """Affiche le menu contextuel"""
        if self.main_menu:
            self.main_menu.popup_at_pointer(event)
            
    def _on_toggle_mode_clicked(self, menuitem):
        """Bascule vers le mode HeaderBar"""
        if hasattr(self.app, 'header_migration'):
            self.app.header_migration.toggle_mode()
            
    def _on_quit_clicked(self, menuitem):
        """Ferme l'application"""
        if hasattr(self.app, 'main_window'):
            self.app.main_window.close()
        else:
            Gtk.main_quit()
            
    def deactivate_context_menus(self):
        """Désactive les menus contextuels"""
        if self.app.albums_grid:
            # Déconnecter les signaux si possible
            pass
        if self.app.main_window:
            # Déconnecter les signaux si possible
            pass