#!/usr/bin/env python3
"""
Test spécifique du MetadataFormatter
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_metadata_formatter():
    print("🔍 TEST METADATA FORMATTER")
    print("=" * 50)
    
    try:
        from core.metadata_formatter import MetadataFormatter
        mf = MetadataFormatter()
        print("✅ Import et init MetadataFormatter OK")
        
        # Test sur album compilation (années multiples)
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/02_compilation_complex'
        print(f"🎯 Test sur: {test_path}")
        
        # Inventaire avant
        import glob
        mp3_files = glob.glob(f"{test_path}/*.mp3")
        print(f"📊 Fichiers MP3: {len(mp3_files)}")
        for f in sorted(mp3_files):
            name = os.path.basename(f)
            if '1995' in name or '1998' in name or '2001' in name:
                print(f"   📅 {name}")
        
        # Chercher la méthode appropriée
        methods = [method for method in dir(mf) if not method.startswith('_') and 'album' in method.lower()]
        print(f"📋 Méthodes disponibles: {methods}")
        
        # Test avec la méthode la plus probable
        if hasattr(mf, 'format_album_metadata'):
            result = mf.format_album_metadata(test_path)
        elif hasattr(mf, 'process_album'):
            result = mf.process_album(test_path)
        elif hasattr(mf, 'format_album'):
            result = mf.format_album(test_path)
        else:
            print("❌ Aucune méthode album trouvée")
            return False
            
        print(f"📋 Résultat:")
        print(f"   Type: {type(result)}")
        
        # Adapter selon le type de résultat
        if hasattr(result, 'success'):
            print(f"   Success: {result.success}")
        if hasattr(result, 'files_processed'):
            print(f"   Files processed: {result.files_processed}")
        if hasattr(result, 'files_modified'):
            print(f"   Files modified: {result.files_modified}")
        if hasattr(result, 'total_changes'):
            print(f"   Total changes: {result.total_changes}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_metadata_formatter()
