"""
Vue principale moderne pour Nonotags
Interface principale avec grille d'albums et navigation moderne
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
from typing import TYPE_CHECKING, List
import os

if TYPE_CHECKING:
    from ..app_controller import NonotagsApp

from ..components.album_grid import AlbumGrid
from ..models.album_model import AlbumModel

class MainView(Adw.ApplicationWindow):
    """
    Fenêtre principale moderne avec design épuré
    Grille d'albums responsive et navigation intuitive
    """
    
    def __init__(self, app: 'NonotagsApp'):
        super().__init__(
            application=app,
            title="Nonotags - Gestionnaire MP3",
            default_width=1200,
            default_height=800
        )
        
        # Permet la maximisation et le plein écran
        self.set_resizable(True)
        self.set_can_target(True)
        
        self.app = app
        self.selected_albums: List[AlbumModel] = []
        
        self._setup_ui()
        self._setup_actions()
        self._load_sample_data()  # Pour la démo
        
        self.app.logger.info("Fenêtre principale initialisée")
    
    def _setup_ui(self):
        """Configure l'interface utilisateur moderne"""
        
        # === HEADER BAR MODERNE ===
        header_bar = Adw.HeaderBar()
        header_bar.add_css_class("modern-headerbar")
        
        # Titre avec sous-titre
        title_widget = Adw.WindowTitle(
            title="Nonotags",
            subtitle="Gestionnaire de métadonnées MP3"
        )
        header_bar.set_title_widget(title_widget)
        
        # Boutons de la header bar
        self._setup_header_buttons(header_bar)
        
        self.set_titlebar(header_bar)
        
        # === CONTENU PRINCIPAL ===
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Barre d'outils moderne
        toolbar = self._create_modern_toolbar()
        main_box.append(toolbar)
        
        # Zone de contenu avec grille d'albums
        content_area = self._create_content_area()
        main_box.append(content_area)
        
        # Barre de statut
        status_bar = self._create_status_bar()
        main_box.append(status_bar)
        
        self.set_content(main_box)
    
    def _setup_header_buttons(self, header_bar: Adw.HeaderBar):
        """Configure les boutons de la header bar"""
        
        # Bouton d'import à gauche
        import_button = Gtk.Button()
        import_button.set_icon_name("folder-open-symbolic")
        import_button.set_tooltip_text("Importer des albums")
        import_button.add_css_class("suggested-action")
        import_button.connect("clicked", self._on_import_clicked)
        header_bar.pack_start(import_button)
        
        # Menu principal à droite
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menu principal")
        
        # Menu model
        menu_model = Gio.Menu()
        menu_model.append("Préférences", "app.preferences")
        menu_model.append("À propos", "app.about")
        menu_model.append("Quitter", "app.quit")
        
        menu_button.set_menu_model(menu_model)
        header_bar.pack_end(menu_button)
        
        # Bouton de recherche
        search_button = Gtk.ToggleButton()
        search_button.set_icon_name("edit-find-symbolic")
        search_button.set_tooltip_text("Rechercher")
        search_button.connect("toggled", self._on_search_toggled)
        header_bar.pack_end(search_button)
    
    def _create_modern_toolbar(self) -> Gtk.Box:
        """Crée la barre d'outils moderne avec gestion de sélection"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        toolbar.set_margin_start(20)
        toolbar.set_margin_end(20)
        toolbar.add_css_class("modern-toolbar")
        
        # Titre de la section
        section_label = Gtk.Label()
        section_label.set_markup("<b>Albums importés</b>")
        section_label.add_css_class("section-title")
        toolbar.append(section_label)
        
        # Espaceur
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Informations de sélection
        self.selection_label = Gtk.Label(label="0 albums sélectionnés")
        self.selection_label.add_css_class("selection-info")
        toolbar.append(self.selection_label)
        
        # Bouton "Éditer la sélection" (initialement caché)
        self.edit_selection_button = Gtk.Button(label="Éditer la sélection")
        self.edit_selection_button.set_icon_name("document-edit-symbolic")
        self.edit_selection_button.add_css_class("suggested-action")
        self.edit_selection_button.set_visible(False)
        self.edit_selection_button.connect("clicked", self._on_edit_selection_clicked)
        toolbar.append(self.edit_selection_button)
        
        return toolbar
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.set_margin_top(10)
        toolbar.set_margin_bottom(10)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        
        # Titre de la section
        section_label = Gtk.Label()
        section_label.set_markup("<b>Albums importés</b>")
        toolbar.append(section_label)
        
        # Espaceur
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Informations de sélection
        self.selection_label = Gtk.Label(label="0 albums sélectionnés")
        toolbar.append(self.selection_label)
        
        return toolbar
    
    def _create_content_area(self) -> Gtk.Widget:
        """Crée la zone de contenu principal avec grille d'albums"""
        
        # ScrolledWindow pour la grille
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Grille d'albums moderne
        self.album_grid = AlbumGrid(self)
        self.album_grid.add_css_class("album-grid")
        
        scrolled.set_child(self.album_grid)
        
        return scrolled
    
    def _create_status_bar(self) -> Gtk.Box:
        """Crée une barre de statut moderne"""
        status_bar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
            margin_start=12,
            margin_end=12,
            margin_top=4,
            margin_bottom=8
        )
        status_bar.add_css_class("status-bar")
        
        # Statut général
        self.status_label = Gtk.Label(label="Prêt")
        self.status_label.set_halign(Gtk.Align.START)
        
        # Nombre total d'albums
        self.total_albums_label = Gtk.Label(label="0 albums")
        self.total_albums_label.add_css_class("dim-label")
        
        # Espacement
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        
        # Indicateur de progression (caché par défaut)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.set_size_request(200, -1)
        
        status_bar.append(self.status_label)
        status_bar.append(spacer)
        status_bar.append(self.total_albums_label)
        status_bar.append(self.progress_bar)
        
        return status_bar
    
    def _setup_actions(self):
        """Configure les actions de l'application"""
        
        # Action de préférences
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self._on_preferences)
        self.app.add_action(preferences_action)
        
        # Action à propos
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.app.add_action(about_action)
        
        # Action plein écran
        fullscreen_action = Gio.SimpleAction.new("fullscreen", None)
        fullscreen_action.connect("activate", self._on_fullscreen)
        self.app.add_action(fullscreen_action)
        
        # Action quitter
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *args: self.app.quit_application())
        self.app.add_action(quit_action)
        
        # Raccourcis clavier
        self.app.set_accel_for_action("app.fullscreen", "F11")
    
    def _load_sample_data(self):
        """Charge des données d'exemple pour la démo"""
        sample_albums = [
            AlbumModel(
                title="Kind of Blue",
                artist="Miles Davis",
                year="1959",
                genre="Jazz",
                track_count=9,
                folder_path="/music/Miles Davis - Kind of Blue"
            ),
            AlbumModel(
                title="The Dark Side of the Moon",
                artist="Pink Floyd",
                year="1973",
                genre="Progressive Rock",
                track_count=10,
                folder_path="/music/Pink Floyd - The Dark Side of the Moon"
            ),
            AlbumModel(
                title="Thriller",
                artist="Michael Jackson",
                year="1982",
                genre="Pop",
                track_count=9,
                folder_path="/music/Michael Jackson - Thriller"
            ),
        ]
        
        self.album_grid.set_albums(sample_albums)
        self._update_status()
    
    def _update_status(self):
        """Met à jour la barre de statut"""
        total = len(self.album_grid.albums)
        selected = len(self.selected_albums)
        
        self.total_albums_label.set_text(f"{total} albums")
        
        if selected == 0:
            self.selection_label.set_text("Aucun album sélectionné")
            self.process_button.set_sensitive(False)
        else:
            self.selection_label.set_text(f"{selected} album{'s' if selected > 1 else ''} sélectionné{'s' if selected > 1 else ''}")
            self.process_button.set_sensitive(True)
    
    # === CALLBACKS ===
    
    def _on_import_clicked(self, button):
        """Gère l'import d'albums"""
        self.app.logger.info("Import d'albums demandé")
        # TODO: Implémenter l'import
    
    def _on_search_toggled(self, button):
        """Gère l'activation/désactivation de la recherche"""
        if button.get_active():
            self.app.logger.info("Recherche activée")
            # TODO: Afficher la barre de recherche
        else:
            self.app.logger.info("Recherche désactivée")

    def _on_preferences(self, action, param):
        """Ouvre les préférences"""
        self.app.logger.info("Préférences demandées")
        # TODO: Ouvrir la fenêtre de préférences
    
    def _on_edit_selection_clicked(self, button):
        """Ouvre l'édition pour les albums sélectionnés"""
        selected_albums = self.album_grid.get_selected_albums()
        if selected_albums:
            self.app.logger.info(f"Édition de {len(selected_albums)} albums sélectionnés")
            self.app.open_album_edit(selected_albums)
        else:
            self.app.logger.warning("Aucun album sélectionné pour l'édition")
    
    def on_album_selection_changed(self, album, selected):
        """Callback appelé quand la sélection d'un album change"""
        self._update_selection_info()
    
    def _update_selection_info(self):
        """Met à jour les informations de sélection"""
        count = self.album_grid.get_selected_count()
        
        if count == 0:
            self.selection_label.set_text("0 albums sélectionnés")
            self.edit_selection_button.set_visible(False)
        else:
            self.selection_label.set_text(f"{count} album{'s' if count > 1 else ''} sélectionné{'s' if count > 1 else ''}")
            self.edit_selection_button.set_visible(True)
    
    def show_toast(self, message: str):
        """Affiche une notification toast"""
        # Pour l'instant, utilise print - TODO: implémenter avec Adw.Toast
        print(f"Toast: {message}")
        self.app.logger.info(f"Toast affiché: {message}")
    
    def confirm_remove_album(self, album):
        """Demande confirmation avant de retirer un album"""
        # TODO: Implémenter une boîte de dialogue de confirmation
        # Pour l'instant, retire directement
        self.album_grid.remove_album(album)
        self._update_selection_info()
        self.show_toast(f"Album '{album.title}' retiré de la liste")
        self.app.logger.info("Ouverture des préférences")
        # TODO: Fenêtre de préférences
    
    def _on_about(self, action, param):
        """Affiche la boîte à propos"""
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="Nonotags",
            application_icon="audio-x-generic",
            developer_name="Équipe Nonotags",
            version="1.0.0",
            website="https://github.com/nonotags/nonotags",
            copyright="© 2024 Nonotags",
            license_type=Gtk.License.MIT_X11
        )
        about.present()
    
    def _on_fullscreen(self, action, param):
        """Basculer le mode plein écran"""
        if self.is_fullscreen():
            self.unfullscreen()
            self.app.logger.info("Mode fenêtré activé")
        else:
            self.fullscreen()
            self.app.logger.info("Mode plein écran activé")
    
    def on_album_selection_changed(self, album: 'AlbumModel', selected: bool):
        """Callback quand la sélection d'un album change"""
        if selected and album not in self.selected_albums:
            self.selected_albums.append(album)
        elif not selected and album in self.selected_albums:
            self.selected_albums.remove(album)
        
        self._update_status()
