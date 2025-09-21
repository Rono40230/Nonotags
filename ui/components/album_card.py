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

# Import du gestionnaire d'événements
from services.metadata_event_manager import metadata_event_manager

class AlbumCard(Gtk.Frame):
    """Widget représentant une carte d'album"""
    
    def __init__(self, album_data: Dict, parent_app=None):
        super().__init__()
        self.album_data = album_data
        self.parent_app = parent_app
        
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
        
        # Case de sélection en haut à droite
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_halign(Gtk.Align.FILL)
        
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
        
        # Ligne 2 : Titre = nom du dossier (SIMPLE)
        folder_path = album_data.get('folder_path') or album_data.get('path')
        album_title = os.path.basename(folder_path) if folder_path else album_data.get('album', 'Album Inconnu')
        
        # Le titre = nom du dossier, point final
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
        
        # S'enregistrer comme observateur pour les changements de métadonnées
        self._register_metadata_observer()
    
    def _register_metadata_observer(self):
        """Enregistre cette card comme observateur des changements de métadonnées"""
        album_path = self.album_data.get('folder_path') or self.album_data.get('path', '')
        if album_path:
            metadata_event_manager.register_observer(album_path, self._on_metadata_changed)
    
    def _on_metadata_changed(self, updated_metadata=None):
        """Callback appelé quand les métadonnées de cet album changent"""
        try:
            # Mettre à jour les données si fournies
            if updated_metadata:
                self.album_data.update(updated_metadata)
            
            # Rafraîchir l'affichage
            self._update_display()
            self.refresh_cover()
            
            album_name = os.path.basename(self.album_data.get('folder_path', ''))
            print(f"🔄 Card auto-rafraîchie: {album_name}")
        except Exception as e:
            print(f"❌ Erreur auto-rafraîchissement card: {e}")
    
    def __del__(self):
        """Destructeur pour nettoyer l'observateur"""
        try:
            album_path = self.album_data.get('folder_path') or self.album_data.get('path', '')
            if album_path:
                metadata_event_manager.unregister_observer(album_path, self._on_metadata_changed)
        except:
            pass  # Ignorer les erreurs lors de la destruction
    
    def on_edit_clicked(self, button):
        """Ouvre la fenêtre d'édition"""
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
            
            # Notifier l'application parent pour supprimer des structures de données
            if self.parent_app and hasattr(self.parent_app, 'remove_album_from_list'):
                self.parent_app.remove_album_from_list(self.album_data)
            
            # Retirer de la grille parent directement
            if self.get_parent():
                self.get_parent().remove(self)
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
        try:
            # RECHARGER les métadonnées depuis les fichiers au lieu d'utiliser les anciennes données
            folder_path = self.album_data.get('folder_path') or self.album_data.get('path', '')
            if folder_path and os.path.exists(folder_path):
                # Recharger les métadonnées depuis le premier fichier audio du dossier
                audio_files = [f for f in os.listdir(folder_path) 
                              if f.lower().endswith(('.mp3', '.flac', '.m4a', '.mp4'))]
                
                if audio_files:
                    first_file = os.path.join(folder_path, audio_files[0])
                    fresh_metadata = self._load_metadata_from_file(first_file)
                    
                    # Mettre à jour album_data avec les nouvelles métadonnées
                    self.album_data.update(fresh_metadata)
                    print(f"🔄 Métadonnées rechargées depuis: {audio_files[0]}")
        
            # Parcourir la hiérarchie pour trouver les labels
            for child in self.get_children():
                if isinstance(child, Gtk.Box):
                    for box_child in child.get_children():
                        if isinstance(box_child, Gtk.Box):  # Info box
                            labels = [w for w in box_child.get_children() if isinstance(w, Gtk.Label)]
                            if len(labels) >= 3:  # Artiste + Titre + Genre (minimum)
                                # Label 0 : Artiste
                                artist_label = labels[0]
                                new_artist = self.album_data.get("artist", "Artiste Inconnu")
                                artist_label.set_markup(f'<b>{new_artist}</b>')
                                print(f"✅ Artiste mis à jour: {new_artist}")
                                
                                # Label 1 : Titre (nom du dossier)
                                title_label = labels[1]
                                folder_path = self.album_data.get('folder_path') or self.album_data.get('path')
                                new_title = os.path.basename(folder_path) if folder_path else self.album_data.get('album', 'Album Inconnu')
                                title_label.set_text(new_title)
                                print(f"✅ Titre mis à jour: {new_title}")
                                
                                # Label 2 : Genre
                                genre_label = labels[2]
                                new_genre = self.album_data.get("genre", "Genre inconnu")
                                genre_label.set_text(new_genre)
                                print(f"✅ Genre mis à jour: {new_genre}")
                                
                                # Label 3 (optionnel) : Nombre de pistes
                                if len(labels) >= 4:
                                    tracks_label = labels[3]
                                    tracks_count = self.album_data.get('tracks', 0)
                                    tracks_label.set_text(f"{tracks_count} pistes")
                                    print(f"✅ Pistes mises à jour: {tracks_count}")
                                
                                return
        except Exception as e:
            print(f"❌ Erreur mise à jour affichage: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_metadata_from_file(self, file_path):
        """Charge les métadonnées depuis un fichier audio"""
        try:
            from mutagen.id3 import ID3
            from mutagen.mp3 import MP3
            from mutagen.mp4 import MP4
            from mutagen.flac import FLAC
            
            metadata = {}
            
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path, ID3=ID3)
                if audio.tags:
                    metadata['artist'] = str(audio.tags.get('TPE1', [''])[0]) if audio.tags.get('TPE1') else ''
                    metadata['album'] = str(audio.tags.get('TALB', [''])[0]) if audio.tags.get('TALB') else ''
                    metadata['genre'] = str(audio.tags.get('TCON', [''])[0]) if audio.tags.get('TCON') else ''
                    metadata['year'] = str(audio.tags.get('TDRC', [''])[0]) if audio.tags.get('TDRC') else ''
                    
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                if audio.tags:
                    metadata['artist'] = audio.get('ARTIST', [''])[0] if audio.get('ARTIST') else ''
                    metadata['album'] = audio.get('ALBUM', [''])[0] if audio.get('ALBUM') else ''
                    metadata['genre'] = audio.get('GENRE', [''])[0] if audio.get('GENRE') else ''
                    metadata['year'] = audio.get('DATE', [''])[0] if audio.get('DATE') else ''
                    
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                audio = MP4(file_path)
                if audio.tags:
                    metadata['artist'] = audio.get('\xa9ART', [''])[0] if audio.get('\xa9ART') else ''
                    metadata['album'] = audio.get('\xa9alb', [''])[0] if audio.get('\xa9alb') else ''
                    metadata['genre'] = audio.get('\xa9gen', [''])[0] if audio.get('\xa9gen') else ''
                    metadata['year'] = str(audio.get('\xa9day', [''])[0]) if audio.get('\xa9day') else ''
            
            return metadata
            
        except Exception as e:
            print(f"❌ Erreur chargement métadonnées: {e}")
            return {}
    
    def update_folder_path(self, new_folder_path: str):
        """Met à jour le chemin du dossier après renommage et rafraîchit l'affichage"""
        old_path = self.album_data.get('folder_path', '')
        print(f"🔄 Mise à jour chemin dossier: {old_path} → {new_folder_path}")
        
        # Mettre à jour les données de l'album
        self.album_data['folder_path'] = new_folder_path
        
        # Rafraîchir l'affichage pour montrer le nouveau nom
        self._update_display()
        
        print(f"✅ Carte mise à jour avec nouveau chemin: {new_folder_path}")
    
    def refresh_cover(self):
        """Met à jour la pochette de la carte après téléchargement"""
        try:
            # Trouver le frame qui contient la pochette
            for child in self.get_children():
                if isinstance(child, Gtk.Box):
                    for box_child in child.get_children():
                        if isinstance(box_child, Gtk.Frame):  # Cover frame
                            # Supprimer l'ancien widget
                            old_cover = box_child.get_child()
                            if old_cover:
                                box_child.remove(old_cover)
                            
                            # Créer le nouveau widget pochette
                            new_cover = self._create_cover_widget()
                            box_child.add(new_cover)
                            box_child.show_all()
                            
                            print(f"🔄 Pochette de carte rafraîchie")
                            return True
            
            print(f"⚠️ Frame pochette introuvable")
            return False
            
        except Exception as e:
            print(f"❌ Erreur rafraîchissement pochette: {e}")
            return False
    
    def update_cover(self):
        """Met à jour la pochette de la carte après téléchargement d'une nouvelle pochette"""
        try:
            # Récupérer le frame qui contient la pochette
            for child in self.get_children():
                if isinstance(child, Gtk.Box):
                    for box_child in child.get_children():
                        if isinstance(box_child, Gtk.Frame):  # Cover frame
                            # Supprimer l'ancien widget de pochette
                            old_cover = box_child.get_child()
                            if old_cover:
                                box_child.remove(old_cover)
                            
                            # Créer et ajouter la nouvelle pochette
                            new_cover_widget = self._create_cover_widget()
                            box_child.add(new_cover_widget)
                            box_child.show_all()
                            
                            print(f"✅ Pochette de carte mise à jour")
                            return True
            
            print(f"⚠️ Frame de pochette non trouvé pour mise à jour")
            return False
            
        except Exception as e:
            print(f"❌ Erreur mise à jour pochette carte: {e}")
            return False
    
    def on_selection_toggled(self, checkbox):
        """Gère la sélection/déselection de l'album"""
        is_selected = checkbox.get_active()
        album_title = self.album_data.get('album', 'Album Sans Titre')
        if is_selected:
            print(f"✅ Album sélectionné: {album_title}")
        else:
            print(f"❌ Album désélectionné: {album_title}")

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