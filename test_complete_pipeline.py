#!/usr/bin/env python3
"""
Test du pipeline complet avec tous les modules
"""

import sys
import os
import time
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_complete_pipeline():
    print("🚀 TEST PIPELINE COMPLET NONOTAGS")
    print("=" * 80)
    
    try:
        # Test de l'orchestrateur
        from ui.processing_orchestrator import ProcessingOrchestrator
        orchestrator = ProcessingOrchestrator()
        print("✅ ProcessingOrchestrator initialisé")
        
        # Test sur un album fraîchement créé
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/01_album_standard'
        print(f"🎯 Pipeline complet sur: {test_path}")
        
        # Inventaire initial
        import glob
        files_initial = glob.glob(f"{test_path}/**/*", recursive=True)
        mp3_files = glob.glob(f"{test_path}/*.mp3")
        print(f"📊 État initial:")
        print(f"   Total fichiers: {len(files_initial)}")
        print(f"   Fichiers MP3: {len(mp3_files)}")
        
        # Exécution du pipeline complet
        print("🔥 DÉMARRAGE DU PIPELINE...")
        start_time = time.time()
        
        # Simuler un album pour l'orchestrateur
        album_data = {
            'path': test_path,
            'name': 'Album Test Standard',
            'artist': 'Test Artist',
            'album': 'Test Album'
        }
        
        # Exécution
        success = orchestrator._process_single_album(album_data, 1)
        
        execution_time = time.time() - start_time
        print(f"⏱️ Temps d'exécution: {execution_time:.2f}s")
        print(f"📋 Résultat global: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
        
        # Inventaire final
        files_final = glob.glob(f"{test_path}/**/*", recursive=True)
        print(f"📊 État final:")
        print(f"   Total fichiers: {len(files_final)}")
        
        # Changements détectés
        files_changed = len(files_initial) - len(files_final)
        print(f"🔄 Changements: {files_changed} fichiers")
        
        return success
        
    except Exception as e:
        print(f"❌ ERREUR PIPELINE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_modules_summary():
    """Résumé de tous les tests de modules"""
    print("\n📊 RÉSUMÉ TESTS MODULES")
    print("=" * 50)
    
    modules_results = []
    
    # Module 1 - FileCleaner
    try:
        from core.file_cleaner import FileCleaner
        fc = FileCleaner()
        modules_results.append(("Module 1 - FileCleaner", "✅ OPÉRATIONNEL"))
    except:
        modules_results.append(("Module 1 - FileCleaner", "❌ ÉCHEC"))
    
    # Module 2 - MetadataProcessor  
    try:
        from core.metadata_processor import MetadataProcessor
        mp = MetadataProcessor()
        modules_results.append(("Module 2 - MetadataProcessor", "✅ OPÉRATIONNEL"))
    except:
        modules_results.append(("Module 2 - MetadataProcessor", "❌ ÉCHEC"))
    
    # Module 3 - CaseCorrector
    try:
        from core.case_corrector import CaseCorrector
        cc = CaseCorrector()
        modules_results.append(("Module 3 - CaseCorrector", "✅ FONCTIONNEL"))
    except:
        modules_results.append(("Module 3 - CaseCorrector", "❌ ÉCHEC"))
    
    # Module 4 - MetadataFormatter
    try:
        from core.metadata_formatter import MetadataFormatter
        mf = MetadataFormatter()
        modules_results.append(("Module 4 - MetadataFormatter", "✅ FONCTIONNEL"))
    except:
        modules_results.append(("Module 4 - MetadataFormatter", "❌ ÉCHEC"))
    
    # Module 5 - FileRenamer
    try:
        from core.file_renamer import FileRenamer
        fr = FileRenamer()
        modules_results.append(("Module 5 - FileRenamer", "✅ FONCTIONNEL"))
    except:
        modules_results.append(("Module 5 - FileRenamer", "❌ ÉCHEC"))
    
    # Module 6 - TagSynchronizer
    try:
        from core.tag_synchronizer import TagSynchronizer
        ts = TagSynchronizer()
        modules_results.append(("Module 6 - TagSynchronizer", "✅ FONCTIONNEL"))
    except:
        modules_results.append(("Module 6 - TagSynchronizer", "❌ ÉCHEC"))
    
    # Affichage
    for module, status in modules_results:
        print(f"{status} {module}")
    
    success_count = sum(1 for _, status in modules_results if "✅" in status)
    print(f"\n🎯 BILAN: {success_count}/6 modules fonctionnels")
    
    return success_count == 6

if __name__ == "__main__":
    print("🎵 TESTS COMPLETS NONOTAGS")
    print("=" * 80)
    
    # Test de tous les modules
    modules_ok = test_all_modules_summary()
    
    # Test du pipeline complet
    pipeline_ok = test_complete_pipeline()
    
    # Bilan final
    print("\n🏆 BILAN FINAL")
    print("=" * 50)
    print(f"📦 Modules: {'✅ TOUS OK' if modules_ok else '❌ PROBLÈMES'}")
    print(f"🔄 Pipeline: {'✅ FONCTIONNEL' if pipeline_ok else '❌ DÉFAILLANT'}")
    
    if modules_ok and pipeline_ok:
        print("🎉 NONOTAGS PLEINEMENT OPÉRATIONNEL !")
        exit(0)
    else:
        print("⚠️ Corrections nécessaires")
        exit(1)
