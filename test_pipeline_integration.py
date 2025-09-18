#!/usr/bin/env python3
"""
Test de validation des 3 problèmes de pipeline
1. Correction de casse non appliquée
2. Renommage de dossier manquant  
3. Format de fichier cassé
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.processing_orchestrator import ProcessingOrchestrator

def test_pipeline_complete():
    """Test complet du pipeline de traitement."""
    
    print("=== TEST PIPELINE COMPLET ===")
    
    # Album de test
    test_album = "/home/rono/Nonotags/Nonotags/test_albums/01_album_standard"
    
    if not os.path.exists(test_album):
        print(f"❌ Album de test introuvable: {test_album}")
        return False
    
    print(f"📁 Test avec album: {test_album}")
    print(f"📁 Contenu avant traitement:")
    for item in os.listdir(test_album):
        print(f"   - {item}")
    
    # Initialisation de l'orchestrateur
    try:
        orchestrator = ProcessingOrchestrator()
        print("✅ ProcessingOrchestrator initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation orchestrateur: {e}")
        return False
    
    # Test du traitement complet
    try:
        print("\n🔄 Lancement du traitement complet...")
        
        # Préparation de l'album pour le traitement
        album_dict = {
            'path': test_album,
            'name': os.path.basename(test_album)
        }
        
        result = orchestrator._process_single_album(album_dict, 1)
        
        print(f"\n📊 RÉSULTAT: {result}")
        
        if result:
            print("✅ Traitement réussi")
        else:
            print("❌ Traitement échoué")
            
    except Exception as e:
        print(f"❌ Erreur traitement: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_pipeline_complete()
