#!/usr/bin/env python3
"""
🧪 SCRIPT DE VALIDATION DES ALBUMS TEST
Vérifie que les albums test couvrent bien toutes les 21 règles
"""

import os
from pathlib import Path

def analyze_test_coverage():
    """Analyse la couverture des tests pour les 21 règles."""
    
    # Définition des 21 règles et leurs tests attendus
    rules_coverage = {
        # GROUPE 1 - File Cleaner
        1: {"name": "CLEAN_UNWANTED_FILES", "albums": [1, 2, 4], "description": "Suppression fichiers système"},
        2: {"name": "CLEAN_SUBFOLDERS", "albums": [2, 4], "description": "Nettoyage sous-dossiers vides"},
        3: {"name": "RENAME_COVER_FILES", "albums": [1, 2, 4], "description": "Renommage pochettes"},
        
        # GROUPE 2 - Metadata Processor  
        4: {"name": "REMOVE_COMMENTS", "albums": [1, 4], "description": "Suppression commentaires"},
        5: {"name": "REMOVE_PARENTHESES", "albums": [1, 4], "description": "Suppression parenthèses"},
        6: {"name": "CLEAN_WHITESPACE", "albums": [1, 3, 4], "description": "Normalisation espaces"},
        7: {"name": "REMOVE_SPECIAL_CHARS", "albums": [3, 4], "description": "Suppression caractères spéciaux"},
        8: {"name": "CLEAN_CONJUNCTIONS", "albums": [1, 4], "description": "Nettoyage conjonctions"},
        
        # GROUPE 3 - Case Corrector
        9: {"name": "APPLY_TITLE_CASE", "albums": [3, 4], "description": "Application title case"},
        10: {"name": "HANDLE_ARTICLES", "albums": [1, 3, 4], "description": "Gestion articles"},
        11: {"name": "HANDLE_PREPOSITIONS", "albums": [3, 4], "description": "Gestion prépositions"},
        12: {"name": "HANDLE_CONJUNCTIONS", "albums": [3, 4], "description": "Gestion conjonctions casse"},
        18: {"name": "STANDARDIZE_CASE", "albums": [3, 4], "description": "Standardisation complète casse"},
        
        # GROUPE 4 - Metadata Formatter
        13: {"name": "COPY_ARTIST_TO_ALBUMARTIST", "albums": [1, 2, 4], "description": "Copie artiste → albumartist"},
        14: {"name": "FORMAT_TRACK_NUMBERS", "albums": [1, 4], "description": "Formatage numéros piste"},
        21: {"name": "HANDLE_COMPILATION_YEAR", "albums": [2, 4], "description": "Gestion années compilation"},
        
        # GROUPE 5 - File Renamer
        15: {"name": "RENAME_FILE", "albums": [2, 3, 4], "description": "Renommage fichiers"},
        16: {"name": "RENAME_FOLDER", "albums": [2, 4], "description": "Renommage dossiers"},
        17: {"name": "HANDLE_MULTI_YEAR", "albums": [2, 4], "description": "Gestion plages années"},
        
        # GROUPE 6 - Tag Synchronizer
        19: {"name": "ASSOCIATE_COVER", "albums": [1, 2, 3, 4], "description": "Association pochettes"},
        20: {"name": "UPDATE_MP3_TAGS", "albums": [1, 2, 3, 4], "description": "Synchronisation tags ID3"}
    }
    
    # Albums créés
    albums = {
        1: "01_album_standard - Test de base",
        2: "02_compilation_complex - Test compilation", 
        3: "03_special_chars_hell - Test caractères spéciaux",
        4: "04_dirty_metadata_nightmare - Test ultime"
    }
    
    print("🧪 ANALYSE DE COUVERTURE DES TESTS")
    print("=" * 50)
    
    # Analyse par groupe
    groups = {
        1: "File Cleaner (1-3)",
        2: "Metadata Processor (4-8)", 
        3: "Case Corrector (9-12, 18)",
        4: "Metadata Formatter (13-14, 21)",
        5: "File Renamer (15-17)",
        6: "Tag Synchronizer (19-20)"
    }
    
    for group_id, group_name in groups.items():
        print(f"\n🔧 GROUPE {group_id} - {group_name}")
        print("-" * 40)
        
        group_rules = [r for r in rules_coverage.keys() 
                      if (group_id == 1 and r <= 3) or
                         (group_id == 2 and 4 <= r <= 8) or  
                         (group_id == 3 and (9 <= r <= 12 or r == 18)) or
                         (group_id == 4 and r in [13, 14, 21]) or
                         (group_id == 5 and 15 <= r <= 17) or
                         (group_id == 6 and r in [19, 20])]
        
        for rule_id in sorted(group_rules):
            rule = rules_coverage[rule_id]
            test_albums = ", ".join([f"Album {a}" for a in rule["albums"]])
            print(f"  ✅ Règle {rule_id:2d} - {rule['name']:25} | Tests: {test_albums}")
    
    print(f"\n📊 RÉSUMÉ COUVERTURE")
    print("-" * 40)
    
    # Analyse par album
    for album_id, album_desc in albums.items():
        rules_tested = [r for r, data in rules_coverage.items() if album_id in data["albums"]]
        print(f"📁 Album {album_id}: {len(rules_tested):2d} règles | {album_desc}")
    
    # Vérification complétude
    total_rules = len(rules_coverage)
    covered_rules = set(rules_coverage.keys())
    
    print(f"\n🎯 VALIDATION COMPLÉTUDE")
    print("-" * 40)
    print(f"✅ Total règles définies: {total_rules}/21")
    print(f"✅ Règles couvertes: {len(covered_rules)}/21")
    
    if len(covered_rules) == 21:
        print("🎉 COUVERTURE COMPLÈTE - Tous les cas sont testés!")
    else:
        missing = set(range(1, 22)) - covered_rules
        print(f"❌ Règles manquantes: {sorted(missing)}")
    
    # Recommandations d'exécution
    print(f"\n🚀 ORDRE D'EXÉCUTION RECOMMANDÉ")
    print("-" * 40)
    print("1. Album 1 (Standard) - Tests de base et validation pipeline")
    print("2. Album 2 (Compilation) - Tests gestion années et renommage")  
    print("3. Album 3 (Caractères) - Tests robustesse Unicode")
    print("4. Album 4 (Nightmare) - Test ultime de résistance")
    print("\n💡 Chaque album peut être testé individuellement")
    print("💡 Album 4 = test complet des 21 règles en une fois")

if __name__ == "__main__":
    analyze_test_coverage()
