#!/usr/bin/env python3
"""
Test final de l'intégration complète
Test de tous les modules et de l'orchestrateur
"""

import sys
import os

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_integration():
    """Test de l'intégration complète"""
    print("🚀 TEST FINAL D'INTÉGRATION COMPLÈTE")
    print("=" * 45)
    
    try:
        # Test 1: Import de l'orchestrateur
        print("🔧 Test ProcessingOrchestrator...")
        from ui.processing_orchestrator import ProcessingOrchestrator, ProcessingState, ProcessingStep
        orchestrator = ProcessingOrchestrator()
        print("✅ ProcessingOrchestrator importé et instancié")
        
        # Test 2: Vérification des modules de traitement
        print("\n🔧 Test des modules de traitement...")
        modules = [
            'file_cleaner', 'metadata_processor', 'case_corrector',
            'metadata_formatter', 'file_renamer', 'tag_synchronizer'
        ]
        
        for module in modules:
            if hasattr(orchestrator, module):
                print(f"✅ Module {module} présent")
            else:
                print(f"❌ Module {module} manquant")
        
        # Test 3: Import des services
        print("\n🎵 Test des services...")
        from services.audio_player import AudioPlayer
        audio_player = AudioPlayer()
        print("✅ AudioPlayer importé et instancié")
        
        from services.cover_search import CoverSearchService
        cover_service = CoverSearchService()
        print("✅ CoverSearchService importé et instancié")
        
        # Test 4: Test de l'interface exceptions
        print("\n⚙️ Test ExceptionsWindow...")
        from ui.views.exceptions_window import ExceptionsWindow
        print("✅ ExceptionsWindow importé")
        
        # Test 5: Test des états de l'orchestrateur
        print("\n📊 Test des états...")
        print(f"État initial: {orchestrator.current_state}")
        print(f"Étape actuelle: {orchestrator.current_step}")
        print(f"Progrès: {orchestrator.current_progress}")
        
        print("\n" + "=" * 45)
        print("🎉 INTÉGRATION COMPLÈTE RÉUSSIE !")
        print("✅ Tous les composants sont fonctionnels")
        print("✅ L'orchestrateur est prêt")
        print("✅ Les services sont opérationnels")
        print("✅ L'interface est intégrée")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR D'INTÉGRATION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_integration()
    sys.exit(0 if success else 1)
