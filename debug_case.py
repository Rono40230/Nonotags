#!/usr/bin/env python3
"""
Script de debug pour le CaseCorrector
"""

try:
    from unittest.mock import patch, MagicMock
    from core.case_corrector import CaseCorrector

    def debug_case_correction():
        with patch('core.case_corrector.AppLogger') as mock_logger_class:
            with patch('core.case_corrector.ConfigManager') as mock_config_class:
                with patch('core.case_corrector.StateManager') as mock_state_class:
                    with patch('core.case_corrector.MetadataValidator') as mock_validator_class:
                        with patch('core.case_corrector.DatabaseManager') as mock_db_class:
                            
                            # Configuration des mocks
                            mock_logger_class.return_value.get_logger.return_value = MagicMock()
                            mock_config_class.return_value.get_processing_config.return_value = {}
                            mock_state_class.return_value = MagicMock()
                            mock_validator_class.return_value = MagicMock()
                            mock_db_class.return_value.get_case_exceptions.return_value = []
                            
                            print("Initializing CaseCorrector...")
                            corrector = CaseCorrector()
                            
                            test_text = "chanson de la vie"
                            print(f"Input: '{test_text}'")
                            
                            # Étape par étape
                            step1 = corrector._apply_title_case(test_text)
                            print(f"After title case: '{step1}'")
                            
                            step2 = corrector._handle_prepositions(step1)
                            print(f"After prepositions: '{step2}'")
                            
                            step3 = corrector._protect_roman_numerals(step2)
                            print(f"After roman numerals: '{step3}'")
                            
                            step4 = corrector._protect_single_i(step3)
                            print(f"After single I: '{step4}'")
                            
                            step5 = corrector._protect_abbreviations(step4)
                            print(f"After abbreviations: '{step5}'")
                            
                            print(f"'LA' in abbreviations: {'LA' in corrector.abbreviations}")
                            print(f"'la' in prepositions: {'la' in corrector.prepositions}")
                            
                            # Test complet
                            result = corrector.correct_text_case(test_text, "title")
                            print(f"Final result: '{result.corrected}'")

    if __name__ == "__main__":
        debug_case_correction()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
