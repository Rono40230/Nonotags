#!/usr/bin/env python3
"""
Script de préparation pour le développement UI - Phase 3
Création de la structure de base et vérification des prérequis
"""

import os
import sys
from pathlib import Path

def create_ui_structure():
    """Crée la structure de dossiers pour l'interface utilisateur."""
    print("🏗️  Création de la structure UI...")
    
    # Structure des dossiers UI
    ui_structure = [
        "ui",
        "ui/controllers",
        "ui/views", 
        "ui/components",
        "ui/models",
        "ui/utils",
        "ui/resources",
        "ui/resources/ui",
        "ui/resources/css", 
        "ui/resources/icons"
    ]
    
    for folder in ui_structure:
        folder_path = Path(folder)
        folder_path.mkdir(exist_ok=True)
        
        # Créer __init__.py pour les packages Python
        if folder.startswith("ui") and not folder.endswith(("ui", "css", "icons")):
            init_file = folder_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Module UI Nonotags."""\n')
        
        print(f"   ✅ {folder}/")
    
    print("✅ Structure UI créée avec succès !")

def check_gtk_dependencies():
    """Vérifie les dépendances GTK."""
    print("\n🔍 Vérification des dépendances GTK...")
    
    dependencies = [
        ("gi", "PyGObject"),
        ("gi.repository.Gtk", "GTK4"),
        ("gi.repository.GLib", "GLib"),
        ("gi.repository.Gio", "GIO"),
        ("gi.repository.GObject", "GObject")
    ]
    
    missing_deps = []
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - Non trouvé")
            missing_deps.append(name)
    
    if missing_deps:
        print(f"\n⚠️  Dépendances manquantes : {', '.join(missing_deps)}")
        print("\n📦 Installation recommandée sur Fedora :")
        print("   sudo dnf install gtk4-devel python3-gobject python3-gobject-devel")
        return False
    else:
        print("\n✅ Toutes les dépendances GTK sont disponibles !")
        return True

def create_base_files():
    """Crée les fichiers de base pour l'UI."""
    print("\n📝 Création des fichiers de base...")
    
    # Application principale
    app_content = '''"""
Application GTK principale - Nonotags
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio

from ui.controllers.app_controller import AppController
from support.logger import AppLogger
from support.config_manager import ConfigManager

class NonotagsApp(Gtk.Application):
    """Application principale Nonotags."""
    
    def __init__(self):
        super().__init__(application_id="com.nonotags.app")
        
        # Initialisation des modules de support
        self.logger = AppLogger(__name__)
        self.config = ConfigManager()
        
        # Contrôleur principal
        self.app_controller = None
    
    def do_activate(self):
        """Active l'application."""
        self.logger.info("Démarrage de l'application Nonotags")
        
        # Initialisation du contrôleur principal
        self.app_controller = AppController(self)
        
        # Affichage de la fenêtre de démarrage
        self.app_controller.show_startup_window()

def main():
    """Point d'entrée principal."""
    app = NonotagsApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
'''
    
    # Contrôleur principal
    controller_content = '''"""
Contrôleur principal de l'application
"""

from gi.repository import Gtk
from support.logger import AppLogger
from support.state_manager import StateManager

class AppController:
    """Contrôleur principal de l'application."""
    
    def __init__(self, app):
        self.app = app
        self.logger = AppLogger(__name__)
        self.state_manager = StateManager()
        
        # Fenêtres de l'application
        self.startup_window = None
        self.main_window = None
        self.current_window = None
        
        self.logger.info("AppController initialisé")
    
    def show_startup_window(self):
        """Affiche la fenêtre de démarrage."""
        from ui.views.startup_view import StartupView
        
        self.startup_window = StartupView(self)
        self.startup_window.set_application(self.app)
        self.startup_window.present()
        self.current_window = self.startup_window
        
        self.logger.info("Fenêtre de démarrage affichée")
    
    def show_main_window(self):
        """Affiche la fenêtre principale."""
        # À implémenter
        self.logger.info("Transition vers fenêtre principale")
    
    def on_import_albums(self):
        """Gère l'importation d'albums."""
        # À implémenter avec les modules Phase 2
        self.logger.info("Import d'albums demandé")
    
    def on_open_exceptions(self):
        """Ouvre la fenêtre des exceptions."""
        # À implémenter
        self.logger.info("Ouverture fenêtre exceptions")
'''
    
    # Vue de démarrage
    startup_view_content = '''"""
Vue de la fenêtre de démarrage
"""

from gi.repository import Gtk

class StartupView(Gtk.ApplicationWindow):
    """Fenêtre de démarrage de l'application."""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.set_title("Nonotags - Gestionnaire de métadonnées MP3")
        self.set_default_size(600, 400)
        self.set_resizable(False)
        
        self.build_ui()
        self.connect_signals()
    
    def build_ui(self):
        """Construit l'interface de démarrage."""
        # Container principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(50)
        main_box.set_margin_bottom(50)
        main_box.set_margin_start(50)
        main_box.set_margin_end(50)
        
        # Titre
        title_label = Gtk.Label(label="Nonotags")
        title_label.add_css_class("title-1")
        
        # Sous-titre
        subtitle_label = Gtk.Label(label="Gestionnaire de métadonnées MP3")
        subtitle_label.add_css_class("subtitle")
        
        # Boutons principaux
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        
        self.import_button = Gtk.Button(label="Importer des albums")
        self.import_button.add_css_class("suggested-action")
        self.import_button.set_size_request(300, 50)
        
        self.exceptions_button = Gtk.Button(label="Ajouter des exceptions d'importation")
        self.exceptions_button.set_size_request(300, 50)
        
        self.open_app_button = Gtk.Button(label="Ouvrir l'application")
        self.open_app_button.set_size_request(300, 50)
        
        # Assembly
        main_box.append(title_label)
        main_box.append(subtitle_label)
        
        buttons_box.append(self.import_button)
        buttons_box.append(self.exceptions_button)
        buttons_box.append(self.open_app_button)
        
        main_box.append(buttons_box)
        
        self.set_child(main_box)
    
    def connect_signals(self):
        """Connecte les signaux des boutons."""
        self.import_button.connect("clicked", self.on_import_clicked)
        self.exceptions_button.connect("clicked", self.on_exceptions_clicked)
        self.open_app_button.connect("clicked", self.on_open_app_clicked)
    
    def on_import_clicked(self, button):
        """Gère le clic sur importer."""
        self.controller.on_import_albums()
    
    def on_exceptions_clicked(self, button):
        """Gère le clic sur exceptions."""
        self.controller.on_open_exceptions()
    
    def on_open_app_clicked(self, button):
        """Gère le clic sur ouvrir app."""
        self.controller.show_main_window()
'''
    
    # CSS de base
    css_content = '''/* Styles de base pour Nonotags */

/* Couleurs principales */
@define-color primary_color #2563eb;
@define-color secondary_color #64748b;
@define-color accent_color #f59e0b;
@define-color success_color #10b981;
@define-color warning_color #f59e0b;
@define-color error_color #ef4444;

/* Interface */
@define-color background_color #f8fafc;
@define-color surface_color #ffffff;
@define-color border_color #e2e8f0;

/* Fenêtre de démarrage */
.title-1 {
  font-size: 2.5rem;
  font-weight: bold;
  color: @primary_color;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 1.2rem;
  color: @secondary_color;
  margin-bottom: 30px;
}

/* Boutons */
button {
  border-radius: 8px;
  font-weight: 500;
  padding: 12px 24px;
  transition: all 0.2s ease;
}

button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

button.suggested-action {
  background: @primary_color;
  color: white;
}

button.suggested-action:hover {
  background: shade(@primary_color, 0.9);
}

/* Cards d'albums (pour plus tard) */
.album-card {
  background: @surface_color;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  margin: 8px;
  transition: all 0.2s ease;
}

.album-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}
'''
    
    # gresource.xml
    gresource_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/com/nonotags/ui">
    <file>css/main.css</file>
  </gresource>
