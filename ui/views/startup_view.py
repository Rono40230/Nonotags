"""
Vue de démarrage moderne pour Nonotags
Interface épurée et intuitive avec 3 actions principales
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app_controller import NonotagsApp

class StartupView(Adw.ApplicationWindow):
    """
    Fenêtre de démarrage moderne et épurée
    Design minimaliste avec 3 actions principales
    """
    
    def __init__(self, app: 'NonotagsApp'):
        super().__init__(
            application=app,
            title="Nonotags",
            default_width=400,
            default_height=350,
            resizable=False
        )
        
        self.app = app
        self._setup_ui()
        self._connect_signals()
        
        # Applique la classe CSS
        self.add_css_class("startup-window")
    
    def _setup_ui(self):
        """Configure l'interface utilisateur moderne"""
        
        # Container principal avec padding
        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER
        )
        main_box.add_css_class("startup-container")
        
        # === HEADER SECTION ===
        header_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            halign=Gtk.Align.CENTER
        )
        header_box.add_css_class("startup-header")
        
        # Logo/Titre principal
        title_label = Gtk.Label(
            label="Nonotags",
            halign=Gtk.Align.CENTER
        )
        title_label.add_css_class("startup-title")
        
        # Sous-titre descriptif
        subtitle_label = Gtk.Label(
            label="Gestionnaire de métadonnées MP3 moderne",
            halign=Gtk.Align.CENTER,
            wrap=True,
            justify=Gtk.Justification.CENTER
        )
        subtitle_label.add_css_class("startup-subtitle")
        
        header_box.append(title_label)
        header_box.append(subtitle_label)
        
        # === ACTIONS SECTION ===
        actions_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            halign=Gtk.Align.CENTER,
            margin_top=48
        )
        
        # Bouton principal - Importer des albums
        self.import_button = self._create_action_button(
            "📁 Importer des albums",
            "Sélectionner un dossier contenant vos albums MP3",
            "button-primary modern-button"
        )
        
        # Bouton secondaire - Gérer les exceptions
        self.exceptions_button = self._create_action_button(
            "⚙️ Gérer les exceptions",
            "Configurer les règles de formatage personnalisées",
            "button-secondary modern-button"
        )
        
        # Bouton tertiaire - Ouvrir l'application
        self.open_app_button = self._create_action_button(
            "🚀 Ouvrir l'application",
            "Accéder à l'interface principale",
            "button-tertiary modern-button"
        )
        
        actions_box.append(self.import_button)
        actions_box.append(self.exceptions_button)
        actions_box.append(self.open_app_button)
        
        # === FOOTER ===
        footer_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=16,
            halign=Gtk.Align.CENTER,
            margin_top=48
        )
        
        version_label = Gtk.Label(
            label="Version 1.0.0",
            halign=Gtk.Align.CENTER
        )
        version_label.add_css_class("text-small")
        version_label.set_opacity(0.6)
        
        footer_box.append(version_label)
        
        # Assemblage
        main_box.append(header_box)
        main_box.append(actions_box)
        main_box.append(footer_box)
        
        self.set_content(main_box)
    
    def _create_action_button(self, title: str, subtitle: str, css_classes: str) -> Gtk.Button:
        """
        Crée un bouton d'action moderne avec titre et sous-titre
        """
        button = Gtk.Button()
        button.set_size_request(350, 64)
        
        # Container du bouton
        button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER
        )
        
        # Titre du bouton
        title_label = Gtk.Label(
            label=title,
            halign=Gtk.Align.CENTER
        )
        title_label.set_markup(f"<b>{title}</b>")
        
        # Sous-titre
        subtitle_label = Gtk.Label(
            label=subtitle,
            halign=Gtk.Align.CENTER
        )
        subtitle_label.add_css_class("text-small")
        subtitle_label.set_opacity(0.8)
        
        button_box.append(title_label)
        button_box.append(subtitle_label)
        
        button.set_child(button_box)
        
        # Applique les classes CSS
        for css_class in css_classes.split():
            button.add_css_class(css_class)
        
        return button
    
    def _connect_signals(self):
        """Connecte les signaux des boutons"""
        self.import_button.connect("clicked", self._on_import_clicked)
        self.exceptions_button.connect("clicked", self._on_exceptions_clicked)
        self.open_app_button.connect("clicked", self._on_open_app_clicked)
    
    def _on_import_clicked(self, button):
        """Gère le clic sur importer des albums"""
        self.app.logger.info("Clic sur importer des albums")
        
        # Ouvre un sélecteur de dossier moderne
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner le dossier contenant vos albums",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        dialog.add_buttons(
            "Annuler", Gtk.ResponseType.CANCEL,
            "Sélectionner", Gtk.ResponseType.ACCEPT
        )
        
        dialog.connect("response", self._on_folder_selected)
        dialog.show()
    
    def _on_folder_selected(self, dialog, response):
        """Traite la sélection de dossier"""
        if response == Gtk.ResponseType.ACCEPT:
            folder = dialog.get_file()
            folder_path = folder.get_path()
            
            self.app.logger.info(f"Dossier sélectionné: {folder_path}")
            
            # TODO: Intégrer avec le module d'import
            # Pour l'instant, on ouvre juste la fenêtre principale
            self.app.show_main_window()
        
        dialog.destroy()
    
    def _on_exceptions_clicked(self, button):
        """Gère le clic sur gérer les exceptions"""
        self.app.logger.info("Clic sur gérer les exceptions")
        
        # TODO: Ouvrir la fenêtre de gestion des exceptions
        # Pour l'instant, placeholder
        self._show_toast("Fonctionnalité bientôt disponible")
    
    def _on_open_app_clicked(self, button):
        """Gère le clic sur ouvrir l'application"""
        self.app.logger.info("Clic sur ouvrir l'application")
        self.app.show_main_window()
    
    def _show_toast(self, message: str):
        """Affiche un message toast moderne"""
        toast = Adw.Toast(title=message)
        
        # Si on a un toast overlay, on l'utilise
        # Sinon on log le message
        self.app.logger.info(f"Toast: {message}")
        
        # TODO: Implémenter un système de toast moderne
        print(f"🍞 {message}")  # Placeholder pour l'instant
