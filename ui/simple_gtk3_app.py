"""
Application Nonotags simple avec GTK3
Interface moderne adaptée pour la compatibilité GTK3
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf, Pango, GLib
import os
from typing import List, Dict

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
        year_title_text = f"{album_data.get('year', '----')} - {album_data.get('title', 'Album Sans Titre')}"
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
        edit_btn.set_size_request(180, 32)  # Largeur fixe, hauteur réduite
        edit_btn.connect("clicked", self.on_edit_clicked)
        button_box.pack_start(edit_btn, False, False, 0)
        
        playlist_btn = Gtk.Button.new_with_label("📋 Créer la playlist")
        playlist_btn.set_size_request(180, 32)  # Largeur fixe, hauteur réduite
        playlist_btn.connect("clicked", self.on_playlist_clicked)
        button_box.pack_start(playlist_btn, False, False, 0)
        
        remove_btn = Gtk.Button.new_with_label("🗑️ Retirer de la liste")
        remove_btn.set_size_request(180, 32)  # Largeur fixe, hauteur réduite
        remove_btn.connect("clicked", self.on_remove_clicked)
        button_box.pack_start(remove_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        self.add(vbox)
    
    def on_edit_clicked(self, button):
        """Ouvre la fenêtre d'édition"""
        print(f"✏️ Édition de l'album: {self.album_data.get('title')}")
        edit_window = AlbumEditWindow(self.album_data)
        edit_window.show_all()
    
    def on_playlist_clicked(self, button):
        """Crée une playlist avec cet album"""
        print(f"📋 Création de playlist: {self.album_data.get('title')}")
    
    def on_remove_clicked(self, button):
        """Retire l'album de la liste"""
        print(f"🗑️ Retrait de la liste: {self.album_data.get('title')}")
        # Ici on peut ajouter la logique pour retirer l'album de la liste
    
    def on_selection_toggled(self, checkbox):
        """Gère la sélection/déselection de l'album"""
        is_selected = checkbox.get_active()
        album_title = self.album_data.get('title', 'Album Sans Titre')
        if is_selected:
            print(f"✅ Album sélectionné: {album_title}")
        else:
            print(f"❌ Album désélectionné: {album_title}")
        # Ici on peut ajouter la logique pour gérer la sélection multiple