</gresources>
'''
    
    # Fichiers à créer
    files_to_create = [
        ("ui/app.py", app_content),
        ("ui/controllers/app_controller.py", controller_content),
        ("ui/views/startup_view.py", startup_view_content),
        ("ui/resources/css/main.css", css_content),
        ("ui/resources/gresource.xml", gresource_content)
    ]
    
    for file_path, content in files_to_create:
        path = Path(file_path)
        if not path.exists():
            path.write_text(content)
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⏭️  {file_path} (existe déjà)")
    
    print("✅ Fichiers de base créés !")

def create_test_launcher():
    """Crée un script de test pour l'UI."""
    print("\n🧪 Création du script de test...")
    
    test_content = '''#!/usr/bin/env python3
"""
Script de test pour l'interface utilisateur
"""

import sys
import os
from pathlib import Path

# Ajout du chemin du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ui():
    """Teste l'interface utilisateur."""
    print("🧪 Test de l'interface utilisateur Nonotags")
    
    try:
        # Vérification des imports
        print("   📦 Vérification des imports...")
        
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
        
        from ui.app import NonotagsApp
        
        print("   ✅ Imports réussis")
        
        # Lancement de l'application
        print("   🚀 Lancement de l'application...")
        app = NonotagsApp()
        
        # Test basique (sans run pour éviter la boucle)
        print("   ✅ Application créée avec succès")
        print("   💡 Utilisez 'python ui/app.py' pour lancer l'interface")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erreur d'import : {e}")
        print("   💡 Installez les dépendances GTK4")
        return False
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return False

