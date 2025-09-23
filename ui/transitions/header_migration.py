"""
Gestionnaire de migration HeaderBar
Coordonne la transition entre interface avec/sans header
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Optional, Callable

class HeaderMigration:
    """Gère la migration progressive du HeaderBar vers interface contextuelle"""
    
    def __init__(self, app_instance):
        """
        Args:
            app_instance: Instance de NonotagsApp
        """
        self.app = app_instance
        self.use_headerbar = True  # Par défaut, on garde le header
        self.context_menu_manager = None
        self.window_manager = None
        
    def initialize_transition_components(self):
        """Initialise les composants de transition"""
        from .context_menu_manager import ContextMenuManager
        from .window_manager import WindowManager
        
        self.context_menu_manager = ContextMenuManager(self.app)
        self.window_manager = WindowManager(self.app)
        
    def setup_window_with_mode(self, use_headerbar: bool = True):
        """
        Configure la fenêtre selon le mode choisi
        
        Args:
            use_headerbar: True pour mode classique, False pour mode contextuel
        """
        self.use_headerbar = use_headerbar
        
        if self.use_headerbar:
            self._setup_classic_mode()
        else:
            self._setup_contextual_mode()
            
    def _setup_classic_mode(self):
        """Configure l'interface avec HeaderBar (mode actuel)"""
        # Le code existant de création du HeaderBar
        self._create_classic_headerbar()
        
    def _setup_contextual_mode(self):
        """Configure l'interface sans HeaderBar (nouveau mode)"""
        if not self.context_menu_manager or not self.window_manager:
            self.initialize_transition_components()
            
        # Supprimer le HeaderBar
        self.app.main_window.set_titlebar(None)
        
        # Configurer la fenêtre pour mode contextuel
        self.window_manager.setup_headerless_window()
        
        # Activer les menus contextuels
        self.context_menu_manager.activate_context_menus()
        
    def _create_classic_headerbar(self):
        """Recrée le HeaderBar classique (code existant)"""
        # Créer le HeaderBar moderne avec boutons intégrés
        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(True)
        headerbar.get_style_context().add_class("titlebar")
        
        # Boutons de gauche du header
        left_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        import_btn = Gtk.Button.new_with_label("Importer des albums")
        import_btn.get_style_context().add_class("header-button")
        import_btn.get_style_context().add_class("button-import")
        import_btn.set_size_request(-1, 22)
        import_btn.connect("clicked", self.app.on_import_clicked)
        left_buttons_box.pack_start(import_btn, False, False, 0)
        
        edit_selection_btn = Gtk.Button.new_with_label("Éditer les albums sélectionnés")
        edit_selection_btn.get_style_context().add_class("header-button")
        edit_selection_btn.get_style_context().add_class("button-edit-selection")
        edit_selection_btn.set_size_request(-1, 22)
        edit_selection_btn.connect("clicked", self.app.on_edit_selection_clicked)
        left_buttons_box.pack_start(edit_selection_btn, False, False, 0)
        
        exceptions_btn = Gtk.Button.new_with_label("Ajouter des exceptions de casse")
        exceptions_btn.get_style_context().add_class("header-button")
        exceptions_btn.get_style_context().add_class("button-exceptions")
        exceptions_btn.set_size_request(-1, 22)
        exceptions_btn.connect("clicked", self.app.on_exceptions_clicked)
        left_buttons_box.pack_start(exceptions_btn, False, False, 0)
        
        # Boutons de droite du header
        right_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        playlists_btn = Gtk.Button.new_with_label("Gestionnaire de playlists")
        playlists_btn.get_style_context().add_class("header-button")
        playlists_btn.get_style_context().add_class("button-playlists")
        playlists_btn.set_size_request(-1, 22)
        playlists_btn.connect("clicked", self.app.on_playlists_clicked)
        right_buttons_box.pack_start(playlists_btn, False, False, 0)
        
        converter_btn = Gtk.Button.new_with_label("Convertir les formats musicaux")
        converter_btn.get_style_context().add_class("header-button")
        converter_btn.get_style_context().add_class("button-converter")
        converter_btn.set_size_request(-1, 22)
        converter_btn.connect("clicked", self.app.on_converter_clicked)
        right_buttons_box.pack_start(converter_btn, False, False, 0)
        
        # Ajouter les boutons à gauche et à droite du header
        headerbar.pack_start(left_buttons_box)
        headerbar.pack_end(right_buttons_box)
        
        # Définir le HeaderBar comme barre de titre
        self.app.main_window.set_titlebar(headerbar)
        
    def toggle_mode(self):
        """Bascule entre les deux modes"""
        self.setup_window_with_mode(not self.use_headerbar)
        
    def get_current_mode(self) -> str:
        """Retourne le mode actuel"""
        return "headerbar" if self.use_headerbar else "contextual"