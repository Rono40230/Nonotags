#!/usr/bin/env python3
"""
Test complet du pipeline NonoTags
Teste chaque module individuellement puis en séquence complète
"""

import sys
import os
import traceback
from pathlib import Path

# Ajout du chemin pour les imports
sys.path.insert(0, '/home/rono/Nonotags/Nonotags')

def test_imports():
    """Test de tous les imports nécessaires"""
    print("🔍 TEST DES IMPORTS")
    print("=" * 50)
    
    modules = [
        ('core.file_cleaner', 'FileCleaner'),
        ('core.metadata_processor', 'MetadataProcessor'),
        ('core.case_corrector', 'CaseCorrector'),
        ('core.metadata_formatter', 'MetadataFormatter'),
        ('core.file_renamer', 'FileRenamer'),
        ('core.tag_synchronizer', 'TagSynchronizer'),
        ('support.validator', 'FileValidator'),
        ('support.honest_logger', 'HonestLogger')
    ]
    
    results = {}
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls()
            results[module_name] = "✅ OK"
            print(f"✅ {module_name}.{class_name} - Import et instanciation OK")
        except Exception as e:
            results[module_name] = f"❌ ERREUR: {e}"
            print(f"❌ {module_name}.{class_name} - ERREUR: {e}")
    
    return results

def test_file_cleaner():
    """Test spécifique du FileCleaner"""
    print("\n🧹 TEST FILE CLEANER")
    print("=" * 50)
    
    try:
        from core.file_cleaner import FileCleaner
        fc = FileCleaner()
        
        # Test sur l'album 3 (caractères spéciaux)
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/03_special_chars_hell'
        if not os.path.exists(test_path):
            print(f"❌ Album test introuvable: {test_path}")
            return False
            
        print(f"🎯 Test du nettoyage sur: {test_path}")
        
        # Inventaire avant
        files_before = list(Path(test_path).rglob('*'))
        print(f"📊 Fichiers avant nettoyage: {len(files_before)}")
        
        # Exécution du nettoyage
        result = fc.clean_album_folder(test_path)
        
        # Inventaire après
        files_after = list(Path(test_path).rglob('*'))
        print(f"📊 Fichiers après nettoyage: {len(files_after)}")
        
        print(f"📋 Résultat: files_deleted={result.files_deleted}, files_renamed={result.files_renamed}")
        
        # Calculer le "succès" basé sur l'activité
        total_activity = result.files_deleted + result.files_renamed + result.folders_deleted
        success = total_activity > 0
        
        if hasattr(result, 'errors') and result.errors:
            print(f"⚠️ Erreurs détectées: {len(result.errors)}")
            for i, error in enumerate(result.errors[:3]):
                print(f"   {i+1}. {error}")
        
        return success
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE dans test_file_cleaner: {e}")
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test du ProcessingOrchestrator"""
    print("\n🎼 TEST ORCHESTRATOR")
    print("=" * 50)
    
    try:
        from ui.processing_orchestrator import ProcessingOrchestrator
        orchestrator = ProcessingOrchestrator()
        
        # Test sur l'album 3 (caractères spéciaux)
        test_path = '/home/rono/Nonotags/Nonotags/test_albums/03_special_chars_hell'
        print(f"🎯 Test orchestration complète sur: {test_path}")
        
        # Simuler un album dict
        album_data = {'path': test_path, 'name': 'Album Caractères Spéciaux Test'}
        
        # Exécution via _process_single_album pour test
        success = orchestrator._process_single_album(album_data, 1)
        print(f"📋 Résultat orchestration: {success}")
        
        return success
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE dans test_orchestrator: {e}")
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DU TEST PIPELINE COMPLET")
    print("=" * 80)
    
    # Phase 1: Test des imports
    import_results = test_imports()
    
    # Phase 2: Test du FileCleaner
    cleaner_success = test_file_cleaner()
    
    # Phase 3: Test de l'orchestrateur
    orchestrator_success = test_orchestrator()
    
    # Résumé final
    print("\n📊 RÉSUMÉ FINAL")
    print("=" * 50)
    
    failed_imports = [mod for mod, result in import_results.items() if "❌" in result]
    if failed_imports:
        print(f"❌ Imports échoués: {len(failed_imports)}")
        for mod in failed_imports:
            print(f"   - {mod}: {import_results[mod]}")
    else:
        print("✅ Tous les imports réussis")
    
    print(f"🧹 FileCleaner: {'✅ OK' if cleaner_success else '❌ ÉCHEC'}")
    print(f"🎼 Orchestrator: {'✅ OK' if orchestrator_success else '❌ ÉCHEC'}")
    
    # État du système
    if len(failed_imports) == 0 and cleaner_success and orchestrator_success:
        print("\n🎉 PIPELINE COMPLET FONCTIONNEL !")
        return 0
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS - Correction nécessaire")
        return 1

if __name__ == "__main__":
    sys.exit(main())
