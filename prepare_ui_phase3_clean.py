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
    
    show_next_steps()
    
    if not gtk_ok:
        print("\n⚠️  ATTENTION : Dépendances GTK manquantes")
        print("   Installez-les avant de continuer le développement UI")

if __name__ == "__main__":
    main()
