#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des optimisations d'affichage du gestionnaire de playlists
- Colonnes de conversion intégrées dans le tableau
- Boutons Appliquer/Annuler repositionnés à droite des statistiques
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from ui.views.playlist_manager_window import PlaylistManagerWindow

def main():
    """Teste les optimisations d'affichage du gestionnaire de playlists"""
    
    # Créer l'application
    app = Gtk.Application()
    
    # Créer la fenêtre optimisée
    playlist_window = PlaylistManagerWindow()
    
    # Connecter la fermeture de la fenêtre
    playlist_window.connect("delete-event", Gtk.main_quit)
    
    print("🎵 Gestionnaire de playlists OPTIMISÉ lancé")
    print()
    print("✨ NOUVELLES FONCTIONNALITÉS D'AFFICHAGE :")
    print("📊 1. Boutons 'Appliquer' et 'Annuler' maintenant à DROITE des statistiques")
    print("🔄 2. Nouvelles colonnes '🔄→ Relatif' et '🔄→ Absolu' dans le tableau")
    print("🖱️  3. Cliquez directement sur ces colonnes pour convertir une playlist")
    print("💾 4. Plus de place pour l'affichage des détails !")
    print()
    print("🧪 TEST DES FONCTIONNALITÉS :")
    print("• Importez des playlists avec le bouton 'Importer des playlists'")
    print("• Cliquez sur les colonnes '🔄→ Relatif' ou '🔄→ Absolu' dans le tableau")
    print("• Utilisez les boutons 'Appliquer' et 'Annuler' à droite des stats")
    print("• Ajustez la répartition avec la barre de séparation")
    print()
    print("❌ Fermez la fenêtre pour arrêter le test")
    
    # Lancer la boucle principale
    Gtk.main()

if __name__ == "__main__":
    main()
