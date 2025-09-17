#!/usr/bin/env python3
"""
Test des corrections de formatage FileRenamer
- Numérotation : 01, 02, 03 au lieu de 1, 2, 3
- Extensions : Noms sans .mp3
"""

import sys
import os
sys.path.append('.')

from core.file_renamer import FileRenamer

def test_track_formatting():
    """Test du formatage des numéros de piste"""
    renamer = FileRenamer()
    
    test_cases = [
        ("1", "My Song", ".mp3"),
        ("2", "Another Track", ".mp3"),
        ("10", "Double Digit", ".mp3"),
        ("1/12", "With Total", ".mp3")
    ]
    
    print("🧪 TEST FORMATAGE NUMÉROS DE PISTE")
    print("=" * 50)
    
    for track_num, title, ext in test_cases:
        formatted_name, rules = renamer.format_track_filename(track_num, title, ext)
        print(f"📝 Input:  '{track_num}' + '{title}' + '{ext}'")
        print(f"✅ Output: '{formatted_name}'")
        print(f"📋 Règles: {[r.value for r in rules]}")
        print("-" * 30)

if __name__ == "__main__":
    test_track_formatting()
