#!/usr/bin/env python3
"""
Test rapide du chargement de pochette dans album_edit_window
"""

import sys
import os
sys.path.append('.')

# Simuler le chargement de pochette
def test_cover_loading():
    """Test du chargement de pochette"""
    from ui.views.album_edit_window import AlbumEditWindow
    
    # Données de test pour l'album 4 (qui a des pochettes)
    album_data = {
        'path': 'test_albums/04_dirty_metadata_nightmare',
        'folder_path': 'test_albums/04_dirty_metadata_nightmare',
        'artist': 'Test Artist',
        'album': 'Test Album',
        'year': '2024'
    }
    
    # Créer une instance temporaire pour tester
    edit_window = AlbumEditWindow.__new__(AlbumEditWindow)
    edit_window.album_data = album_data
    
    # Tester la détection de pochette
    cover_path = edit_window._find_cover_file(album_data['path'])
    
    print("🧪 TEST DÉTECTION POCHETTE FENÊTRE D'ÉDITION")
    print("=" * 50)
    print(f"📁 Dossier testé: {album_data['path']}")
    print(f"🖼️ Pochette trouvée: {cover_path}")
    
    if cover_path:
        print(f"✅ SUCCESS: Pochette détectée à {cover_path}")
    else:
        print("❌ ÉCHEC: Aucune pochette détectée")

if __name__ == "__main__":
    test_cover_loading()
