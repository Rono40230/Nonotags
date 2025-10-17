"""
Fenêtre de démarrage Nonotags
Module dédié pour la fenêtre de démarrage avec navigation et sélection de dossiers
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
import os


class StartupWindow(Gtk.Window):
    """Fenêtre de démarrage conforme au cahier des charges"""
    
    def __init__(self, app):
        super().__init__(title="🎵 Nonotags")
        self.app = app
        
        # Charger le CSS pour les styles
        self._load_css()
        
        # Configuration de la fenêtre
        self.set_default_size(400, 400)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self.on_startup_window_close)
        
        # Conteneur principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_left(30)
        main_box.set_margin_right(30)
        main_box.set_margin_top(30)
        main_box.set_margin_bottom(30)
        main_box.set_halign(Gtk.Align.CENTER)
        main_box.set_valign(Gtk.Align.CENTER)
        self.add(main_box)
        
        # Boutons d'action selon cahier des charges
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        import_btn = Gtk.Button.new_with_label("Importer des albums")
        import_btn.get_style_context().add_class("button-import")
        import_btn.set_size_request(250, 40)
        import_btn.connect("clicked", self.on_import_clicked)
        buttons_box.pack_start(import_btn, False, False, 0)
        
        exceptions_btn = Gtk.Button.new_with_label("Ajouter des exceptions d'importation")
        exceptions_btn.get_style_context().add_class("button-exceptions")
        exceptions_btn.set_size_request(250, 40)
        exceptions_btn.connect("clicked", self.on_exceptions_clicked)
        buttons_box.pack_start(exceptions_btn, False, False, 0)
        
        playlists_btn = Gtk.Button.new_with_label("Gérer des Playlists")
        playlists_btn.get_style_context().add_class("button-playlists")
        playlists_btn.set_size_request(250, 40)
        playlists_btn.connect("clicked", self.on_playlists_clicked)
        buttons_box.pack_start(playlists_btn, False, False, 0)
        
        converter_btn = Gtk.Button.new_with_label("Convertir des fichiers audio")
        converter_btn.get_style_context().add_class("button-converter")
        converter_btn.set_size_request(250, 40)
        converter_btn.connect("clicked", self.on_converter_clicked)
        buttons_box.pack_start(converter_btn, False, False, 0)
        
        main_box.pack_start(buttons_box, False, False, 0)
        
    def on_import_clicked(self, button):
        """Importer des albums et ouvrir l'application avec les résultats"""
        # Ouvrir le sélecteur de dossier
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier d'albums à importer",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            folder_path = dialog.get_filename()
            dialog.destroy()
            
            # Ouvrir l'application principale avec le dossier
            self.hide()
            self.app.create_main_window_with_scan(folder_path)
        else:
            dialog.destroy()
    
    def on_exceptions_clicked(self, button):
        """Ouvre la fenêtre des exceptions"""
        # Importer et ouvrir la fenêtre des exceptions
        from ui.views.exceptions_window import ExceptionsWindow
        
        exceptions_window = ExceptionsWindow(parent=self)
        exceptions_window.show_all()
    
    def on_playlists_clicked(self, button):
        """Ouvre le gestionnaire de playlists"""
        # Importer et ouvrir la fenêtre du gestionnaire de playlists
        from ui.views.playlist_manager_window import PlaylistManagerWindow
        
        playlist_window = PlaylistManagerWindow(parent=self)
        playlist_window.show_all()
    
    def on_converter_clicked(self, button):
        """Ouvre le convertisseur audio"""
        # Importer et ouvrir la fenêtre du convertisseur audio
        from ui.views.audio_converter_window import AudioConverterWindow
        
        converter_window = AudioConverterWindow()
        converter_window.show_all()
        
    def on_startup_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre de démarrage"""
        Gtk.main_quit()
        return False
    
    def _load_css(self):
        """Charge le fichier CSS pour les styles des boutons"""
        try:
            css_provider = Gtk.CssProvider()
            css_file = os.path.join(os.path.dirname(__file__), "resources", "styles.css")
            
            if os.path.exists(css_file):
                css_provider.load_from_path(css_file)
                screen = Gdk.Screen.get_default()
                style_context = Gtk.StyleContext()
                style_context.add_provider_for_screen(
                    screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                print(f"✅ CSS chargé depuis: {css_file}")
            else:
                print(f"⚠️ Fichier CSS introuvable: {css_file}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du CSS: {e}")