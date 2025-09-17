#!/usr/bin/env python3
"""
🔍 AUDIT TECHNIQUE COMPLET - Diagnostic infrastructure NonoTags
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 AUDIT TECHNIQUE COMPLET - NonoTags")
    print("=" * 60)
    
    # Test 1: Environnement Python
    print(f"\n📍 Python Version: {sys.version}")
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"📍 Python Path: {sys.path[:3]}...")
    
    # Test 2: Structure des dossiers
    print(f"\n📂 STRUCTURE DOSSIERS:")
    required_dirs = ['core', 'support', 'ui', 'database', 'services']
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/: OK")
        else:
            print(f"  ❌ {dir_name}/: MANQUANT")
    
    # Test 3: Fichiers core critiques
    print(f"\n📄 FICHIERS CORE:")
    core_files = [
        'core/metadata_processor.py',
        'core/case_corrector.py', 
        'core/metadata_formatter.py',
        'core/file_renamer.py',
        'core/tag_synchronizer.py',
        'core/file_cleaner.py'  # Celui qui manque selon l'analyse
    ]
    
    for file_path in core_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}: OK")
        else:
            print(f"  ❌ {file_path}: MANQUANT")
    
    # Test 4: Support files
    print(f"\n🛠️ FICHIERS SUPPORT:")
    support_files = [
        'support/honest_logger.py',
        'support/logger.py',
        'support/config_manager.py'
    ]
    
    for file_path in support_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}: OK")
        else:
            print(f"  ❌ {file_path}: MANQUANT")
    
    # Test 5: Imports basiques
    print(f"\n🔗 TEST IMPORTS BASIQUES:")
    
    # Test import support
    try:
        sys.path.insert(0, '.')
        from support.honest_logger import HonestLogger
        print(f"  ✅ support.honest_logger: OK")
    except Exception as e:
        print(f"  ❌ support.honest_logger: {e}")
    
    # Test import core existants
    core_modules = [
        ('core.metadata_processor', 'MetadataProcessor'),
        ('core.case_corrector', 'CaseCorrector')
    ]
    
    for module_name, class_name in core_modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✅ {module_name}.{class_name}: OK")
        except ImportError as e:
            print(f"  ❌ {module_name}.{class_name}: ImportError - {e}")
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name}: {type(e).__name__} - {e}")
    
    # Test 6: Test file_cleaner manquant
    print(f"\n🚨 TEST MODULE MANQUANT:")
    try:
        from core.file_cleaner import FileCleaner
        print(f"  ✅ core.file_cleaner.FileCleaner: OK")
    except Exception as e:
        print(f"  ❌ core.file_cleaner.FileCleaner: {e}")
        print(f"  📋 CONFIRME: Module file_cleaner manquant (selon analyse)")
    
    # Test 7: ProcessingOrchestrator
    print(f"\n🎯 TEST ORCHESTRATEUR:")
    try:
        from ui.processing_orchestrator import ProcessingOrchestrator
        print(f"  ✅ Import ProcessingOrchestrator: OK")
        
        # Test initialisation
        orchestrator = ProcessingOrchestrator()
        print(f"  ✅ Initialisation ProcessingOrchestrator: OK")
        
    except Exception as e:
        print(f"  ❌ ProcessingOrchestrator: {type(e).__name__} - {e}")
        import traceback
        print(f"  📜 Traceback complet:")
        traceback.print_exc()
    
    print(f"\n🎯 CONCLUSION AUDIT TECHNIQUE:")
    print(f"📋 Voir détails ci-dessus pour identifier problèmes exacts")

if __name__ == "__main__":
    main()