class AlbumEditWindow(Gtk.Window):
    """Fenêtre d'édition d'album selon le cahier des charges"""
    
    def __init__(self, album_data: Dict):
        super().__init__()
        self.album_data = album_data
        self.set_title(f"Édition - {album_data.get('title', 'Album')}")
        self.set_default_size(1000, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Container principal avec marges
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        
        # Titre de la fenêtre
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">📝 Édition d\'Album - 4 Blocs</span>')
        title_label.get_style_context().add_class("title-label")
        main_box.pack_start(title_label, False, False, 0)
        
        # BLOCS SUPÉRIEURS (12.1 + 12.2)
        top_box = Gtk.Box(spacing=20)
        
        # 12.1 - BLOC POCHETTE (haut gauche)
        cover_frame = Gtk.Frame()
        cover_frame.set_label("12.1 - Pochette de l'album")
        cover_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        cover_vbox.set_margin_left(15)
        cover_vbox.set_margin_right(15)
        cover_vbox.set_margin_top(15)
        cover_vbox.set_margin_bottom(15)
        
        # Pochette 250x250
        cover_placeholder = Gtk.Frame()
        cover_placeholder.set_size_request(250, 250)
        cover_placeholder.set_halign(Gtk.Align.CENTER)
        cover_label = Gtk.Label()
        cover_label.set_markup(f'<span font="72">{album_data.get("emoji", "🎵")}</span>')
        cover_placeholder.add(cover_label)
        cover_vbox.pack_start(cover_placeholder, False, False, 0)
        
        # Bouton chercher pochette
        search_btn = Gtk.Button.new_with_label("🔍 Chercher une pochette")
        search_btn.get_style_context().add_class("modern-button")
        cover_vbox.pack_start(search_btn, False, False, 0)
        
        cover_frame.add(cover_vbox)
        top_box.pack_start(cover_frame, False, False, 0)
        
        # 12.2 - BLOC CHAMPS DE SAISIE (haut droite)
        fields_frame = Gtk.Frame()
        fields_frame.set_label("12.2 - Champs de saisie (applique à toutes les pistes)")
        fields_grid = Gtk.Grid()
        fields_grid.set_margin_left(15)
        fields_grid.set_margin_right(15)
        fields_grid.set_margin_top(15)
        fields_grid.set_margin_bottom(15)
        fields_grid.set_row_spacing(10)
        fields_grid.set_column_spacing(10)
        
        # Champ Album
        fields_grid.attach(Gtk.Label(label="Album:"), 0, 0, 1, 1)
        album_entry = Gtk.Entry()
        album_entry.set_text(album_data.get("title", ""))
        album_entry.set_hexpand(True)
        fields_grid.attach(album_entry, 1, 0, 1, 1)
        
        # Champ Artiste
        fields_grid.attach(Gtk.Label(label="Artiste:"), 0, 1, 1, 1)
        artist_entry = Gtk.Entry()
        artist_entry.set_text(album_data.get("artist", ""))
        artist_entry.set_hexpand(True)
        fields_grid.attach(artist_entry, 1, 1, 1, 1)
        
        # Champ Année
        fields_grid.attach(Gtk.Label(label="Année:"), 0, 2, 1, 1)
        year_entry = Gtk.Entry()
        year_entry.set_text(str(album_data.get("year", "")))
        year_entry.set_hexpand(True)
        fields_grid.attach(year_entry, 1, 2, 1, 1)
        
        # Menu Genre
        fields_grid.attach(Gtk.Label(label="Genre:"), 0, 3, 1, 1)
        genre_combo = Gtk.ComboBoxText()
        genres = ["Jazz", "Rock", "Pop", "Blues", "Acid Jazz", "B.O. de Films", 
                 "Chansons Française", "Disco", "Electronique", "Flamenco"]
        for genre in genres:
            genre_combo.append_text(genre)
        genre_combo.set_active_id(album_data.get("genre", "Jazz"))
        genre_combo.set_hexpand(True)
        fields_grid.attach(genre_combo, 1, 3, 1, 1)
        
        fields_frame.add(fields_grid)
        top_box.pack_start(fields_frame, True, True, 0)
        
        main_box.pack_start(top_box, False, False, 0)
        
        # 12.3 - BLOC TABLEAU MÉTADONNÉES
        table_frame = Gtk.Frame()
        table_frame.set_label("12.3 - Tableau des métadonnées (tri, double-clic édition)")
        
        # ScrolledWindow pour le tableau
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        # TreeView avec colonnes
        liststore = Gtk.ListStore(str, str, str, str, str, str, str, str, str)
        treeview = Gtk.TreeView(model=liststore)
        
        # Colonnes selon 11.3.1
        columns = [
            ("Cover", 60), ("Nom fichier", 200), ("Titre", 150), ("Interprète", 120),
            ("Artiste", 120), ("Album", 120), ("Année", 80), ("N° piste", 80), ("Genre", 100)
        ]
        
        for i, (title, width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_min_width(width)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            treeview.append_column(column)
        
        # Données d'exemple
        sample_tracks = [
            ("✅", "01 - So What.mp3", "So What", "Miles Davis", "Miles Davis", album_data.get("title", ""), str(album_data.get("year", "")), "01", album_data.get("genre", "")),
            ("✅", "02 - Freddie Freeloader.mp3", "Freddie Freeloader", "Miles Davis", "Miles Davis", album_data.get("title", ""), str(album_data.get("year", "")), "02", album_data.get("genre", "")),
            ("❌", "03 - Blue in Green.mp3", "Blue in Green", "Miles Davis", "Miles Davis", album_data.get("title", ""), str(album_data.get("year", "")), "03", album_data.get("genre", ""))
        ]
        
        for track in sample_tracks:
            liststore.append(track)
        
        scrolled.add(treeview)
        table_frame.add(scrolled)
        main_box.pack_start(table_frame, True, True, 0)
        
        # 12.4 - BLOC LECTEUR AUDIO
        player_frame = Gtk.Frame()
        player_frame.set_label("12.4 - Lecteur audio complet")
        player_hbox = Gtk.Box(spacing=20)
        player_hbox.set_margin_left(15)
        player_hbox.set_margin_right(15)
        player_hbox.set_margin_top(15)
        player_hbox.set_margin_bottom(15)
        
        # Contrôles
        controls_box = Gtk.Box(spacing=5)
        controls = ["⏮️", "▶️", "⏹️", "⏭️"]
        for control in controls:
            btn = Gtk.Button.new_with_label(control)
            if control == "▶️":
                btn.get_style_context().add_class("modern-button")
            controls_box.pack_start(btn, False, False, 0)
        player_hbox.pack_start(controls_box, False, False, 0)
        
        # Progression
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(0.35)
        progress_bar.set_hexpand(True)
        progress_box.pack_start(progress_bar, False, False, 0)
        
        time_box = Gtk.Box()
        time_box.pack_start(Gtk.Label(label="3:15"), False, False, 0)
        time_box.pack_end(Gtk.Label(label="9:22"), False, False, 0)
        progress_box.pack_start(time_box, False, False, 0)
        
        player_hbox.pack_start(progress_box, True, True, 0)
        
        # Égaliseur
        eq_box = Gtk.Box(spacing=10)
        eq_box.pack_start(Gtk.Label(label="EQ:"), False, False, 0)
        eq_combo = Gtk.ComboBoxText()
        eq_presets = ["Flat", "Rock", "Pop", "Jazz", "Classical", "Electronic", "Hip-Hop", "Vocal", "Bass Boost", "Treble Boost"]
        for preset in eq_presets:
            eq_combo.append_text(preset)
        eq_combo.set_active(0)
        eq_box.pack_start(eq_combo, False, False, 0)
        player_hbox.pack_start(eq_box, False, False, 0)
        
        player_frame.add(player_hbox)
        main_box.pack_start(player_frame, False, False, 0)
        
        # Boutons d'action
        action_box = Gtk.Box()
        action_box.set_halign(Gtk.Align.END)
        apply_btn = Gtk.Button.new_with_label("Appliquer les changements")
        apply_btn.get_style_context().add_class("modern-button")
        action_box.pack_start(apply_btn, False, False, 0)
        main_box.pack_start(action_box, False, False, 0)
        
        self.add(main_box)

class SimpleNonotagsApp:
    """Application Nonotags simplifiée avec GTK3"""
    
    def __init__(self):
        self.window = None
        self.albums = self._get_sample_albums()
    
    def _get_sample_albums(self) -> List[Dict]:
        """Retourne des albums d'exemple pour la démonstration"""
        return [
            {
                "title": "Kind of Blue",
                "artist": "Miles Davis", 
                "year": 1959,
                "tracks": 5,
                "genre": "Jazz",
                "emoji": "🎺",
                "color": "blue"
            },
            {
                "title": "The Dark Side of the Moon",
                "artist": "Pink Floyd",
                "year": 1973,
                "tracks": 10,
                "genre": "Progressive Rock",
                "emoji": "🌙",
                "color": "purple"
            },
            {
                "title": "Abbey Road",
                "artist": "The Beatles",
                "year": 1969,
                "tracks": 17,
                "genre": "Rock",
                "emoji": "🎸",
                "color": "green"
            },
            {
                "title": "Thriller",
                "artist": "Michael Jackson",
                "year": 1982,
                "tracks": 9,
                "genre": "Pop",
                "emoji": "🕺",
                "color": "red"
            },
            {
                "title": "Random Access Memories",
                "artist": "Daft Punk",
                "year": 2013,
                "tracks": 13,
                "genre": "Electronic",
                "emoji": "🤖",
                "color": "orange"
            },
            {
                "title": "OK Computer",
                "artist": "Radiohead",
                "year": 1997,
                "tracks": 12,
                "genre": "Alternative Rock",
                "emoji": "💾",
                "color": "gray"
            }
        ]
    
    def create_window(self):
        """Crée la fenêtre principale"""
        self.window = Gtk.Window()
        self.window.set_title("🎵 Nonotags - Gestionnaire de Métadonnées MP3")
        self.window.set_default_size(1200, 800)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Container principal avec ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
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
        self.albums_grid.set_halign(Gtk.Align.CENTER)
        self.albums_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.albums_grid.set_homogeneous(True)
        self.albums_grid.set_row_spacing(20)
        self.albums_grid.set_column_spacing(20)
        
        # Ajout des cartes d'albums directement
        for album in self.albums:
            card = AlbumCard(album)
            self.albums_grid.add(card)
        
        main_box.pack_start(self.albums_grid, True, True, 0)
        
        # Calcul initial du nombre de cartes par ligne
        self.update_cards_per_line()
        
        # Connexion pour mise à jour dynamique lors du redimensionnement
        self.window.connect("size-allocate", self.on_window_resize)
        
        # Pied de page avec statistiques
        stats_box = Gtk.Box()
        stats_box.set_halign(Gtk.Align.CENTER)
        stats_label = Gtk.Label()
        stats_label.set_markup(f'<span color="#64748b">📊 {len(self.albums)} albums • Interface moderne GTK3 • Design épuré</span>')
        stats_box.pack_start(stats_label, False, False, 0)
        main_box.pack_start(stats_box, False, False, 0)
        
        scrolled.add(main_box)
        self.window.add(scrolled)
    
    def on_scan_clicked(self, button):
        """Gestion du scan de dossiers"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier à scanner",
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
            print(f"📁 Scan du dossier: {folder}")
            # Ici on peut ajouter la logique de scan
        
        dialog.destroy()
    
    def on_import_clicked(self, button):
        """Gestion de l'import de fichiers"""
        dialog = Gtk.FileChooserDialog(
            title="Importer des fichiers MP3",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            "Annuler", Gtk.ResponseType.CANCEL,
            "Importer", Gtk.ResponseType.OK
        )
        dialog.set_select_multiple(True)
        
        # Filtre pour les fichiers MP3
        filter_mp3 = Gtk.FileFilter()
        filter_mp3.set_name("Fichiers MP3")
        filter_mp3.add_pattern("*.mp3")
        dialog.add_filter(filter_mp3)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            print(f"📂 Import de {len(files)} fichiers MP3")
            # Ici on peut ajouter la logique d'import
        
        dialog.destroy()
    
    def on_settings_clicked(self, button):
        """Ouvre la fenêtre des paramètres"""
        settings_dialog = Gtk.Dialog(
            title="⚙️ Paramètres Nonotags",
            parent=self.window,
            modal=True
        )
        settings_dialog.add_buttons(
            "Annuler", Gtk.ResponseType.CANCEL,
            "Appliquer", Gtk.ResponseType.OK
        )
        settings_dialog.set_size_request(400, 300)
        
        content = settings_dialog.get_content_area()
        content.set_margin_left(20)
        content.set_margin_right(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        settings_grid = Gtk.Grid()
        settings_grid.set_row_spacing(10)
        settings_grid.set_column_spacing(10)
        
        # Option auto-scan
        settings_grid.attach(Gtk.Label(label="Auto-scan au démarrage:"), 0, 0, 1, 1)
        auto_scan_switch = Gtk.Switch()
        settings_grid.attach(auto_scan_switch, 1, 0, 1, 1)
        
        # Dossier par défaut
        settings_grid.attach(Gtk.Label(label="Dossier musique par défaut:"), 0, 1, 1, 1)
        folder_btn = Gtk.FileChooserButton(title="Choisir le dossier")
        folder_btn.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        settings_grid.attach(folder_btn, 1, 1, 1, 1)
        
        content.pack_start(settings_grid, True, True, 0)
        settings_dialog.show_all()
        
        response = settings_dialog.run()
        if response == Gtk.ResponseType.OK:
            print("⚙️ Paramètres sauvegardés")
        
        settings_dialog.destroy()
    
    def on_edit_selection_clicked(self, button):
        """Ouvre l'édition groupée pour les albums sélectionnés"""
        # Collecter tous les albums sélectionnés
        selected_albums = []
        
        # Parcourir toutes les cartes d'albums pour trouver celles sélectionnées
        for child in self.albums_grid.get_children():
            if hasattr(child, 'selection_checkbox') and child.selection_checkbox.get_active():
                selected_albums.append(child.album_data)
        
        if not selected_albums:
            # Afficher un message si aucun album n'est sélectionné
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
        
        # Ouvrir la fenêtre d'édition groupée
        print(f"✏️ Édition groupée de {len(selected_albums)} album(s) sélectionné(s)")
        for album in selected_albums:
            print(f"   - {album.get('artist', 'Artiste')} - {album.get('title', 'Titre')}")
        
        # TODO: Implémenter la fenêtre d'édition groupée
        # edit_group_window = AlbumGroupEditWindow(selected_albums)
        # edit_group_window.show_all()
    
    def calculate_cards_per_line(self, window_width=None):
        """Calcule le nombre optimal de cartes par ligne selon la largeur disponible"""
        if window_width is None:
            if hasattr(self, 'window') and self.window:
                window_width = self.window.get_allocated_width()
            else:
                # Valeur par défaut si la fenêtre n'est pas encore créée
                window_width = 1200
        
        # Constantes pour le calcul
        CARD_WIDTH = 290  # Largeur d'une carte
        CARD_SPACING = 20  # Espacement entre cartes
        WINDOW_MARGINS = 40  # Marges de la fenêtre (20 de chaque côté)
        
        # Largeur disponible pour les cartes
        available_width = window_width - WINDOW_MARGINS
        
        # Largeur totale nécessaire par carte (carte + espacement)
        total_card_width = CARD_WIDTH + CARD_SPACING
        
        # Calcul du nombre de cartes qui rentrent
        cards_per_line = max(1, available_width // total_card_width)
        
        # Limiter à un maximum raisonnable (pour éviter des cartes trop petites sur très grands écrans)
        cards_per_line = min(cards_per_line, 8)
        
        return int(cards_per_line)
    
    def update_cards_per_line(self):
        """Met à jour le nombre de cartes par ligne dans la grille"""
        if hasattr(self, 'albums_grid') and self.albums_grid:
            cards_per_line = self.calculate_cards_per_line()
            self.albums_grid.set_max_children_per_line(cards_per_line)
            self.albums_grid.set_min_children_per_line(1)
            
            # Debug: afficher le calcul
            window_width = self.window.get_allocated_width() if hasattr(self, 'window') and self.window else 1200
            print(f"📐 Largeur fenêtre: {window_width}px → {cards_per_line} cartes par ligne")
    
    def on_window_resize(self, widget, allocation):
        """Callback appelé lors du redimensionnement de la fenêtre"""
        # Eviter les calculs répétitifs pendant le redimensionnement
        if not hasattr(self, '_resize_timeout'):
            self._resize_timeout = None
        
        if self._resize_timeout:
            GLib.source_remove(self._resize_timeout)
        
        # Délai de 100ms pour éviter trop de recalculs pendant le redimensionnement
        self._resize_timeout = GLib.timeout_add(100, self._delayed_resize_update)
    
    def _delayed_resize_update(self):
        """Mise à jour différée du layout après redimensionnement"""
        self.update_cards_per_line()
        self._resize_timeout = None
        return False  # Ne pas répéter le timeout
    
    def run(self):
        """Lance l'application"""
        self.create_window()
        self.window.show_all()
        
        print("✅ Application Nonotags démarrée avec succès!")
        print("📱 Interface moderne et épurée prête")
        print("🎨 Design conforme au cahier des charges")
        
        Gtk.main()
