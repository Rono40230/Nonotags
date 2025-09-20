#!/usr/bin/env python3
"""
Test des corrections d'erreurs du gestionnaire de playlists
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import sys

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, '/home/rono/Nonotags')

from ui.views.playlist_manager_window import PlaylistManagerWindow

def test_error_fixes():
    """Test des corrections d'erreurs"""
    print("🧪 Test des corrections d'erreurs du gestionnaire de playlists")
    
    # Créer la fenêtre
    window = PlaylistManagerWindow()
    window.connect("destroy", Gtk.main_quit)
    
    # Test 1: Simuler une sélection vide pour tester _clear_playlist_details
    print("📋 Test 1: Nettoyage des détails avec playlist vide")
    try:
        window.current_playlist = None
        window._clear_playlist_details()
        print("✅ Test 1 réussi: Pas d'erreur avec playlist None")
    except AttributeError as e:
        print(f"❌ Test 1 échoué: {e}")
    except Exception as e:
        print(f"⚠️ Test 1 autre erreur: {e}")
    
    # Test 2: Tester _on_apply_conversion avec playlist None
    print("📋 Test 2: Application conversion avec playlist vide")
    try:
        window.current_playlist = None
        window.current_conversion_type = None
        # Cette méthode devrait faire return early
        window._preview_conversion()
        print("✅ Test 2 réussi: Pas d'erreur avec preview et playlist None")
    except Exception as e:
        print(f"❌ Test 2 échoué: {e}")
    
    # Test 3: Tester _perform_conversion avec playlist None
    print("📋 Test 3: Conversion avec playlist vide")
    try:
        window.current_playlist = None
        result = window._perform_conversion()
        if result == False:
            print("✅ Test 3 réussi: Conversion retourne False avec playlist None")
        else:
            print("⚠️ Test 3: Résultat inattendu")
    except Exception as e:
        print(f"❌ Test 3 échoué: {e}")
    
    print("🧪 Tests terminés - interface prête à utiliser")
    
    window.show_all()
    return window

if __name__ == "__main__":
    # Lancer les tests
    window = test_error_fixes()
    
    # Afficher l'interface
    print("🎵 Interface lancée - vous pouvez tester manuellement")
    print("🔧 Corrections appliquées:")
    print("   - Suppression des références aux anciens boutons de conversion")
    print("   - Ajout de vérifications de sécurité pour current_playlist")
    print("   - Protection contre les accès à file_path sur None")
    
    Gtk.main()
