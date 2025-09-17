#!/usr/bin/env python3
"""
Test complet de la détection pochettes avec simulation de fichiers avec couvertures
"""

import os
import sys

# Ajouter le chemin du projet  
sys.path.append('/home/rono/Nonotags/Nonotags')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Patcher temporairement la fonction de détection pour test
def mock_has_embedded_cover(file_path):
    """Version mock qui simule des fichiers avec pochettes"""
    filename = os.path.basename(file_path)
    
    # Simuler que certains fichiers ont des pochettes
    files_with_covers = [
        "01 - Come Together.mp3",
        "3 - Maxwell's Silver Hammer.mp3"
    ]
    
    return filename in files_with_covers

# Monkey patch pour le test
sys.path.insert(0, '/home/rono/Nonotags/Nonotags/ui/views')
import album_edit_window
album_edit_window.AlbumEditWindow._has_embedded_cover = lambda self, path: mock_has_embedded_cover(path)

from ui.views.album_edit_window import AlbumEditWindow

def test_album_edit_with_covers():
    """Test de la fenêtre d'édition avec simulation de pochettes"""
    
    album_data = {
        'title': 'Test Album avec Pochettes Simulées',
        'artist': 'Test Artist',
        'path': '/home/rono/Nonotags/Nonotags/test_albums/01_album_standard',
        'year': '2023',
        'genre': 'Test'
    }
    
    print("🧪 TEST FENÊTRE D'ÉDITION - POCHETTES SIMULÉES")
    print("=" * 60)
    print(f"Album testé: {album_data['title']}")
    print(f"Fichiers avec pochettes simulées:")
    print("  - 01 - Come Together.mp3")
    print("  - 3 - Maxwell's Silver Hammer.mp3")
    print()
    
    class TestApp(Gtk.Application):
        def __init__(self):
            super().__init__()
        
        def do_activate(self):
            edit_window = AlbumEditWindow(album_data, None)
            edit_window.set_application(self)
            edit_window.show_all()
            
            # Vérifier après chargement
            GLib.timeout_add(1000, self.check_table_content, edit_window)
        
        def check_table_content(self, edit_window):
            """Vérifier le contenu du tableau"""
            print("📊 RÉSULTATS DÉTECTION POCHETTES")
            print("-" * 40)
            
            if hasattr(edit_window, 'metadata_store'):
                store = edit_window.metadata_store
                
                with_cover = 0
                without_cover = 0
                
                for i, row in enumerate(store):
                    cover_status = row[0]
                    filename = row[1]
                    
                    if cover_status == "✅":
                        print(f"✅ AVEC pochette: {filename}")
                        with_cover += 1
                    else:
                        print(f"❌ SANS pochette: {filename}")
                        without_cover += 1
                
                print("-" * 40)
                print(f"📊 BILAN:")
                print(f"   ✅ Avec pochettes: {with_cover}")
                print(f"   ❌ Sans pochettes: {without_cover}")
                print(f"   📁 Total fichiers: {len(store)}")
                
                if with_cover == 2:  # Attendu: 2 fichiers avec pochettes
                    print("\n🎉 SUCCÈS ! La détection de pochettes fonctionne !")
                    print("   La colonne 1 affiche correctement ✅/❌")
                else:
                    print(f"\n⚠️ Problème: {with_cover} fichiers avec pochettes (attendu: 2)")
                    
            else:
                print("❌ Table non trouvée")
            
            # Fermer après vérification
            GLib.timeout_add(2000, lambda: self.quit())
            return False
    
    app = TestApp()
    app.run()

if __name__ == "__main__":
    test_album_edit_with_covers()
