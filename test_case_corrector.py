#!/usr/bin/env python3
"""
Test spécifique du CaseCorrector
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_case_corrector():
    print("🔍 TEST CASE CORRECTOR")
    print("=" * 50)
    
    try:
        from core.case_corrector import CaseCorrector
        cc = CaseCorrector()
        print("✅ Import et init CaseCorrector OK")
        
        # Test sur album avec problèmes de casse 
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/03_special_chars_hell'
        print(f"🎯 Test sur: {test_path}")
        
        # Liste des fichiers avant
        import glob
        files_before = glob.glob(f"{test_path}/*")
        print(f"📊 Fichiers avant: {len(files_before)}")
        for f in sorted(files_before):
            if 'MAJUSCULES' in f or 'minuscules' in f:
                print(f"   📝 {os.path.basename(f)}")
        
        # Test du traitement
        result = cc.correct_album_case(test_path)
        print(f"📋 Résultat:")
        print(f"   Type result: {type(result)}")
        print(f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Le résultat est un Dict[str, CaseCorrectionResult]
        total_files_renamed = 0
        total_errors = 0
        
        for file_path, correction_result in result.items():
            if hasattr(correction_result, 'renamed') and correction_result.renamed:
                total_files_renamed += 1
                print(f"   ✅ Renommé: {os.path.basename(file_path)}")
            if hasattr(correction_result, 'errors') and correction_result.errors:
                total_errors += len(correction_result.errors)
        
        print(f"   Files renamed: {total_files_renamed}")
        print(f"   Total errors: {total_errors}")
        
        # Liste des fichiers après
        files_after = glob.glob(f"{test_path}/*")
        print(f"📊 Fichiers après: {len(files_after)}")
        for f in sorted(files_after):
            if 'MAJUSCULES' in f or 'minuscules' in f or 'Majuscules' in f or 'Minuscules' in f:
                print(f"   📝 {os.path.basename(f)}")
        
        # Calculer succès
        success = total_files_renamed > 0 or total_errors == 0
        
        return success
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_case_corrector()
