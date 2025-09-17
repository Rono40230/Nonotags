#!/usr/bin/env python3
"""
Test direct du FileRenamer sur le vrai album
"""

import sys
import os
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_filerenamer_real_album():
    print("🔍 TEST FILERENAMER SUR VRAI ALBUM")
    print("=" * 50)
    
    try:
        from core.file_renamer import FileRenamer
        fr = FileRenamer()
        print("✅ FileRenamer initialisé")
        
        # Test sur le vrai album de l'appli
        test_path = '/home/rono/Téléchargements/1'
        print(f"🎯 Test sur: {test_path}")
        
        # Inventaire avant
        import glob
        mp3_files = glob.glob(f"{test_path}/*.mp3") + glob.glob(f"{test_path}/*.MP3")
        print(f"📊 Fichiers MP3 trouvés: {len(mp3_files)}")
        for f in sorted(mp3_files):
            name = os.path.basename(f)
            print(f"   🎵 {name}")
        
        # Test de validation sur le premier fichier
        from support.validator import FileValidator
        validator = FileValidator()
        
        if mp3_files:
            first_file = mp3_files[0]
            print(f"\n🔍 Test validation sur: {os.path.basename(first_file)}")
            validation = validator.validate_mp3_file(first_file)
            print(f"   Valid: {validation.is_valid}")
            print(f"   Errors: {validation.errors}")
            print(f"   Details: {validation.details}")
        
        # Test du renommage complet
        print(f"\n🚀 Lancement du renommage...")
        result = fr.rename_album(test_path)
        
        print(f"📋 Résultat du renommage:")
        print(f"   Files renamed: {result.files_renamed}")
        print(f"   Total files: {result.total_files}")
        print(f"   Folder renamed: {result.folder_renamed}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        
        if result.errors:
            print(f"\n❌ Erreurs détectées:")
            for i, error in enumerate(result.errors[:5]):
                print(f"   {i+1}. {error}")
        
        # Inventaire après
        mp3_files_after = glob.glob(f"{test_path}/*.mp3") + glob.glob(f"{test_path}/*.MP3")
        print(f"\n📊 Fichiers après: {len(mp3_files_after)}")
        for f in sorted(mp3_files_after):
            name = os.path.basename(f)
            if name.startswith(('01 -', '02 -', '03 -', '1 -', '2 -', '3 -')):
                print(f"   ✅ {name}")
            else:
                print(f"   ❓ {name}")
        
        return result.files_renamed > 0
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_filerenamer_real_album()
