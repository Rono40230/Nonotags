#!/usr/bin/env python3
"""
Test fonctionnel de la fenêtre des exceptions
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_exceptions_integration():
    """Test d'intégration de la fenêtre des exceptions"""
    print("⚙️ Test d'intégration ExceptionsWindow...")
    
    try:
        # Test du import dans startup_window
        from ui.startup_window import StartupWindow
        print("✅ Import StartupWindow réussi")
        
        # Vérifier que l'import de ExceptionsWindow fonctionne
        try:
            from ui.views.exceptions_window import ExceptionsWindow
            print("✅ Import ExceptionsWindow dans le contexte réussi")
            return True
        except Exception as e:
            print(f"❌ Erreur import ExceptionsWindow: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

def test_audio_integration():
    """Test d'intégration du lecteur audio"""
    print("\n🎵 Test d'intégration AudioPlayer...")
    
    try:
        # Test du import dans album_edit_window
        from ui.views.album_edit_window import AlbumEditWindow
        print("✅ Import AlbumEditWindow réussi")
        
        # Vérifier les imports des services
        from services.audio_player import AudioPlayer
        from services.cover_search import CoverSearchService
        print("✅ Imports services dans AlbumEditWindow réussis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration audio: {e}")
        return False

def main():
    """Lance les tests d'intégration"""
    print("🔗 TESTS D'INTÉGRATION DES MODULES")
    print("=" * 45)
    
    results = []
    
    # Test intégration exceptions
    results.append(test_exceptions_integration())
    
    # Test intégration audio
    results.append(test_audio_integration())
    
    # Bilan
    print("\n" + "=" * 45)
    print("📊 BILAN DES TESTS D'INTÉGRATION")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"✅ Intégrations réussies: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 TOUTES LES INTÉGRATIONS FONCTIONNENT !")
        return True
    else:
        print("⚠️ Certaines intégrations nécessitent des corrections")
        return False

if __name__ == "__main__":
    main()
