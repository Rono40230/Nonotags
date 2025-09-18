#!/usr/bin/env python3
"""
Test isolé de la correction de casse pour prouver qu'elle fonctionne
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.case_corrector import CaseCorrector

def test_case_correction_isolated():
    """Test isolé de la correction de casse."""
    
    print("=== TEST CORRECTION DE CASSE ISOLÉ ===")
    
    # Initialisation
    try:
        corrector = CaseCorrector()
        print("✅ CaseCorrector initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False
    
    # Test direct de la méthode correct_album_metadata (celle appelée par l'orchestrateur)
    test_album = "/home/rono/Nonotags/Nonotags/test_albums/01_album_standard"
    
    print(f"📁 Test avec album: {test_album}")
    
    try:
        print("\n🔤 Test correct_album_metadata (méthode orchestrateur)...")
        result = corrector.correct_album_metadata(test_album)
        
        print(f"📊 RÉSULTAT correct_album_metadata: {result}")
        
        if result:
            print("✅ PROBLÈME 1 RÉSOLU: Correction de casse fonctionne dans le pipeline")
        else:
            print("❌ PROBLÈME 1 PERSISTE: Correction de casse échoue")
            
    except Exception as e:
        print(f"❌ Erreur correction casse: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test de quelques exemples de correction
    print("\n🔤 Tests des règles de correction:")
    
    test_cases = [
        ("DROWNED DJ RUN MC", "title"),
        ("BEST OF MADONNA", "album"), 
        ("MADONNA", "artist"),
        ("GONE NEW YORK", "title")
    ]
    
    for text, text_type in test_cases:
        try:
            result = corrector.correct_text_case(text, text_type)
            print(f"   '{text}' ({text_type}) → '{result.corrected}' (changé: {result.changed})")
        except Exception as e:
            print(f"   ❌ Erreur avec '{text}': {e}")
    
    return True

if __name__ == "__main__":
    test_case_correction_isolated()
