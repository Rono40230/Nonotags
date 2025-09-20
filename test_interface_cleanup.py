#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des modifications d'interface du gestionnaire de playlists
- Suppression des boutons "Actualiser" et "Ouvrir le dossier"
- Déplacement du bouton "Importer des playlists" à gauche des statistiques
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from ui.views.playlist_manager_window import PlaylistManagerWindow

def main():
    """Teste l'interface modifiée du gestionnaire de playlists"""
    
    # Créer l'application
    app = Gtk.Application()
    
    # Créer la fenêtre modifiée
    playlist_window = PlaylistManagerWindow()
    
    # Connecter la fermeture de la fenêtre
    playlist_window.connect("delete-event", Gtk.main_quit)
    
    print("🎵 Gestionnaire de playlists MODIFIÉ lancé")
    print()
    print("✅ MODIFICATIONS APPLIQUÉES :")
    print("🗑️  1. Boutons 'Actualiser' et 'Ouvrir le dossier' SUPPRIMÉS")
    print("📂 2. Bouton 'Importer des playlists' déplacé À GAUCHE des statistiques")
    print("📊 3. Statistiques maintenant CENTRÉES entre Import et boutons d'action")
    print("🎨 4. Interface plus compacte et épurée")
    print()
    print("🎯 NOUVEAU LAYOUT :")
    print("   [Import] [Stats centrées] [Appliquer] [Annuler]")
    print()
    print("❌ Fermez la fenêtre pour arrêter le test")
    
    # Lancer la boucle principale
    Gtk.main()

if __name__ == "__main__":
    main()
