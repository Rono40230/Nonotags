"""
Application Nonotags simple avec GTK3
Interface moderne adaptée pour la compatibilité GTK3
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf, Pango, GLib
import os
from typing import List, Dict
from services.music_scanner import MusicScanner

class AlbumCard(Gtk.Frame):
    """Widget représentant une carte d'album"""
    
    def __init__(self, album_data: Dict):
        super().__init__()
        self.album_data = album_data
        self.set_shadow_type(Gtk.ShadowType.OUT)
        self.get_style_context().add_class("album-card")
        
        # Taille fixe stricte pour empêcher le redimensionnement
        self.set_size_request(290, 450)
        self.set_property("width-request", 290)
        self.set_property("height-request", 450)
        
        # Container principal avec taille contrôlée
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        # Case de sélection en haut à droite
        selection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        selection_box.set_halign(Gtk.Align.END)
        
        self.selection_checkbox = Gtk.CheckButton()
        self.selection_checkbox.set_halign(Gtk.Align.END)
        self.selection_checkbox.connect("toggled", self.on_selection_toggled)
        selection_box.pack_end(self.selection_checkbox, False, False, 0)
        
        vbox.pack_start(selection_box, False, False, 0)
        
        # Pochette d'album (placeholder coloré)
        cover_frame = Gtk.Frame()
        cover_frame.set_size_request(250, 250)
        cover_frame.set_halign(Gtk.Align.CENTER)
        
        # Placeholder coloré avec emoji
        cover_label = Gtk.Label()
        cover_label.set_markup(f'<span font="48">{album_data.get("emoji", "🎵")}</span>')
        cover_label.get_style_context().add_class(f"cover-{album_data.get('color', 'blue')}")
        cover_frame.add(cover_label)
        
        vbox.pack_start(cover_frame, False, False, 0)
        
        # Informations de l'album (centrées)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_halign(Gtk.Align.CENTER)
        
        # Ligne 1 : Artiste (en gras)
        artist_label = Gtk.Label()
        artist_label.set_markup(f'<b>{album_data.get("artist", "Artiste Inconnu")}</b>')
        artist_label.set_halign(Gtk.Align.CENTER)
        artist_label.set_justify(Gtk.Justification.CENTER)
        artist_label.set_ellipsize(Pango.EllipsizeMode.END)
        artist_label.set_max_width_chars(25)
        info_box.pack_start(artist_label, False, False, 0)
        
        # Ligne 2 : Année et titre de l'album
        year_title_text = f"{album_data.get('year', '----')} - {album_data.get('album', 'Album Sans Titre')}"
        year_title_label = Gtk.Label()
        year_title_label.set_text(year_title_text)
        year_title_label.set_halign(Gtk.Align.CENTER)
        year_title_label.set_justify(Gtk.Justification.CENTER)
        year_title_label.get_style_context().add_class("subtitle-label")
        year_title_label.set_ellipsize(Pango.EllipsizeMode.END)
        year_title_label.set_max_width_chars(25)
        info_box.pack_start(year_title_label, False, False, 0)
        
        # Ligne 3 : Genre
        genre_label = Gtk.Label()
        genre_label.set_text(album_data.get("genre", "Genre inconnu"))
        genre_label.set_halign(Gtk.Align.CENTER)
        genre_label.set_justify(Gtk.Justification.CENTER)
        genre_label.get_style_context().add_class("subtitle-label")
        genre_label.set_ellipsize(Pango.EllipsizeMode.END)
        genre_label.set_max_width_chars(25)
        info_box.pack_start(genre_label, False, False, 0)
        
        # Ligne 4 : Nombre de pistes
        tracks_text = f"{album_data.get('tracks', 0)} pistes"
        tracks_label = Gtk.Label()
        tracks_label.set_text(tracks_text)
        tracks_label.set_halign(Gtk.Align.CENTER)
        tracks_label.set_justify(Gtk.Justification.CENTER)
        tracks_label.get_style_context().add_class("subtitle-label")
        tracks_label.set_ellipsize(Pango.EllipsizeMode.END)
        tracks_label.set_max_width_chars(25)
        info_box.pack_start(tracks_label, False, False, 0)
        
        vbox.pack_start(info_box, False, False, 0)
        
        # Boutons d'action (verticaux, centrés, hauteur réduite)
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(8)
        
        edit_btn = Gtk.Button.new_with_label("✏️ Éditer")
        edit_btn.get_style_context().add_class("modern-button")
        edit_btn.set_size_request(180, 32)
        edit_btn.connect("clicked", self.on_edit_clicked)
        button_box.pack_start(edit_btn, False, False, 0)
        
        playlist_btn = Gtk.Button.new_with_label("📋 Créer la playlist")
        playlist_btn.set_size_request(180, 32)
        playlist_btn.connect("clicked", self.on_playlist_clicked)
        button_box.pack_start(playlist_btn, False, False, 0)
        
        remove_btn = Gtk.Button.new_with_label("🗑️ Retirer de la liste")
        remove_btn.set_size_request(180, 32)
        remove_btn.connect("clicked", self.on_remove_clicked)
        button_box.pack_start(remove_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        self.add(vbox)
    
    def on_edit_clicked(self, button):
        """Ouvre la fenêtre d'édition"""
        print(f"✏️ Édition de l'album: {self.album_data.get('album')}")
        edit_window = AlbumEditWindow(self.album_data, self)
        edit_window.show_all()
    
    def on_playlist_clicked(self, button):
        """Crée une playlist avec cet album"""
        print(f"📋 Création de playlist: {self.album_data.get('album')}")
    
    def on_remove_clicked(self, button):
        """Retire cet album de la liste"""
        print(f"🗑️ Retrait de l'album: {self.album_data.get('album')}")
    
    def _update_display(self):
        """Met à jour l'affichage de la carte après édition"""
        # Récupérer les nouveaux labels
        for child in self.get_children():
            if isinstance(child, Gtk.Box):
                for subchild in child.get_children():
                    if isinstance(subchild, Gtk.Label):
                        # Reconstruit le texte des labels avec les nouvelles données
                        if "🎤" in subchild.get_text():  # Label artiste
                            subchild.set_markup(f"<b>🎤 {self.album_data.get('artist', 'Artiste inconnu')}</b>")
                        elif "📅" in subchild.get_text():  # Label année-titre
                            year = self.album_data.get('year', '')
                            album = self.album_data.get('album', 'Album inconnu')
                            year_text = f"{year} - " if year else ""
                            subchild.set_markup(f"<b>📅 {year_text}{album}</b>")
                        elif "🎼" in subchild.get_text():  # Label genre
                            subchild.set_markup(f"🎼 {self.album_data.get('genre', 'Genre inconnu')}")
                        elif "🎵" in subchild.get_text():  # Label pistes
                            tracks = self.album_data.get('tracks', 0)
                            piste_text = "piste" if tracks <= 1 else "pistes"
                            subchild.set_markup(f"🎵 {tracks} {piste_text}")
                break
    
    def on_selection_toggled(self, checkbox):
        """Gère la sélection/déselection de l'album"""
        is_selected = checkbox.get_active()
        album_title = self.album_data.get('album', 'Album Sans Titre')
        if is_selected:
            print(f"✅ Album sélectionné: {album_title}")
        else:
            print(f"❌ Album désélectionné: {album_title}")

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC


class AlbumEditWindow(Gtk.Window):
    """Fenêtre d'édition conforme au cahier des charges - 4 blocs"""
    
    def __init__(self, album_data, parent_card):
        super().__init__(title="🎵 Édition d'album")
        self.album_data = album_data
        self.parent_card = parent_card
        self.tracks = []
        
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
        
        play_btn = Gtk.Button("▶️")
        play_btn.connect("clicked", self.on_play)
        controls_box.pack_start(play_btn, False, False, 0)
        
        prev_btn = Gtk.Button("⏮️")
        prev_btn.connect("clicked", self.on_previous)
        controls_box.pack_start(prev_btn, False, False, 0)
        
        next_btn = Gtk.Button("⏭️")
        next_btn.connect("clicked", self.on_next)
        controls_box.pack_start(next_btn, False, False, 0)
        
        stop_btn = Gtk.Button("⏹️")
        stop_btn.connect("clicked", self.on_stop)
        controls_box.pack_start(stop_btn, False, False, 0)
        
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
        folder_path = self.album_data.get('path', '')
        if folder_path and os.path.exists(folder_path):
            self._load_tracks_to_table(folder_path)
    
    def _load_tracks_to_table(self, folder_path):
        """Charge les pistes dans le tableau des métadonnées"""
        audio_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg')):
                audio_files.append(os.path.join(folder_path, file))
        
        audio_files.sort()
        
        for file_path in audio_files:
            try:
                metadata = self._extract_track_metadata(file_path)
                
                # Vérifier si pochette associée
                has_cover = "✅" if self._has_embedded_cover(file_path) else "❌"
                
                self.metadata_store.append([
                    has_cover,                                    # Cover
                    os.path.basename(file_path),                 # Nom fichier
                    metadata.get('title', ''),                  # Titre
                    metadata.get('performer', ''),              # Interprète
                    metadata.get('artist', ''),                 # Artiste
                    metadata.get('album', ''),                  # Album
                    str(metadata.get('year', '')),              # Année
                    str(metadata.get('track', '')),             # N° piste
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
        print("▶️ Lecture")
    
    def on_previous(self, button):
        print("⏮️ Précédent")
    
    def on_next(self, button):
        print("⏭️ Suivant")
    
    def on_stop(self, button):
        print("⏹️ Stop")
    
    def on_seek(self, scale, scroll_type, value):
        print(f"🎯 Seek: {value}%")
    
    def _play_audio_file(self, file_path):
        """Lance la lecture d'un fichier audio"""
        print(f"🎵 Lecture: {os.path.basename(file_path)}")
        # TODO: Implémenter la lecture audio réelle
    
    # === CALLBACKS POCHETTE ===
    def on_search_cover(self, button):
        """Ouvre la fenêtre de recherche de pochette internet"""
        print("🔍 Recherche de pochette sur internet")
        # TODO: Implémenter la recherche de pochette


class NonotagsApp(Gtk.Window):
    """Application Nonotags simple avec interface moderne"""
    
    def __init__(self):
        self.window = None
        self.albums_grid = None
        self._resize_timeout_id = None
        
    def create_window(self):
        """Crée la fenêtre principale"""
        self.window = Gtk.Window()
        self.window.set_title("🎵 Nonotags - Gestionnaire de Tags MP3")
        self.window.set_default_size(1200, 800)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("check-resize", self.on_window_resize)
        
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
        
        # Ajouter quelques albums de démonstration au démarrage
        self._add_demo_albums()
        
        main_box.pack_start(self.albums_grid, True, True, 0)
        
        scrolled.add(main_box)
        self.window.add(scrolled)
    
    def _add_demo_albums(self):
        """Ajoute quelques albums de démonstration"""
        demo_albums = [
            {
                "album": "The Dark Side of the Moon",
                "artist": "Pink Floyd",
                "year": "1973",
                "genre": "Progressive Rock",
                "tracks": 10,
                "emoji": "🌙",
                "color": "purple"
            },
            {
                "album": "Abbey Road",
                "artist": "The Beatles",
                "year": "1969",
                "genre": "Rock",
                "tracks": 17,
                "emoji": "🎸",
                "color": "blue"
            },
            {
                "album": "Thriller",
                "artist": "Michael Jackson",
                "year": "1982",
                "genre": "Pop",
                "tracks": 9,
                "emoji": "🎤",
                "color": "red"
            }
        ]
        
        for album_data in demo_albums:
            card = AlbumCard(album_data)
            self.albums_grid.add(card)
    
    def on_scan_clicked(self, button):
        """Gestion du scan de dossiers"""
        dialog = Gtk.FileChooserDialog(
            title="Choisir le dossier à scanner",
            parent=self.window,
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
            parent=self.window,
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
            scanner = MusicScanner()
            albums = scanner.scan_directory(folder_path, progress_callback)
            progress_dialog.destroy()
            self._update_albums_display(albums)
            
            success_dialog = Gtk.MessageDialog(
                parent=self.window,
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
                parent=self.window,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Erreur lors du scan"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
    
    def _update_albums_display(self, albums: List[Dict]):
        """Met à jour l'affichage avec les vrais albums scannés"""
        if albums:
            for child in self.albums_grid.get_children():
                self.albums_grid.remove(child)
            
            for album_data in albums:
                card = AlbumCard(album_data)
                self.albums_grid.add(card)
        
        self.albums_grid.show_all()
        self.update_cards_per_line()

    def on_import_clicked(self, button):
        """Gestion de l'import de fichiers"""
        print("📂 Import de fichiers - Fonctionnalité à implémenter")
    
    def on_edit_selection_clicked(self, button):
        """Ouvre l'édition groupée pour les albums sélectionnés"""
        selected_albums = []
        for child in self.albums_grid.get_children():
            if hasattr(child, 'selection_checkbox') and child.selection_checkbox.get_active():
                selected_albums.append(child.album_data)
        
        if not selected_albums:
            dialog = Gtk.MessageDialog(
                parent=self.window,
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
            if hasattr(self, 'window') and self.window:
                window_width = self.window.get_allocated_width()
            else:
                window_width = 1200
        
        CARD_WIDTH = 290
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
        
        if hasattr(self, 'window') and self.window:
            width = self.window.get_allocated_width()
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
    
    def run(self):
        """Lance l'application"""
        self.create_window()
        self.window.show_all()
        
        GLib.idle_add(self.update_cards_per_line)
        
        print("✅ Application Nonotags lancée avec succès!")
        print("🎯 Interface responsive avec scan fonctionnel")
        Gtk.main()

if __name__ == "__main__":
    app = NonotagsApp()
    app.run()
