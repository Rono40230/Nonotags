"""
Fenêtre de démarrage Nonotags
Module dédié pour la fenêtre de démarrage avec navigation et sélection de dossiers
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk


class StartupWindow(Gtk.Window):
    """Fenêtre de démarrage conforme au cahier des charges"""
    
    def __init__(self, app):
        super().__init__(title="🎵 Nonotags")
        self.app = app
        
        # Configuration de la fenêtre
        self.set_default_size(400, 350)
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
        
        import_btn = Gtk.Button.new_with_label("📁 Importer des albums")
        import_btn.get_style_context().add_class("modern-button")
        import_btn.set_size_request(250, 40)
        import_btn.connect("clicked", self.on_import_clicked)
        buttons_box.pack_start(import_btn, False, False, 0)
        
        exceptions_btn = Gtk.Button.new_with_label("⚙️ Ajouter des exceptions d'importation")
        exceptions_btn.get_style_context().add_class("modern-button")
        exceptions_btn.set_size_request(250, 40)
        exceptions_btn.connect("clicked", self.on_exceptions_clicked)
        buttons_box.pack_start(exceptions_btn, False, False, 0)
        
        open_app_btn = Gtk.Button.new_with_label("🚀 Ouvrir l'application")
        open_app_btn.get_style_context().add_class("modern-button")
        open_app_btn.set_size_request(250, 40)
        open_app_btn.connect("clicked", self.on_open_app_clicked)
        buttons_box.pack_start(open_app_btn, False, False, 0)
        
        main_box.pack_start(buttons_box, False, False, 0)
        
    def on_import_clicked(self, button):
        """Importer des albums et ouvrir l'application avec les résultats"""
        print("📁 Importer des albums sélectionné")
        
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
            print(f"📁 Dossier sélectionné: {folder_path}")
            dialog.destroy()
            
            # Ouvrir l'application principale avec le dossier
            self.hide()
            self.app.create_main_window_with_scan(folder_path)
        else:
            dialog.destroy()
    
    def on_exceptions_clicked(self, button):
        """Ouvre la fenêtre des exceptions"""
        print("⚙️ Fenêtre des exceptions")
        
        # Importer et ouvrir la fenêtre des exceptions
        from ui.views.exceptions_window import ExceptionsWindow
        
        exceptions_window = ExceptionsWindow(parent=self)
        exceptions_window.show_all()
        
    def on_open_app_clicked(self, button):
        """Ouvre la fenêtre principale et ferme la fenêtre de démarrage"""
        print("🚀 Ouverture de l'application principale")
        self.hide()  # Cache la fenêtre de démarrage
        self.app.create_main_window()  # Crée et affiche la fenêtre principale

    def on_startup_window_close(self, window, event):
        """Gestionnaire de fermeture de la fenêtre de démarrage"""
        print("👋 Fermeture de l'application depuis la fenêtre de démarrage")
        Gtk.main_quit()
        return False