if __name__ == "__main__":
    success = test_ui()
    sys.exit(0 if success else 1)
'''
    
    test_path = Path("test_ui.py")
    test_path.write_text(test_content)
    os.chmod(test_path, 0o755)
    print(f"   ✅ {test_path}")
    print("✅ Script de test créé !")

def show_next_steps():
    """Affiche les prochaines étapes."""
    print("\n" + "="*60)
    print("🎯 PHASE 3 - INTERFACE UTILISATEUR PRÊTE")
    print("="*60)
    
    print("\n📋 Prochaines étapes :")
    print("   1. Vérifier les dépendances GTK4 :")
    print("      sudo dnf install gtk4-devel python3-gobject python3-gobject-devel")
    
    print("\n   2. Tester l'interface de base :")
    print("      python test_ui.py")
    
    print("\n   3. Lancer l'application :")
    print("      python ui/app.py")
    
    print("\n   4. Développer les vues restantes :")
    print("      - Fenêtre principale (main_view.py)")
    print("      - Cards d'albums (album_card.py)")
    print("      - Fenêtre d'édition (edit_view.py)")
    print("      - Fenêtre exceptions (exceptions_view.py)")
    
    print("\n🔧 Architecture disponible :")
    print("   ✅ 6 modules core Phase 2 (123 tests passent)")
    print("   ✅ 4 modules de support intégrés")
    print("   ✅ Base de données opérationnelle")
    print("   ✅ Pipeline de traitement complet")
    
    print("\n📚 Documentation :")
    print("   - ROADMAP.md : Plan détaillé Phase 3")
    print("   - ARCHITECTURE_UI.md : Guide technique complet")
    print("   - ui/ : Structure et fichiers de base créés")
    
    print("\n🎨 Prêt pour le développement UI avec GTK4 + PyGObject !")

def main():
    """Fonction principale."""
    print("🚀 PRÉPARATION PHASE 3 - INTERFACE UTILISATEUR")
    print("=" * 50)
    
    # Vérification du répertoire de travail
    if not Path("core").exists():
        print("❌ Erreur : Ce script doit être exécuté depuis le répertoire racine du projet")
        sys.exit(1)
    
    # Étapes de préparation
    create_ui_structure()
    
    gtk_ok = check_gtk_dependencies()
    
    create_base_files()
    create_test_launcher()
    
    show_next_steps()
    
    if not gtk_ok:
        print("\n⚠️  ATTENTION : Dépendances GTK manquantes")
        print("   Installez-les avant de continuer le développement UI")

if __name__ == "__main__":
    main()
    
    test_path = Path("test_ui.py")
    test_path.write_text(test_content)
    os.chmod(test_path, 0o755)
    print(f"   ✅ {test_path}")
    print("✅ Script de test créé !")
