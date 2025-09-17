#!/usr/bin/env python3
"""
Test spécifique du MetadataProcessor
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_metadata_processor():
    print("🔍 TEST METADATA PROCESSOR")
    print("=" * 50)
    
    try:
        from core.metadata_processor import MetadataProcessor
        mp = MetadataProcessor()
        print("✅ Import et init MetadataProcessor OK")
        
        # Test sur album standard
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/01_album_standard'
        print(f"🎯 Test sur: {test_path}")
        
        # Liste des MP3 
        import glob
        mp3_files = glob.glob(f"{test_path}/*.mp3")
        print(f"📊 Fichiers MP3 trouvés: {len(mp3_files)}")
        
        # Test du traitement
        result = mp.clean_album_metadata(test_path)
        print(f"📋 Résultat:")
        print(f"   Files processed: {result.files_processed}")
        print(f"   Files modified: {result.files_modified}")
        print(f"   Total changes: {result.total_changes}")
        print(f"   Total errors: {result.total_errors}")
        
        # Calculer succès
        success = result.total_errors == 0 and result.files_processed > 0
        
        if result.total_errors > 0:
            print(f"⚠️ Erreurs détectées: {result.total_errors}")
        
        return success
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_metadata_processor()
