"""
Module 9 - Fenêtre principale de l'application
Interface utilisateur principale avec GTK.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager

class MainWindow:
    """Fenêtre principale de l'application Nonotags."""
    
    def __init__(self, config: ConfigManager, state: StateManager, logger: AppLogger):
        """
        Initialise la fenêtre principale.
        
        Args:
            config: Gestionnaire de configuration
            state: Gestionnaire d'état
            logger: Gestionnaire de logs
        """
        self.config = config
        self.state = state
        self.logger = logger
        
        # Création de la fenêtre principale
        self.window = Gtk.Window()
        self.window.set_title("Nonotags - Gestionnaire de métadonnées MP3")
        self.window.set_default_size(
            self.config.ui.window_width,
            self.config.ui.window_height
        )
        self.window.connect("destroy", self._on_destroy)
        
        # Interface temporaire pour la Phase 1
        self._create_temporary_interface()
        
        self.logger.info("Main window initialized")
    
    def _create_temporary_interface(self):
        """Crée une interface temporaire pour la Phase 1."""
        # Conteneur principal
        vbox = Gtk.VBox(spacing=10)
        vbox.set_border_width(20)
        
        # Titre
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large' weight='bold'>Nonotags - Phase 1</span>")
        title_label.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(title_label, False, False, 10)
        
        # Message de statut
        status_label = Gtk.Label()
        status_label.set_text("Architecture et modules de support initialisés ✅")
        status_label.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(status_label, False, False, 5)
        
        # Informations sur les modules
        info_label = Gtk.Label()
        info_label.set_markup("""
<b>Modules de support créés :</b>
• Module 13 - Validation des données
• Module 14 - Système de logging centralisé  
• Module 15 - Gestionnaire de configuration
• Module 16 - Gestion d'état global
• Module 10 - Base de données SQLite

<b>Prochaines étapes :</b>
• Phase 2 : Moteur de règles et traitement
• Phase 3 : Interface utilisateur complète
        """)
        info_label.set_halign(Gtk.Align.START)
        vbox.pack_start(info_label, True, True, 10)
        
        # Bouton de test
        test_button = Gtk.Button(label="Tester les modules de support")
        test_button.connect("clicked", self._on_test_modules)
        vbox.pack_start(test_button, False, False, 10)
        
        # Bouton de fermeture
        close_button = Gtk.Button(label="Fermer")
        close_button.connect("clicked", self._on_destroy)
        vbox.pack_start(close_button, False, False, 5)
        
        self.window.add(vbox)
    
    def _on_test_modules(self, button):
        """Test des modules de support."""
        self.logger.info("Testing support modules...")
        
        # Test du logging
        self.logger.debug("Test DEBUG log")
        self.logger.info("Test INFO log") 
        self.logger.warning("Test WARNING log")
        
        # Test de la configuration
        self.config.set('ui', 'test_value', 'Module test successful')
        test_value = self.config.get('ui', 'test_value')
        
        # Test de l'état
        from support.state_manager import ApplicationState
        self.state.set_app_state(ApplicationState.READY, "")
        
        # Affichage du résultat
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Test des modules réussi !"
        )
        dialog.format_secondary_text(
            f"Logging: ✅\n"
            f"Configuration: ✅ (test_value = {test_value})\n"
            f"État: ✅ (État actuel: {self.state.get_app_state().value})\n"
            f"Base de données: ✅"
        )
        dialog.run()
        dialog.destroy()
    
    def _on_destroy(self, widget=None):
        """Gestionnaire de fermeture de l'application."""
        self.logger.info("Application closing...")
        
        # Sauvegarde de la configuration
        self.config.save()
        
        # Arrêt de l'application GTK
        Gtk.main_quit()
    
    def run(self):
        """Lance l'application."""
        self.window.show_all()
        
        # Mise à jour de l'état
        from support.state_manager import ApplicationState
        self.state.set_app_state(ApplicationState.READY)
        
        # Démarrage de la boucle GTK
        Gtk.main()
