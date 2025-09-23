"""
Fenêtre d'édition d'album
Fenêtre d'édition conforme au cahier des charges avec 4 blocs
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, GdkPixbuf, Pango
import os
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from services.audio_player import AudioPlayer, PlayerState
from services.cover_search import CoverSearchService
from core.case_corrector import CaseCorrector
# from services.metadata_event_manager import metadata_event_manager  # DÉSACTIVÉ - Remplacé par RefreshManager
from core.refresh_manager import refresh_manager

class AlbumEditWindow(Gtk.Window):
    """Fenêtre d'édition conforme au cahier des charges - 4 blocs"""
    
    def __init__(self, album_data, parent_card):
        super().__init__(title="🎵 Édition d'albums")
        
        # Gérer les cas : un seul album ou liste d'albums
        if isinstance(album_data, list):
            self.selected_albums = album_data
            self.album_data = album_data[0] if album_data else {}  # Premier album pour compatibilité
            print(f"🎵 Fenêtre d'édition ouverte pour {len(album_data)} albums")
        else:
            self.selected_albums = [album_data]
            self.album_data = album_data
            print(f"🎵 Fenêtre d'édition ouverte pour 1 album")
        
        self.parent_card = parent_card
        self.tracks = []
        
        # Services
        self.audio_player = AudioPlayer()
        self.cover_search = CoverSearchService()
        self.case_corrector = CaseCorrector()
        self.current_track_index = 0
        
        # Callbacks du lecteur audio
        self.audio_player.on_state_changed = self.on_audio_state_changed
        self.audio_player.on_position_changed = self.on_audio_position_changed
        self.audio_player.on_duration_changed = self.on_audio_duration_changed
        self.audio_player.on_error_occurred = self.on_audio_error
        
        # Timer pour mise à jour position
        self.position_timer = None
        
        # Timer pour sauvegarde automatique des métadonnées (debounce)
        self.metadata_save_timer = None
        
        # Configuration de la fenêtre - PLEIN ÉCRAN comme spécifié
        self.set_default_size(1200, 800)
        self.maximize()  # Plein écran par défaut
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Signal de fermeture pour rafraîchir la carte parente
        self.connect("delete-event", self.on_window_closing)
        
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
        
        # Charger la vraie pochette si elle existe
        self._load_album_cover()
        
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
        
        # Changement de sélection = mise à jour de la pochette
        selection = self.metadata_view.get_selection()
        selection.connect("changed", self.on_selection_changed)
        
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
        
        # Charger les pistes de tous les albums sélectionnés dans le tableau
        self._load_all_selected_albums_tracks()
    
    def _load_all_selected_albums_tracks(self):
        """Charge les pistes de tous les albums sélectionnés dans le tableau"""
        print(f"📋 Chargement des pistes pour {len(self.selected_albums)} albums...")
        
        for album_data in self.selected_albums:
            folder_path = album_data.get('folder_path') or album_data.get('path', '')
            if folder_path and os.path.exists(folder_path):
                self._load_tracks_to_table(folder_path, album_data)
    
    def _load_tracks_to_table(self, folder_path, album_data=None):
        """Charge les pistes dans le tableau des métadonnées"""
        if not folder_path or not os.path.exists(folder_path):
            print(f"❌ Chemin album invalide: {folder_path}")
            return
            
        # Si c'est un fichier, prendre le dossier parent
        if os.path.isfile(folder_path):
            folder_path = os.path.dirname(folder_path)
        
        # Utiliser album_data si fourni, sinon self.album_data
        current_album = album_data or self.album_data
        album_title = current_album.get('album', 'Album Inconnu')  # ✅ FIX: 'album' au lieu de 'title'
        album_artist = current_album.get('artist', 'Artiste Inconnu')
        
        # ✅ FIX: Réinitialiser self.tracks pour le premier album seulement
        if not hasattr(self, '_tracks_initialized'):
            self.tracks = []
            self.current_track_index = 0
            self._tracks_initialized = True
            
        audio_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg')):
                audio_files.append(os.path.join(folder_path, file))
        
        if not audio_files:
            return  # Aucun fichier audio trouvé
            
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
                    album_title,                                 # Album (utilise le titre de l'album sélectionné)
                    str(metadata.get('year', '')),              # Année
                    str(track_num),                             # N° piste AVEC zéro initial
                    metadata.get('genre', ''),                  # Genre
                    file_path                                    # Path (caché)
                ])
                
                # ✅ FIX: Ajouter à self.tracks pour le lecteur audio
                track_data = {
                    'file_path': file_path,
                    'title': metadata.get('title', display_filename),
                    'artist': metadata.get('artist', ''),
                    'album': album_title,
                    'track_num': track_num,
                    'display_filename': display_filename
                }
                self.tracks.append(track_data)
                
            except Exception as e:
                print(f"Erreur lecture {file_path}: {e}")
    
    def _extract_track_metadata(self, file_path):
        """Extrait les métadonnées d'une piste"""
        metadata = {}
        
        try:
            if file_path.lower().endswith('.mp3'):
                # Essayer plusieurs méthodes de lecture MP3
                audio = None
                try:
                    audio = MP3(file_path, ID3=ID3)
                except:
                    try:
                        audio = MP3(file_path)
                    except:
                        # Fichier MP3 corrompu - utiliser valeurs par défaut
                        pass
                
                if audio and audio.tags:
                    metadata['title'] = str(audio.tags.get('TIT2', '')) if audio.tags.get('TIT2') else ''
                    metadata['artist'] = str(audio.tags.get('TPE1', '')) if audio.tags.get('TPE1') else ''
                    metadata['performer'] = str(audio.tags.get('TPE1', '')) if audio.tags.get('TPE1') else ''  # Copie artiste vers interprète
                    metadata['album'] = str(audio.tags.get('TALB', '')) if audio.tags.get('TALB') else ''
                    metadata['year'] = str(audio.tags.get('TDRC', '')) if audio.tags.get('TDRC') else ''
                    metadata['genre'] = str(audio.tags.get('TCON', '')) if audio.tags.get('TCON') else ''
                    metadata['track'] = str(audio.tags.get('TRCK', '')) if audio.tags.get('TRCK') else ''
                    
        except Exception as e:
            print(f"Erreur extraction métadonnées {file_path}: {e}")
            
        # Valeurs par défaut si extraction échoue
        if not metadata:
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
                # Essayer plusieurs méthodes de lecture
                try:
                    audio = MP3(file_path, ID3=ID3)
                except:
                    try:
                        audio = MP3(file_path)
                    except:
                        return False
                
                if audio.tags:
                    # Chercher toutes les tags APIC (Attached Picture)
                    for key in audio.tags.keys():
                        if key.startswith('APIC:'):
                            return True
                return False
                
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                return len(audio.pictures) > 0
                
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                audio = MP4(file_path)
                return 'covr' in audio.tags if audio.tags else False
                
        except Exception as e:
            # Erreur de lecture du fichier - pas de pochette détectable
            pass
            
        return False
    
    def _load_album_cover(self):
        """Charge et affiche la pochette d'album si elle existe"""
        album_path = self.album_data.get('path') or self.album_data.get('folder_path')
        
        if album_path and os.path.exists(album_path):
            cover_path = self._find_cover_file(album_path)
            
            if cover_path and os.path.exists(cover_path):
                try:
                    # Charger et redimensionner l'image à 250x250
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        cover_path, 250, 250, True
                    )
                    self.cover_image.set_from_pixbuf(pixbuf)
                    return
                except Exception as e:
                    print(f"Erreur chargement pochette {cover_path}: {e}")
        
        # Fallback: icône par défaut
        self.cover_image.set_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
    
    def _find_cover_file(self, album_path):
        """Cherche un fichier de pochette dans le dossier d'album"""
        cover_names = [
            'cover.jpg', 'cover.jpeg', 'cover.png',
            'folder.jpg', 'folder.jpeg', 'folder.png',
            'front.jpg', 'front.jpeg', 'front.png',
            'album.jpg', 'album.jpeg', 'album.png'
        ]
        
        for cover_name in cover_names:
            cover_path = os.path.join(album_path, cover_name)
            if os.path.exists(cover_path):
                return cover_path
        
        return None

    # === CALLBACKS CHAMPS DE SAISIE ===
    def on_album_changed(self, entry):
        """Mise à jour en temps réel de la colonne Album"""
        new_album = entry.get_text()
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 5, new_album)  # Colonne Album
            iter = self.metadata_store.iter_next(iter)
        
        # Programmer la sauvegarde automatique
        self._schedule_metadata_save()
    
    def on_artist_changed(self, entry):
        """Mise à jour en temps réel des colonnes Artiste et Interprète"""
        new_artist = entry.get_text()
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 3, new_artist)  # Interprète
            self.metadata_store.set_value(iter, 4, new_artist)  # Artiste
            iter = self.metadata_store.iter_next(iter)
        
        # Programmer la sauvegarde automatique
        self._schedule_metadata_save()
    
    def on_year_changed(self, entry):
        """Mise à jour en temps réel de la colonne Année"""
        new_year = entry.get_text()
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 6, new_year)  # Colonne Année
            iter = self.metadata_store.iter_next(iter)
        
        # Programmer la sauvegarde automatique
        self._schedule_metadata_save()
    
    def on_genre_changed(self, combo):
        """Mise à jour en temps réel de la colonne Genre"""
        new_genre = combo.get_active_text() or ""
        iter = self.metadata_store.get_iter_first()
        while iter:
            self.metadata_store.set_value(iter, 8, new_genre)  # Colonne Genre
            iter = self.metadata_store.iter_next(iter)
        
        # Programmer la sauvegarde automatique
        self._schedule_metadata_save()
    
    # === CALLBACKS TABLEAU ===
    def on_title_edited(self, renderer, path, new_text):
        """Édition du titre d'une piste"""
        iter = self.metadata_store.get_iter(path)
        self.metadata_store.set_value(iter, 2, new_text)  # Colonne Titre
        
        # Sauvegarder le titre dans les métadonnées physiques et renommer le fichier
        file_path = self.metadata_store.get_value(iter, 9)  # Path caché
        track_num = self.metadata_store.get_value(iter, 7)  # N° piste
        if file_path and os.path.exists(file_path):
            new_file_path = self._save_title_to_file(file_path, new_text, track_num)
            if new_file_path and new_file_path != file_path:
                # Mettre à jour le tableau avec le nouveau nom de fichier
                new_filename = os.path.splitext(os.path.basename(new_file_path))[0]
                self.metadata_store.set_value(iter, 1, new_filename)  # Colonne Nom fichier
                self.metadata_store.set_value(iter, 9, new_file_path)  # Path caché
                
                # Mettre à jour self.tracks pour le lecteur audio
                for track in self.tracks:
                    if track.get('file_path') == file_path:
                        track['file_path'] = new_file_path
                        track['title'] = new_text
                        track['display_filename'] = new_filename
                        break
    
    def on_row_activated(self, tree_view, path, column):
        """Double-clic sur une ligne du tableau"""
        iter = self.metadata_store.get_iter(path)
        file_path = self.metadata_store.get_value(iter, 9)  # Path caché
        
        # ✅ FIX: Lancer la lecture directement avec le file_path
        if file_path and os.path.exists(file_path):
            # Trouver l'index dans self.tracks pour synchroniser
            for i, track in enumerate(self.tracks):
                if track.get('file_path') == file_path:
                    self.current_track_index = i
                    break
            
            # Lancer la lecture
            if self.audio_player.load_file(file_path):
                self.audio_player.play()
                self._start_position_timer()
                print(f"🎵 Lecture démarrée: {os.path.basename(file_path)}")
            else:
                print(f"❌ Erreur chargement: {file_path}")
    
    # === CALLBACKS LECTEUR AUDIO ===
    def on_play(self, button):
        """Bouton play/pause"""
        if self.audio_player.is_playing():
            self.audio_player.pause()
            self.play_btn.set_label("▶️")
        elif self.audio_player.is_paused():
            self.audio_player.play()
            self.play_btn.set_label("⏸️")
        else:
            # ✅ FIX: Jouer la première piste si aucune n'est chargée
            if self.tracks:
                if not hasattr(self, 'current_track_index') or self.current_track_index >= len(self.tracks):
                    self.current_track_index = 0
                self._play_current_track()
            else:
                print("❌ Aucune piste disponible")
    
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
            print("❌ Aucune piste à jouer")
            return
        
        track = self.tracks[self.current_track_index]
        file_path = track.get('file_path')
        
        if file_path and os.path.exists(file_path):
            if self.audio_player.load_file(file_path):
                self.audio_player.play()
                print(f"🎵 Lecture: {track.get('display_filename', os.path.basename(file_path))}")
            else:
                print(f"❌ Erreur chargement: {file_path}")
        else:
            print(f"❌ Fichier introuvable: {file_path}")
    
    def _start_position_timer(self):
        """Démarre le timer de mise à jour de la position"""
        if hasattr(self, 'position_timer') and self.position_timer:
            GLib.source_remove(self.position_timer)
        
        # ✅ FIX: Ajouter import GLib si manquant
        from gi.repository import GLib
        self.position_timer = GLib.timeout_add(500, self._update_position)  # Toutes les 500ms
    
    def _update_position(self):
        """Met à jour la position du lecteur"""
        # Vérifier que le lecteur et les widgets existent encore
        if not hasattr(self, 'audio_player') or not hasattr(self, 'progress_scale'):
            return False  # Arrêter le timer
            
        # Continuer le timer même si pas en lecture pour éviter les arrêts intempestifs
        # Le timer sera arrêté explicitement dans on_audio_state_changed
        position = self.audio_player.get_position()
        duration = self.audio_player.get_duration()
        
        # Debug: afficher les valeurs obtenues
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 1
            
        if self._debug_counter % 20 == 0:  # Afficher toutes les 10 secondes
            print(f"🎵 DEBUG: position={position:.1f}s, duration={duration:.1f}s")
        
        if duration > 0 and position >= 0:
            progress = min(100, max(0, (position / duration) * 100))
            
            # Éviter les mises à jour trop fréquentes qui peuvent causer des saccades
            current_value = self.progress_scale.get_value()
            if abs(progress - current_value) > 0.5:  # Seuil de 0.5%
                self.progress_scale.set_value(progress)
            
            # Mettre à jour les labels de temps
            pos_str = self._format_time(position)
            dur_str = self._format_time(duration)
            self.time_start_label.set_text(pos_str)
            self.time_end_label.set_text(dur_str)
        
        return True  # Continuer le timer
    
    def _format_time(self, seconds):
        """Formate le temps en mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def on_audio_state_changed(self, state):
        """Callback changement d'état audio"""
        if state == PlayerState.PLAYING:
            self.play_btn.set_label("⏸️")
            # Démarrer le timer seulement si pas déjà actif
            if not hasattr(self, 'position_timer') or not self.position_timer:
                self._start_position_timer()
        elif state == PlayerState.STOPPED:
            self.play_btn.set_label("▶️")
            # Arrêter le timer seulement lors d'un arrêt complet
            if hasattr(self, 'position_timer') and self.position_timer:
                from gi.repository import GLib
                GLib.source_remove(self.position_timer)
                self.position_timer = None
            # Remettre la barre de progression à zéro
            if hasattr(self, 'progress_scale'):
                self.progress_scale.set_value(0)
            if hasattr(self, 'time_start_label'):
                self.time_start_label.set_text("00:00")
        else:  # PAUSED ou autres états
            self.play_btn.set_label("▶️")
            # Ne PAS arrêter le timer pour les pauses, permet de reprendre fluidement
    
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
        # Même taille que la fenêtre d'édition
        dialog.set_default_size(1200, 800)
        dialog.set_resizable(True)
        
        # Boutons
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Utiliser", Gtk.ResponseType.OK)
        
        # Contenu
        content_area = dialog.get_content_area()
        
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
        
        print(f"🎯 Dialog response: {response}")
        print(f"🎯 Response OK? {response == Gtk.ResponseType.OK}")
        
        if response == Gtk.ResponseType.OK:
            # Appliquer la pochette sélectionnée
            print(f"🎯 hasattr selected_cover: {hasattr(self, 'selected_cover')}")
            if hasattr(self, 'selected_cover'):
                print(f"🎯 selected_cover value: {self.selected_cover}")
            
            if hasattr(self, 'selected_cover') and self.selected_cover:
                print(f"🎯 APPEL _apply_selected_cover avec: {self.selected_cover}")
                self._apply_selected_cover(self.selected_cover)
            else:
                print(f"🎯 Aucune pochette sélectionnée ou selected_cover manquant")
                # Montrer un message si aucune pochette sélectionnée
                msg_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="Aucune pochette sélectionnée"
                )
                msg_dialog.run()
                msg_dialog.destroy()
        
        dialog.destroy()
    
    def _apply_selected_cover(self, cover_result):
        """Applique la pochette sélectionnée"""
        print(f"🎯 DÉBUT _apply_selected_cover - URL: {cover_result.url}")
        print(f"🎯 Nombre de tracks: {len(self.tracks) if hasattr(self, 'tracks') else 'AUCUN'}")
        
        try:
            import requests
            from PIL import Image as PILImage
            import io
            
            # Télécharger l'image complète
            response = requests.get(cover_result.url, timeout=15)
            response.raise_for_status()
            
            # Sauver dans le dossier de l'album et appliquer aux tags
            if self.tracks:
                # Utiliser le premier track pour déterminer le dossier de l'album
                album_folder = os.path.dirname(self.tracks[0]['file_path'])
                cover_path = os.path.join(album_folder, 'cover.jpg')
                
                # Traiter l'image avec PIL
                pil_image = PILImage.open(io.BytesIO(response.content))
                
                # Convertir en RGB si nécessaire
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Redimensionner si trop grande (max 1000x1000)
                if pil_image.width > 1000 or pil_image.height > 1000:
                    pil_image.thumbnail((1000, 1000), PILImage.Resampling.LANCZOS)
                
                # Sauver le fichier cover.jpg
                pil_image.save(cover_path, 'JPEG', quality=90)
                print(f"🎯 Fichier cover.jpg sauvé: {cover_path}")
                
                # Appliquer la pochette aux tags de tous les morceaux de l'album
                print(f"🎯 AVANT appel _embed_cover_to_tracks")
                self._embed_cover_to_tracks(cover_path)
                print(f"🎯 APRÈS appel _embed_cover_to_tracks")
                
                # Mettre à jour l'affichage de la pochette dans la fenêtre d'édition
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cover_path, 250, 250, True)
                self.cover_image.set_from_pixbuf(pixbuf)
                
                # Mettre à jour la carte dans la fenêtre principale
                if self.parent_card and hasattr(self.parent_card, 'refresh_cover'):
                    def update_card_cover():
                        try:
                            self.parent_card.refresh_cover()
                        except Exception as e:
                            print(f"❌ Erreur rafraîchissement carte: {e}")
                    
                    GLib.idle_add(update_card_cover)
            else:
                print("⚠️ Aucun morceau chargé pour appliquer la pochette")
                
        except Exception as e:
            print(f"❌ Erreur application pochette: {e}")
            import traceback
            traceback.print_exc()
    
    def _embed_cover_to_tracks(self, cover_path):
        """Intègre la pochette dans les tags de tous les morceaux de l'album"""
        if not os.path.exists(cover_path):
            print(f"❌ Fichier de pochette introuvable: {cover_path}")
            return
        
        print(f"🎵 Début application pochette aux tags: {len(self.tracks)} morceaux")
        success_count = 0
        error_count = 0
        
        for track in self.tracks:
            try:
                file_path = track['file_path']
                
                if not os.path.exists(file_path):
                    print(f"❌ Fichier morceau introuvable: {file_path}")
                    error_count += 1
                    continue
                
                # Lire les données de l'image
                with open(cover_path, 'rb') as img_file:
                    cover_data = img_file.read()
                
                # Appliquer selon le format de fichier
                if file_path.lower().endswith('.mp3'):
                    self._embed_cover_mp3(file_path, cover_data)
                    # Vérifier que la pochette a été appliquée
                    self._verify_cover_embedded(file_path, 'mp3')
                elif file_path.lower().endswith('.flac'):
                    self._embed_cover_flac(file_path, cover_data)
                    # Vérifier que la pochette a été appliquée
                    self._verify_cover_embedded(file_path, 'flac')
                elif file_path.lower().endswith(('.m4a', '.mp4')):
                    self._embed_cover_mp4(file_path, cover_data)
                    # Vérifier que la pochette a été appliquée
                    self._verify_cover_embedded(file_path, 'mp4')
                else:
                    print(f"⚠️ Format non supporté pour le tag cover: {file_path}")
                    error_count += 1
                    continue
                
                success_count += 1
                
            except Exception as e:
                print(f"❌ Erreur application pochette sur {track['file_path']}: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
        
        if error_count > 0:
            print(f"⚠️ {error_count} erreurs lors de l'application")
    
    def _embed_cover_mp3(self, file_path, cover_data):
        """Intègre la pochette dans un fichier MP3"""
        from mutagen.id3 import ID3, APIC, ID3NoHeaderError
        
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
        
        # SUPPRIMER TOUTES LES ANCIENNES POCHETTES D'ABORD
        apic_keys = [key for key in audio.keys() if key.startswith('APIC')]
        for key in apic_keys:
            del audio[key]
        
        # Ajouter la nouvelle pochette
        audio['APIC'] = APIC(
            encoding=3,  # UTF-8
            mime='image/jpeg',
            type=3,  # Front cover
            desc='Cover',
            data=cover_data
        )
        
        audio.save(file_path)
    
    def _embed_cover_flac(self, file_path, cover_data):
        """Intègre la pochette dans un fichier FLAC"""
        from mutagen.flac import FLAC, Picture
        
        audio = FLAC(file_path)
        
        # SUPPRIMER TOUTES LES ANCIENNES POCHETTES D'ABORD
        audio.clear_pictures()
        
        # Créer l'objet Picture
        picture = Picture()
        picture.data = cover_data
        picture.type = 3  # Front cover
        picture.mime = 'image/jpeg'
        picture.desc = 'Cover'
        
        # Ajouter la nouvelle pochette
        audio.add_picture(picture)
        
        print(f"💾 Sauvegarde tags FLAC: {file_path}")
        audio.save()
    
    def _embed_cover_mp4(self, file_path, cover_data):
        """Intègre la pochette dans un fichier MP4/M4A"""
        from mutagen.mp4 import MP4, MP4Cover
        
        audio = MP4(file_path)
        
        # SUPPRIMER TOUTES LES ANCIENNES POCHETTES D'ABORD
        if 'covr' in audio:
            del audio['covr']
        
        # Ajouter la nouvelle pochette
        audio['covr'] = [MP4Cover(cover_data, MP4Cover.FORMAT_JPEG)]
        
        audio.save()
    
    def _verify_cover_embedded(self, file_path, format_type):
        """Vérifie que la pochette a bien été intégrée dans le fichier"""
        try:
            if format_type == 'mp3':
                from mutagen.id3 import ID3
                audio = ID3(file_path)
                apic_keys = [key for key in audio.keys() if key.startswith('APIC')]
                if not apic_keys:
                    print(f"❌ Vérification MP3: AUCUNE pochette trouvée!")
                    
            elif format_type == 'flac':
                from mutagen.flac import FLAC
                audio = FLAC(file_path)
                if not audio.pictures:
                    print(f"❌ Vérification FLAC: AUCUNE pochette trouvée!")
                    
            elif format_type == 'mp4':
                from mutagen.mp4 import MP4
                audio = MP4(file_path)
                if 'covr' not in audio or not audio['covr']:
                    print(f"❌ Vérification MP4: AUCUNE pochette trouvée!")
                    
        except Exception as e:
            print(f"❌ Erreur vérification {format_type}: {e}")
    
    def _schedule_metadata_save(self):
        """Planifie la sauvegarde des métadonnées avec un délai (debounce)"""
        if self.metadata_save_timer:
            GLib.source_remove(self.metadata_save_timer)
        self.metadata_save_timer = GLib.timeout_add(500, self._save_metadata_to_files)
    
    def _save_metadata_to_files(self):
        """Sauvegarde les métadonnées dans tous les fichiers audio"""
        try:
            if not self.tracks:
                return False
            
            # Récupérer les valeurs communes (partagées entre tous les albums)
            new_artist = self.artist_entry.get_text().strip()
            new_year = self.year_entry.get_text().strip()
            new_genre = self.genre_combo.get_active_text() or ""
            
            # Logique différente selon le mode d'édition
            is_multi_album = len(self.selected_albums) > 1
            
            if is_multi_album:
                # MODE MULTI-ALBUMS: Préserver les titres d'albums individuels
                self._save_metadata_multi_album(new_artist, new_year, new_genre)
            else:
                # MODE ALBUM UNIQUE: Utiliser le titre saisi
                new_album = self.album_entry.get_text().strip()
                self._save_metadata_single_album(new_album, new_artist, new_year, new_genre)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde métadonnées: {e}")
        
        self.metadata_save_timer = None
        return False
    
    def _save_metadata_single_album(self, new_album, new_artist, new_year, new_genre):
        """Sauvegarde pour un seul album - applique toutes les valeurs saisies"""
        for track in self.tracks:
            file_path = track['file_path']
            if not os.path.exists(file_path):
                continue
            
            if file_path.lower().endswith('.mp3'):
                self._save_metadata_mp3(file_path, new_album, new_artist, new_year, new_genre)
            elif file_path.lower().endswith('.flac'):
                self._save_metadata_flac(file_path, new_album, new_artist, new_year, new_genre)
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                self._save_metadata_mp4(file_path, new_album, new_artist, new_year, new_genre)
    
    def _save_metadata_multi_album(self, new_artist, new_year, new_genre):
        """Sauvegarde pour plusieurs albums - préserve les titres individuels"""
        # Créer un mapping album_path -> titre_original pour préserver les titres
        album_titles = {}
        for album in self.selected_albums:
            album_path = album.get('folder_path') or album.get('path', '')
            album_title = album.get('album', os.path.basename(album_path))
            album_titles[album_path] = album_title
            print(f"📀 Album {os.path.basename(album_path)} → Titre préservé: '{album_title}'")
        
        for track in self.tracks:
            file_path = track['file_path']
            if not os.path.exists(file_path):
                continue
            
            # Déterminer le titre de l'album pour ce fichier
            track_album_path = os.path.dirname(file_path)
            original_album_title = album_titles.get(track_album_path, "Album Inconnu")
            
            print(f"💾 Fichier {os.path.basename(file_path)} → Album: '{original_album_title}'")
            
            if file_path.lower().endswith('.mp3'):
                self._save_metadata_mp3(file_path, original_album_title, new_artist, new_year, new_genre)
            elif file_path.lower().endswith('.flac'):
                self._save_metadata_flac(file_path, original_album_title, new_artist, new_year, new_genre)
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                self._save_metadata_mp4(file_path, original_album_title, new_artist, new_year, new_genre)

    def _emit_metadata_changed_events(self, new_album, new_artist, new_year, new_genre):
        """Émet les événements de changement de métadonnées pour tous les albums modifiés"""
        try:
            album_paths = []
            updated_metadata = {}
            
            # Préparer les données pour chaque album modifié
            for album in self.selected_albums:
                album_path = album.get('folder_path') or album.get('path', '')
                if album_path:
                    album_paths.append(album_path)
                    
                    # Préparer les métadonnées mises à jour
                    metadata_update = {}
                    
                    # En mode multi-albums : seulement les champs non vides
                    if len(self.selected_albums) > 1:
                        if new_album:
                            metadata_update['album'] = new_album
                            metadata_update['title'] = new_album
                        if new_artist:
                            metadata_update['artist'] = new_artist
                        if new_year:
                            metadata_update['year'] = new_year
                        if new_genre:
                            metadata_update['genre'] = new_genre
                    else:
                        # En mode single album : tous les champs
                        metadata_update['album'] = new_album or album.get('album', '')
                        metadata_update['title'] = new_album or album.get('title', '')
                        metadata_update['artist'] = new_artist or album.get('artist', '')
                        metadata_update['year'] = new_year or album.get('year', '')
                        metadata_update['genre'] = new_genre or album.get('genre', '')
                    
                    # Mettre à jour les données de l'album aussi
                    album.update(metadata_update)
                    updated_metadata[album_path] = metadata_update
            
            # Émettre les événements pour tous les albums modifiés
            if album_paths:
                # metadata_event_manager.notify_metadata_changed(album_paths, updated_metadata)  # DÉSACTIVÉ - Remplacé par RefreshManager
                print(f"📡 Ancien système d'événements désactivé pour {len(album_paths)} albums")
            
        except Exception as e:
            print(f"❌ Erreur émission événements: {e}")
    
    def _save_title_to_file(self, file_path, title, track_num=None):
        """Sauvegarde un titre individuel dans les métadonnées physiques et renomme le fichier"""
        try:
            # 1. Sauvegarder les métadonnées
            if file_path.lower().endswith('.mp3'):
                from mutagen.id3 import ID3, TIT2, ID3NoHeaderError
                try:
                    audio = ID3(file_path)
                except ID3NoHeaderError:
                    audio = ID3()
                audio['TIT2'] = TIT2(encoding=3, text=title)
                audio.save(file_path)
                
            elif file_path.lower().endswith('.flac'):
                from mutagen.flac import FLAC
                audio = FLAC(file_path)
                audio['TITLE'] = title
                audio.save()
                
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                from mutagen.mp4 import MP4
                audio = MP4(file_path)
                audio['\xa9nam'] = title
                audio.save()
            
            # 2. Renommer le fichier selon la règle "N° - Titre"
            new_file_path = file_path
            if track_num and title:
                directory = os.path.dirname(file_path)
                extension = os.path.splitext(file_path)[1]
                
                # Nettoyer le titre pour le nom de fichier
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                new_filename = f"{track_num} - {clean_title}{extension}"
                new_file_path = os.path.join(directory, new_filename)
                
                # Renommer seulement si le nom change
                if new_file_path != file_path:
                    os.rename(file_path, new_file_path)
            
            return new_file_path
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde titre {file_path}: {e}")
            return file_path
    
    def _save_metadata_mp3(self, file_path, album, artist, year, genre):
        """Sauvegarde métadonnées MP3"""
        try:
            from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, TDRC, TCON, ID3NoHeaderError
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                audio = ID3()
            
            if artist:
                audio['TPE1'] = TPE1(encoding=3, text=artist)  # Artiste
                audio['TPE2'] = TPE2(encoding=3, text=artist)  # Artiste de l'album
            if album:
                # Appliquer sentence case sur l'album
                corrected_album = self.case_corrector.correct_text_case(album, 'album').corrected
                audio['TALB'] = TALB(encoding=3, text=corrected_album)
            if year:
                audio['TDRC'] = TDRC(encoding=3, text=year)
            if genre:
                audio['TCON'] = TCON(encoding=3, text=genre)
            
            audio.save(file_path)
        except Exception as e:
            print(f"❌ Erreur MP3 {file_path}: {e}")
    
    def _save_metadata_flac(self, file_path, album, artist, year, genre):
        """Sauvegarde métadonnées FLAC"""
        try:
            audio = FLAC(file_path)
            if artist:
                audio['ARTIST'] = artist
                audio['ALBUMARTIST'] = artist  # Artiste de l'album
            if album:
                # Appliquer sentence case sur l'album
                corrected_album = self.case_corrector.correct_text_case(album, 'album').corrected
                audio['ALBUM'] = corrected_album
            if year:
                audio['DATE'] = year
            if genre:
                audio['GENRE'] = genre
            audio.save()
        except Exception as e:
            print(f"❌ Erreur FLAC {file_path}: {e}")
    
    def _save_metadata_mp4(self, file_path, album, artist, year, genre):
        """Sauvegarde métadonnées MP4"""
        try:
            audio = MP4(file_path)
            if artist:
                audio['\xa9ART'] = [artist]
                audio['aART'] = [artist]  # Artiste de l'album
            if album:
                # Appliquer sentence case sur l'album
                corrected_album = self.case_corrector.correct_text_case(album, 'album').corrected
                audio['\xa9alb'] = [corrected_album]
            if year:
                audio['\xa9day'] = [year]
            if genre:
                audio['\xa9gen'] = [genre]
            audio.save()
        except Exception as e:
            print(f"❌ Erreur MP4 {file_path}: {e}")
    
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
            
            # Grille de pochettes avec vraies images
            grid = Gtk.Grid()
            grid.set_column_spacing(20)
            grid.set_row_spacing(20)
            grid.set_margin_top(20)
            grid.set_margin_bottom(20)
            grid.set_margin_left(20)
            grid.set_margin_right(20)
            
            self.selected_cover = None
            
            for i, result in enumerate(results[:4]):  # Limiter à 4 résultats (2x2)
                # Box vertical pour image seulement (pas de frame, pas de label)
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                vbox.set_margin_top(10)
                vbox.set_margin_bottom(10)
                
                # Image placeholder d'abord (300x300)
                image = Gtk.Image()
                image.set_size_request(300, 300)
                image.set_from_icon_name("image-loading", Gtk.IconSize.DIALOG)
                vbox.pack_start(image, False, False, 0)
                
                # Faire le vbox cliquable directement avec frame pour sélection
                event_box = Gtk.EventBox()
                
                # Frame pour l'encadrement (invisible par défaut)
                frame = Gtk.Frame()
                frame.set_shadow_type(Gtk.ShadowType.NONE)
                frame.add(vbox)
                
                event_box.add(frame)
                event_box.connect("button-press-event", self._on_cover_selected, result, event_box, frame)
                
                # Positionner dans la grille (2 colonnes)
                row = i // 2
                col = i % 2
                grid.attach(event_box, col, row, 1, 1)
                
                # Charger l'image en arrière-plan (300x300)
                self._load_cover_image_async(result, image, 300)
            
            scrolled.add(grid)
        
        dialog.show_all()
    
    def _load_cover_image_async(self, cover_result, image_widget, size=300):
        """Charge une image de pochette en arrière-plan"""
        def load_image():
            try:
                import requests
                from PIL import Image as PILImage
                import io
                
                # Utiliser l'URL de miniature si disponible, sinon l'URL complète
                url = cover_result.thumbnail_url or cover_result.url
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Convertir en GdkPixbuf
                pil_image = PILImage.open(io.BytesIO(response.content))
                
                # Redimensionner à la taille demandée
                pil_image.thumbnail((size, size), PILImage.Resampling.LANCZOS)
                
                # Convertir en format compatible GTK
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Sauver temporairement et charger avec GTK
                temp_path = f"/tmp/cover_{hash(url)}.jpg"
                pil_image.save(temp_path, 'JPEG')
                
                # Charger dans GTK
                GLib.idle_add(self._update_cover_image, image_widget, temp_path, size)
                
            except Exception as e:
                print(f"Erreur chargement image {url}: {e}")
                GLib.idle_add(self._update_cover_image, image_widget, None, size)
        
        import threading
        thread = threading.Thread(target=load_image)
        thread.daemon = True
        thread.start()
    
    def _update_cover_image(self, image_widget, image_path, size=300):
        """Met à jour l'image dans le thread principal GTK"""
        try:
            if image_path and os.path.exists(image_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, size, size, True)
                image_widget.set_from_pixbuf(pixbuf)
                # Nettoyer le fichier temporaire
                try:
                    os.remove(image_path)
                except:
                    pass
            else:
                image_widget.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        except Exception as e:
            print(f"Erreur mise à jour image: {e}")
            image_widget.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
    
    def _on_cover_selected(self, event_box, event, cover_result, container, frame):
        """Gère la sélection d'une pochette"""
        # Enlever la sélection précédente
        if hasattr(self, '_selected_frame'):
            self._selected_frame.set_shadow_type(Gtk.ShadowType.NONE)
            # Retirer le style CSS personnalisé
            style_context = self._selected_frame.get_style_context()
            style_context.remove_class("selected-cover")
        
        # Marquer comme sélectionné avec un encadrement bleu
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        # Ajouter un style CSS pour l'encadrement bleu
        style_context = frame.get_style_context()
        style_context.add_class("selected-cover")
        
        # Ajouter le CSS si pas déjà fait
        if not hasattr(self, '_css_provider_added'):
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(b"""
                .selected-cover {
                    border: 3px solid #0066CC;
                    border-radius: 5px;
                }
            """)
            
            screen = frame.get_screen()
            style_context.add_provider_for_screen(
                screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self._css_provider_added = True
        
        self._selected_frame = frame
        self.selected_cover = cover_result
        
        print(f"🎯 POCHETTE SÉLECTIONNÉE: {cover_result.source} - {cover_result.url}")
        print(f"🎯 self.selected_cover défini: {self.selected_cover}")
    
    def _display_cover_error(self, dialog, content_area, error_msg, spinner, loading_label):
        """Affiche une erreur de recherche"""
        content_area.remove(spinner)
        content_area.remove(loading_label)
        
        error_label = Gtk.Label(f"Erreur de recherche: {error_msg}")
        content_area.pack_start(error_label, True, True, 0)
        dialog.show_all()
    
    def on_selection_changed(self, selection):
        """Met à jour la pochette selon la piste sélectionnée"""
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return
            
        # Récupérer le chemin du fichier sélectionné (colonne cachée)
        file_path = model[tree_iter][9]  # La colonne path est à l'index 9
        if not file_path or not os.path.exists(file_path):
            return
            
        # Obtenir le dossier de la piste pour chercher la pochette
        track_folder = os.path.dirname(file_path)
        
        # Trouver et charger la pochette du dossier de cette piste
        cover_path = self._find_cover_file(track_folder)
        
        if cover_path and os.path.exists(cover_path):
            try:
                # Charger et redimensionner l'image à 250x250
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    cover_path, 250, 250, True
                )
                self.cover_image.set_from_pixbuf(pixbuf)
                print(f"🖼️ Pochette mise à jour depuis: {cover_path}")
            except Exception as e:
                print(f"Erreur chargement pochette {cover_path}: {e}")
                # Fallback: icône par défaut
                self.cover_image.set_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
        else:
            # Aucune pochette trouvée, utiliser l'icône par défaut
            self.cover_image.set_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
            print(f"❌ Aucune pochette trouvée dans: {track_folder}")
    
    def on_window_closing(self, window, event):
        """Gestionnaire de fermeture de la fenêtre d'édition"""
        
        # Forcer une sauvegarde finale et émission d'événements si nécessaire
        if hasattr(self, 'metadata_save_timer') and self.metadata_save_timer:
            GLib.source_remove(self.metadata_save_timer)
            self._save_metadata_delayed()  # Sauvegarde immédiate
        
        # Collecter les albums modifiés pour notification
        modified_albums = []
        if hasattr(self, 'tracks') and self.tracks:
            # Extraire les dossiers d'albums uniques
            album_folders = set()
            for track in self.tracks:
                if 'file_path' in track:
                    album_folder = os.path.dirname(track['file_path'])
                    album_folders.add(album_folder)
            modified_albums = list(album_folders)
        
        # Notifier le RefreshManager des changements
        if modified_albums:
            refresh_manager.notify_metadata_changed(modified_albums, immediate=True)
        
        # Nettoyer le lecteur audio
        if hasattr(self, 'audio_player'):
            self.audio_player.cleanup()
        
        # Arrêter le timer
        if hasattr(self, 'position_timer') and self.position_timer:
            GLib.source_remove(self.position_timer)
        
        return False
    
    def _refresh_all_modified_cards(self):
        """Rafraîchit toutes les cartes correspondant aux albums modifiés (mode multi-albums)"""
        try:
            # Récupérer l'instance de l'application principale (NonotagsApp)
            app_instance = None
            for widget in Gtk.Window.list_toplevels():
                if hasattr(widget, 'albums_grid'):  # NonotagsApp a albums_grid
                    app_instance = widget
                    break
            
            if not app_instance:
                print("⚠️ Impossible de trouver l'instance de l'application principale")
                return
            
            # Récupérer toutes les cartes existantes
            all_cards = app_instance.albums_grid.get_children()
            
            # Créer un set des chemins d'albums modifiés pour recherche rapide
            modified_paths = set()
            for album in self.selected_albums:
                path = album.get('folder_path') or album.get('path', '')
                if path:
                    modified_paths.add(path)
            
            # Rafraîchir chaque carte correspondant aux albums modifiés
            refreshed_count = 0
            for card in all_cards:
                if hasattr(card, 'album_data'):
                    card_path = card.album_data.get('folder_path') or card.album_data.get('path', '')
                    if card_path in modified_paths:
                        GLib.idle_add(card._update_display)
                        refreshed_count += 1
            
        except Exception as e:
            print(f"❌ Erreur lors du rafraîchissement multi-cartes: {e}")
            import traceback
            traceback.print_exc()
    
    def on_startup_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre"""
        
        # Nettoyer le lecteur audio
        if hasattr(self, 'audio_player'):
            self.audio_player.cleanup()
        
        # Arrêter le timer
        if hasattr(self, 'position_timer') and self.position_timer:
            GLib.source_remove(self.position_timer)
        
        return False
    
    def _load_album_cover(self):
        """Charge et affiche la pochette d'album si elle existe"""
        album_path = self.album_data.get('path') or self.album_data.get('folder_path')
        
        if album_path and os.path.exists(album_path):
            cover_path = self._find_cover_file(album_path)
            
            if cover_path and os.path.exists(cover_path):
                try:
                    # Charger et redimensionner l'image à 250x250
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        cover_path, 250, 250, True
                    )
                    self.cover_image.set_from_pixbuf(pixbuf)
                    return
                except Exception as e:
                    print(f"Erreur chargement pochette {cover_path}: {e}")
        
        # Fallback: icône par défaut
        self.cover_image.set_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
    
    def _find_cover_file(self, album_path):
        """Cherche un fichier de pochette dans le dossier d'album"""
        cover_names = [
            'cover.jpg', 'cover.jpeg', 'cover.png',
            'folder.jpg', 'folder.jpeg', 'folder.png',
            'front.jpg', 'front.jpeg', 'front.png',
            'album.jpg', 'album.jpeg', 'album.png'
        ]
        
        for cover_name in cover_names:
            cover_path = os.path.join(album_path, cover_name)
            if os.path.exists(cover_path):
                return cover_path
        
        return None