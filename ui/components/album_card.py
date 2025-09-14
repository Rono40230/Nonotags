"""
Composant AlbumCard
Widget représentant une carte d'album dans l'interface
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Pango
from typing import Dict

# États visuels des cartes d'albums après traitement automatique
CARD_STATES = {
    'SUCCESS': ('✅', 'Traité avec succès', 'card-success'),
    'ERROR_METADATA': ('🏷️', 'Erreur métadonnées', 'card-error-metadata'),
    'ERROR_FILE': ('📁', 'Erreur fichiers', 'card-error-file'),
    'ERROR_COVER': ('🖼️', 'Erreur pochette', 'card-error-cover'),
    'ERROR_PROCESSING': ('⚠️', 'Erreur traitement', 'card-error-processing')
}


class AlbumCard(Gtk.Frame):
    """Widget représentant une carte d'album"""
    
    def __init__(self, album_data: Dict):
        super().__init__()
        self.album_data = album_data
        self.current_state = 'SUCCESS'  # État par défaut après traitement automatique
        self.status_label = None  # Label pour afficher l'état
        
        self.set_shadow_type(Gtk.ShadowType.OUT)
        self.get_style_context().add_class("album-card")
        self.get_style_context().add_class("album-card-large")  # Nouvelle classe pour forcer la taille
        
                # Taille fixe pour la carte - FORCER avec toutes les méthodes
        self.set_size_request(320, 500)
        self.set_property("width-request", 320)
        self.set_property("height-request", 500)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        
        # Container principal avec taille contrôlée
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        # Forcer la taille du conteneur principal
        vbox.set_size_request(296, 476)  # 320-24 pour les marges
        
        # Case de sélection et indicateur d'état en haut
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_halign(Gtk.Align.FILL)
        
        # Indicateur d'état à gauche
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        self._update_status_display()
        header_box.pack_start(self.status_label, False, False, 0)
        
        # Case de sélection à droite
        self.selection_checkbox = Gtk.CheckButton()
        self.selection_checkbox.set_halign(Gtk.Align.END)
        self.selection_checkbox.connect("toggled", self.on_selection_toggled)
        header_box.pack_end(self.selection_checkbox, False, False, 0)
        
        vbox.pack_start(header_box, False, False, 0)
        
        # Pochette d'album (taille souhaitée 300x300)
        cover_frame = Gtk.Frame()
        cover_frame.set_size_request(300, 300)
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
        edit_btn.set_size_request(200, 32)
        edit_btn.connect("clicked", self.on_edit_clicked)
        button_box.pack_start(edit_btn, False, False, 0)
        
        playlist_btn = Gtk.Button.new_with_label("📋 Créer la playlist")
        playlist_btn.set_size_request(200, 32)
        playlist_btn.connect("clicked", self.on_playlist_clicked)
        button_box.pack_start(playlist_btn, False, False, 0)
        
        remove_btn = Gtk.Button.new_with_label("🗑️ Retirer de la liste")
        remove_btn.set_size_request(200, 32)
        remove_btn.connect("clicked", self.on_remove_clicked)
        button_box.pack_start(remove_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        self.add(vbox)
    
    def on_edit_clicked(self, button):
        """Ouvre la fenêtre d'édition"""
        print(f"✏️ Édition de l'album: {self.album_data.get('album')}")
        # Import local pour éviter les dépendances circulaires
        from ui.views.album_edit_window import AlbumEditWindow
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

    def set_state(self, state: str):
        """Change l'état de la carte et met à jour l'affichage"""
        if state in CARD_STATES:
            old_state = self.current_state
            self.current_state = state
            
            # Supprimer l'ancienne classe CSS
            if old_state in CARD_STATES:
                self.get_style_context().remove_class(CARD_STATES[old_state][2])
            
            # Ajouter la nouvelle classe CSS
            self.get_style_context().add_class(CARD_STATES[state][2])
            
            # Mettre à jour l'affichage du statut
            self._update_status_display()
            
            print(f"🔄 Carte {self.album_data.get('album', 'Inconnu')} : {old_state} → {state}")

    def get_state(self) -> str:
        """Retourne l'état actuel de la carte"""
        return self.current_state

    def _update_status_display(self):
        """Met à jour l'affichage de l'indicateur d'état"""
        if self.status_label and self.current_state in CARD_STATES:
            emoji, text, css_class = CARD_STATES[self.current_state]
            self.status_label.set_markup(f'<span font="12">{emoji}</span>')
            self.status_label.set_tooltip_text(text)
            
            # Supprimer les anciennes classes d'état
            for state_info in CARD_STATES.values():
                self.status_label.get_style_context().remove_class(state_info[2])
            
            # Ajouter la classe CSS correspondante
            self.status_label.get_style_context().add_class(css_class)
