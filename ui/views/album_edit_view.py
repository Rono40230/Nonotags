"""
Vue d'édition d'albums pour Nonotags
Interface d'édition détaillée avec support plein écran
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
from typing import TYPE_CHECKING, List, Optional
import os

if TYPE_CHECKING:
    from ..app_controller import NonotagsApp

from ..models.album_model import AlbumModel

class AlbumEditView(Adw.ApplicationWindow):
    """
    Fenêtre d'édition d'albums avec support plein écran
    Interface détaillée pour l'édition des métadonnées
    """
    
    def __init__(self, app: 'NonotagsApp', albums: List[AlbumModel]):
        super().__init__(
            application=app,
            title="Édition d'albums - Nonotags",
            default_width=1400,
            default_height=900
        )
        
        # Permet la maximisation et le plein écran
        self.set_resizable(True)
        self.set_can_target(True)
        
        self.app = app
        self.albums = albums
        self.current_album_index = 0
        
        self._setup_ui()
        self._setup_actions()
        self._load_current_album()
        
        # CSS pour l'édition
        self.add_css_class("edit-window")
        
        self.app.logger.info(f"Fenêtre d'édition initialisée pour {len(albums)} albums")
    
    def _setup_ui(self):
        """Configure l'interface d'édition"""
        
        # === HEADER BAR ===
        header_bar = Adw.HeaderBar()
        header_bar.add_css_class("edit-headerbar")
        
        # Bouton retour
        back_button = Gtk.Button()
        back_button.set_icon_name("go-previous-symbolic")
        back_button.set_tooltip_text("Retour à la liste")
        back_button.connect("clicked", self._on_back_clicked)
        header_bar.pack_start(back_button)
        
        # Titre avec indicateur
        title_widget = Adw.WindowTitle()
        title_widget.set_title("Édition d'albums")
        title_widget.set_subtitle(f"Album {self.current_album_index + 1} sur {len(self.albums)}")
        header_bar.set_title_widget(title_widget)
        self.title_widget = title_widget
        
        # Boutons d'action
        save_button = Gtk.Button(label="Enregistrer")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self._on_save_clicked)
        header_bar.pack_end(save_button)
        
        # Menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Options")
        header_bar.pack_end(menu_button)
        
        self.set_titlebar(header_bar)
        
        # === CONTENU PRINCIPAL ===
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        # === NAVIGATION LATÉRALE ===
        sidebar = self._create_sidebar()
        main_box.append(sidebar)
        
        # === ZONE D'ÉDITION ===
        edit_area = self._create_edit_area()
        main_box.append(edit_area)
        
        self.set_content(main_box)
    
    def _create_sidebar(self):
        """Crée la barre latérale de navigation"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.set_size_request(300, -1)
        sidebar_box.add_css_class("sidebar")
        
        # Header de la sidebar
        sidebar_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        sidebar_header.set_margin_top(10)
        sidebar_header.set_margin_bottom(10)
        sidebar_header.set_margin_start(15)
        sidebar_header.set_margin_end(15)
        
        sidebar_title = Gtk.Label()
        sidebar_title.set_markup("<b>Albums à éditer</b>")
        sidebar_title.set_halign(Gtk.Align.START)
        sidebar_header.append(sidebar_title)
        
        sidebar_box.append(sidebar_header)
        
        # Séparateur
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sidebar_box.append(separator)
        
        # Liste des albums
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        self.album_list = Gtk.ListBox()
        self.album_list.add_css_class("album-list")
        self.album_list.connect("row-selected", self._on_album_selected)
        
        # Remplir la liste
        for i, album in enumerate(self.albums):
            row = self._create_album_row(album, i)
            self.album_list.append(row)
        
        scrolled.set_child(self.album_list)
        sidebar_box.append(scrolled)
        
        return sidebar_box
    
    def _create_album_row(self, album: AlbumModel, index: int):
        """Crée une ligne d'album pour la sidebar"""
        row = Gtk.ListBoxRow()
        row.album_index = index
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(15)
        box.set_margin_end(15)
        
        # Icône de statut
        status_icon = Gtk.Label()
        status_icon.set_text(album.status_icon)
        status_icon.set_size_request(20, -1)
        box.append(status_icon)
        
        # Informations de l'album
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{album.title}</b>")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(3)  # ELLIPSIZE_END
        info_box.append(title_label)
        
        artist_label = Gtk.Label(label=album.artist)
        artist_label.set_halign(Gtk.Align.START)
        artist_label.add_css_class("dim-label")
        artist_label.set_ellipsize(3)
        info_box.append(artist_label)
        
        box.append(info_box)
        
        # Indicateur de modification
        if album.has_changes:
            modified_icon = Gtk.Label(label="●")
            modified_icon.add_css_class("modified-indicator")
            box.append(modified_icon)
        
        row.set_child(box)
        return row
    
    def _create_edit_area(self):
        """Crée la zone d'édition principale selon le cahier des charges"""
        # ScrolledWindow pour le contenu
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Container principal vertical
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_container.set_margin_start(20)
        main_container.set_margin_end(20)
        main_container.set_margin_top(20)
        main_container.set_margin_bottom(20)
        
        # === BLOC SUPÉRIEUR (12.1 + 12.2) ===
        top_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        
        # 12.1 - BLOC POCHETTE (en haut à gauche)
        cover_block = self._create_cover_block()
        top_container.append(cover_block)
        
        # 12.2 - BLOC CHAMPS DE SAISIE (en haut à droite)
        fields_block = self._create_fields_block()
        top_container.append(fields_block)
        
        main_container.append(top_container)
        
        # === 12.3 - BLOC TABLEAU MÉTADONNÉES (toute la largeur) ===
        metadata_table = self._create_metadata_table()
        main_container.append(metadata_table)
        
        # === 12.4 - BLOC LECTEUR AUDIO (toute la largeur) ===
        audio_player = self._create_audio_player()
        main_container.append(audio_player)
        
        scrolled.set_child(main_container)
        return scrolled
    
    def _create_cover_block(self):
        """12.1 - Crée le bloc pochette (haut gauche) - 250x250 + bouton"""
        cover_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        cover_container.set_size_request(280, -1)
        
        # Image de pochette 250x250
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(250, 250)
        self.cover_image.add_css_class("album-cover-edit")
        
        # Charge la pochette par défaut
        self._load_cover_image()
        
        cover_container.append(self.cover_image)
        
        # Bouton "Chercher une pochette"
        search_cover_btn = Gtk.Button(label="Chercher une pochette")
        search_cover_btn.set_icon_name("emblem-photos-symbolic")
        search_cover_btn.add_css_class("suggested-action")
        search_cover_btn.connect("clicked", self._on_search_cover_clicked)
        cover_container.append(search_cover_btn)
        
        return cover_container
    
    def _create_fields_block(self):
        """12.2 - Crée le bloc des 4 champs de saisie (haut droite)"""
        fields_group = Adw.PreferencesGroup()
        fields_group.set_title("Métadonnées de l'album")
        fields_group.set_description("Les modifications s'appliquent à toutes les pistes")
        
        # Champ Album
        self.album_row = Adw.EntryRow()
        self.album_row.set_title("Album")
        self.album_row.connect("notify::text", self._on_album_field_changed)
        fields_group.add(self.album_row)
        
        # Champ Artiste
        self.artist_row = Adw.EntryRow()
        self.artist_row.set_title("Artiste")
        self.artist_row.connect("notify::text", self._on_artist_field_changed)
        fields_group.add(self.artist_row)
        
        # Champ Année
        self.year_row = Adw.EntryRow()
        self.year_row.set_title("Année")
        self.year_row.set_input_purpose(Gtk.InputPurpose.NUMBER)
        self.year_row.connect("notify::text", self._on_year_field_changed)
        fields_group.add(self.year_row)
        
        # Champ Genre (menu déroulant)
        self.genre_row = Adw.ComboRow()
        self.genre_row.set_title("Genre")
        
        # Liste des genres selon le cahier des charges
        genre_model = Gtk.StringList()
        genres = [
            "Acid Jazz", "B.O. de Films", "Blues", "Chansons Française", "Disco",
            "Electronique", "Flamenco", "Folk", "Funk", "Jazz", "Musique Afriquaine",
            "Musique Andine", "Musique Brésilienne", "Musique Classique", "Musique Cubaine",
            "Musique Franco-Hispanique", "New-Wave", "Pop", "Rap", "Reggae", "Rock",
            "Soul", "Top 50", "Trip-Hop", "Zouk"
        ]
        for genre in genres:
            genre_model.append(genre)
        
        self.genre_row.set_model(genre_model)
        self.genre_row.connect("notify::selected", self._on_genre_field_changed)
        fields_group.add(self.genre_row)
        
        return fields_group
    
    def _create_metadata_table(self):
        """12.3 - Crée le tableau des métadonnées (toute la largeur)"""
        table_group = Adw.PreferencesGroup()
        table_group.set_title("Tableau des métadonnées")
        table_group.set_description("Double-clic : fichier → lecture, titre → édition")
        
        # Container pour le tableau
        table_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # ScrolledWindow pour le tableau
        scrolled_table = Gtk.ScrolledWindow()
        scrolled_table.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_table.set_size_request(-1, 300)
        
        # TreeView pour le tableau selon spécifications 11.3.1
        self.tracks_store = Gtk.ListStore(
            bool,    # Cover (coche verte/croix rouge)
            str,     # Nom de fichier
            str,     # Titre
            str,     # Interprète
            str,     # Artiste
            str,     # Album
            str,     # Année
            str,     # N° de piste
            str,     # Genre
            object   # Référence TrackModel
        )
        
        self.tracks_tree = Gtk.TreeView(model=self.tracks_store)
        self.tracks_tree.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        self.tracks_tree.add_css_class("metadata-table")
        
        # Colonnes selon 11.3.1
        self._create_table_columns()
        
        scrolled_table.set_child(self.tracks_tree)
        table_container.append(scrolled_table)
        
        # Wrapper pour Adw.PreferencesGroup
        container_row = Adw.ActionRow()
        container_row.set_child(table_container)
        table_group.add(container_row)
        
        return table_group
    
    def _create_audio_player(self):
        """12.4 - Crée le lecteur audio complet (toute la largeur)"""
        player_group = Adw.PreferencesGroup()
        player_group.set_title("Lecteur audio")
        
        # Container principal du lecteur
        player_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        player_container.set_margin_start(10)
        player_container.set_margin_end(10)
        player_container.set_margin_top(10)
        player_container.set_margin_bottom(10)
        
        # 11.4.1 - GAUCHE : Boutons de contrôle
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.prev_btn = Gtk.Button()
        self.prev_btn.set_icon_name("media-skip-backward-symbolic")
        self.prev_btn.connect("clicked", self._on_prev_track)
        controls_box.append(self.prev_btn)
        
        self.play_btn = Gtk.Button()
        self.play_btn.set_icon_name("media-playback-start-symbolic")
        self.play_btn.connect("clicked", self._on_play_pause)
        controls_box.append(self.play_btn)
        
        self.stop_btn = Gtk.Button()
        self.stop_btn.set_icon_name("media-playback-stop-symbolic")
        self.stop_btn.connect("clicked", self._on_stop)
        controls_box.append(self.stop_btn)
        
        self.next_btn = Gtk.Button()
        self.next_btn.set_icon_name("media-skip-forward-symbolic")
        self.next_btn.connect("clicked", self._on_next_track)
        controls_box.append(self.next_btn)
        
        player_container.append(controls_box)
        
        # 11.4.2 - CENTRE : Curseur de progression
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        progress_box.set_hexpand(True)
        
        # Curseur
        self.progress_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress_scale.set_range(0, 100)
        self.progress_scale.set_value(0)
        self.progress_scale.connect("value-changed", self._on_progress_changed)
        progress_box.append(self.progress_scale)
        
        # Labels temps (début - fin)
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.time_start_label = Gtk.Label(label="0:00")
        self.time_end_label = Gtk.Label(label="0:00")
        
        time_spacer = Gtk.Box()
        time_spacer.set_hexpand(True)
        
        time_box.append(self.time_start_label)
        time_box.append(time_spacer)
        time_box.append(self.time_end_label)
        progress_box.append(time_box)
        
        player_container.append(progress_box)
        
        # 11.4.3 - DROITE : Équaliseur
        eq_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        eq_label = Gtk.Label(label="EQ:")
        eq_box.append(eq_label)
        
        self.eq_combo = Gtk.ComboBoxText()
        eq_presets = [
            "Flat", "Rock", "Pop", "Jazz", "Classical",
            "Electronic", "Hip-Hop", "Vocal", "Bass Boost", "Treble Boost"
        ]
        for preset in eq_presets:
            self.eq_combo.append_text(preset)
        self.eq_combo.set_active(0)
        self.eq_combo.connect("changed", self._on_eq_changed)
        eq_box.append(self.eq_combo)
        
        player_container.append(eq_box)
        
        # Wrapper pour Adw.PreferencesGroup
        player_row = Adw.ActionRow()
        player_row.set_child(player_container)
        player_group.add(player_row)
        
        return player_group
    
    def _create_table_columns(self):
        """Crée les colonnes du tableau selon 11.3.1"""
        columns_info = [
            ("Cover", 50, "bool"),
            ("Nom de fichier", 150, "str"),
            ("Titre", 200, "str"),
            ("Interprète", 120, "str"),
            ("Artiste", 120, "str"),
            ("Album", 150, "str"),
            ("Année", 60, "str"),
            ("N° de piste", 80, "str"),
            ("Genre", 100, "str"),
        ]
        
        for i, (title, width, col_type) in enumerate(columns_info):
            if col_type == "bool":
                # Colonne Cover avec icône
                renderer = Gtk.CellRendererPixbuf()
                column = Gtk.TreeViewColumn(title, renderer)
                column.set_cell_data_func(renderer, self._render_cover_cell)
            else:
                renderer = Gtk.CellRendererText()
                renderer.set_property("editable", title == "Titre")  # 11.3.4
                if title == "Titre":
                    renderer.connect("edited", self._on_title_edited)
                column = Gtk.TreeViewColumn(title, renderer, text=i)
            
            column.set_resizable(True)  # 11.3.2
            column.set_min_width(width)
            
            # 11.3.3 - Tri pour titre, années et N° de piste
            if title in ["Titre", "Année", "N° de piste"]:
                column.set_sort_column_id(i)
                column.set_clickable(True)
            
            self.tracks_tree.append_column(column)
        
        # 11.3.5 - Double-clic sur nom de fichier → lecture
        self.tracks_tree.connect("row-activated", self._on_row_activated)
    
    def _load_cover_image(self):
        """Charge l'image de pochette dans le bloc cover"""
        # TODO: Charger la vraie pochette de l'album
        pass
    
    def _render_cover_cell(self, column, cell, model, iter, data):
        """Affiche la coche verte/croix rouge pour la colonne Cover"""
        has_cover = model.get_value(iter, 0)
        if has_cover:
            cell.set_property("icon-name", "emblem-default-symbolic")  # Coche verte
        else:
            cell.set_property("icon-name", "window-close-symbolic")    # Croix rouge
    
    def _create_album_info_group(self):
        """Crée le groupe d'informations de l'album"""
        group = Adw.PreferencesGroup()
        group.set_title("Informations de l'album")
        group.set_description("Métadonnées principales de l'album")
        
        # Titre de l'album
        self.title_row = Adw.EntryRow()
        self.title_row.set_title("Titre de l'album")
        group.add(self.title_row)
        
        # Artiste
        self.artist_row = Adw.EntryRow()
        self.artist_row.set_title("Artiste")
        group.add(self.artist_row)
        
        # Année et genre sur la même ligne
        year_genre_row = Adw.ActionRow()
        year_genre_row.set_title("Année et Genre")
        
        year_genre_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.year_entry = Gtk.Entry()
        self.year_entry.set_placeholder_text("Année")
        self.year_entry.set_size_request(100, -1)
        year_genre_box.append(self.year_entry)
        
        self.genre_entry = Gtk.Entry()
        self.genre_entry.set_placeholder_text("Genre")
        self.genre_entry.set_hexpand(True)
        year_genre_box.append(self.genre_entry)
        
        year_genre_row.add_suffix(year_genre_box)
        group.add(year_genre_row)
        
        return group
    
    def _create_tracks_group(self):
        """Crée le groupe d'édition des pistes"""
        group = Adw.PreferencesGroup()
        group.set_title("Pistes de l'album")
        group.set_description("Édition des métadonnées de chaque piste")
        
        # Container pour la liste des pistes
        tracks_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header du tableau
        header_row = self._create_tracks_header()
        tracks_container.append(header_row)
        
        # Zone scrollable pour les pistes
        scrolled_tracks = Gtk.ScrolledWindow()
        scrolled_tracks.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_tracks.set_size_request(-1, 300)  # Hauteur fixe
        
        # Liste des pistes
        self.tracks_list = Gtk.ListBox()
        self.tracks_list.add_css_class("tracks-list")
        self.tracks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        
        # Ajouter les pistes de l'album courant
        self._populate_tracks_list()
        
        scrolled_tracks.set_child(self.tracks_list)
        tracks_container.append(scrolled_tracks)
        
        # Boutons d'action pour les pistes
        tracks_actions = self._create_tracks_actions()
        tracks_container.append(tracks_actions)
        
        # Wrapper pour intégrer dans Adw.PreferencesGroup
        container_row = Adw.ActionRow()
        container_row.set_title("")
        container_row.set_child(tracks_container)
        group.add(container_row)
        
        return group
    
    def _create_tracks_header(self):
        """Crée l'en-tête du tableau des pistes"""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.add_css_class("tracks-header")
        header.set_margin_top(10)
        header.set_margin_bottom(5)
        header.set_margin_start(15)
        header.set_margin_end(15)
        
        # Numéro
        num_label = Gtk.Label(label="#")
        num_label.set_size_request(40, -1)
        num_label.set_halign(Gtk.Align.CENTER)
        num_label.add_css_class("header-label")
        header.append(num_label)
        
        # Titre
        title_label = Gtk.Label(label="Titre")
        title_label.set_hexpand(True)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("header-label")
        header.append(title_label)
        
        # Artiste
        artist_label = Gtk.Label(label="Artiste")
        artist_label.set_size_request(150, -1)
        artist_label.set_halign(Gtk.Align.START)
        artist_label.add_css_class("header-label")
        header.append(artist_label)
        
        # Durée
        duration_label = Gtk.Label(label="Durée")
        duration_label.set_size_request(70, -1)
        duration_label.set_halign(Gtk.Align.CENTER)
        duration_label.add_css_class("header-label")
        header.append(duration_label)
        
        return header
    
    def _create_tracks_actions(self):
        """Crée les boutons d'action pour les pistes"""
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        actions_box.set_margin_top(10)
        actions_box.set_margin_start(15)
        actions_box.set_margin_end(15)
        
        # Bouton ajouter piste
        add_track_btn = Gtk.Button(label="+ Ajouter une piste")
        add_track_btn.add_css_class("suggested-action")
        add_track_btn.connect("clicked", self._on_add_track)
        actions_box.append(add_track_btn)
        
        # Espaceur
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        actions_box.append(spacer)
        
        # Bouton auto-numérotation
        auto_number_btn = Gtk.Button(label="Auto-numéroter")
        auto_number_btn.connect("clicked", self._on_auto_number_tracks)
        actions_box.append(auto_number_btn)
        
        # Bouton réinitialiser pistes
        reset_tracks_btn = Gtk.Button(label="Réinitialiser")
        reset_tracks_btn.connect("clicked", self._on_reset_tracks)
        actions_box.append(reset_tracks_btn)
        
        return actions_box
    
    def _populate_tracks_list(self):
        """Remplit la liste des pistes"""
        if not self.albums or self.current_album_index >= len(self.albums):
            return
            
        album = self.albums[self.current_album_index]
        
        # Nettoie la liste existante
        while True:
            child = self.tracks_list.get_first_child()
            if child is None:
                break
            self.tracks_list.remove(child)
        
        # Ajoute les pistes (données d'exemple pour la démo)
        sample_tracks = [
            {"num": 1, "title": "So What", "artist": "Miles Davis", "duration": "9:22"},
            {"num": 2, "title": "Freddie Freeloader", "artist": "Miles Davis", "duration": "9:46"},
            {"num": 3, "title": "Blue in Green", "artist": "Miles Davis", "duration": "5:37"},
            {"num": 4, "title": "All Blues", "artist": "Miles Davis", "duration": "11:33"},
            {"num": 5, "title": "Flamenco Sketches", "artist": "Miles Davis", "duration": "9:26"},
        ]
        
        for track in sample_tracks:
            track_row = self._create_track_row(track)
            self.tracks_list.append(track_row)
    
    def _create_track_row(self, track_data):
        """Crée une ligne d'édition pour une piste"""
        row = Gtk.ListBoxRow()
        row.set_margin_top(2)
        row.set_margin_bottom(2)
        
        # Container principal
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(15)
        box.set_margin_end(15)
        
        # Numéro de piste
        num_entry = Gtk.Entry()
        num_entry.set_text(str(track_data["num"]))
        num_entry.set_size_request(40, -1)
        num_entry.set_alignment(0.5)  # Centré
        num_entry.add_css_class("track-number")
        box.append(num_entry)
        
        # Titre de la piste
        title_entry = Gtk.Entry()
        title_entry.set_text(track_data["title"])
        title_entry.set_hexpand(True)
        title_entry.set_placeholder_text("Titre de la piste")
        box.append(title_entry)
        
        # Artiste
        artist_entry = Gtk.Entry()
        artist_entry.set_text(track_data["artist"])
        artist_entry.set_size_request(150, -1)
        artist_entry.set_placeholder_text("Artiste")
        box.append(artist_entry)
        
        # Durée
        duration_entry = Gtk.Entry()
        duration_entry.set_text(track_data["duration"])
        duration_entry.set_size_request(70, -1)
        duration_entry.set_placeholder_text("0:00")
        duration_entry.add_css_class("track-duration")
        box.append(duration_entry)
        
        # Bouton supprimer
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.add_css_class("destructive-action")
        delete_btn.set_tooltip_text("Supprimer cette piste")
        delete_btn.connect("clicked", lambda btn: self._on_delete_track(row))
        box.append(delete_btn)
        
        row.set_child(box)
        row.track_data = track_data
        
        return row
    
    def _create_advanced_group(self):
        """Crée le groupe d'options avancées"""
        group = Adw.PreferencesGroup()
        group.set_title("Options avancées")
        
        # Format de fichier
        format_row = Adw.ComboRow()
        format_row.set_title("Format de sortie")
        format_row.set_subtitle("Format des fichiers traités")
        
        format_model = Gtk.StringList()
        format_model.append("Conserver le format original")
        format_model.append("Convertir en MP3")
        format_model.append("Convertir en FLAC")
        format_row.set_model(format_model)
        
        group.add(format_row)
        
        return group
    
    def _create_bottom_toolbar(self):
        """Crée la barre d'outils du bas"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.add_css_class("bottom-toolbar")
        toolbar.set_margin_top(10)
        toolbar.set_margin_bottom(10)
        toolbar.set_margin_start(20)
        toolbar.set_margin_end(20)
        
        # Navigation
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.prev_button = Gtk.Button()
        self.prev_button.set_icon_name("go-previous-symbolic")
        self.prev_button.set_tooltip_text("Album précédent")
        self.prev_button.connect("clicked", self._on_prev_album)
        nav_box.append(self.prev_button)
        
        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("go-next-symbolic")
        self.next_button.set_tooltip_text("Album suivant")
        self.next_button.connect("clicked", self._on_next_album)
        nav_box.append(self.next_button)
        
        toolbar.append(nav_box)
        
        # Espaceur
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Actions
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        reset_button = Gtk.Button(label="Réinitialiser")
        reset_button.connect("clicked", self._on_reset_clicked)
        actions_box.append(reset_button)
        
        apply_button = Gtk.Button(label="Appliquer les changements")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", self._on_apply_clicked)
        actions_box.append(apply_button)
        
        toolbar.append(actions_box)
        
        return toolbar
    
    def _setup_actions(self):
        """Configure les actions de l'application"""
        # Actions pour la fenêtre d'édition
        action_group = Gio.SimpleActionGroup()
        
        # Action plein écran
        fullscreen_action = Gio.SimpleAction.new("fullscreen", None)
        fullscreen_action.connect("activate", self._on_fullscreen)
        action_group.add_action(fullscreen_action)
        
        self.insert_action_group("edit", action_group)
        
        # Raccourcis clavier
        self.set_accel_for_action("edit.fullscreen", "F11")
    
    def _load_current_album(self):
        """Charge les données de l'album actuel"""
        if not self.albums:
            return
            
        album = self.albums[self.current_album_index]
        
        # Mise à jour des nouveaux champs (12.2)
        self.album_row.set_text(album.title)
        self.artist_row.set_text(album.artist)
        self.year_row.set_text(str(album.year) if album.year else "")
        
        # Genre - trouve l'index dans la liste
        if hasattr(self, 'genre_row') and album.genre:
            model = self.genre_row.get_model()
            for i in range(model.get_n_items()):
                if model.get_string(i) == album.genre:
                    self.genre_row.set_selected(i)
                    break
        
        # Charge le tableau des métadonnées (12.3)
        self._populate_metadata_table()
        
        # Mise à jour du titre de la fenêtre
        if hasattr(self, 'title_widget'):
            self.title_widget.set_subtitle(f"Album {self.current_album_index + 1} sur {len(self.albums)}")
        
        # Mise à jour des boutons de navigation
        if hasattr(self, 'prev_button'):
            self.prev_button.set_sensitive(self.current_album_index > 0)
        if hasattr(self, 'next_button'):
            self.next_button.set_sensitive(self.current_album_index < len(self.albums) - 1)
        
        # Sélection dans la sidebar
        if hasattr(self, 'album_list'):
            self.album_list.select_row(self.album_list.get_row_at_index(self.current_album_index))
    
    # === CALLBACKS ===
    
    def _on_back_clicked(self, button):
        """Retour à la fenêtre principale"""
        self.close()
    
    def _on_save_clicked(self, button):
        """Sauvegarde les modifications"""
        self.app.logger.info("Sauvegarde des modifications")
        # TODO: Implémenter la sauvegarde
    
    def _on_album_selected(self, list_box, row):
        """Album sélectionné dans la sidebar"""
        if row:
            self.current_album_index = row.album_index
            self._load_current_album()
    
    def _on_prev_album(self, button):
        """Album précédent"""
        if self.current_album_index > 0:
            self.current_album_index -= 1
            self._load_current_album()
    
    def _on_next_album(self, button):
        """Album suivant"""
        if self.current_album_index < len(self.albums) - 1:
            self.current_album_index += 1
            self._load_current_album()
    
    def _on_reset_clicked(self, button):
        """Réinitialise les modifications"""
        self._load_current_album()
        self.app.logger.info("Modifications réinitialisées")
    
    def _on_apply_clicked(self, button):
        """Applique les modifications"""
        album = self.albums[self.current_album_index]
        
        # Sauvegarde les modifications
        album.title = self.title_row.get_text()
        album.artist = self.artist_row.get_text()
        album.year = int(self.year_entry.get_text()) if self.year_entry.get_text().isdigit() else None
        album.genre = self.genre_entry.get_text()
        album.has_changes = True
        
        self.app.logger.info(f"Modifications appliquées pour {album.title}")
    
    def _on_fullscreen(self, action, param):
        """Basculer le mode plein écran"""
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()
    
    def _on_add_track(self, button):
        """Ajoute une nouvelle piste"""
        # Trouve le prochain numéro de piste
        next_num = 1
        child = self.tracks_list.get_first_child()
        while child:
            if hasattr(child, 'track_data'):
                next_num = max(next_num, child.track_data.get("num", 0) + 1)
            child = child.get_next_sibling()
        
        # Crée une nouvelle piste
        new_track = {
            "num": next_num,
            "title": "Nouvelle piste",
            "artist": self.artist_row.get_text(),
            "duration": "0:00"
        }
        
        track_row = self._create_track_row(new_track)
        self.tracks_list.append(track_row)
        
        self.app.logger.info(f"Nouvelle piste ajoutée: {next_num}")
    
    def _on_delete_track(self, row):
        """Supprime une piste"""
        if hasattr(row, 'track_data'):
            track_num = row.track_data.get("num", "?")
            self.tracks_list.remove(row)
            self.app.logger.info(f"Piste {track_num} supprimée")
    
    def _on_auto_number_tracks(self, button):
        """Auto-numérotation des pistes"""
        num = 1
        child = self.tracks_list.get_first_child()
        while child:
            if hasattr(child, 'get_child'):
                box = child.get_child()
                if box and hasattr(box, 'get_first_child'):
                    # Trouve l'entry du numéro (premier enfant)
                    num_entry = box.get_first_child()
                    if isinstance(num_entry, Gtk.Entry):
                        num_entry.set_text(str(num))
                        if hasattr(child, 'track_data'):
                            child.track_data["num"] = num
                        num += 1
            child = child.get_next_sibling()
        
        self.app.logger.info("Auto-numérotation appliquée")
    
    def _on_reset_tracks(self, button):
        """Réinitialise la liste des pistes"""
        self._populate_tracks_list()
        self.app.logger.info("Liste des pistes réinitialisée")
    
    # === NOUVEAUX CALLBACKS POUR LE CAHIER DES CHARGES ===
    
    def _on_search_cover_clicked(self, button):
        """11.1.1 - Ouvre la fenêtre de recherche de pochettes"""
        self.app.logger.info("Recherche de pochette demandée")
        # TODO: Implémenter la fenêtre de recherche de pochettes internet
        # Critères: pochettes min 250x250, bouton télécharger
        
    def _on_album_field_changed(self, row, param):
        """11.2.1 - Applique la correction d'album à toutes les pistes"""
        new_album = row.get_text()
        if new_album:
            self._update_all_tracks_field("album", new_album)
            self.app.logger.info(f"Album mis à jour: {new_album}")
    
    def _on_artist_field_changed(self, row, param):
        """11.2.1 - Applique la correction d'artiste à toutes les pistes"""
        new_artist = row.get_text()
        if new_artist:
            self._update_all_tracks_field("artist", new_artist)
            self.app.logger.info(f"Artiste mis à jour: {new_artist}")
    
    def _on_year_field_changed(self, row, param):
        """11.2.1 - Applique la correction d'année à toutes les pistes"""
        new_year = row.get_text()
        if new_year:
            self._update_all_tracks_field("year", new_year)
            self.app.logger.info(f"Année mise à jour: {new_year}")
    
    def _on_genre_field_changed(self, row, param):
        """11.2.1 - Applique la correction de genre à toutes les pistes"""
        selected = row.get_selected()
        if selected != Gtk.INVALID_LIST_POSITION:
            model = row.get_model()
            genre = model.get_string(selected)
            self._update_all_tracks_field("genre", genre)
            self.app.logger.info(f"Genre mis à jour: {genre}")
    
    def _update_all_tracks_field(self, field_name, value):
        """Met à jour un champ pour toutes les pistes du tableau"""
        # Colonne mapping selon 11.3.1
        column_map = {
            "album": 5,    # Album
            "artist": 4,   # Artiste  
            "year": 6,     # Année
            "genre": 8     # Genre
        }
        
        if field_name in column_map:
            col_index = column_map[field_name]
            iter = self.tracks_store.get_iter_first()
            while iter:
                self.tracks_store.set_value(iter, col_index, value)
                iter = self.tracks_store.iter_next(iter)
    
    def _on_title_edited(self, renderer, path, new_text):
        """11.3.4 - Édition du titre en double-clic"""
        iter = self.tracks_store.get_iter(path)
        self.tracks_store.set_value(iter, 2, new_text)  # Colonne Titre
        self.app.logger.info(f"Titre modifié: {new_text}")
    
    def _on_row_activated(self, tree_view, path, column):
        """11.3.5 - Double-clic sur nom de fichier → lecture"""
        if column.get_title() == "Nom de fichier":
            iter = self.tracks_store.get_iter(path)
            filename = self.tracks_store.get_value(iter, 1)
            self._play_track(filename)
            # 11.3.6 - Surligner en bleu
            self._highlight_playing_track(path)
            self.app.logger.info(f"Lecture: {filename}")
    
    def _play_track(self, filename):
        """Lance la lecture d'une piste"""
        # TODO: Implémenter la lecture audio
        self.play_btn.set_icon_name("media-playback-pause-symbolic")
    
    def _highlight_playing_track(self, path):
        """11.3.6 - Surligne la piste en cours en bleu"""
        # TODO: Implémenter le surlignage bleu
        selection = self.tracks_tree.get_selection()
        selection.select_path(path)
    
    # Callbacks lecteur audio
    def _on_prev_track(self, button):
        """11.4.1 - Piste précédente"""
        self.app.logger.info("Piste précédente")
    
    def _on_play_pause(self, button):
        """11.4.1 - Play/Pause"""
        current_icon = button.get_icon_name()
        if current_icon == "media-playback-start-symbolic":
            button.set_icon_name("media-playback-pause-symbolic")
            self.app.logger.info("Lecture")
        else:
            button.set_icon_name("media-playback-start-symbolic")
            self.app.logger.info("Pause")
    
    def _on_stop(self, button):
        """11.4.1 - Stop"""
        self.play_btn.set_icon_name("media-playback-start-symbolic")
        self.progress_scale.set_value(0)
        self.app.logger.info("Stop")
    
    def _on_next_track(self, button):
        """11.4.1 - Piste suivante"""
        self.app.logger.info("Piste suivante")
    
    def _on_progress_changed(self, scale):
        """11.4.2 - Changement de position dans le morceau"""
        position = scale.get_value()
        # TODO: Changer la position de lecture
        # Mettre à jour time_start_label
    
    def _on_eq_changed(self, combo):
        """11.4.3 - Changement de préréglage égaliseur"""
        preset = combo.get_active_text()
        self.app.logger.info(f"Égaliseur: {preset}")
    
    def _populate_metadata_table(self):
        """Remplit le tableau des métadonnées avec les pistes de l'album"""
        self.tracks_store.clear()
        
        if not self.albums or self.current_album_index >= len(self.albums):
            return
        
        album = self.albums[self.current_album_index]
        
        # Données d'exemple selon les colonnes 11.3.1
        sample_tracks = [
            (True, "01 - So What.mp3", "So What", "Miles Davis", "Miles Davis", "Kind of Blue", "1959", "01", "Jazz"),
            (True, "02 - Freddie Freeloader.mp3", "Freddie Freeloader", "Miles Davis", "Miles Davis", "Kind of Blue", "1959", "02", "Jazz"),
            (False, "03 - Blue in Green.mp3", "Blue in Green", "Miles Davis", "Miles Davis", "Kind of Blue", "1959", "03", "Jazz"),
            (True, "04 - All Blues.mp3", "All Blues", "Miles Davis", "Miles Davis", "Kind of Blue", "1959", "04", "Jazz"),
            (True, "05 - Flamenco Sketches.mp3", "Flamenco Sketches", "Miles Davis", "Miles Davis", "Kind of Blue", "1959", "05", "Jazz"),
        ]
        
        for track_data in sample_tracks:
            iter = self.tracks_store.append(track_data + (None,))  # + référence TrackModel
