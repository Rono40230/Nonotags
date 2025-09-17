"""
Fenêtre d'édition d'album
Fenêtre d'édition conforme au cahier des charges avec 4 blocs
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib
import os
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from services.audio_player import AudioPlayer, PlayerState
from services.cover_search import CoverSearchService


class AlbumEditWindow(Gtk.Window):
    """Fenêtre d'édition conforme au cahier des charges - 4 blocs"""
    
    def __init__(self, album_data, parent_card):
        super().__init__(title="🎵 Édition d'album")
        self.album_data = album_data
        self.parent_card = parent_card
        self.tracks = []
        
        # Services
        self.audio_player = AudioPlayer()
        self.cover_search = CoverSearchService()
        self.current_track_index = 0
        
        # Callbacks du lecteur audio
        self.audio_player.on_state_changed = self.on_audio_state_changed
        self.audio_player.on_position_changed = self.on_audio_position_changed
        self.audio_player.on_duration_changed = self.on_audio_duration_changed
        self.audio_player.on_error_occurred = self.on_audio_error
        
        # Timer pour mise à jour position
        self.position_timer = None
        
        # Configuration de la fenêtre - PLEIN ÉCRAN comme spécifié
        self.set_default_size(1200, 800)
        self.maximize()  # Plein écran par défaut
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Conteneur principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)
        
        # Conteneur haut pour les blocs 1 et 2 (côte à côte)
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.pack_start(top_box, False, False, 0)
        
        # BLOC 1 : Pochette + bouton (haut gauche)
        self._create_cover_block(top_box)
        
        # BLOC 2 : Champs de saisie (haut droite)
        self._create_fields_block(top_box)
        
        # BLOC 3 : Tableau des métadonnées (toute la largeur)
        self._create_metadata_table_block(main_box)
        
        # BLOC 4 : Lecteur audio (toute la largeur)
        self._create_audio_player_block(main_box)
        
        # Charger les données
        self._load_album_data()
    
    def _create_cover_block(self, parent_box):
        """BLOC 1 : Pochette 250×250 + bouton 'Chercher une pochette'"""
        frame = Gtk.Frame(label="🖼️ Pochette d'album")
        frame.set_size_request(300, 320)
        parent_box.pack_start(frame, False, False, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Image de la pochette 250×250
        self.cover_image = Gtk.Image()
        self.cover_image.set_size_request(250, 250)
        self.cover_image.set_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
        vbox.pack_start(self.cover_image, False, False, 0)
        
        # Bouton "Chercher une pochette"
        search_cover_btn = Gtk.Button("🔍 Chercher une pochette")
        search_cover_btn.connect("clicked", self.on_search_cover)
        vbox.pack_start(search_cover_btn, False, False, 0)
    
    def _create_fields_block(self, parent_box):
        """BLOC 2 : 4 champs de saisie (Album, Artiste, Année, Genre)"""
        frame = Gtk.Frame(label="📝 Informations générales")
        parent_box.pack_start(frame, True, True, 0)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(15)
        grid.set_column_spacing(15)
        grid.set_margin_left(20)
        grid.set_margin_right(20)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        frame.add(grid)
        
        # Album
        grid.attach(Gtk.Label("💿 Album:"), 0, 0, 1, 1)
        self.album_entry = Gtk.Entry()
        self.album_entry.set_placeholder_text("Nom de l'album")
        self.album_entry.connect("changed", self.on_album_changed)
        grid.attach(self.album_entry, 1, 0, 1, 1)
        
        # Artiste
        grid.attach(Gtk.Label("🎤 Artiste:"), 0, 1, 1, 1)
        self.artist_entry = Gtk.Entry()
        self.artist_entry.set_placeholder_text("Nom de l'artiste")
        self.artist_entry.connect("changed", self.on_artist_changed)
        grid.attach(self.artist_entry, 1, 1, 1, 1)
        
        # Année
        grid.attach(Gtk.Label("📅 Année:"), 0, 2, 1, 1)
        self.year_entry = Gtk.Entry()
        self.year_entry.set_placeholder_text("YYYY")
        self.year_entry.connect("changed", self.on_year_changed)
        grid.attach(self.year_entry, 1, 2, 1, 1)
        
        # Genre (menu déroulant)
        grid.attach(Gtk.Label("🎼 Genre:"), 0, 3, 1, 1)
        self.genre_combo = Gtk.ComboBoxText()
        genres = [
            "Acid Jazz", "B.O. de Films", "Blues", "Chansons Française", "Disco",
            "Electronique", "Flamenco", "Folk", "Funk", "Jazz", "Musique Afriquaine",
            "Musique Andine", "Musique Brésilienne", "Musique Classique", "Musique Cubaine",
            "Musique Franco-Hispanique", "New-Wave", "Pop", "Rap", "Reggae", "Rock",
            "Soul", "Top 50", "Trip-Hop", "Zouk"
        ]
        for genre in genres:
            self.genre_combo.append_text(genre)
        self.genre_combo.connect("changed", self.on_genre_changed)
        grid.attach(self.genre_combo, 1, 3, 1, 1)
    
    def _create_metadata_table_block(self, parent_box):
        """BLOC 3 : Tableau des métadonnées (9 colonnes)"""
        frame = Gtk.Frame(label="📊 Métadonnées des pistes")
        parent_box.pack_start(frame, True, True, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Scrolled window pour le tableau
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        vbox.pack_start(scrolled, True, True, 0)
        
        # TreeStore : Cover, Nom fichier, Titre, Interprète, Artiste, Album, Année, N°piste, Genre
        self.metadata_store = Gtk.ListStore(str, str, str, str, str, str, str, str, str, str)  # +1 pour le path
        self.metadata_view = Gtk.TreeView(model=self.metadata_store)
        
        # Colonnes du tableau selon cahier des charges
        columns_config = [
            ("✓", 0, 40, False),      # Cover (coche/croix)
            ("Fichier", 1, 200, False),   # Nom de fichier
            ("Titre", 2, 250, True),      # Titre (éditable)
            ("Interprète", 3, 150, False), # Interprète
            ("Artiste", 4, 150, False),   # Artiste
            ("Album", 5, 200, False),     # Album
            ("Année", 6, 80, True),       # Année (triable)
            ("N°", 7, 50, True),          # N° de piste (triable)
            ("Genre", 8, 120, False),     # Genre
        ]
        
        for title, col_id, width, sortable in columns_config:
            renderer = Gtk.CellRendererText()
            if col_id == 2:  # Titre éditable
                renderer.set_property("editable", True)
                renderer.connect("edited", self.on_title_edited)
            
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            if sortable:
                column.set_sort_column_id(col_id)
            self.metadata_view.append_column(column)
        
        # Double-clic sur nom de fichier = lecture
        self.metadata_view.connect("row-activated", self.on_row_activated)
        
        scrolled.add(self.metadata_view)
    
    def _create_audio_player_block(self, parent_box):
        """BLOC 4 : Lecteur audio (contrôles + progressbar + égaliseur)"""
        frame = Gtk.Frame(label="🎵 Lecteur audio")
        parent_box.pack_start(frame, False, False, 0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        hbox.set_margin_left(20)
        hbox.set_margin_right(20)
        hbox.set_margin_top(15)
        hbox.set_margin_bottom(15)
        frame.add(hbox)
        
        # Gauche : Contrôles audio
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.play_btn = Gtk.Button("▶️")
        self.play_btn.connect("clicked", self.on_play)
        controls_box.pack_start(self.play_btn, False, False, 0)
        
        self.prev_btn = Gtk.Button("⏮️")
        self.prev_btn.connect("clicked", self.on_previous)
        controls_box.pack_start(self.prev_btn, False, False, 0)
        
        self.next_btn = Gtk.Button("⏭️")
        self.next_btn.connect("clicked", self.on_next)
        controls_box.pack_start(self.next_btn, False, False, 0)
        
        self.stop_btn = Gtk.Button("⏹️")
        self.stop_btn.connect("clicked", self.on_stop)
        controls_box.pack_start(self.stop_btn, False, False, 0)
        
        hbox.pack_start(controls_box, False, False, 0)
        
        # Centre : Progressbar avec temps
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.time_start_label = Gtk.Label("00:00")
        self.time_end_label = Gtk.Label("00:00")
        time_box.pack_start(self.time_start_label, False, False, 0)
        time_box.pack_end(self.time_end_label, False, False, 0)
        
        self.progress_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.progress_scale.set_draw_value(False)
        self.progress_scale.connect("change-value", self.on_seek)
        
        progress_box.pack_start(time_box, False, False, 0)
        progress_box.pack_start(self.progress_scale, False, False, 0)
        
        hbox.pack_start(progress_box, True, True, 0)
        
        # Droite : Égaliseur
        eq_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        eq_label = Gtk.Label("🎚️ EQ:")
        self.eq_combo = Gtk.ComboBoxText()
        eq_presets = ["Désactivé", "Rock", "Pop", "Jazz", "Classique", "Électronique", "Hip-Hop", "R&B", "Country", "Reggae"]
        for preset in eq_presets:
            self.eq_combo.append_text(preset)
        self.eq_combo.set_active(0)
        
        eq_box.pack_start(eq_label, False, False, 0)
        eq_box.pack_start(self.eq_combo, False, False, 0)
        
        hbox.pack_start(eq_box, False, False, 0)
    
    def _load_album_data(self):
        """Charge les données de l'album dans l'interface"""
        # Champs généraux
        self.artist_entry.set_text(self.album_data.get('artist', ''))
        self.album_entry.set_text(self.album_data.get('album', ''))
        self.year_entry.set_text(str(self.album_data.get('year', '')))
        
        # Genre
        genre = self.album_data.get('genre', '')
        if genre:
            for i, text in enumerate([self.genre_combo.get_model()[j][0] for j in range(len(self.genre_combo.get_model()))]):
                if text == genre:
                    self.genre_combo.set_active(i)
                    break
        
        # Charger les pistes dans le tableau
        # ✅ FIX: Le scanner utilise 'folder_path', pas 'path'
        folder_path = self.album_data.get('folder_path') or self.album_data.get('path', '')
        if folder_path and os.path.exists(folder_path):
            self._load_tracks_to_table(folder_path)
    
    def _load_tracks_to_table(self, folder_path):
        """Charge les pistes dans le tableau des métadonnées"""
        if not folder_path or not os.path.exists(folder_path):
            print(f"❌ Chemin album invalide: {folder_path}")
            return
            
        # Si c'est un fichier, prendre le dossier parent
        if os.path.isfile(folder_path):
            folder_path = os.path.dirname(folder_path)
            
        audio_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg')):
                audio_files.append(os.path.join(folder_path, file))
        
        if not audio_files:
            print(f"⚠️ Aucun fichier audio trouvé dans: {folder_path}")
            return
            
        audio_files.sort()
        
        for file_path in audio_files:
            try:
                metadata = self._extract_track_metadata(file_path)
                
                # Vérifier si pochette associée
                has_cover = "✅" if self._has_embedded_cover(file_path) else "❌"
                
                # Formatage nom fichier SANS extension pour affichage
                display_filename = os.path.splitext(os.path.basename(file_path))[0]
                
                # Formatage numéro piste avec zéro initial pour affichage
                track_num = metadata.get('track', '')
                if track_num and '/' in str(track_num):
                    track_num = str(track_num).split('/')[0]
                if track_num and str(track_num).isdigit() and len(str(track_num)) == 1:
                    track_num = f"0{track_num}"
                
                self.metadata_store.append([
                    has_cover,                                    # Cover
                    display_filename,                            # Nom fichier SANS extension
                    metadata.get('title', ''),                  # Titre
                    metadata.get('performer', ''),              # Interprète
                    metadata.get('artist', ''),                 # Artiste
                    metadata.get('album', ''),                  # Album
                    str(metadata.get('year', '')),              # Année
                    str(track_num),                             # N° piste AVEC zéro initial
                    metadata.get('genre', ''),                  # Genre
                    file_path                                    # Path (caché)
                ])
                
            except Exception as e:
                print(f"Erreur lecture {file_path}: {e}")
    
    def _extract_track_metadata(self, file_path):
        """Extrait les métadonnées d'une piste"""
        metadata = {}
        
        try:
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path, ID3=ID3)
                if audio.tags:
                    metadata['title'] = str(audio.tags.get('TIT2', '')) if audio.tags.get('TIT2') else ''
                    metadata['artist'] = str(audio.tags.get('TPE1', '')) if audio.tags.get('TPE1') else ''
                    metadata['performer'] = str(audio.tags.get('TPE1', '')) if audio.tags.get('TPE1') else ''  # Copie artiste vers interprète
                    metadata['album'] = str(audio.tags.get('TALB', '')) if audio.tags.get('TALB') else ''
                    metadata['year'] = str(audio.tags.get('TDRC', '')) if audio.tags.get('TDRC') else ''
                    metadata['genre'] = str(audio.tags.get('TCON', '')) if audio.tags.get('TCON') else ''
                    metadata['track'] = str(audio.tags.get('TRCK', '')) if audio.tags.get('TRCK') else ''
                    
        except Exception as e:
            print(f"Erreur extraction métadonnées {file_path}: {e}")
            metadata = {
                'title': os.path.splitext(os.path.basename(file_path))[0],
                'artist': '', 'performer': '', 'album': '',
                'year': '', 'genre': '', 'track': ''
            }
        
        return metadata
    
    def _has_embedded_cover(self, file_path):
        """Vérifie si une pochette est intégrée dans le fichier"""
        try:
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path, ID3=ID3)
                return audio.tags and 'APIC:' in audio.tags
        except:
            pass
        return False
    
    # === CALLBACKS CHAMPS DE SAISIE ===
    def on_album_changed(self, entry):
        """Mise à jour en temps réel de la colonne Album"""
        new_album = entry.get_text()
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 5, new_album)  # Colonne Album
            iter = self.metadata_store.iter_next(iter)
    
    def on_artist_changed(self, entry):
        """Mise à jour en temps réel des colonnes Artiste et Interprète"""
        new_artist = entry.get_text()
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 3, new_artist)  # Interprète
            self.metadata_store.set_value(iter, 4, new_artist)  # Artiste
            iter = self.metadata_store.iter_next(iter)
    
    def on_year_changed(self, entry):
        """Mise à jour en temps réel de la colonne Année"""
        new_year = entry.get_text()
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 6, new_year)  # Colonne Année
            iter = self.metadata_store.iter_next(iter)
    
    def on_genre_changed(self, combo):
        """Mise à jour en temps réel de la colonne Genre"""
        new_genre = combo.get_active_text() or ""
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 8, new_genre)  # Colonne Genre
            iter = self.metadata_store.iter_next(iter)
    
    # === CALLBACKS TABLEAU ===
    def on_title_edited(self, renderer, path, new_text):
        """Édition du titre d'une piste"""
        iter = self.metadata_store.get_iter(path)
        self.metadata_store.set_value(iter, 2, new_text)  # Colonne Titre
    
    def on_row_activated(self, treeview, path, column):
        """Double-clic sur une ligne = lecture du fichier"""
        iter = self.metadata_store.get_iter(path)
        file_path = self.metadata_store.get_value(iter, 9)  # Path caché
        if column.get_title() == "Fichier":  # Double-clic sur nom fichier
            self._play_audio_file(file_path)
    
    # === CALLBACKS LECTEUR AUDIO ===
    def on_play(self, button):
        """Bouton play/pause"""
        if self.audio_player.is_playing():
            self.audio_player.pause()
        elif self.audio_player.is_paused():
            self.audio_player.play()
        else:
            # Jouer le premier fichier ou celui sélectionné
            self._play_current_track()
    
    def on_previous(self, button):
        """Piste précédente"""
        if self.current_track_index > 0:
            self.current_track_index -= 1
            self._play_current_track()
    
    def on_next(self, button):
        """Piste suivante"""
        if self.current_track_index < len(self.tracks) - 1:
            self.current_track_index += 1
            self._play_current_track()
    
    def on_stop(self, button):
        """Arrêter la lecture"""
        self.audio_player.stop()
        if self.position_timer:
            GLib.source_remove(self.position_timer)
            self.position_timer = None
    
    def on_seek(self, scale, scroll_type, value):
        """Seek dans la piste"""
        if self.audio_player.get_duration() > 0:
            position = (value / 100.0) * self.audio_player.get_duration()
            self.audio_player.seek(position)
    
    def _play_audio_file(self, file_path):
        """Lance la lecture d'un fichier audio"""
        try:
            # Trouver l'index du fichier
            for i, track in enumerate(self.tracks):
                if track.get('file_path') == file_path:
                    self.current_track_index = i
                    break
            
            self._play_current_track()
            
        except Exception as e:
            print(f"Erreur lecture: {e}")
    
    def _play_current_track(self):
        """Joue la piste actuelle"""
        if not self.tracks or self.current_track_index >= len(self.tracks):
            return
        
        track = self.tracks[self.current_track_index]
        file_path = track.get('file_path')
        
        if file_path and os.path.exists(file_path):
            if self.audio_player.load_file(file_path):
                self.audio_player.play()
                self._start_position_timer()
            else:
                print(f"Erreur chargement: {file_path}")
    
    def _start_position_timer(self):
        """Démarre le timer de mise à jour de position"""
        if self.position_timer:
            GLib.source_remove(self.position_timer)
        
        self.position_timer = GLib.timeout_add(100, self._update_position)
    
    def _update_position(self):
        """Met à jour la position du lecteur"""
        if not self.audio_player.is_playing():
            return False
        
        position = self.audio_player.get_position()
        duration = self.audio_player.get_duration()
        
        if duration > 0:
            percentage = (position / duration) * 100
            self.progress_scale.set_value(percentage)
            
            # Mise à jour des labels de temps
            self.time_start_label.set_text(self._format_time(position))
            self.time_end_label.set_text(self._format_time(duration))
        
        return True
    
    def _format_time(self, seconds):
        """Formate le temps en mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def on_audio_state_changed(self, state):
        """Callback changement d'état audio"""
        if state == PlayerState.PLAYING:
            self.play_btn.set_label("⏸️")
        else:
            self.play_btn.set_label("▶️")
    
    def on_audio_position_changed(self, position):
        """Callback changement de position"""
        pass  # Géré par le timer
    
    def on_audio_duration_changed(self, duration):
        """Callback changement de durée"""
        self.time_end_label.set_text(self._format_time(duration))
    
    def on_audio_error(self, error_message):
        """Callback erreur audio"""
        print(f"Erreur audio: {error_message}")
        
        # Afficher un dialog d'erreur
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Erreur de lecture audio"
        )
        dialog.format_secondary_text(error_message)
        dialog.run()
        dialog.destroy()
    
    # === CALLBACKS POCHETTE ===
    def on_search_cover(self, button):
        """Ouvre la fenêtre de recherche de pochette internet"""
        artist = self.artist_entry.get_text().strip()
        album = self.album_entry.get_text().strip()
        year = self.year_entry.get_text().strip()
        
        if not artist or not album:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Informations manquantes"
            )
            dialog.format_secondary_text("Veuillez renseigner l'artiste et l'album avant de rechercher une pochette.")
            dialog.run()
            dialog.destroy()
            return
        
        # Ouvrir la fenêtre de recherche de pochettes
        self._open_cover_search_dialog(artist, album, year)
    
    def _open_cover_search_dialog(self, artist, album, year):
        """Ouvre le dialog de recherche de pochettes"""
        dialog = Gtk.Dialog(
            title="🔍 Recherche de pochettes",
            transient_for=self,
            flags=0
        )
        dialog.set_default_size(600, 400)
        
        # Boutons
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Utiliser", Gtk.ResponseType.OK)
        
        # Contenu
        content_area = dialog.get_content_area()
        
        # Label de recherche
        search_label = Gtk.Label(f"Recherche pour: {artist} - {album}")
        search_label.set_margin_top(10)
        content_area.pack_start(search_label, False, False, 0)
        
        # Zone de chargement/résultats
        spinner = Gtk.Spinner()
        spinner.set_size_request(50, 50)
        spinner.start()
        content_area.pack_start(spinner, True, True, 0)
        
        loading_label = Gtk.Label("Recherche en cours...")
        content_area.pack_start(loading_label, False, False, 0)
        
        dialog.show_all()
        
        # Lancer la recherche en arrière-plan
        def search_covers():
            try:
                results = self.cover_search.search_covers(artist, album, year)
                GLib.idle_add(lambda: self._display_cover_results(dialog, content_area, results, spinner, loading_label))
            except Exception as e:
                GLib.idle_add(lambda: self._display_cover_error(dialog, content_area, str(e), spinner, loading_label))
        
        import threading
        thread = threading.Thread(target=search_covers)
        thread.daemon = True
        thread.start()
        
        # Attendre la réponse
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # TODO: Implémenter la sélection de pochette
            pass
        
        dialog.destroy()
    
    def _display_cover_results(self, dialog, content_area, results, spinner, loading_label):
        """Affiche les résultats de recherche de pochettes"""
        # Supprimer le spinner
        content_area.remove(spinner)
        content_area.remove(loading_label)
        
        if not results:
            no_results_label = Gtk.Label("Aucune pochette trouvée")
            content_area.pack_start(no_results_label, True, True, 0)
        else:
            results_label = Gtk.Label(f"{len(results)} pochettes trouvées:")
            content_area.pack_start(results_label, False, False, 0)
            
            # Scrolled window pour les résultats
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            content_area.pack_start(scrolled, True, True, 0)
            
            # Grille de pochettes (pour plus tard)
            results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            for i, result in enumerate(results[:5]):  # Limiter à 5 résultats
                result_label = Gtk.Label(f"{i+1}. {result.source} - {result.url[:50]}...")
                results_box.pack_start(result_label, False, False, 0)
            
            scrolled.add(results_box)
        
        dialog.show_all()
    
    def _display_cover_error(self, dialog, content_area, error_msg, spinner, loading_label):
        """Affiche une erreur de recherche"""
        content_area.remove(spinner)
        content_area.remove(loading_label)
        
        error_label = Gtk.Label(f"Erreur de recherche: {error_msg}")
        content_area.pack_start(error_label, True, True, 0)
        dialog.show_all()
    
    def on_startup_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre"""
        print("👋 Fermeture de la fenêtre d'édition")
        
        # Nettoyer le lecteur audio
        if hasattr(self, 'audio_player'):
            self.audio_player.cleanup()
        
        # Arrêter le timer
        if hasattr(self, 'position_timer') and self.position_timer:
            GLib.source_remove(self.position_timer)
        
        return False
