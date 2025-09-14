#!/usr/bin/env python3
"""
Version de l'UI moderne compatible GTK3
Interface épurée et moderne adaptée pour la compatibilité
"""

import sys
import os

# Ajoute le chemin du projet
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import gi

# Essaie GTK4, puis fallback sur GTK3
try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw
    GTK_VERSION = 4
    print("🚀 Utilisation de GTK4 + Libadwaita")
except ValueError:
    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        GTK_VERSION = 3
        print("🔄 Fallback sur GTK3 (interface adaptée)")
        # Adw n'est pas disponible avec GTK3
        Adw = None
    except ValueError:
        print("❌ Aucune version de GTK disponible")
        sys.exit(1)

from gi.repository import GLib, Gdk, GdkPixbuf, Gio
import tempfile
import shutil

# Import des modèles
from ui.models.album_model import AlbumModel, AlbumStatus

class ModernWindow(Gtk.ApplicationWindow):
    """
    Fenêtre moderne compatible GTK3/GTK4
    Interface épurée et intuitive
    """
    
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_title("Nonotags - Gestionnaire MP3 Moderne")
        self.set_default_size(1200, 800)
        
        # Données de démo
        self.albums = self._create_demo_albums()
        self.selected_albums = []
        
        self._setup_ui()
        self._load_css()
        
        print(f"✨ Interface moderne initialisée avec {len(self.albums)} albums de démo")
    
    def _setup_ui(self):
        """Configure l'interface moderne"""
        
        # Container principal
        if GTK_VERSION == 4:
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.set_child(main_box)
        else:
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.add(main_box)
        
        # Header bar moderne
        if GTK_VERSION == 4:
            header_bar = Gtk.HeaderBar()
            header_bar.set_title_widget(Gtk.Label(label="Nonotags"))
        else:
            header_bar = Gtk.HeaderBar()
            header_bar.set_title("Nonotags")
            header_bar.set_subtitle("Gestionnaire MP3 moderne")
        
        # Boutons header
        import_button = Gtk.Button(label="📁 Importer")
        if hasattr(import_button, 'add_css_class'):
            import_button.add_css_class("suggested-action")
        
        menu_button = Gtk.Button(label="☰")
        
        if GTK_VERSION == 4:
            header_bar.pack_start(import_button)
            header_bar.pack_end(menu_button)
        else:
            header_bar.pack_start(import_button)
            header_bar.pack_end(menu_button)
        
        self.set_titlebar(header_bar)
        
        # Barre d'outils
        toolbar = self._create_toolbar()
        main_box.append(toolbar) if GTK_VERSION == 4 else main_box.pack_start(toolbar, False, False, 0)
        
        # Zone de contenu
        scrolled = Gtk.ScrolledWindow()
        if GTK_VERSION == 4:
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        else:
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Grille d'albums
        self.album_grid = self._create_album_grid()
        scrolled.set_child(self.album_grid) if GTK_VERSION == 4 else scrolled.add(self.album_grid)
        
        main_box.append(scrolled) if GTK_VERSION == 4 else main_box.pack_start(scrolled, True, True, 0)
        
        # Barre de statut
        status_bar = self._create_status_bar()
        main_box.append(status_bar) if GTK_VERSION == 4 else main_box.pack_start(status_bar, False, False, 0)
    
    def _create_toolbar(self):
        """Crée la barre d'outils moderne"""
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        if hasattr(toolbar_box, 'set_margin_start'):
            toolbar_box.set_margin_start(12)
            toolbar_box.set_margin_end(12)
            toolbar_box.set_margin_top(8)
            toolbar_box.set_margin_bottom(8)
        else:
            toolbar_box.set_margin_left(12)
            toolbar_box.set_margin_right(12)
            toolbar_box.set_margin_top(8)
            toolbar_box.set_margin_bottom(8)
        
        # Titre de la section
        section_label = Gtk.Label()
        section_label.set_markup("<b>Albums importés</b>")
        
        # Label de sélection
        self.selection_label = Gtk.Label(label="6 albums")
        
        # Assemblage
        toolbar_box.append(section_label) if GTK_VERSION == 4 else toolbar_box.pack_start(section_label, False, False, 0)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar_box.append(spacer) if GTK_VERSION == 4 else toolbar_box.pack_start(spacer, True, True, 0)
        
        toolbar_box.append(self.selection_label) if GTK_VERSION == 4 else toolbar_box.pack_start(self.selection_label, False, False, 0)
        
        return toolbar_box
    
    def _create_album_grid(self):
        """Crée la grille d'albums moderne"""
        if GTK_VERSION == 4:
            # Utilise FlowBox pour GTK4
            flowbox = Gtk.FlowBox()
            flowbox.set_min_children_per_line(2)
            flowbox.set_max_children_per_line(6)
            flowbox.set_row_spacing(20)
            flowbox.set_column_spacing(20)
            flowbox.set_margin_start(20)
            flowbox.set_margin_end(20)
            flowbox.set_margin_top(20)
            flowbox.set_margin_bottom(20)
            flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        else:
            # Utilise FlowBox pour GTK3 aussi
            flowbox = Gtk.FlowBox()
            flowbox.set_min_children_per_line(2)
            flowbox.set_max_children_per_line(6)
            flowbox.set_row_spacing(20)
            flowbox.set_column_spacing(20)
            flowbox.set_margin_left(20)
            flowbox.set_margin_right(20)
            flowbox.set_margin_top(20)
            flowbox.set_margin_bottom(20)
            flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        
        # Ajoute les albums
        for album in self.albums:
            card = self._create_album_card(album)
            flowbox.add(card)
        
        return flowbox
    
    def _create_album_card(self, album):
        """Crée une card d'album moderne"""
        # Container principal (ajusté pour 250x250 + padding)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.set_size_request(270, 350)
        
        # Style CSS
        if hasattr(card, 'add_css_class'):
            card.add_css_class("album-card")
        
        # Container avec overlay pour checkbox
        if GTK_VERSION == 4:
            overlay = Gtk.Overlay()
        else:
            overlay = Gtk.Overlay()
        
        # Image placeholder (250x250 pour compatibilité pochettes standard)
        image_box = Gtk.Box()
        image_box.set_size_request(250, 250)
        if hasattr(image_box, 'add_css_class'):
            image_box.add_css_class("album-cover-placeholder")
        
        # Style par défaut
        image_box.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0.9, 0.9, 0.9, 1.0)
        ) if GTK_VERSION == 3 else None
        
        overlay.set_child(image_box) if GTK_VERSION == 4 else overlay.add(image_box)
        
        # Checkbox de sélection
        checkbox = Gtk.CheckButton()
        checkbox.set_halign(Gtk.Align.END)
        checkbox.set_valign(Gtk.Align.START)
        if hasattr(checkbox, 'set_margin_start'):
            checkbox.set_margin_top(8)
            checkbox.set_margin_end(8)
        else:
            checkbox.set_margin_top(8)
            checkbox.set_margin_right(8)
        
        checkbox.connect("toggled", self._on_album_selected, album)
        overlay.add_overlay(checkbox)
        
        # Badge de statut
        status_label = Gtk.Label()
        status_text = f"{album.status_emoji} {album.status_text}"
        status_label.set_text(status_text)
        status_label.set_halign(Gtk.Align.END)
        status_label.set_valign(Gtk.Align.END)
        if hasattr(status_label, 'set_margin_end'):
            status_label.set_margin_bottom(8)
            status_label.set_margin_end(8)
        else:
            status_label.set_margin_bottom(8)
            status_label.set_margin_right(8)
        
        if hasattr(status_label, 'add_css_class'):
            status_label.add_css_class("status-badge")
            status_label.add_css_class(album.status_css_class)
        
        overlay.add_overlay(status_label)
        
        # Informations textuelles
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        if hasattr(info_box, 'set_margin_start'):
            info_box.set_margin_start(8)
            info_box.set_margin_end(8)
            info_box.set_margin_bottom(8)
        else:
            info_box.set_margin_left(8)
            info_box.set_margin_right(8)
            info_box.set_margin_bottom(8)
        
        # Titre
        title_label = Gtk.Label(label=album.title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(3)  # ELLIPSIZE_END
        title_label.set_max_width_chars(25)
        if hasattr(title_label, 'add_css_class'):
            title_label.add_css_class("album-title")
        
        # Artiste
        artist_label = Gtk.Label(label=album.display_artist)
        artist_label.set_halign(Gtk.Align.START)
        artist_label.set_ellipsize(3)
        artist_label.set_max_width_chars(25)
        if hasattr(artist_label, 'add_css_class'):
            artist_label.add_css_class("album-artist")
        
        # Métadonnées
        meta_text = f"{album.year} • {album.track_count} pistes"
        if album.genre:
            meta_text += f" • {album.genre}"
        
        meta_label = Gtk.Label(label=meta_text)
        meta_label.set_halign(Gtk.Align.START)
        meta_label.set_ellipsize(3)
        if hasattr(meta_label, 'add_css_class'):
            meta_label.add_css_class("album-meta")
        
        # Assemblage
        info_box.append(title_label) if GTK_VERSION == 4 else info_box.pack_start(title_label, False, False, 0)
        info_box.append(artist_label) if GTK_VERSION == 4 else info_box.pack_start(artist_label, False, False, 0)
        info_box.append(meta_label) if GTK_VERSION == 4 else info_box.pack_start(meta_label, False, False, 0)
        
        card.append(overlay) if GTK_VERSION == 4 else card.pack_start(overlay, False, False, 0)
        card.append(info_box) if GTK_VERSION == 4 else card.pack_start(info_box, False, False, 0)
        
        # Stocke la référence de l'album et checkbox
        card.album = album
        card.checkbox = checkbox
        
        return card
    
    def _create_status_bar(self):
        """Crée la barre de statut"""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        if hasattr(status_box, 'set_margin_start'):
            status_box.set_margin_start(12)
            status_box.set_margin_end(12)
            status_box.set_margin_top(4)
            status_box.set_margin_bottom(8)
        else:
            status_box.set_margin_left(12)
            status_box.set_margin_right(12)
            status_box.set_margin_top(4)
            status_box.set_margin_bottom(8)
        
        # Label de statut
        self.status_label = Gtk.Label(label="Prêt")
        self.status_label.set_halign(Gtk.Align.START)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        
        # Total albums
        total_label = Gtk.Label(label=f"{len(self.albums)} albums")
        
        status_box.append(self.status_label) if GTK_VERSION == 4 else status_box.pack_start(self.status_label, False, False, 0)
        status_box.append(spacer) if GTK_VERSION == 4 else status_box.pack_start(spacer, True, True, 0)
        status_box.append(total_label) if GTK_VERSION == 4 else status_box.pack_start(total_label, False, False, 0)
        
        return status_box
    
    def _load_css(self):
        """Charge le CSS moderne adapté"""
        css = """
        .album-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 150ms ease;
            margin: 4px;
            padding: 8px;
        }
        
        .album-card:hover {
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .album-title {
            font-weight: 600;
            color: #1f2937;
            font-size: 14px;
        }
        
        .album-artist {
            color: #6b7280;
            font-size: 13px;
        }
        
        .album-meta {
            color: #9ca3af;
            font-size: 11px;
        }
        
        .status-badge {
            background: #f3f4f6;
            border-radius: 6px;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: 500;
        }
        
        .status-success {
            background: #dcfce7;
            color: #166534;
        }
        
        .status-error {
            background: #fef2f2;
            color: #dc2626;
        }
        
        .status-warning {
            background: #fef3c7;
            color: #d97706;
        }
        
        .status-processing {
            background: #dbeafe;
            color: #1d4ed8;
        }
        
        .album-cover-placeholder {
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            border-radius: 8px;
        }
        """
        
        try:
            css_provider = Gtk.CssProvider()
            if GTK_VERSION == 4:
                css_provider.load_from_data(css.encode())
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            else:
                css_provider.load_from_data(css.encode())
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
        except Exception as e:
            print(f"⚠️  Impossible de charger le CSS: {e}")
    
    def _create_demo_albums(self):
        """Crée des albums de démonstration"""
        return [
            AlbumModel(
                title="Kind of Blue",
                artist="Miles Davis",
                year="1959",
                genre="Jazz",
                track_count=9,
                status=AlbumStatus.SUCCESS
            ),
            AlbumModel(
                title="The Dark Side of the Moon",
                artist="Pink Floyd",
                year="1973",
                genre="Progressive Rock",
                track_count=10,
                status=AlbumStatus.PENDING
            ),
            AlbumModel(
                title="Thriller",
                artist="Michael Jackson",
                year="1982",
                genre="Pop",
                track_count=9,
                status=AlbumStatus.WARNING
            ),
            AlbumModel(
                title="Abbey Road",
                artist="The Beatles",
                year="1969",
                genre="Rock",
                track_count=17,
                status=AlbumStatus.ERROR
            ),
            AlbumModel(
                title="Random Access Memories",
                artist="Daft Punk",
                year="2013",
                genre="Electronic",
                track_count=13,
                status=AlbumStatus.PROCESSING
            ),
            AlbumModel(
                title="OK Computer",
                artist="Radiohead",
                year="1997",
                genre="Alternative Rock",
                track_count=12,
                status=AlbumStatus.SUCCESS
            ),
        ]
    
    def _update_selection_display(self):
        """Met à jour l'affichage de la sélection"""
        count = len(self.selected_albums)
        total = len(self.albums)
        
        if count == 0:
            text = f"{total} albums"
        else:
            text = f"{count} sélectionnés sur {total}"
            
        self.selection_label.set_text(text)
    
    # === CALLBACKS ===
    
    def _on_album_selected(self, checkbox, album):
        """Gère la sélection d'un album"""
        if checkbox.get_active():
            if album not in self.selected_albums:
                self.selected_albums.append(album)
        else:
            if album in self.selected_albums:
                self.selected_albums.remove(album)
        
        self._update_selection_display()

class ModernApp(Gtk.Application):
    """Application moderne"""
    
    def __init__(self):
        super().__init__(application_id='com.nonotags.modern')
    
    def do_activate(self):
        window = ModernWindow(self)
        window.present()

def main():
    """Lance l'interface moderne"""
    print("\n🎨 Interface Moderne Nonotags")
    print("=" * 40)
    print("✨ Design épuré et intuitif")
    print("🎯 Pas de superflu")
    print("🚀 Focus sur l'efficacité")
    print()
    
    app = ModernApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
