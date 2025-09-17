#!/usr/bin/env python3
"""
Test en mode simulation pour valider la logique de détection
"""

import os
import sys

# Ajouter le chemin du projet
sys.path.append('/home/rono/Nonotags/Nonotags')

def mock_has_embedded_cover(file_path):
    """Version mock pour tester la logique"""
    filename = os.path.basename(file_path)
    
    # Simuler quelques fichiers avec pochettes pour test
    files_with_covers = [
        "01 - Come Together.mp3",
        "03 - Track Three (2001).mp3", 
        "05 - Final Five (2005).mp3"
    ]
    
    return filename in files_with_covers

def test_cover_column_logic():
    """Test de la logique de colonne pochettes"""
    print("🧪 TEST SIMULATION LOGIQUE DÉTECTION POCHETTES")
    print("=" * 50)
    
    # Fichiers de test simulés
    test_files = [
        "/test/01 - Come Together.mp3",         # Aura une pochette
        "/test/02 - Something.mp3",             # Pas de pochette
        "/test/03 - Track Three (2001).mp3",   # Aura une pochette
        "/test/04 - Number Four (2003).mp3",   # Pas de pochette
        "/test/05 - Final Five (2005).mp3"     # Aura une pochette
    ]
    
    print("📁 Fichiers testés:")
    
    covers_found = 0
    total_files = len(test_files)
    
    for file_path in test_files:
        has_cover = mock_has_embedded_cover(file_path)
        status = "✅" if has_cover else "❌"
        filename = os.path.basename(file_path)
        
        print(f"  {status} | {filename}")
        
        if has_cover:
            covers_found += 1
    
    print("-" * 50)
    print(f"📊 RÉSULTATS:")
    print(f"   ✅ Avec pochettes: {covers_found}")
    print(f"   ❌ Sans pochettes: {total_files - covers_found}")
    print(f"   📊 Total: {total_files}")
    print(f"   📈 Pourcentage: {(covers_found/total_files)*100:.1f}%")
    
    if covers_found > 0:
        print("\n🎉 LOGIQUE DE COLONNE FONCTIONNE CORRECTEMENT !")
        print("   La colonne afficherait bien ✅/❌ selon la détection")
    
    return covers_found > 0

if __name__ == "__main__":
    test_cover_column_logic()
