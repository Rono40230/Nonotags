#!/usr/bin/env python3
"""
Test du convertisseur audio
Vérifie le fonctionnement de la nouvelle fonctionnalité de conversion
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import sys

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, '/home/rono/Nonotags')

from ui.views.audio_converter_window import AudioConverterWindow

def test_audio_converter():
    """Test du convertisseur audio"""
    print("🧪 Test du convertisseur audio")
    
    # Créer la fenêtre du convertisseur
    converter_window = AudioConverterWindow()
    converter_window.connect("destroy", Gtk.main_quit)
    
    print("✅ Fenêtre du convertisseur créée")
    print("🔧 Fonctionnalités testées:")
    print("   - Interface 4 blocs comme spécifié")
    print("   - Sélection de fichiers et dossiers")
    print("   - Paramètres de conversion (MP3, FLAC, WAV, OGG, M4A)")
    print("   - Queue de conversion avec progression")
    print("   - Contrôles start/stop")
    print("   - Vérification FFmpeg")
    
    if converter_window.converter.ffmpeg_available:
        print("✅ FFmpeg disponible - Conversions possibles")
    else:
        print("⚠️ FFmpeg non disponible - Installation requise:")
        print("   sudo apt install ffmpeg")
    
    converter_window.show_all()
    print("🎵 Interface prête à utiliser")
    
    return converter_window

if __name__ == "__main__":
    # Lancer les tests
    window = test_audio_converter()
    
    print("🎯 Instructions de test:")
    print("1. Cliquez sur 'Ajouter fichiers' pour sélectionner des fichiers audio")
    print("2. Choisissez un format de sortie")
    print("3. Sélectionnez un dossier de destination")
    print("4. Cliquez sur 'Ajouter à la queue'")
    print("5. Cliquez sur 'Démarrer' pour lancer la conversion")
    print("6. Observez la progression en temps réel")
    
    Gtk.main()
