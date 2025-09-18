#!/usr/bin/env python3
"""
Script de lancement Nonotags compatible GTK3
Version de compatibilité pour les systèmes sans GTK4
"""

import sys
import os

# Ajoute le chemin du projet
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
from ui.main_app import NonotagsApp

def main():
    """Point d'entrée principal pour l'UI GTK3"""
    
    # Lancement de Nonotags (mode compatibilité GTK3)
    
    # Style CSS moderne pour GTK3
    css_provider = Gtk.CssProvider()
    css_data = """
    .title-label {
        font-size: 24px;
        font-weight: bold;
        color: #2563eb;
    }
    
    .subtitle-label {
        font-size: 14px;
        color: #64748b;
    }
    
    .album-card {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin: 8px;
        padding: 16px;
    }
    
    .album-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .modern-button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    .modern-button:hover {
        background: #1d4ed8;
    }
    """
    
    css_provider.load_from_data(css_data.encode())
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    
    # Crée et lance l'application
    app = NonotagsApp()
    app.run()

if __name__ == "__main__":
    main()
