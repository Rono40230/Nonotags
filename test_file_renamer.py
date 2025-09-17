#!/usr/bin/env python3
"""
Test spécifique du FileRenamer
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_file_renamer():
    print("🔍 TEST FILE RENAMER")
    print("=" * 50)
    
    try:
        from core.file_renamer import FileRenamer
        fr = FileRenamer()
        print("✅ Import et init FileRenamer OK")
        
        # Test sur album avec problèmes de nommage
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/03_special_chars_hell'
        print(f"🎯 Test sur: {test_path}")
        
        # Inventaire avant (fichiers avec problèmes de casse/caractères)
        import glob
        files_before = glob.glob(f"{test_path}/*")
        print(f"📊 Fichiers avant: {len(files_before)}")
        problem_files = []
        for f in sorted(files_before):
            name = os.path.basename(f)
            if 'MAJUSCULES' in name or 'minuscules' in name or '$' in name or '@' in name:
                problem_files.append(name)
                print(f"   🔤 {name}")
        
        print(f"📋 Fichiers problématiques: {len(problem_files)}")
        
        # Chercher les méthodes disponibles
        methods = [method for method in dir(fr) if not method.startswith('_') and ('album' in method.lower() or 'rename' in method.lower())]
        print(f"📋 Méthodes disponibles: {methods}")
        
        # Test avec la méthode la plus probable
        if hasattr(fr, 'rename_album_files'):
            result = fr.rename_album_files(test_path)
        elif hasattr(fr, 'process_album'):
            result = fr.process_album(test_path)
        elif hasattr(fr, 'rename_files_in_album'):
            result = fr.rename_files_in_album(test_path)
        else:
            print("❌ Aucune méthode album trouvée")
            print(f"Toutes les méthodes: {[m for m in dir(fr) if not m.startswith('_')]}")
            return False
            
        print(f"📋 Résultat:")
        print(f"   Type: {type(result)}")
        
        # Analyser le résultat
        if hasattr(result, 'files_renamed'):
            print(f"   Files renamed: {result.files_renamed}")
        if hasattr(result, 'success'):
            print(f"   Success: {result.success}")
        if hasattr(result, 'errors'):
            print(f"   Errors: {len(result.errors) if result.errors else 0}")
        
        # Inventaire après
        files_after = glob.glob(f"{test_path}/*")
        print(f"📊 Fichiers après: {len(files_after)}")
        
        remaining_problems = []
        for f in sorted(files_after):
            name = os.path.basename(f)
            if 'MAJUSCULES' in name or 'minuscules' in name or '$' in name or '@' in name:
                remaining_problems.append(name)
                print(f"   🔤 Encore: {name}")
        
        renamed_count = len(problem_files) - len(remaining_problems)
        print(f"📊 Fichiers effectivement renommés: {renamed_count}")
        
        return renamed_count > 0 or len(remaining_problems) == 0
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_file_renamer()
