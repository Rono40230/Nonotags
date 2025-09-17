#!/usr/bin/env python3
"""
Test de la fenêtre d'édition avec validation des colonnes
"""

import os
import sys

# Ajouter le chemin du projet
sys.path.append('/home/rono/Nonotags/Nonotags')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from ui.views.album_edit_window import AlbumEditWindow

def test_album_edit_window():
    """Test de la fenêtre d'édition avec un album"""
    
    # Données d'album de test
    album_data = {
        'title': 'Album Test Détection Pochettes',
        'artist': 'Artiste Test',
        'path': '/home/rono/Nonotags/Nonotags/test_albums/01_album_standard',
        'year': '2023',
        'genre': 'Test'
    }
    
    print("🧪 TEST FENÊTRE D'ÉDITION - DÉTECTION POCHETTES")
    print("=" * 60)
    print(f"Album testé: {album_data['title']}")
    print(f"Chemin: {album_data['path']}")
    
    class TestApp(Gtk.Application):
        def __init__(self):
            super().__init__()
        
        def do_activate(self):
            # Créer la fenêtre d'édition
            edit_window = AlbumEditWindow(album_data, None)
            edit_window.set_application(self)
            edit_window.show_all()
            
            # Programmer la vérification après chargement
            GLib.timeout_add(1000, self.check_table_content, edit_window)
        
        def check_table_content(self, edit_window):
            """Vérifier le contenu du tableau après chargement"""
            print("\n📊 VÉRIFICATION TABLEAU MÉTADONNÉES")
            print("-" * 40)
            
            if hasattr(edit_window, 'metadata_store'):
                store = edit_window.metadata_store
                
                print(f"Nombre de lignes dans le tableau: {len(store)}")
                
                for i, row in enumerate(store):
                    cover_status = row[0]  # Première colonne = statut pochette
                    filename = row[1]      # Deuxième colonne = nom fichier
                    
                    print(f"{i+1:2d}. {cover_status} | {filename}")
                
                # Compter les statuts
                with_cover = sum(1 for row in store if row[0] == "✅")
                without_cover = sum(1 for row in store if row[0] == "❌")
                
                print("-" * 40)
                print(f"✅ Avec pochettes: {with_cover}")
                print(f"❌ Sans pochettes: {without_cover}")
                print(f"📊 Total fichiers: {len(store)}")
                
                if with_cover > 0:
                    print("🎉 Détection de pochettes FONCTIONNE !")
                else:
                    print("⚠️ Aucune pochette détectée - Vérifier la logique")
                    
            else:
                print("❌ Table des métadonnées non trouvée")
            
            # Fermer l'application après vérification
            GLib.timeout_add(2000, lambda: self.quit())
            return False
    
    # Lancer l'application de test
    app = TestApp()
    app.run()

if __name__ == "__main__":
    test_album_edit_window()
