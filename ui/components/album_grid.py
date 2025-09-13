"""
Grille d'albums moderne et responsive
Composant réutilisable pour afficher les albums avec design épuré
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
from typing import List, Optional, Callable, TYPE_CHECKING
import os

if TYPE_CHECKING:
    from ..views.main_view import MainView

from ..models.album_model import AlbumModel, AlbumStatus

class AlbumCard(Gtk.Box):
    """
    Card moderne pour un album avec design épuré
    Affichage compact avec pochette, métadonnées et statut
    """
    
    def __init__(self, album: AlbumModel, parent_view: 'MainView', on_selection_changed: Optional[Callable] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.album = album
        self.parent_view = parent_view
        self.on_selection_changed = on_selection_changed
        self._is_selected = False
        
        self._setup_ui()
        self._setup_interactions()
        self.add_css_class("album-card")
        
        # Met à jour l'affichage initial
        self._update_selection_style()
    
    def _setup_ui(self):
        """Configure l'interface de la card"""
        
        # === CONTAINER PRINCIPAL ===
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # === SECTION POCHETTE ===
        cover_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            halign=Gtk.Align.CENTER
        )
        
        # Image de pochette (250x250 pour compatibilité pochettes standard)
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(250, 250)
        self.cover_image.add_css_class("album-cover")
        
        # Charge la pochette
        self._load_cover_image()
        
        # Overlay pour la case à cocher et statut
        overlay = Gtk.Overlay()
        overlay.set_child(self.cover_image)
        
        # Case à cocher (en haut à droite)
        self.checkbox = Gtk.CheckButton()
        self.checkbox.set_halign(Gtk.Align.END)
        self.checkbox.set_valign(Gtk.Align.START)
        self.checkbox.set_margin_top(8)
        self.checkbox.set_margin_end(8)
        self.checkbox.add_css_class("selection-checkbox")
        overlay.add_overlay(self.checkbox)
        
        # Badge de statut (en bas à droite)
        self.status_badge = Gtk.Label()
        self.status_badge.set_halign(Gtk.Align.END)
        self.status_badge.set_valign(Gtk.Align.END)
        self.status_badge.set_margin_bottom(8)
        self.status_badge.set_margin_end(8)
        self._update_status_badge()
        overlay.add_overlay(self.status_badge)
        
        cover_container.append(overlay)
        
        # === SECTION INFORMATIONS ===
        info_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4
        )
        info_container.add_css_class("album-info")
        
        # Titre de l'album
        self.title_label = Gtk.Label(
            label=self.album.title,
            halign=Gtk.Align.START,
            ellipsize=3,  # ELLIPSIZE_END
            max_width_chars=25
        )
        self.title_label.add_css_class("album-title")
        
        # Artiste
        self.artist_label = Gtk.Label(
            label=self.album.display_artist,
            halign=Gtk.Align.START,
            ellipsize=3,
            max_width_chars=25
        )
        self.artist_label.add_css_class("album-artist")
        
        # Métadonnées (année, genre, nombre de pistes)
        meta_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8
        )
        meta_box.add_css_class("album-meta")
        
        # Année
        if self.album.year:
            year_label = Gtk.Label(label=self.album.year)
            year_label.add_css_class("meta-year")
            meta_box.append(year_label)
        
        # Nombre de pistes
        tracks_label = Gtk.Label(label=f"{self.album.track_count} pistes")
        tracks_label.add_css_class("meta-tracks")
        meta_box.append(tracks_label)
        
        # Spacer pour pousser le genre à droite
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        meta_box.append(spacer)
        
        # Genre
        if self.album.genre:
            genre_label = Gtk.Label(label=self.album.genre)
            genre_label.add_css_class("meta-genre")
            meta_box.append(genre_label)
        
        # Assemblage des infos
        info_container.append(self.title_label)
        info_container.append(self.artist_label)
        info_container.append(meta_box)
        
        # === SECTION BOUTONS D'ACTION ===
        actions_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            margin_top=8
        )
        actions_container.add_css_class("album-actions")
        
        # Bouton "Créer la playlist"
        self.playlist_button = Gtk.Button(label="Playlist")
        self.playlist_button.add_css_class("suggested-action")
        self.playlist_button.add_css_class("action-button")
        self.playlist_button.set_tooltip_text("Créer la playlist de l'album")
        self.playlist_button.connect("clicked", self._on_create_playlist)
        actions_container.append(self.playlist_button)
        
        # Spacer
        spacer_actions = Gtk.Box()
        spacer_actions.set_hexpand(True)
        actions_container.append(spacer_actions)
        
        # Bouton "Retirer de la liste"
        self.remove_button = Gtk.Button()
        self.remove_button.set_icon_name("user-trash-symbolic")
        self.remove_button.add_css_class("destructive-action")
        self.remove_button.add_css_class("action-button")
        self.remove_button.set_tooltip_text("Retirer de la liste")
        self.remove_button.connect("clicked", self._on_remove_from_list)
        actions_container.append(self.remove_button)
        
        # Assemblage des infos avec boutons
        info_container.append(actions_container)
        
        # Assemblage final
        main_container.append(cover_container)
        main_container.append(info_container)
        
        self.append(main_container)
    
    def _setup_interactions(self):
        """Configure les interactions utilisateur"""
        
        # Gestionnaire de clic pour sélection
        click_controller = Gtk.GestureClick()
        click_controller.connect("pressed", self._on_clicked)
        self.add_controller(click_controller)
        
        # Checkbox pour sélection
        self.checkbox.connect("toggled", self._on_checkbox_toggled)
        
        # Hover effects avec CSS
        self.connect("enter-notify-event", self._on_enter)
        self.connect("leave-notify-event", self._on_leave)
    
    def _load_cover_image(self):
        """Charge l'image de pochette"""
        if self.album.has_cover:
            try:
                # Charge l'image avec GdkPixbuf pour le redimensionnement
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    self.album.cover_path, 200, 200
                )
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.cover_image.set_paintable(texture)
                
            except Exception as e:
                print(f"Erreur lors du chargement de la pochette: {e}")
                self._set_placeholder_cover()
        else:
            self._set_placeholder_cover()
    
    def _set_placeholder_cover(self):
        """Définit une pochette placeholder"""
        # Crée une image placeholder simple
        # TODO: Utiliser une vraie image SVG placeholder
        self.cover_image.set_filename(None)  # Reset
    
    def _update_status_badge(self):
        """Met à jour le badge de statut"""
        status_text = f"{self.album.status_emoji} {self.album.status_text}"
        self.status_badge.set_text(status_text)
        
        # Retire les anciennes classes de statut
        style_context = self.status_badge.get_style_context()
        for status in AlbumStatus:
            style_context.remove_class(f"status-{status.value}")
        
        # Ajoute la classe de statut actuelle
        self.status_badge.add_css_class("status-badge")
        self.status_badge.add_css_class(self.album.status_css_class)
    
    def _update_selection_style(self):
        """Met à jour le style de sélection"""
        if self._is_selected:
            self.add_css_class("selected")
        else:
            self.remove_css_class("selected")
    
    # === CALLBACKS ===
    
    def _on_clicked(self, gesture, n_press, x, y):
        """Gère le clic sur la card"""
        if n_press == 1:  # Simple clic
            self.toggle_selection()
        elif n_press == 2:  # Double clic
            self._on_double_click()
    
    def _on_checkbox_toggled(self, checkbox):
        """Gère le changement de la checkbox"""
        self.set_selected(checkbox.get_active())
    
    def _on_double_click(self):
        """Gère le double clic - ouvre l'édition"""
        # Ouvre la fenêtre d'édition pour cet album
        if hasattr(self.parent_view, 'app'):
            self.parent_view.app.open_album_edit([self.album])
            print(f"Ouverture de l'édition pour: {self.album.title}")
        else:
            print(f"Édition de l'album: {self.album.title} (pas d'app disponible)")
    
    def _on_create_playlist(self, button):
        """Crée une playlist M3U pour l'album"""
        try:
            playlist_path = self.album.create_playlist()
            print(f"Playlist créée: {playlist_path}")
            
            # Notification à l'utilisateur
            if hasattr(self.parent_view, 'show_toast'):
                self.parent_view.show_toast(f"Playlist créée dans le dossier de l'album")
            
        except Exception as e:
            print(f"Erreur lors de la création de la playlist: {e}")
            if hasattr(self.parent_view, 'show_toast'):
                self.parent_view.show_toast(f"Erreur: {e}")
    
    def _on_remove_from_list(self, button):
        """Retire l'album de la liste affichée"""
        # Demande confirmation
        if hasattr(self.parent_view, 'confirm_remove_album'):
            self.parent_view.confirm_remove_album(self.album)
        else:
            print(f"Retrait de l'album: {self.album.title}")
    
    def _on_enter(self, widget, event):
        """Gère l'entrée de la souris"""
        self.add_css_class("hover")
    
    def _on_leave(self, widget, event):
        """Gère la sortie de la souris"""
        self.remove_css_class("hover")
    
    # === MÉTHODES PUBLIQUES ===
    
    def set_selected(self, selected: bool):
        """Définit l'état de sélection"""
        if self._is_selected != selected:
            self._is_selected = selected
            self.checkbox.set_active(selected)
            self._update_selection_style()
            
            if self.on_selection_changed:
                self.on_selection_changed(self.album, selected)
    
    def toggle_selection(self):
        """Inverse l'état de sélection"""
        self.set_selected(not self._is_selected)
    
    @property
    def is_selected(self) -> bool:
        """Retourne l'état de sélection"""
        return self._is_selected
    
    def update_album(self, album: AlbumModel):
        """Met à jour les données de l'album"""
        self.album = album
        
        # Met à jour l'affichage
        self.title_label.set_text(album.title)
        self.artist_label.set_text(album.display_artist)
        self._update_status_badge()
        self._load_cover_image()

