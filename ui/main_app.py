"""
Application principale Nonotags
Gestionnaire de l'application avec fenêtre principale et navigation
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib
import os
from typing import List, Dict
from ui.startup_window import StartupWindow
from ui.components.album_card import AlbumCard
from ui.processing_orchestrator import ProcessingOrchestrator, ProcessingState, ProcessingStep


class NonotagsApp:
    """Application Nonotags avec séquence de démarrage"""
    
    def __init__(self):
        self.startup_window = None
        self.main_window = None
        self.albums_grid = None
        self._resize_timeout_id = None
        
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
        
        print("✅ Application Nonotags lancée avec succès!")
        print("🎯 Fenêtre de démarrage affichée")
        Gtk.main()
        
    def create_main_window_with_scan(self, folder_path):
        """Crée la fenêtre principale et lance le scan du dossier"""
        self.create_main_window()
        
        # Lancer le scan automatiquement
        print(f"🔍 Lancement du scan pour: {folder_path}")
        # Simuler le scan pour l'instant
        GLib.idle_add(self._scan_folder, folder_path)
    
    def _scan_folder(self, folder_path):
        """Scanne un dossier et ajoute les albums trouvés"""
        try:
            # Stocker le dossier actuel pour rescans futurs
            self.current_folder = folder_path
            print(f"🔍 SCAN - Scanning: {folder_path}")
            
            from services.music_scanner import MusicScanner
            scanner = MusicScanner()
            albums = scanner.scan_directory(folder_path)
            
            print(f"✅ {len(albums)} albums trouvés")
            
            # Effacer les albums de démonstration
            if self.albums_grid:
                for child in self.albums_grid.get_children():
                    child.destroy()
                    
            # Ajouter les vrais albums
            for album in albums:
                card = AlbumCard(album)
                self.albums_grid.add(card)
                
            # Sauvegarder les albums pour le traitement
            self.loaded_albums = albums
            self.orchestrator.clear_queue()
            self.orchestrator.add_albums(albums)
                
            self.albums_grid.show_all()
            self.update_cards_per_line()
            
            # ✅ TRAITEMENT AUTOMATIQUE : Démarrer immédiatement le traitement
            print("🚀 Démarrage automatique du traitement...")
            if self.orchestrator.start_processing():
                print("✅ Traitement automatique démarré")
            else:
                print("❌ Impossible de démarrer le traitement automatique")
            
            # Sauvegarder le dossier actuel
            self.current_folder = folder_path
            
        except Exception as e:
            print(f"❌ Erreur lors du scan: {e}")
            # En cas d'erreur, garder les albums de démo
        
        return False  # Pour GLib.idle_add
        
    def create_main_window(self):
        """Crée la fenêtre principale après le démarrage"""
        self.main_window = Gtk.Window()
        self.main_window.set_title("🎵 Nonotags - Gestionnaire de Tags MP3")
        
        # Force l'affichage en plein écran
        self.main_window.maximize()  # Maximise la fenêtre (recommandé)
        # Alternative : self.main_window.fullscreen()  # Plein écran sans barre de titre
        
        self.main_window.set_position(Gtk.WindowPosition.CENTER)
        self.main_window.connect("delete-event", self.on_main_window_close)
        self.main_window.connect("check-resize", self.on_window_resize)
        
        # Container principal avec scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        
        # Boutons d'action principaux
        action_box = Gtk.Box(spacing=10)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(10)
        
        scan_btn = Gtk.Button.new_with_label("📁 Scanner des dossiers")
        scan_btn.get_style_context().add_class("modern-button")
        scan_btn.connect("clicked", self.on_scan_clicked)
        action_box.pack_start(scan_btn, False, False, 0)
        
        import_btn = Gtk.Button.new_with_label("📂 Importer des fichiers")
        import_btn.get_style_context().add_class("modern-button")
        import_btn.connect("clicked", self.on_import_clicked)
        action_box.pack_start(import_btn, False, False, 0)
        
        edit_selection_btn = Gtk.Button.new_with_label("✏️ Editer la sélection d'albums")
        edit_selection_btn.get_style_context().add_class("modern-button")
        edit_selection_btn.connect("clicked", self.on_edit_selection_clicked)
        action_box.pack_start(edit_selection_btn, False, False, 0)
        
        settings_btn = Gtk.Button.new_with_label("⚙️ Paramètres")
        settings_btn.connect("clicked", self.on_settings_clicked)
        action_box.pack_start(settings_btn, False, False, 0)
        
        main_box.pack_start(action_box, False, False, 0)
        
        # Grille d'albums avec calcul dynamique
        self.albums_grid = Gtk.FlowBox()
        self.albums_grid.set_valign(Gtk.Align.START)
        self.albums_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        
        # Forcer le FlowBox à respecter les tailles des enfants
        self.albums_grid.set_homogeneous(False)
        self.albums_grid.set_column_spacing(20)
        self.albums_grid.set_row_spacing(20)
        self.albums_grid.set_min_children_per_line(1)
        self.albums_grid.set_max_children_per_line(10)
        
        main_box.pack_start(self.albums_grid, True, True, 0)
        
        scrolled.add(main_box)
        self.main_window.add(scrolled)
        
        # Affichage de la fenêtre principale
        self.main_window.show_all()
        
        GLib.idle_add(self.update_cards_per_line)
        print("🎯 Fenêtre principale ouverte")
        
        # Fermer la fenêtre de démarrage
        if self.startup_window:
            self.startup_window.destroy()
            self.startup_window = None
    
    def on_main_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre principale"""
        print("👋 Fermeture de l'application")
        Gtk.main_quit()
        return False
    
    def on_scan_clicked(self, button):
        """Gestion du scan de dossiers"""
        dialog = Gtk.FileChooserDialog(
            title="Choisir le dossier à scanner",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            "Annuler", Gtk.ResponseType.CANCEL,
            "Scanner", Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            dialog.destroy()
            self._start_scanning(folder)
        else:
            dialog.destroy()
    
    def _start_scanning(self, folder_path: str):
        """Démarre le processus de scan avec progress dialog"""
        progress_dialog = Gtk.Dialog(
            title="Scan en cours...",
            parent=self.main_window,
            modal=True
        )
        progress_dialog.set_size_request(400, 150)
        
        content = progress_dialog.get_content_area()
        content.set_margin_left(20)
        content.set_margin_right(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        status_label = Gtk.Label()
        status_label.set_text(f"Scan du dossier: {os.path.basename(folder_path)}")
        content.pack_start(status_label, False, False, 0)
        
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_pulse_step(0.1)
        content.pack_start(progress_bar, False, False, 10)
        
        details_label = Gtk.Label()
        details_label.set_text("Recherche des fichiers musicaux...")
        content.pack_start(details_label, False, False, 0)
        
        progress_dialog.show_all()
        
        def progress_callback(albums_count, current_album):
            details_label.set_text(f"Albums trouvés: {albums_count} - {current_album}")
            progress_bar.pulse()
            while Gtk.events_pending():
                Gtk.main_iteration()
        
        try:
            from services.music_scanner import MusicScanner
            scanner = MusicScanner()
            albums = scanner.scan_directory(folder_path, progress_callback)
            progress_dialog.destroy()
            self._update_albums_display(albums)
            
            success_dialog = Gtk.MessageDialog(
                parent=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Scan terminé !"
            )
            success_dialog.format_secondary_text(
                f"{len(albums)} albums ont été trouvés et ajoutés à votre collection."
            )
            success_dialog.run()
            success_dialog.destroy()
            
        except Exception as e:
            progress_dialog.destroy()
            error_dialog = Gtk.MessageDialog(
                parent=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Erreur lors du scan"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
    
    def _update_albums_display(self, albums: List[Dict]):
        """Met à jour l'affichage des albums"""
        print(f"🔄 _update_albums_display appelée avec {len(albums)} albums")
        
        # Vider la grille actuelle
        if self.albums_grid:
            for child in self.albums_grid.get_children():
                child.destroy()
        
        # Ajouter les nouvelles cartes
        for album_data in albums:
            print(f"📋 Création card pour: {album_data.get('path', 'AUCUN_PATH')}")
            card = AlbumCard(album_data)

    def on_import_clicked(self, button):
        """Gestion de l'import de fichiers avec traitement automatique"""
        dialog = Gtk.FileChooserDialog(
            title="Importer des fichiers musicaux",
            parent=self.main_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            "Annuler", Gtk.ResponseType.CANCEL,
            "Importer", Gtk.ResponseType.OK
        )
        
        # Filtres pour fichiers audio
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Fichiers audio")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.flac")
        filter_audio.add_pattern("*.ogg")
        filter_audio.add_pattern("*.wav")
        filter_audio.add_pattern("*.m4a")
        dialog.add_filter(filter_audio)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("Tous les fichiers")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        dialog.set_select_multiple(True)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
            dialog.destroy()
            self._start_importing(filenames)
        else:
            dialog.destroy()
    
    def _start_importing(self, filenames: List[str]):
        """Démarre l'import de fichiers avec traitement automatique"""
        progress_dialog = Gtk.Dialog(
            title="Import en cours...",
            parent=self.main_window,
            modal=True
        )
        progress_dialog.set_size_request(400, 150)
        
        content = progress_dialog.get_content_area()
        content.set_margin_left(20)
        content.set_margin_right(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        status_label = Gtk.Label()
        status_label.set_text(f"Import de {len(filenames)} fichier(s)...")
        content.pack_start(status_label, False, False, 0)
        
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_pulse_step(0.1)
        content.pack_start(progress_bar, False, False, 10)
        
        details_label = Gtk.Label()
        details_label.set_text("Traitement en cours...")
        content.pack_start(details_label, False, False, 0)
        
        progress_dialog.show_all()
        
        try:
            # Simuler l'import en créant des albums à partir des fichiers
            albums = []
            for i, filename in enumerate(filenames):
                # Mettre à jour la progress bar
                progress_bar.set_fraction((i + 1) / len(filenames))
                details_label.set_text(f"Import: {os.path.basename(filename)}")
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                # Créer un album factice à partir du fichier
                # (Dans la vraie implémentation, on utiliserait mutagen pour lire les métadonnées)
                album_data = {
                    "album": f"Album {i+1}",
                    "artist": "Artiste importé",
                    "year": "2023",
                    "genre": "Inconnu",
                    "tracks": 1,
                    "path": os.path.dirname(filename),  # ✅ DOSSIER de l'album, pas le fichier MP3
                    "emoji": "🎵",
                    "color": "green"
                }
                albums.append(album_data)
            
            progress_dialog.destroy()
            
            # Mettre à jour l'affichage avec traitement automatique
            self._update_albums_display(albums)
            
            success_dialog = Gtk.MessageDialog(
                parent=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Import terminé !"
            )
            success_dialog.format_secondary_text(
                f"{len(albums)} fichier(s) importé(s) et traitement automatique démarré."
            )
            success_dialog.run()
            success_dialog.destroy()
            
        except Exception as e:
            progress_dialog.destroy()
            error_dialog = Gtk.MessageDialog(
                parent=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Erreur lors de l'import"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
    
    def on_edit_selection_clicked(self, button):
        """Ouvre l'édition groupée pour les albums sélectionnés"""
        selected_albums = []
        for child in self.albums_grid.get_children():
            if hasattr(child, 'selection_checkbox') and child.selection_checkbox.get_active():
                selected_albums.append(child.album_data)
        
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
        
        print(f"✏️ Édition groupée de {len(selected_albums)} album(s) sélectionné(s)")
        for album in selected_albums:
            print(f"   - {album.get('artist', 'Artiste')} - {album.get('album', 'Titre')}")
    
    def on_settings_clicked(self, button):
        """Ouvre la fenêtre des paramètres"""
        print("⚙️ Paramètres - Fonctionnalité à implémenter")
    
    def calculate_cards_per_line(self, window_width=None):
        """Calcule le nombre optimal de cartes par ligne selon la largeur disponible"""
        if window_width is None:
            if hasattr(self, 'main_window') and self.main_window:
                window_width = self.main_window.get_allocated_width()
            else:
                window_width = 1200
        
        CARD_WIDTH = 320
        CARD_SPACING = 20
        WINDOW_MARGINS = 40
        
        available_width = window_width - WINDOW_MARGINS
        cards_per_line = max(1, available_width // (CARD_WIDTH + CARD_SPACING))
        cards_per_line = min(8, cards_per_line)
        
        return int(cards_per_line)
    
    def update_cards_per_line(self):
        """Met à jour le nombre de cartes par ligne selon la taille de fenêtre actuelle"""
        if not hasattr(self, 'albums_grid') or not self.albums_grid:
            return
            
        cards_per_line = self.calculate_cards_per_line()
        
        self.albums_grid.set_min_children_per_line(cards_per_line)
        self.albums_grid.set_max_children_per_line(cards_per_line)
        
        if hasattr(self, 'main_window') and self.main_window:
            width = self.main_window.get_allocated_width()
            print(f"📐 Largeur fenêtre: {width}px → {cards_per_line} cartes par ligne")
    
    def on_window_resize(self, window):
        """Gestionnaire de redimensionnement de fenêtre avec debouncing"""
        if self._resize_timeout_id:
            GLib.source_remove(self._resize_timeout_id)
        
        self._resize_timeout_id = GLib.timeout_add(100, self._delayed_resize_update)
    
    def _delayed_resize_update(self):
        """Met à jour le layout avec un délai pour éviter les calculs excessifs"""
        self.update_cards_per_line()
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
        
        print(f"🔄 État traitement: {old_state} → {new_state}")
    
    def on_processing_progress_updated(self, progress, processed, total):
        """Callback mise à jour du progrès"""
        if self.progress_bar:
            self.progress_bar.set_fraction(progress / 100.0)
            self.progress_bar.set_text(f"{processed}/{total} albums ({progress:.1f}%)")
        
        print(f"📊 Progrès: {progress:.1f}% ({processed}/{total})")
    
    def on_processing_step_changed(self, step, album_number):
        """Callback changement d'étape"""
        step_name = self.orchestrator.get_step_description(step)
        
        if self.step_label:
            self.step_label.set_markup(f"<span size='small'>Étape: <b>{step_name}</b> (Album {album_number})</span>")
        
        print(f"🔧 Étape: {step_name} - Album {album_number}")
    
    def on_album_processed(self, album, success):
        """Callback album traité"""
        album_title = album.get('title', 'Sans titre')
        status = "✅ Réussi" if success else "❌ Échec"
        print(f"🎵 Album traité: {album_title} - {status}")
        
        # TODO: Mettre à jour l'état de la carte d'album correspondante
    
    def on_processing_error(self, error_message):
        """Callback erreur de traitement"""
        print(f"❌ Erreur traitement: {error_message}")
        
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
            print(f"✅ {message}")
            
            # RESCAN pour rafraîchir les cards avec les nouveaux noms
            print("🔄 Rafraîchissement des cartes après traitement...")
            print(f"🔍 DEBUG - current_folder disponible: {hasattr(self, 'current_folder')}")
            if hasattr(self, 'current_folder') and self.current_folder:
                # SOLUTION: Chercher le nouveau nom du dossier après renommage
                old_folder = self.current_folder
                print(f"🔍 DEBUG - Ancien dossier: {old_folder}")
                
                # Si l'ancien dossier n'existe plus, chercher le nouveau nom
                if not os.path.exists(old_folder):
                    parent_dir = os.path.dirname(old_folder)
                    print(f"🔍 DEBUG - Recherche dans parent: {parent_dir}")
                    
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
                                        print(f"✅ DEBUG - Dossier RÈGLE 17 trouvé: {item}")
                                        break
                                except PermissionError:
                                    continue
                    
                    if new_folder:
                        self.current_folder = new_folder
                        print(f"✅ DEBUG - Nouveau dossier configuré: {new_folder}")
                    else:
                        print("❌ DEBUG - Aucun dossier RÈGLE 17 trouvé")
                
                print(f"🔍 DEBUG - Rescanning: {self.current_folder}")
                GLib.idle_add(self._scan_folder, self.current_folder)
            else:
                print("❌ DEBUG - Pas de current_folder pour rescan")
            
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
            print(f"⚠️ {message}")
        
        # Réinitialiser la barre de progression
        if self.progress_bar:
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text("Prêt")
    
    def _refresh_albums_display(self):
        """Rafraîchit l'affichage des albums en rescannant le dossier actuel"""
        try:
            # Récupère le dossier actuellement affiché
            if hasattr(self, 'current_folder') and self.current_folder:
                # Rescanne le dossier pour récupérer les noms mis à jour
                from services.music_scanner import MusicScanner
                scanner = MusicScanner()
                updated_albums = scanner.scan_directory(self.current_folder)
                
                # Met à jour l'affichage avec les nouvelles données
                self._update_albums_display(updated_albums)
                print(f"🔄 Affichage rafraîchi: {len(updated_albums)} albums")
            else:
                print("❌ Pas de dossier actuel pour rafraîchissement")
        except Exception as e:
            print(f"❌ Erreur lors du rafraîchissement: {e}")
