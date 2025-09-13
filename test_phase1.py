#!/usr/bin/env python3
"""
Script de test pour les modules de support - Phase 1
Teste tous les modules de support sans interface graphique.
"""

import sys
import os
from pathlib import Path

# Ajout du répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging_module():
    """Test du module de logging."""
    print("🔍 Test du Module 14 - Logging...")
    
    from support.logger import AppLogger, get_logger
    
    # Test création logger
    logger = AppLogger()
    
    # Test des différents niveaux
    logger.debug("Test message DEBUG")
    logger.info("Test message INFO")
    logger.warning("Test message WARNING")
    logger.error("Test message ERROR")
    
    # Test logger spécialisés
    logger.log_import_error("/test/album", "Test error")
    logger.log_metadata_change("/test/file.mp3", "title", "old", "new")
    logger.log_performance("test_operation", 1.234, "test details")
    
    # Test instance globale
    global_logger = get_logger()
    global_logger.info("Test logger global")
    
    print("✅ Module 14 - Logging : OK")
    return True

def test_config_module():
    """Test du module de configuration."""
    print("🔍 Test du Module 15 - Configuration...")
    
    from support.config_manager import ConfigManager
    import tempfile
    import os
    
    # Test avec répertoire temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ConfigManager(temp_dir)
        
        # Test des valeurs par défaut
        print(f"  - Window width: {config.ui.window_width}")
        print(f"  - Auto apply rules: {config.processing.auto_apply_rules}")
        
        assert config.ui.window_width == 1200, f"Expected 1200, got {config.ui.window_width}"
        assert config.processing.auto_apply_rules == True, f"Expected True, got {config.processing.auto_apply_rules}"
        
        # Test modification
        config.set('ui', 'window_width', 1400)
        width_after = config.get('ui', 'window_width')
        assert width_after == 1400, f"Expected 1400, got {width_after}"
        
        # Test sauvegarde/chargement
        save_result = config.save()
        assert save_result == True, f"Save failed: {save_result}"
        
        # Test export/import
        test_export = os.path.join(temp_dir, "test_config.json")
        export_result = config.export_config(test_export)
        assert export_result == True, f"Export failed: {export_result}"
    
    print("✅ Module 15 - Configuration : OK")
    return True

def test_state_module():
    """Test du module de gestion d'état."""
    print("🔍 Test du Module 16 - Gestion d'état...")
    
    from support.state_manager import StateManager, ApplicationState, AlbumState, ImportStatus
    
    # Test création state manager
    state = StateManager()
    
    # Test état application
    state.set_app_state(ApplicationState.READY)
    assert state.get_app_state() == ApplicationState.READY
    
    # Test gestion albums
    album = AlbumState(
        id="test_album_1",
        path="/test/album",
        name="Test Album",
        artist="Test Artist"
    )
    
    assert state.add_album(album) == True
    retrieved_album = state.get_album("test_album_1")
    assert retrieved_album.name == "Test Album"
    
    # Test sélection
    assert state.select_album("test_album_1") == True
    assert "test_album_1" in state.get_selected_albums()
    
    print("✅ Module 16 - Gestion d'état : OK")
    return True

def test_validator_module():
    """Test du module de validation."""
    print("🔍 Test du Module 13 - Validation...")
    
    from support.validator import Validator
    
    # Test création validator
    validator = Validator()
    
    # Test validation métadonnées
    metadata = {
        'title': 'Test Title',
        'artist': 'Test Artist',
        'album': 'Test Album',
        'year': '2024'
    }
    
    result = validator.metadata_validator.validate_complete_metadata(metadata)
    assert result.is_valid == True
    
    # Test validation année invalide
    result = validator.metadata_validator.validate_metadata_field('year', 'invalid')
    assert result.is_valid == False
    
    # Test validation exception
    result = validator.input_validator.validate_exception_word('iPhone')
    assert result.is_valid == True
    
    print("✅ Module 13 - Validation : OK")
    return True

def test_database_module():
    """Test du module de base de données."""
    print("🔍 Test du Module 10 - Base de données...")
    
    from database.db_manager import DatabaseManager
    import tempfile
    
    # Test avec base temporaire
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db = DatabaseManager(db_path)
    
    # Test exceptions de casse
    assert db.add_case_exception('iphone', 'iPhone') == True
    assert db.get_case_exception('iphone') == 'iPhone'
    
    # Test configuration
    assert db.set_config_value('test_key', 'test_value', 'test') == True
    assert db.get_config_value('test_key') == 'test_value'
    
    # Test historique import
    assert db.add_import_record('/test/album', 'success', '', 5, ['rule1', 'rule2']) == True
    
    # Test informations base
    info = db.get_database_info()
    assert 'database_path' in info
    
    # Nettoyage
    os.unlink(db_path)
    
    print("✅ Module 10 - Base de données : OK")
    return True

def main():
    """Fonction principale de test."""
    print("🚀 Test des modules de support - Phase 1")
    print("=" * 50)
    
    tests = [
        test_logging_module,
        test_config_module, 
        test_state_module,
        test_validator_module,
        test_database_module
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} : ERREUR - {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Résultats : {passed} réussis, {failed} échoués")
    
    if failed == 0:
        print("🎉 Tous les modules de support fonctionnent correctement !")
        print("✅ Phase 1 : Fondations et Architecture - COMPLÈTE")
    else:
        print("⚠️  Certains modules nécessitent des corrections")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
