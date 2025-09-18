"""
Composant AlbumCard
Widget représentant une carte d'album dans l'interface
"""

import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Pango, GdkPixbuf, GdkPixbuf
from typing import Dict
import os
from pathlib import Path
import glob

# Import pour lecture métadonnées
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

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
    
    def __init__(self, album_data: Dict, parent_app=None):
        super().__init__()
        self.album_data = album_data
        self.parent_app = parent_app
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
        
        # Affichage de la pochette d'album (vraie image ou placeholder)
        self.cover_widget = self._create_cover_widget()
        cover_frame.add(self.cover_widget)
        
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
        
        # Ligne 2 : Année et titre de l'album (lecture directe du nom de dossier)
        # LOG: Debug pour comprendre le problème de synchronisation
        print(f"🔍 CARD INIT - album_data keys: {list(album_data.keys())}")
        print(f"🔍 CARD INIT - album_data: {album_data}")
        
        folder_path = album_data.get('folder_path', '')
        print(f"🔍 CARD INIT - folder_path: {folder_path}")
        
        if folder_path and os.path.exists(folder_path):
            # Lecture directe du nom du dossier depuis le filesystem
            album_title = os.path.basename(folder_path)
            print(f"✅ CARD INIT - Titre lu depuis filesystem: {album_title}")
        else:
            # Fallback sur les données d'album
            album_title = album_data.get('title', 'Album Inconnu')
            print(f"❌ CARD INIT - Fallback album_data: {album_title}")
        
        print(f"📝 CARD INIT - Texte final: {album_title}")
        
        # Année et titre de l'album
        year_title_text = album_title
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
        try:
            # Récupérer le chemin du dossier de l'album
            folder_path = self.album_data.get('folder_path') or self.album_data.get('path')
            if not folder_path or not os.path.exists(folder_path):
                self._show_error("Dossier de l'album non trouvé")
                return
            
            # Créer la playlist M3U
            playlist_path = self._create_playlist_m3u(folder_path)
            
            if playlist_path:
                album_title = self.album_data.get('title') or self.album_data.get('album', 'Album')
                print(f"✅ Playlist créée: {playlist_path}")
                self._show_success(f"Playlist créée pour '{album_title}'")
            else:
                self._show_error("Impossible de créer la playlist")
                
        except Exception as e:
            print(f"❌ Erreur création playlist: {e}")
            self._show_error(f"Erreur: {str(e)}")
    
    def on_remove_clicked(self, button):
        """Retire cet album de la liste"""
        try:
            album_title = self.album_data.get('title') or self.album_data.get('album', 'Album')
            
            # Retirer de la grille parent directement sans confirmation
            if self.get_parent():
                self.get_parent().remove(self)
                print(f"🗑️ Album retiré: {album_title}")
                self._show_success(f"Album '{album_title}' retiré de la liste")
                    
        except Exception as e:
            print(f"❌ Erreur suppression album: {e}")
            self._show_error(f"Erreur: {str(e)}")
    
    def _create_playlist_m3u(self, folder_path):
        """Crée une playlist M3U avec les fichiers MP3 du dossier"""
        try:
            # Chercher tous les fichiers MP3 dans le dossier
            mp3_files = []
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith('.mp3'):
                    mp3_files.append(file_name)
            
            if not mp3_files:
                raise ValueError("Aucun fichier MP3 trouvé dans le dossier")
            
            # Trier les fichiers par nom
            mp3_files.sort()
            
            # Récupérer l'artiste depuis les données de l'album
            artist = self.album_data.get('artist', 'Artiste Inconnu')
            
            # Récupérer le titre de l'album depuis le nom du dossier (comme affiché dans la carte)
            if folder_path and os.path.exists(folder_path):
                album_folder_name = os.path.basename(folder_path)
            else:
                album_folder_name = self.album_data.get('title') or self.album_data.get('album') or 'Album'
            
            # Construire le nom au format : artiste - titre de l'album (tel qu'affiché)
            playlist_name = f"{artist} - {album_folder_name}"
            
            # Nettoyer le nom de fichier des caractères non autorisés
            safe_name = "".join(c for c in playlist_name if c.isalnum() or c in (' ', '-', '_', '(', ')')).strip()
            playlist_filename = f"{safe_name}.m3u"
            playlist_path = os.path.join(folder_path, playlist_filename)
            
            # Contenu de la playlist
            playlist_content = ["#EXTM3U"]
            
            for mp3_file in mp3_files:
                # Ajouter chaque fichier avec chemin relatif
                playlist_content.append(f"#EXTINF:-1,{mp3_file}")
                playlist_content.append(mp3_file)
            
            # Écrire le fichier playlist
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(playlist_content))
            
            return playlist_path
            
        except Exception as e:
            print(f"❌ Erreur création playlist M3U: {e}")
            return None
    
    def _show_success(self, message):
        """Affiche un message de succès"""
        print(f"✅ {message}")
        # TODO: Implémenter notification toast si disponible
    
    def _show_error(self, message):
        """Affiche un message d'erreur"""
        print(f"❌ {message}")
        # TODO: Implémenter notification toast si disponible
    
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
                            print(f"🔄 UPDATE_DISPLAY appelée pour: {self.album_data.get('path', 'AUCUN_PATH')}")
                            year = self.album_data.get('year', '')
                            
                            # LECTURE DIRECTE DU NOM DE DOSSIER (même logique que __init__)
                            folder_path = self.album_data.get('path', '')
                            print(f"🔍 UPDATE_DISPLAY - folder_path: {folder_path}")
                            
                            if folder_path and os.path.exists(folder_path):
                                album = os.path.basename(folder_path)
                                print(f"✅ UPDATE_DISPLAY - Titre du dossier: {album}")
                            else:
                                album = self.album_data.get('album', 'Album inconnu')
                                print(f"❌ UPDATE_DISPLAY - Fallback album_data: {album}")
                                
                            year_text = f"{year} - " if year else ""
                            final_text = f"📅 {year_text}{album}"
                            print(f"📝 UPDATE_DISPLAY - Texte final: {final_text}")
                            subchild.set_markup(f"<b>{final_text}</b>")
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

    def _create_cover_widget(self):
        """Crée le widget de pochette - vraie image ou placeholder"""
        album_path = self.album_data.get('path') or self.album_data.get('folder_path')
        
        if album_path and os.path.exists(album_path):
            # Chercher une pochette dans le dossier
            cover_path = self._find_cover_file(album_path)
            
            if cover_path and os.path.exists(cover_path):
                # Charger et afficher la vraie pochette
                return self._create_cover_image(cover_path)
        
        # Fallback: placeholder avec emoji
        return self._create_cover_placeholder()
    
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
    
    def _create_cover_image(self, cover_path):
        """Crée un widget Gtk.Image avec la pochette redimensionnée"""
        try:
            # Charger et redimensionner l'image à 300x300
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                cover_path, 300, 300, True
            )
            
            image = Gtk.Image()
            image.set_from_pixbuf(pixbuf)
            return image
            
        except Exception as e:
            print(f"Erreur chargement pochette {cover_path}: {e}")
            return self._create_cover_placeholder()
    
    def _create_cover_placeholder(self):
        """Crée le placeholder coloré avec emoji"""
        cover_label = Gtk.Label()
        cover_label.set_markup(f'<span font="48">{self.album_data.get("emoji", "🎵")}</span>')
        cover_label.get_style_context().add_class(f"cover-{self.album_data.get('color', 'blue')}")
        return cover_label
