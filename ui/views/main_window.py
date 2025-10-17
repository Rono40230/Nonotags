"""
Application principale Nonotags
Gestionnaire de l'application avec fenêtre principale et navigation
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, Gdk
import os
from typing import List, Dict
from ui.startup_window import StartupWindow
from ui.components.album_card import AlbumCard
from ui.processing_orchestrator import ProcessingOrchestrator, ProcessingState, ProcessingStep
from ui.views.exceptions_window import ExceptionsWindow
from core.refresh_manager import refresh_manager
from ui.transitions.header_migration import HeaderMigration
from support.config_manager import ConfigManager
from ui.managers.persistent_window_manager import persistent_window_manager, WindowType

class NonotagsApp:
    """Application Nonotags avec séquence de démarrage"""
    
    def __init__(self):
        self.startup_window = None
        self.main_window = None
        self.albums_grid = None
        self._resize_timeout_id = None
        
        # Configuration et migration HeaderBar
        self.config_manager = ConfigManager()
        self.header_migration = HeaderMigration(self)
        
        # Orchestrateur de traitement
        self.orchestrator = ProcessingOrchestrator()
        self._setup_orchestrator_callbacks()
        
        # Initialiser les factories pour les fenêtres persistantes
        self._setup_persistent_window_factories()
        
        # Interface de progression (pour affichage pendant traitement automatique)
        self.progress_bar = None
        self.status_label = None
        self.step_label = None
        
        # Configuration lazy loading
        self.lazy_loading_batch = 20  # Nombre d'albums à charger par lot
        self.current_displayed_count = 0
        self.all_albums_data = []  # Tous les albums scannés
        self.displayed_album_cards = []  # Cards actuellement affichées
    
    def run(self):
        """Lance l'application avec la fenêtre de démarrage"""
        self.startup_window = StartupWindow(self)
        self.startup_window.show_all()
        
        Gtk.main()
        
    def create_main_window_with_scan(self, folder_path):
        """Crée la fenêtre principale et lance le scan du dossier"""
        self.create_main_window()
        
        # Lancer le scan automatiquement
        # Simuler le scan pour l'instant
        GLib.idle_add(self._scan_folder, folder_path)
    
    def _scan_folder(self, folder_path):
        """Scanne un dossier et ajoute les albums trouvés"""
        try:

            # Stocker le dossier actuel pour rescans futurs
            self.current_folder = folder_path
            
            from services.music_scanner import MusicScanner
            scanner = MusicScanner()

            albums = scanner.scan_directory(folder_path)
            
            # ✅ TRI PAR ANNÉE CROISSANTE : Trier les albums avant affichage
            albums = self._sort_albums_by_year(albums)

            # MODIFICATION: Stocker tous les albums pour lazy loading
            self.all_albums_data = albums
            self.current_displayed_count = 0
            self.displayed_album_cards = []

            # MODIFICATION: Ne plus effacer les albums existants
            # Initialiser les listes si elles n'existent pas
            if not hasattr(self, 'loaded_albums') or self.loaded_albums is None:
                self.loaded_albums = []
            
            # Vérifier si on a des albums existants dans la grille
            existing_albums_count = len(self.albums_grid.get_children()) if self.albums_grid else 0
            
            # Si c'est le premier import ET que la grille contient des albums de démo
            # (détecté par le fait qu'il n'y a pas encore de loaded_albums réels)
            if existing_albums_count > 0 and len(self.loaded_albums) == 0:
                # Effacer seulement les albums de démonstration
                for child in self.albums_grid.get_children():
                    child.destroy()
                # Nettoyer aussi la queue de l'orchestrator pour le premier import
                self.orchestrator.clear_queue()

            # MODIFICATION: Afficher le premier lot d'albums avec lazy loading
            self._display_next_batch()

            self.albums_grid.show_all()
            # Plus besoin de update_cards_per_line() - FlowBox s'adapte automatiquement

            # ✅ TRAITEMENT AUTOMATIQUE : Démarrer immédiatement le traitement
            if self.orchestrator.start_processing():
                pass  # Traitement automatique démarré
            else:
                pass  # Impossible de démarrer le traitement automatique
            
            # Sauvegarder le dossier actuel
            self.current_folder = folder_path
            
        except Exception as e:
            print(f"Erreur lors du scan: {e}")
            # En cas d'erreur, garder les albums de démo

    def _display_next_batch(self):
        """Affiche le prochain lot d'albums avec lazy loading"""
        if self.current_displayed_count >= len(self.all_albums_data):
            return  # Tous les albums sont déjà affichés

        # Calculer le nombre d'albums à afficher dans ce lot
        remaining_albums = len(self.all_albums_data) - self.current_displayed_count
        batch_size = min(self.lazy_loading_batch, remaining_albums)
        
        # Obtenir le lot d'albums à afficher
        start_index = self.current_displayed_count
        end_index = start_index + batch_size
        batch_albums = self.all_albums_data[start_index:end_index]

        # Ajouter les albums du lot à l'interface
        new_albums_added = []
        for album in batch_albums:
            # Vérifier si l'album n'est pas déjà dans la liste (éviter les doublons)
            album_path = album.get('folder_path') or album.get('path', '')
            already_exists = any(
                existing.get('folder_path') == album_path or existing.get('path') == album_path 
                for existing in self.loaded_albums
            )
            
            if not already_exists:
                card = AlbumCard(album, self)
                self.albums_grid.add(card)
                self.loaded_albums.append(album)
                new_albums_added.append(card)

        # Mettre à jour le compteur
        self.current_displayed_count += len(new_albums_added)
        
        # Afficher les cartes du lot
        for card in new_albums_added:
            card.show_all()

    def _sort_albums_by_year(self, albums):
        """Trie les albums par année croissante"""
        def get_year(album):
            try:
                year_str = album.get('year') or album.get('date', '')
                if year_str:
                    # Extraire l'année (format YYYY ou YYYY-MM-DD)
                    year = int(str(year_str)[:4])
                    return year
            except (ValueError, TypeError):
                pass
            return 9999  # Albums sans année à la fin
        
        return sorted(albums, key=get_year)

    def _on_scroll_value_changed(self, adjustment):
        """Callback pour lazy loading lors du scroll"""
        if self.albums_grid is None:
            return

        # Obtenir la position du scroll
        scrolled = adjustment.get_page_size() + adjustment.get_value()
        upper_bound = adjustment.get_upper()
        
        # Si on est à 80% du scroll, charger plus d'albums
        if scrolled >= upper_bound * 0.8:
            self._display_next_batch()

    def create_main_window(self):
        """Crée la fenêtre principale avec la barre d'outils et la grille d'albums"""
        
        # Configuration de base de la fenêtre
        self.main_window = Gtk.Window()
        self.main_window.set_default_size(1200, 800)  # Taille par défaut plus grande
        self.main_window.set_title("🎵 Nonotags - Gestionnaire de métadonnées musicales")

        # Charger le CSS pour les styles
        self._load_css()
        
        # Conteneur vertical principal (header + contenu)
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # ===== CRÉATION DE LA BARRE D'OUTILS =====
        toolbar = Gtk.HeaderBar()
        toolbar.set_show_close_button(True)
        toolbar.set_title("Nonotags")
        toolbar.set_subtitle("Gestionnaire de métadonnées musicales")
        
        # Bouton Importer (SANS rectangle)
        import_btn = Gtk.Button.new_with_label("Importer")
        import_btn.connect("clicked", self.on_import_clicked)
        toolbar.pack_start(import_btn)
        
        # Bouton Rafraîchir
        refresh_btn = Gtk.Button.new_with_label("Rafraîchir")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        toolbar.pack_start(refresh_btn)
        
        # Bouton Exceptions
        exceptions_btn = Gtk.Button.new_with_label("Exceptions")
        exceptions_btn.connect("clicked", self.on_exceptions_clicked)
        toolbar.pack_end(exceptions_btn)
        
        # Bouton Playlists
        playlists_btn = Gtk.Button.new_with_label("Playlists")
        playlists_btn.connect("clicked", self.on_playlists_clicked)
        toolbar.pack_end(playlists_btn)
        
        # Bouton Convertisseur
        converter_btn = Gtk.Button.new_with_label("Convertir")
        converter_btn.connect("clicked", self.on_converter_clicked)
        toolbar.pack_end(converter_btn)
        
        main_vbox.pack_start(toolbar, False, False, 0)
        
        # ===== CONTENU PRINCIPAL =====
        # Container principal avec scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Connecter le signal de scroll pour lazy loading
        scrolled.get_vadjustment().connect("value-changed", self._on_scroll_value_changed)
        
        # FlowBox pour affichage en grille
        self.albums_grid = Gtk.FlowBox()
        self.albums_grid.set_column_spacing(15)
        self.albums_grid.set_row_spacing(15)
        self.albums_grid.set_homogeneous(True)
        self.albums_grid.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.albums_grid.set_margin_left(20)
        self.albums_grid.set_margin_right(20)
        self.albums_grid.set_margin_top(20)
        self.albums_grid.set_margin_bottom(20)
        
        scrolled.add(self.albums_grid)
        main_vbox.pack_start(scrolled, True, True, 0)
        
        self.main_window.add(main_vbox)
        
        # Connecter le signal de fermeture
        self.main_window.connect("delete-event", self.on_main_window_close)
        
        # Afficher la fenêtre
        self.main_window.show_all()
        
        # Initialiser loaded_albums
        self.loaded_albums = []
        
        # Ajouter un message d'accueil
        self._add_welcome_message()

    def _add_welcome_message(self):
        """Ajoute un message d'accueil si aucun album n'est chargé"""
        # Message de bienvenue supprimé - l'interface reste vide lors du démarrage
        pass

    def on_main_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre principale"""
        # Désenregistrer du RefreshManager
        refresh_manager.unregister_display_component(self)
        
        Gtk.main_quit()

    def on_import_clicked(self, button):
        """Callback du bouton Importer"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier d'albums à importer",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            folder_path = dialog.get_filename()
            dialog.destroy()
            
            # Lancer le scan
            GLib.idle_add(self._scan_folder, folder_path)
        else:
            dialog.destroy()

    def on_refresh_clicked(self, button):
        """Callback du bouton Rafraîchir"""
        if hasattr(self, 'current_folder'):
            GLib.idle_add(self._scan_folder, self.current_folder)

    def on_exceptions_clicked(self, button):
        """Ouvre la fenêtre des exceptions"""
        window = persistent_window_manager.get_window(WindowType.EXCEPTIONS, self.main_window)
        if window:
            window.show_all()

    def on_playlists_clicked(self, button):
        """Ouvre la fenêtre du gestionnaire de playlists"""
        window = persistent_window_manager.get_window(WindowType.PLAYLIST_MANAGER, self.main_window)
        if window:
            window.show_all()

    def on_converter_clicked(self, button):
        """Ouvre la fenêtre du convertisseur audio"""
        window = persistent_window_manager.get_window(WindowType.AUDIO_CONVERTER, self.main_window)
        if window:
            window.show_all()

    def _load_css(self):
        """Charge le fichier CSS pour les styles"""
        try:
            css_provider = Gtk.CssProvider()
            css_file = os.path.join(os.path.dirname(__file__), "..", "resources", "styles.css")
            
            if os.path.exists(css_file):
                css_provider.load_from_path(css_file)
                screen = Gdk.Screen.get_default()
                style_context = Gtk.StyleContext()
                style_context.add_provider_for_screen(
                    screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                print(f"✅ CSS chargé depuis: {css_file}")
            else:
                print(f"⚠️ Fichier CSS introuvable: {css_file}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du CSS: {e}")

    def _setup_orchestrator_callbacks(self):
        """Configure les callbacks de l'orchestrateur"""
        pass

    def _setup_persistent_window_factories(self):
        """Configure les factories pour les fenêtres persistantes"""
        pass
