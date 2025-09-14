#!/usr/bin/env python3
"""
Démonstration de l'UI moderne Nonotags
Intégration avec les modules core existants
"""

import sys
import os

# Ajoute le chemin du projet
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from ui.models.album_model import AlbumModel, AlbumStatus
import tempfile
import shutil

# Import des modules core pour l'intégration
try:
    from support.logger import AppLogger
    from support.config_manager import ConfigManager
    from support.state_manager import StateManager
    CORE_MODULES_AVAILABLE = True
except ImportError:
    print("⚠️  Modules core non disponibles - mode démo seulement")
    CORE_MODULES_AVAILABLE = False

class NonotagsDemo:
    """
    Application de démonstration de l'UI moderne
    """
    
    def __init__(self):
        # Initialise les modules support si disponibles
        if CORE_MODULES_AVAILABLE:
            self.logger = AppLogger(__name__)
            self.config = ConfigManager()
            self.state = StateManager()
            self.logger.info("Démo initialisée avec modules core")
        else:
            self.logger = None
            self.config = None
            self.state = None
        
        self._create_demo_data()
    
    def _create_demo_data(self):
        """Crée des données de démonstration réalistes"""
        
        # Crée un dossier temporaire pour la démo
        self.demo_dir = tempfile.mkdtemp(prefix="nonotags_demo_")
        
        self.demo_albums = [
            AlbumModel(
                title="Kind of Blue",
                artist="Miles Davis",
                year="1959",
                genre="Jazz",
                track_count=9,
                folder_path=os.path.join(self.demo_dir, "Miles Davis - Kind of Blue"),
                status=AlbumStatus.SUCCESS
            ),
            AlbumModel(
                title="The Dark Side of the Moon",
                artist="Pink Floyd",
                year="1973",
                genre="Progressive Rock",
                track_count=10,
                folder_path=os.path.join(self.demo_dir, "Pink Floyd - Dark Side"),
                status=AlbumStatus.PENDING
            ),
            AlbumModel(
                title="Thriller",
                artist="Michael Jackson",
                year="1982",
                genre="Pop",
                track_count=9,
                folder_path=os.path.join(self.demo_dir, "Michael Jackson - Thriller"),
                status=AlbumStatus.WARNING
            ),
            AlbumModel(
                title="Abbey Road",
                artist="The Beatles",
                year="1969",
                genre="Rock",
                track_count=17,
                folder_path=os.path.join(self.demo_dir, "The Beatles - Abbey Road"),
                status=AlbumStatus.ERROR
            ),
            AlbumModel(
                title="Random Access Memories",
                artist="Daft Punk",
                year="2013",
                genre="Electronic",
                track_count=13,
                folder_path=os.path.join(self.demo_dir, "Daft Punk - RAM"),
                status=AlbumStatus.PROCESSING
            ),
            AlbumModel(
                title="OK Computer",
                artist="Radiohead",
                year="1997",
                genre="Alternative Rock",
                track_count=12,
                folder_path=os.path.join(self.demo_dir, "Radiohead - OK Computer"),
                status=AlbumStatus.SUCCESS
            ),
            AlbumModel(
                title="Rumours",
                artist="Fleetwood Mac",
                year="1977",
                genre="Rock",
                track_count=11,
                folder_path=os.path.join(self.demo_dir, "Fleetwood Mac - Rumours"),
                status=AlbumStatus.PENDING
            ),
            AlbumModel(
                title="The Wall",
                artist="Pink Floyd",
                year="1979",
                genre="Progressive Rock",
                track_count=26,
                folder_path=os.path.join(self.demo_dir, "Pink Floyd - The Wall"),
                status=AlbumStatus.SUCCESS
            ),
        ]
        
        # Crée les dossiers de démonstration
        for album in self.demo_albums:
            os.makedirs(album.folder_path, exist_ok=True)
        
        if self.logger:
            self.logger.info(f"Données de démo créées: {len(self.demo_albums)} albums")
    
    def cleanup(self):
        """Nettoie les fichiers de démonstration"""
        if hasattr(self, 'demo_dir') and os.path.exists(self.demo_dir):
            shutil.rmtree(self.demo_dir)
            if self.logger:
                self.logger.info("Nettoyage des fichiers de démo terminé")

def run_demo():
    """Lance la démonstration de l'UI moderne"""
    
    print("🎨 Démonstration de l'UI moderne Nonotags")
    print("=" * 50)
    print("✨ Interface épurée et intuitive")
    print("🚀 Design moderne avec GTK4 + Libadwaita")
    print("📱 Responsive et accessible")
    print("🎯 Pas de superflu, focus sur l'essentiel")
    print()
    
    # Initialise Libadwaita
    Adw.init()
    
    # Crée la démo
    demo = NonotagsDemo()
    
    try:
        # Lance l'application avec données de démo
        from ui.app_controller import NonotagsApp
        
        app = NonotagsApp()
        
        # Injecte les données de démo (nous implémenterons cela)
        app.demo_albums = demo.demo_albums
        
        # Lance l'UI
        result = app.run(sys.argv)
        
        print(f"\n✅ Démonstration terminée (code: {result})")
        return result
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Nettoie
        demo.cleanup()

def show_design_info():
    """Affiche les informations sur le design moderne"""
    
    print("\n" + "="*60)
    print("🎨 DESIGN SYSTEM MODERNE NONOTAGS")
    print("="*60)
    
    print("\n📐 PRINCIPES DE DESIGN:")
    print("  • Épuré et minimaliste")
    print("  • Pas de superflu ni d'éléments distrayants")
    print("  • Interface intuitive et accessible")
    print("  • Design system cohérent")
    print("  • Responsive et adaptatif")
    
    print("\n🎨 PALETTE DE COULEURS:")
    print("  • Primaire: Bleu moderne (#2563eb)")
    print("  • Secondaire: Gris élégant (#64748b)")
    print("  • Accent: Orange chaleureux (#f59e0b)")
    print("  • États: Vert, Orange, Rouge")
    
    print("\n🧩 COMPOSANTS MODERNES:")
    print("  • Cards d'albums avec hover effects")
    print("  • Boutons avec design system unifié")
    print("  • Grille responsive automatique")
    print("  • Navigation épurée")
    print("  • Indicateurs de statut visuels")
    
    print("\n⚡ INTERACTIONS:")
    print("  • Animations fluides et subtiles")
    print("  • Feedback visuel immédiat")
    print("  • Raccourcis clavier intuitifs")
    print("  • Sélection multiple ergonomique")
    
    print("\n🎯 PHILOSOPHIE UI:")
    print("  • 'Moins c'est plus' - chaque élément a un but")
    print("  • Interface qui disparaît pour laisser place au contenu")
    print("  • Workflow optimisé pour l'efficacité")
    print("  • Design accessible et inclusif")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    # Affiche les infos design
    show_design_info()
    
    # Demande confirmation
    print("\n🚀 Lancer la démonstration de l'UI moderne? (y/N): ", end="")
    try:
        response = input().strip().lower()
        if response in ['y', 'yes', 'oui', 'o']:
            sys.exit(run_demo())
        else:
            print("👋 À bientôt !")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n👋 À bientôt !")
        sys.exit(0)
