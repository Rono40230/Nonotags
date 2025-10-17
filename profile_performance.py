#!/usr/bin/env python3
"""
Script de profiling pour analyser les performances de Nonotags
Utilise cProfile pour identifier les goulots d'étranglement
"""

import cProfile
import pstats
import io
import sys
import os
from pathlib import Path

# Ajouter le répertoire du projet au path
sys.path.insert(0, str(Path(__file__).parent))

def profile_import_scan():
    """Profile l'import et scan d'un dossier de test"""
    from services.music_scanner import MusicScanner

    # Créer un dossier de test si nécessaire
    test_dir = Path("test_data")
    if not test_dir.exists():
        print("⚠️ Aucun dossier test_data trouvé - profiling sur dossier vide")
        return

    scanner = MusicScanner()

    def progress_callback(current, total):
        print(f"📊 Progression: {current}/{total}")

    # Profiler le scan
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        albums = scanner.scan_directory(str(test_dir), progress_callback)
        print(f"✅ Scan terminé: {len(albums)} albums trouvés")
    except Exception as e:
        print(f"❌ Erreur scan: {e}")

    profiler.disable()

    # Analyser les résultats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 fonctions

    print("\n" + "="*80)
    print("📈 RAPPORT DE PROFILING - TOP 20 FONCTIONS")
    print("="*80)
    print(s.getvalue())

    # Sauvegarder le rapport détaillé
    with open("profiling_report.txt", "w") as f:
        f.write("RAPPORT DE PROFILING DÉTAILLÉ\n")
        f.write("="*50 + "\n\n")
        f.write(s.getvalue())

    print("💾 Rapport sauvegardé dans profiling_report.txt")

def profile_metadata_processing():
    """Profile le traitement des métadonnées"""
    from core.metadata_processor import MetadataProcessor

    processor = MetadataProcessor()

    # Test data
    test_strings = [
        "Titre (version live) ! avec caractères $ spéciaux",
        "Album (remasterisé 2023)   avec   espaces",
        "Artiste and Autre",
        "Titre normal sans problème",
        "Un autre (test) avec [crochets] et {accolades}",
    ] * 100  # Multiplier pour avoir plus de données

    profiler = cProfile.Profile()
    profiler.enable()

    results = []
    for text in test_strings:
        result = processor._apply_cleaning_rules(text)
        results.append(result)

    profiler.disable()

    print(f"✅ Traitement terminé: {len(results)} chaînes nettoyées")

    # Analyser
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(15)

    print("\n" + "="*80)
    print("📈 PROFILING MÉTADONNÉES - TOP 15 FONCTIONS")
    print("="*80)
    print(s.getvalue())

if __name__ == "__main__":
    print("🚀 Démarrage du profiling Nonotags...")
    print("1. Scan d'import")
    print("2. Traitement métadonnées")
    print("3. Les deux")

    choice = input("Choix (1-3): ").strip()

    if choice in ["1", "3"]:
        print("\n🔍 Profiling du scan d'import...")
        profile_import_scan()

    if choice in ["2", "3"]:
        print("\n🔍 Profiling du traitement métadonnées...")
        profile_metadata_processing()

    print("\n✅ Profiling terminé!")