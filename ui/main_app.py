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
        
        # Interface de progression (pour affichage pendant traitement automatique)
        self.progress_bar = None
        self.status_label = None
        self.step_label = None
        
        # Albums chargés
        self.loaded_albums = []
        self.current_folder = None  # Dossier actuellement affiché
    
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
                    
            # Ajouter les nouveaux albums sans dupliquer
            new_albums_added = []

            for album in albums:
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
                    new_albums_added.append(album)

            # Ajouter SEULEMENT les nouveaux albums à l'orchestrator
            if new_albums_added:
                self.orchestrator.add_albums(new_albums_added)

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
            print(f"❌ Erreur lors du scan: {e}")
            # En cas d'erreur, garder les albums de démo

    def _sort_albums_by_year(self, albums: List[Dict]) -> List[Dict]:
        """Trie les albums par ordre croissant des années"""
        def get_year_for_sorting(album):
            """Extrait l'année pour le tri, avec gestion des cas spéciaux"""
            year = album.get('year', album.get('date', ''))
            
            if not year:
                return 9999  # Albums sans année en fin
                
            year_str = str(year)
            
            # Gestion des compilations avec plusieurs années (ex: "1990, 1993, 1995")
            if ',' in year_str:
                # Prendre la première année pour le tri
                years = [y.strip() for y in year_str.split(',')]
                try:
                    return int(years[0])
                except (ValueError, IndexError):
                    return 9999
            
            # Extraire les 4 premiers caractères pour l'année (gestion des dates complètes)
            try:
                year_int = int(year_str[:4])
                # Vérifier que c'est une année valide
                if 1900 <= year_int <= 2100:
                    return year_int
                else:
                    return 9999
            except (ValueError, TypeError):
                return 9999
        
        try:
            sorted_albums = sorted(albums, key=get_year_for_sorting)
            return sorted_albums
        except Exception as e:
            return albums  # Retourner la liste originale en cas d'erreur
        
        return False  # Pour GLib.idle_add
    
    def remove_album_from_list(self, album_data):
        """
        Supprime un album de toutes les structures de données
        
        Args:
            album_data: Les données de l'album à supprimer
        """
        try:
            # Supprimer de loaded_albums
            if hasattr(self, 'loaded_albums') and self.loaded_albums:
                album_path = album_data.get('folder_path') or album_data.get('path', '')
                self.loaded_albums = [
                    album for album in self.loaded_albums 
                    if (album.get('folder_path') or album.get('path', '')) != album_path
                ]
            
            # Supprimer de la queue de l'orchestrator
            if hasattr(self, 'orchestrator') and self.orchestrator:
                album_path = album_data.get('folder_path') or album_data.get('path', '')
                self.orchestrator.albums_queue = [
                    album for album in self.orchestrator.albums_queue 
                    if (album.get('folder_path') or album.get('path', '')) != album_path
                ]
                self.orchestrator.total_albums = len(self.orchestrator.albums_queue)
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression de l'album: {e}")
        
    def create_main_window(self):
        """Crée la fenêtre principale après le démarrage"""
        self.main_window = Gtk.Window()
        self.main_window.get_style_context().add_class("main-window")  # Appliquer le style fond blanc
        
        # Charger le CSS pour les styles
        self._load_css()
        
        # Utiliser le système de migration pour configurer l'interface
        use_headerbar = self.config_manager.ui.use_headerbar
        self.header_migration.setup_window_with_mode(use_headerbar)
        
        # Force l'affichage en plein écran
        self.main_window.maximize()  # Maximise la fenêtre (recommandé)
        # Alternative : self.main_window.fullscreen()  # Plein écran sans barre de titre
        
        self.main_window.set_position(Gtk.WindowPosition.CENTER)
        self.main_window.connect("delete-event", self.on_main_window_close)
        self.main_window.connect("size-allocate", self.on_window_resize)
        
        # Container principal avec scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        
        # Grille d'albums avec affichage responsive et adaptatif
        self.albums_grid = Gtk.FlowBox()
        self.albums_grid.set_valign(Gtk.Align.START)
        self.albums_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        
        # Configuration FlowBox pour affichage responsive sans troncature
        self.albums_grid.set_homogeneous(False)
        self.albums_grid.set_column_spacing(20)
        self.albums_grid.set_row_spacing(20)
        self.albums_grid.set_min_children_per_line(1)
        self.albums_grid.set_max_children_per_line(100)  # Pas de limite artificielle
        
        main_box.pack_start(self.albums_grid, True, True, 0)
        
        scrolled.add(main_box)
        self.main_window.add(scrolled)
        
        # Affichage de la fenêtre principale
        self.main_window.show_all()
        
        # Plus besoin de calcul initial - FlowBox s'adapte automatiquement
        
        # Enregistrer auprès du RefreshManager pour les notifications de rafraîchissement
        refresh_manager.register_display_component(self)
        
        # Fermer la fenêtre de démarrage
        if self.startup_window:
            self.startup_window.destroy()
            self.startup_window = None
    
    def on_main_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre principale"""
        # Désenregistrer du RefreshManager
        refresh_manager.unregister_display_component(self)
        
        Gtk.main_quit()
        return False
    
    def on_import_clicked(self, button):
        """Import de fichiers/albums individuels"""

        dialog = Gtk.FileChooserDialog(
            title="Importer des fichiers musicaux ou des albums",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            "Annuler", Gtk.ResponseType.CANCEL,
            "Importer", Gtk.ResponseType.OK
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()

            dialog.destroy()
            # Utiliser la même fonction que pour le scan depuis la fenêtre de démarrage
            self._scan_folder(folder)
        else:

            dialog.destroy()
    
    def _update_albums_display(self, albums: List[Dict]):
        """Met à jour l'affichage des albums en conservant les cards existantes"""
        
        # ✅ TRI PAR ANNÉE CROISSANTE : Maintenir le tri lors des mises à jour
        albums = self._sort_albums_by_year(albums)
        
        # Au lieu de vider et recréer, mettre à jour les cards existantes
        existing_cards = self.albums_grid.get_children()
        
        # Créer un dictionnaire des albums par chemin pour mise à jour
        albums_by_path = {}
        for album in albums:
            album_path = album.get('folder_path') or album.get('path', '')
            if album_path:
                albums_by_path[album_path] = album
        
        # Mettre à jour les cards existantes avec les nouvelles métadonnées
        for card in existing_cards:
            if hasattr(card, 'album_data'):
                card_path = card.album_data.get('folder_path') or card.album_data.get('path', '')
                if card_path in albums_by_path:
                    # Mettre à jour les données de la card
                    card.album_data.update(albums_by_path[card_path])
                    # Mettre à jour l'affichage de la card
                    card._update_display()
        
        # Sauvegarder la liste mise à jour (remplacer, pas ajouter)
        self.loaded_albums = albums
        
        # Pas besoin de recréer les cards ou d'ajouter à l'orchestrator
        self.albums_grid.show_all()
    
    def on_edit_selection_clicked(self, button):
        """Ouvre l'édition groupée pour les albums sélectionnés"""
        selected_albums = []
        
        # Parcourir les albums et collecter ceux qui sont sélectionnés
        for flowbox_child in self.albums_grid.get_children():
            album_card = flowbox_child.get_child()
            if hasattr(album_card, 'selection_checkbox') and album_card.selection_checkbox.get_active():
                if hasattr(album_card, 'album_data'):
                    selected_albums.append(album_card.album_data)
        
        if not selected_albums:
            dialog = Gtk.MessageDialog(
                parent=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Aucun album sélectionné"
            )
            dialog.format_secondary_text(
                "Veuillez sélectionner au moins un album avant d'utiliser l'édition groupée."
            )
            dialog.run()
            dialog.destroy()
            return
        
        # Edition groupée demandée - Passer TOUS les albums sélectionnés
        try:
            from ui.views.album_edit_window import AlbumEditWindow
            
            print(f"🎯 Ouverture de la fenêtre d'édition pour {len(selected_albums)} albums sélectionnés")
            
            # Créer la fenêtre d'édition avec tous les albums sélectionnés
            edit_window = AlbumEditWindow(selected_albums, None)
            edit_window.show_all()
                
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture de la fenêtre d'édition: {e}")
            import traceback
            traceback.print_exc()
            dialog = Gtk.MessageDialog(
                parent=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Erreur d'ouverture"
            )
            dialog.format_secondary_text(
                f"Impossible d'ouvrir la fenêtre d'édition:\n{str(e)}"
            )
            dialog.run()
            dialog.destroy()
    
    def on_exceptions_clicked(self, button):
        """Ouvre la fenêtre de gestion des exceptions de casse"""
        try:
            exceptions_window = ExceptionsWindow(parent=self.main_window)
            exceptions_window.show_all()
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture de la fenêtre des exceptions: {e}")
    
    def on_playlists_clicked(self, button):
        """Ouvre le gestionnaire de playlists"""
        try:
            from ui.views.playlist_manager_window import PlaylistManagerWindow
            playlist_window = PlaylistManagerWindow(parent=self.main_window)
            playlist_window.show_all()
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du gestionnaire de playlists: {e}")
            import traceback
            traceback.print_exc()
    
    def on_converter_clicked(self, button):
        """Ouvre le convertisseur audio"""
        try:
            from ui.views.audio_converter_window import AudioConverterWindow
            converter_window = AudioConverterWindow()
            converter_window.show_all()
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture du convertisseur audio: {e}")
    
    def on_window_resize(self, window, allocation=None):
        """Gestionnaire de redimensionnement de fenêtre avec debouncing"""
        if self._resize_timeout_id:
            GLib.source_remove(self._resize_timeout_id)
        
        self._resize_timeout_id = GLib.timeout_add(150, self._delayed_resize_update)
    
    def _delayed_resize_update(self):
        """Met à jour le layout avec un délai pour éviter les calculs excessifs"""
        # Plus besoin de calcul manuel - FlowBox s'adapte automatiquement
        self._resize_timeout_id = None
        return False
    
    def _setup_orchestrator_callbacks(self):
        """Configure les callbacks de l'orchestrateur"""
        self.orchestrator.on_state_changed = self.on_processing_state_changed
        self.orchestrator.on_progress_updated = self.on_processing_progress_updated
        self.orchestrator.on_step_changed = self.on_processing_step_changed
        self.orchestrator.on_album_processed = self.on_album_processed
        self.orchestrator.on_error_occurred = self.on_processing_error
        self.orchestrator.on_processing_completed = self.on_processing_completed
    
    # === CALLBACKS DE L'ORCHESTRATEUR ===
    
    def on_processing_state_changed(self, old_state, new_state):
        """Callback changement d'état du traitement"""
        state_names = {
            ProcessingState.IDLE: "Inactif",
            ProcessingState.RUNNING: "En cours",
            ProcessingState.PAUSED: "En pause", 
            ProcessingState.COMPLETED: "Terminé",
            ProcessingState.ERROR: "Erreur",
            ProcessingState.CANCELLED: "Annulé"
        }
        
        state_name = state_names.get(new_state, "Inconnu")
        
        if self.status_label:
            self.status_label.set_markup(f"<span size='small'>État: <b>{state_name}</b></span>")
    
    def on_processing_progress_updated(self, progress, processed, total):
        """Callback mise à jour du progrès"""
        if self.progress_bar:
            self.progress_bar.set_fraction(progress / 100.0)
            self.progress_bar.set_text(f"{processed}/{total} albums ({progress:.1f}%)")
    
    def on_processing_step_changed(self, step, album_number):
        """Callback changement d'étape"""
        step_name = self.orchestrator.get_step_description(step)
        
        if self.step_label:
            self.step_label.set_markup(f"<span size='small'>Étape: <b>{step_name}</b> (Album {album_number})</span>")
    
    def on_album_processed(self, album, success):
        """Callback album traité"""
        album_title = album.get('album', 'Sans titre')
        status = "✅ Réussi" if success else "❌ Échec"
        # Log supprimé car il indiquait de fausses informations d'échec
        
        # Mettre à jour la carte d'album correspondante
        self._update_album_card_after_processing(album, success)
    
    def _update_album_card_after_processing(self, album, success):
        """Met à jour la carte d'album après traitement"""
        try:
            original_folder_path = album.get('folder_path', '')
            if not original_folder_path:
                return
            
            # Trouver la carte correspondante dans la grille
            for child in self.albums_grid.get_children():
                if hasattr(child, 'get_child') and child.get_child():  # FlowBoxChild
                    card = child.get_child()
                    if hasattr(card, 'album_data'):
                        card_folder_path = card.album_data.get('folder_path', '')
                        
                        if card_folder_path == original_folder_path:
                            # ✅ FIX: Mettre à jour directement avec les nouvelles données de l'album
                            # L'orchestrateur a déjà mis à jour album['folder_path']
                            card.album_data.update(album)
                            if hasattr(card, '_update_display'):
                                card._update_display()
                            print(f"✅ Carte mise à jour avec les nouvelles données")
                            
                            break
            
        except Exception as e:
            print(f"❌ Erreur mise à jour carte: {e}")
    
    def _same_music_files(self, old_path, new_path):
        """Vérifie si deux dossiers contiennent les mêmes fichiers musicaux"""
        try:
            if not os.path.exists(new_path):
                return False
                
            # Lister les fichiers MP3 dans les deux dossiers
            old_files = [f for f in os.listdir(old_path) if f.lower().endswith('.mp3')] if os.path.exists(old_path) else []
            new_files = [f for f in os.listdir(new_path) if f.lower().endswith('.mp3')]
            
            return len(old_files) == len(new_files) and len(new_files) > 0
            
        except Exception:
            return False
    
    def on_processing_error(self, error_message):
        """Callback erreur de traitement"""
        
        # Afficher un dialog d'erreur
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Erreur de traitement"
        )
        dialog.format_secondary_text(error_message)
        dialog.run()
        dialog.destroy()
    
    def on_processing_completed(self, success, processed, total):
        """Callback traitement terminé"""
        if success:
            message = f"🎉 Traitement automatique terminé avec succès!\n{processed}/{total} albums traités et optimisés."
            
            # RESCAN pour rafraîchir les cards avec les nouveaux noms
            if hasattr(self, 'current_folder') and self.current_folder:
                # SOLUTION: Chercher le nouveau nom du dossier après renommage
                old_folder = self.current_folder
                
                # Si l'ancien dossier n'existe plus, chercher le nouveau nom
                if not os.path.exists(old_folder):
                    parent_dir = os.path.dirname(old_folder)
                    
                    # Chercher un dossier qui commence par une parenthèse (format RÈGLE 17)
                    new_folder = None
                    if os.path.exists(parent_dir):
                        for item in os.listdir(parent_dir):
                            item_path = os.path.join(parent_dir, item)
                            if os.path.isdir(item_path) and item.startswith('('):
                                # Vérifier si ce dossier contient des MP3
                                try:
                                    mp3_files = [f for f in os.listdir(item_path) if f.lower().endswith('.mp3')]
                                    if mp3_files:
                                        new_folder = item_path
                                        break
                                except PermissionError:
                                    continue
                    
                    if new_folder:
                        self.current_folder = new_folder
                
                # Au lieu de rescanner avec _scan_folder (qui ajoute des doublons),
                # utiliser _refresh_albums_display pour mettre à jour les cards existantes
                GLib.idle_add(self._refresh_albums_display)
            
            # Dialog de succès - DÉSACTIVÉ sur demande utilisateur
            # dialog = Gtk.MessageDialog(
            #     transient_for=self.main_window,
            #     flags=0,
            #     message_type=Gtk.MessageType.INFO,
            #     buttons=Gtk.ButtonsType.OK,
            #     text="Traitement automatique terminé"
            # )
            # dialog.format_secondary_text(f"✅ {processed}/{total} albums ont été automatiquement traités et optimisés.\n\nVos albums sont maintenant prêts à l'usage !")
            # dialog.run()
            # dialog.destroy()
        else:
            message = f"⚠️ Traitement automatique interrompu.\n{processed}/{total} albums traités."
        
        # Réinitialiser la barre de progression
        if self.progress_bar:
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text("Prêt")
    
    def _refresh_albums_display(self, force_reload_metadata=True):
        """Rafraîchit l'affichage des albums en rescannant le dossier actuel"""
        try:
            # Récupère le dossier actuellement affiché
            if hasattr(self, 'current_folder') and self.current_folder:
                # Rescanne le dossier pour récupérer les noms mis à jour
                from services.music_scanner import MusicScanner
                scanner = MusicScanner()
                
                # Forcer le rechargement des métadonnées si demandé
                updated_albums = scanner.scan_directory(self.current_folder)
                
                # Met à jour l'affichage avec les nouvelles données
                self._update_albums_display(updated_albums)
            else:
                pass  # Pas de dossier actuel pour rafraîchissement
        except Exception as e:
            print(f"❌ Erreur lors du rafraîchissement: {e}")
    
    def _load_css(self):
        """Charge les fichiers CSS pour les styles"""
        try:
            screen = Gdk.Screen.get_default()
            style_context = Gtk.StyleContext()
            
            # Charger le CSS principal des boutons
            css_provider = Gtk.CssProvider()
            css_file = os.path.join(os.path.dirname(__file__), "resources", "styles.css")
            
            if os.path.exists(css_file):
                css_provider.load_from_path(css_file)
                style_context.add_provider_for_screen(
                    screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            
            # Charger le thème moderne pour les cartes
            modern_css_provider = Gtk.CssProvider()
            modern_css_file = os.path.join(os.path.dirname(__file__), "resources", "css", "modern_theme.css")
            
            if os.path.exists(modern_css_file):
                modern_css_provider.load_from_path(modern_css_file)
                style_context.add_provider_for_screen(
                    screen, modern_css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
                )
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement du CSS: {e}")