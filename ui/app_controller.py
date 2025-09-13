"""
Contrôleur principal de l'application Nonotags
Architecture MVVM moderne avec GTK4
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
from typing import Optional
import os
import sys

# Import des modules core
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager

# Import des vues
from .views.startup_view import StartupView
from .views.main_view import MainView

class NonotagsApp(Adw.Application):
    """
    Application principale Nonotags avec design moderne
    Utilise Libadwaita pour un look natif moderne
    """
    
    def __init__(self):
        super().__init__(
            application_id='com.nonotags.app',
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        
        # Initialisation des modules support
        self.logger = AppLogger(__name__)
        self.config = ConfigManager()
        self.state = StateManager()
        
        # Variables d'état
        self.startup_window: Optional[StartupView] = None
        self.main_window: Optional[MainView] = None
        
        # Configuration du thème moderne
        self._setup_modern_theme()
        
        self.logger.info("Application Nonotags initialisée")
    
    def _setup_modern_theme(self):
        """Configure le thème moderne de l'application"""
        try:
            # Charge le CSS personnalisé
            css_provider = Gtk.CssProvider()
            css_path = os.path.join(os.path.dirname(__file__), 'resources', 'css', 'modern_theme.css')
            
            if os.path.exists(css_path):
                css_provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_display(
                    Gtk.StyleContext.get_display(Gtk.StyleContext()),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                self.logger.info("Thème moderne chargé avec succès")
            else:
                self.logger.warning(f"Fichier CSS non trouvé: {css_path}")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du thème: {e}")
    
    def do_activate(self):
        """Activation de l'application - affiche la fenêtre de démarrage"""
        self.logger.info("Activation de l'application")
        
        # Crée et affiche la fenêtre de démarrage
        if not self.startup_window:
            self.startup_window = StartupView(self)
        
        self.startup_window.present()
    
    def show_main_window(self):
        """Affiche la fenêtre principale"""
        self.logger.info("Ouverture de la fenêtre principale")
        
        if not self.main_window:
            self.main_window = MainView(self)
        
        # Cache la fenêtre de démarrage
        if self.startup_window:
            self.startup_window.close()
        
        self.main_window.present()
    
    def open_album_edit(self, albums):
        """Ouvre la fenêtre d'édition pour les albums spécifiés"""
        self.logger.info(f"Ouverture de l'édition pour {len(albums)} album(s)")
        
        # Import dynamique pour éviter les imports circulaires
        from .views.album_edit_view import AlbumEditView
        
        # Crée et affiche la fenêtre d'édition
        edit_window = AlbumEditView(self, albums)
        edit_window.present()
    
    def quit_application(self):
        """Ferme l'application proprement"""
        self.logger.info("Fermeture de l'application")
        self.quit()

def main():
    """Point d'entrée principal"""
    app = NonotagsApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    main()