class AlbumGrid(Gtk.FlowBox):
    """
    Grille responsive d'albums avec design moderne
    Utilise FlowBox pour un layout automatique et responsive
    """
    
    def __init__(self, parent_view: 'MainView'):
        super().__init__()
        
        self.parent_view = parent_view
        self.albums: List[AlbumModel] = []
        self.album_cards: List[AlbumCard] = []
        
        self._setup_grid()
        self._setup_interactions()
    
    def _setup_grid(self):
        """Configure la grille"""
        # Configuration du FlowBox
        self.set_min_children_per_line(2)
        self.set_max_children_per_line(8)
        self.set_row_spacing(24)
        self.set_column_spacing(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        
        # Sélection
        self.set_selection_mode(Gtk.SelectionMode.NONE)  # Gestion manuelle
        
        # Style
        self.add_css_class("album-grid")
    
    def _setup_interactions(self):
        """Configure les interactions"""
        # Raccourcis clavier
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)
    
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Gère les raccourcis clavier"""
        # Ctrl+A : Sélectionner tout
        if keyval == Gdk.KEY_a and state & Gdk.ModifierType.CONTROL_MASK:
            self.select_all()
            return True
        
        # Escape : Désélectionner tout
        if keyval == Gdk.KEY_Escape:
            self.deselect_all()
            return True
        
        return False
    
    def set_albums(self, albums: List[AlbumModel]):
        """Définit la liste des albums à afficher"""
        # Efface les cards existantes
        self._clear_cards()
        
        self.albums = albums
        self.album_cards = []
        
        # Crée les nouvelles cards
        for album in albums:
            card = AlbumCard(
                album=album,
                parent_view=self.parent_view,
                on_selection_changed=self.parent_view.on_album_selection_changed
            )
            
            self.album_cards.append(card)
            self.append(card)
        
        # Animation d'apparition
        self._animate_cards_in()
    
    def _clear_cards(self):
        """Efface toutes les cards"""
        # Retire tous les enfants
        child = self.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.remove(child)
            child = next_child
    
    def _animate_cards_in(self):
        """Anime l'apparition des cards"""
        for i, card in enumerate(self.album_cards):
            # Délai progressif pour effet cascade
            GLib.timeout_add(i * 50, lambda c=card: c.add_css_class("fade-in"))
    
    def select_all(self):
        """Sélectionne toutes les cards"""
        for card in self.album_cards:
            card.set_selected(True)
    
    def deselect_all(self):
        """Désélectionne toutes les cards"""
        for card in self.album_cards:
            card.set_selected(False)
    
    def get_selected_albums(self) -> List[AlbumModel]:
        """Retourne la liste des albums sélectionnés"""
        return [card.album for card in self.album_cards if card.is_selected]
    
    def get_selected_count(self) -> int:
        """Retourne le nombre d'albums sélectionnés"""
        return len([card for card in self.album_cards if card.is_selected])
    
    def has_selection(self) -> bool:
        """Vérifie s'il y a des albums sélectionnés"""
        return self.get_selected_count() > 0
    
    def remove_album(self, album: AlbumModel):
        """Retire un album de la grille"""
        # Trouve la card correspondante
        card_to_remove = None
        for card in self.album_cards:
            if card.album == album:
                card_to_remove = card
                break
        
        if card_to_remove:
            # Retire de la liste et de l'interface
            self.album_cards.remove(card_to_remove)
            self.remove(card_to_remove)
            
            # Retire de la liste des albums
            if album in self.albums:
                self.albums.remove(album)
            
            print(f"Album retiré: {album.title}")
    
    def update_album_card(self, album: AlbumModel):
        """Met à jour une card d'album spécifique"""
        for card in self.album_cards:
            if card.album == album:
                card.update_album(album)
                break
            card.set_selected(True)
    
    def deselect_all(self):
        """Désélectionne toutes les cards"""
        for card in self.album_cards:
            card.set_selected(False)
    
    def get_selected_albums(self) -> List[AlbumModel]:
        """Retourne la liste des albums sélectionnés"""
        return [card.album for card in self.album_cards if card.is_selected]
    
    def get_selected_count(self) -> int:
        """Retourne le nombre d'albums sélectionnés"""
        return len([card for card in self.album_cards if card.is_selected])
    
    def has_selection(self) -> bool:
        """Vérifie s'il y a des albums sélectionnés"""
        return self.get_selected_count() > 0
    
    def remove_album(self, album: AlbumModel):
        """Retire un album de la grille"""
        # Trouve la card correspondante
        card_to_remove = None
        for card in self.album_cards:
            if card.album == album:
                card_to_remove = card
                break
        
        if card_to_remove:
            # Retire de la liste et de l'interface
            self.album_cards.remove(card_to_remove)
            self.remove(card_to_remove)
            
            # Retire de la liste des albums
            if album in self.albums:
                self.albums.remove(album)
            
            print(f"Album retiré: {album.title}")
    
    def update_album_card(self, album: AlbumModel):
        """Met à jour une card d'album spécifique"""
        for card in self.album_cards:
            if card.album == album:
                card.update_album(album)
                break
