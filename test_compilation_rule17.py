#!/usr/bin/env python3
"""
Test spécifique de la RÈGLE 17 corrigée - Format compilation
"""
import sys
sys.path.append('.')

from core.file_renamer import FileRenamer

def test_compilation_format():
    """Test du format de compilation corrigé"""
    print("=== TEST RÈGLE 17 - FORMAT COMPILATION CORRIGÉ ===")
    
    try:
        fr = FileRenamer()
        print("✅ FileRenamer initialisé")
        
        # Test 1: Cas du README (1995-2005)
        test_year1 = "1995, 1998, 2001, 2003, 2005"
        result1, rules1 = fr._handle_multi_year_folder(test_year1)
        print(f"\nTest 1: '{test_year1}'")
        print(f"  → '{result1}' (attendu: '1995-05')")
        print(f"  Règles: {rules1}")
        
        # Test 2: Autre plage  
        test_year2 = "1990, 1995, 2000"
        result2, rules2 = fr._handle_multi_year_folder(test_year2)
        print(f"\nTest 2: '{test_year2}'")
        print(f"  → '{result2}' (attendu: '1990-00')")
        print(f"  Règles: {rules2}")
        
        # Test 3: Années proches
        test_year3 = "2020, 2021, 2022"
        result3, rules3 = fr._handle_multi_year_folder(test_year3)
        print(f"\nTest 3: '{test_year3}'")
        print(f"  → '{result3}' (attendu: '2020-22')")
        print(f"  Règles: {rules3}")
        
        # Validation
        if result1 == "1995-05" and result2 == "1990-00" and result3 == "2020-22":
            print("\n🎉 TOUS LES TESTS PASSENT - RÈGLE 17 CORRIGÉE !")
        else:
            print("\n❌ Certains tests échouent")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compilation_format()
