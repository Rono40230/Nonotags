"""
Application Nonotags simple avec GTK3
Fichier de compatibilité - toutes les classes ont été déplacées vers leurs modules dédiés
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf, Pango, GLib
import os
from typing import List, Dict
from services.music_scanner import MusicScanner
from ui.startup_window import StartupWindow
from ui.components.album_card import AlbumCard
from ui.views.album_edit_window import AlbumEditWindow
from ui.main_app import NonotagsApp

# Fichier de compatibilité - toutes les classes ont été déplacées vers leurs modules dédiés
# Ce fichier maintient la compatibilité avec les imports existants

# Les imports sont disponibles pour la rétrocompatibilité
__all__ = ['AlbumCard', 'AlbumEditWindow', 'NonotagsApp']

if __name__ == "__main__":
    app = NonotagsApp()
    app.run()
