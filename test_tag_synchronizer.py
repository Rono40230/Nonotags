#!/usr/bin/env python3
"""
Test spécifique du TagSynchronizer
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_tag_synchronizer():
    print("🔍 TEST TAG SYNCHRONIZER")
    print("=" * 50)
    
    try:
        from core.tag_synchronizer import TagSynchronizer
        ts = TagSynchronizer()
        print("✅ Import et init TagSynchronizer OK")
        
        # Test sur album standard
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/01_album_standard'
        print(f"🎯 Test sur: {test_path}")
        
        # Inventaire
        import glob
        mp3_files = glob.glob(f"{test_path}/*.mp3")
        print(f"📊 Fichiers MP3: {len(mp3_files)}")
        
        # Chercher les méthodes disponibles
        methods = [method for method in dir(ts) if not method.startswith('_') and ('album' in method.lower() or 'sync' in method.lower())]
        print(f"📋 Méthodes disponibles: {methods}")
        
        # Test avec la méthode la plus probable
        if hasattr(ts, 'synchronize_album'):
            result = ts.synchronize_album(test_path)
        elif hasattr(ts, 'sync_album_tags'):
            result = ts.sync_album_tags(test_path)
        elif hasattr(ts, 'process_album'):
            result = ts.process_album(test_path)
        else:
            print("❌ Aucune méthode album trouvée")
            print(f"Toutes les méthodes: {[m for m in dir(ts) if not m.startswith('_')]}")
            return False
            
        print(f"📋 Résultat:")
        print(f"   Type: {type(result)}")
        
        # Analyser le résultat selon le type
        if hasattr(result, 'success'):
            print(f"   Success: {result.success}")
        if hasattr(result, 'files_processed'):
            print(f"   Files processed: {result.files_processed}")
        if hasattr(result, 'files_modified'):
            print(f"   Files modified: {result.files_modified}")
        if hasattr(result, 'total_changes'):
            print(f"   Total changes: {result.total_changes}")
        if hasattr(result, 'errors'):
            errors_count = len(result.errors) if result.errors else 0
            print(f"   Errors: {errors_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_tag_synchronizer()
