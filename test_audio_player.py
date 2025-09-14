#!/usr/bin/env python3
"""
Test du module AudioPlayer
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_audio_player():
    """Test basique du module AudioPlayer"""
    print("🎵 Test du module AudioPlayer...")
    
    try:
        from services.audio_player import AudioPlayer, PlayerState
        print("✅ Import AudioPlayer réussi")
        
        # Test d'instanciation
        try:
            player = AudioPlayer()
            print("✅ Instanciation AudioPlayer réussie")
            
            # Test des méthodes basiques
            state = player.get_state()
            print(f"✅ État initial: {state}")
            
            formats = player.get_supported_formats()
            print(f"✅ Formats supportés: {formats}")
            
            # Test de nettoyage
            player.cleanup()
            print("✅ Nettoyage réussi")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur instanciation: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Erreur import AudioPlayer: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_cover_search():
    """Test basique du module CoverSearch"""
    print("\n🔍 Test du module CoverSearchService...")
    
    try:
        from services.cover_search import CoverSearchService, CoverResult
        print("✅ Import CoverSearchService réussi")
        
        # Test d'instanciation
        try:
            service = CoverSearchService()
            print("✅ Instanciation CoverSearchService réussie")
            
            # Test des méthodes de validation
            test_result = service.validate_cover_file("/tmp/inexistant.jpg")
            print(f"✅ Test validation: {test_result}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur instanciation: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Erreur import CoverSearchService: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_exceptions_window():
    """Test basique du module ExceptionsWindow"""
    print("\n⚙️ Test du module ExceptionsWindow...")
    
    try:
        from ui.views.exceptions_window import ExceptionsWindow
        print("✅ Import ExceptionsWindow réussi")
        
        # Note: Ne pas instancier GTK sans environnement graphique
        print("✅ Module ExceptionsWindow disponible (test GUI requis)")
        
        return True
            
    except ImportError as e:
        print(f"❌ Erreur import ExceptionsWindow: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def main():
    """Lance tous les tests"""
    print("🧪 TESTS DES MODULES CRÉÉS")
    print("=" * 40)
    
    results = []
    
    # Test AudioPlayer
    results.append(test_audio_player())
    
    # Test CoverSearch
    results.append(test_cover_search())
    
    # Test ExceptionsWindow
    results.append(test_exceptions_window())
    
    # Bilan
    print("\n" + "=" * 40)
    print("📊 BILAN DES TESTS")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"✅ Modules réussis: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 TOUS LES MODULES FONCTIONNENT !")
        return True
    else:
        print("⚠️ Certains modules nécessitent des corrections")
        return False

if __name__ == "__main__":
    main()
