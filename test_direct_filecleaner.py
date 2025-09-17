#!/usr/bin/env python3
"""
Test minimal et direct du FileCleaner
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_direct():
    print("🔍 Test minimal FileCleaner")
    
    # Import et init
    from core.file_cleaner import FileCleaner
    print("✅ Import OK")
    
    fc = FileCleaner()
    print("✅ Init OK")
    
    # Test path
    test_path = '/home/rono/Nonotags/Nonotags/test_albums/03_special_chars_hell'
    print(f"🎯 Test path: {test_path}")
    print(f"📁 Path exists: {os.path.exists(test_path)}")
    
    # Liste des fichiers avant
    import glob
    files_before = glob.glob(f"{test_path}/**/*", recursive=True)
    print(f"📊 Files before: {len(files_before)}")
    
    # Nettoyage
    print("🚀 Début nettoyage...")
    try:
        result = fc.clean_album_folder(test_path)
        print("✅ Nettoyage terminé")
        print(f"   Files deleted: {result.files_deleted}")
        print(f"   Folders deleted: {result.folders_deleted}")
        print(f"   Files renamed: {result.files_renamed}")
        
        # Liste des fichiers après
        files_after = glob.glob(f"{test_path}/**/*", recursive=True)
        print(f"📊 Files after: {len(files_after)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_direct()
