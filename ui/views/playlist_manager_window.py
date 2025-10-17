#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fenêtre de gestion des playlists M3U pour Nonotags
Interface graphique GTK+ pour scanner, créer et gérer les playlists
"""

import os
import threading
from gi.repository import Gtk, GLib, GdkPixbuf, Pango, Gdk
from services.playlist_manager import PlaylistManager, Playlist
from support.honest_logger import HonestLogger

class PlaylistManagerWindow(Gtk.Window):
    """Fenêtre de gestion des playlists - Design 4 blocs comme l'éditeur d'album"""
    
    def __init__(self, parent=None):
        super().__init__()
        
        self.logger = HonestLogger("PlaylistManagerWindow")
        self.playlist_manager = PlaylistManager()
        self.current_playlists = []
        
        # Configuration de la fenêtre
        self.set_title("🎵 Gestionnaire de Playlists M3U")
        self.set_default_size(1200, 800)
        self.maximize()
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        if parent:
            self.set_transient_for(parent)
            self.set_modal(True)
        
        # Callbacks du gestionnaire
        self.playlist_manager.on_scan_progress = self._on_scan_progress
        self.playlist_manager.on_scan_complete = self._on_scan_complete
        self.playlist_manager.on_playlist_created = self._on_playlist_created
        
        # Conteneur principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)
        
        # NOUVEAU : Paned vertical pour régler la répartition entre les blocs
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.paned.set_wide_handle(True)  # Poignée plus large pour faciliter le redimensionnement
        main_box.pack_start(self.paned, True, True, 0)
        
        # BLOC 1 : Playlists trouvées (partie haute du paned)
        playlists_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._create_playlists_section(playlists_container)
        self.paned.pack1(playlists_container, True, True)  # Redimensionnable, peut rétrécir
        
        # BLOC 2 : Détails de la playlist (partie basse du paned)
        details_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._create_playlist_details_block(details_container)
        self.paned.pack2(details_container, True, True)  # Redimensionnable, peut rétrécir
        
        # Position initiale du séparateur (50/50 par défaut)
        GLib.idle_add(self._set_initial_paned_position)
        
        # État initial
        self._update_stats_display()
        
        self.show_all()
        
        # Handler pour fermeture propre de la fenêtre modale (après initialisation complète)
        self.connect("delete-event", self._on_window_close)
    
    def _on_window_close(self, widget, event):
        """Fermeture propre de la fenêtre modale"""
        self.destroy()  # Force la destruction au lieu du cache
        return False    # Permet la fermeture
    
    def _create_playlists_section(self, parent_box):
        """Section playlists trouvées avec stats intégrées (partie haute du paned)"""
        frame = Gtk.Frame(label="Playlists trouvées")
        parent_box.pack_start(frame, True, True, 0)  # Prend tout l'espace disponible
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Stats compactes en haut de cette section
        self._create_compact_stats(vbox)
        
        # Tableau des playlists
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)
        
        # TreeStore pour les playlists (10 colonnes - 2 nouvelles pour les boutons + 1 cachée pour file_path)
        self.playlists_store = Gtk.ListStore(str, str, str, str, str, str, str, str, str, str)
        self.playlists_view = Gtk.TreeView(model=self.playlists_store)
        
        # Colonnes du tableau avec nouvelles colonnes boutons
        columns_config = [
            ("Nom", 0, 200, True),
            ("Répertoire", 1, 180, True),
            ("Pistes", 2, 60, True),
            ("Valides", 3, 60, True),
            ("Manquantes", 4, 80, True),
            ("Durée", 5, 80, True),
            ("Type", 6, 80, True),
            ("Relatif", 7, 100, False),  # Nouvelle colonne bouton
            ("Absolu", 8, 100, False)   # Nouvelle colonne bouton
        ]
        
        for title, col_id, width, sortable in columns_config:
            if col_id in [7, 8]:  # Colonnes boutons
                # Renderer spécial pour boutons avec style
                renderer = Gtk.CellRendererText()
                renderer.set_property("background", "#e3f2fd")
                renderer.set_property("foreground", "#1976d2")
                renderer.set_property("weight", Pango.Weight.BOLD)
                column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            else:
                # Renderer normal pour texte
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(title, renderer, text=col_id)
                if sortable:
                    column.set_sort_column_id(col_id)
            
            column.set_min_width(width)
            column.set_resizable(True)
            self.playlists_view.append_column(column)
        
        # Sélection de playlist
        selection = self.playlists_view.get_selection()
        selection.connect("changed", self._on_playlist_selection_changed)
        
        # Connecter le clic sur les cellules pour les boutons de conversion
        self.playlists_view.connect("button-press-event", self._on_playlist_table_clicked)
        
        scrolled.add(self.playlists_view)
    
    def _create_compact_stats(self, parent_box):
        """Stats compactes avec bouton d'import à gauche et boutons d'action à droite"""
        stats_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        stats_container.set_margin_bottom(10)
        parent_box.pack_start(stats_container, False, False, 0)
        
        # === BOUTON D'IMPORT À GAUCHE ===
        import_btn = Gtk.Button("Importer des playlists")
        import_btn.connect("clicked", self._on_import_playlists)
        import_btn.set_tooltip_text("Sélectionner un dossier contenant des playlists")
        stats_container.pack_start(import_btn, False, False, 0)
        
        # === STATISTIQUES AU CENTRE ===
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        stats_box.set_halign(Gtk.Align.CENTER)
        stats_container.pack_start(stats_box, True, True, 0)  # True, True pour centrer
        
        # Statistiques compactes en une ligne
        stats_labels = [
            ("🎵", "playlists"),
            ("🎶", "pistes"),
            ("✅", "valides"),
            ("❌", "manquantes")
        ]
        
        self.stats_values = {}
        
        for emoji, key in stats_labels:
            # Container pour chaque statistique
            stat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
            
            # Emoji
            emoji_label = Gtk.Label(emoji)
            stat_box.pack_start(emoji_label, False, False, 0)
            
            # Valeur
            value_label = Gtk.Label("0")
            value_label.set_markup("<b>0</b>")
            stat_box.pack_start(value_label, False, False, 0)
            
            stats_box.pack_start(stat_box, False, False, 0)
            
            # Stocker la référence pour mise à jour
            self.stats_values[emoji] = value_label
        
        # === BOUTONS D'ACTION À DROITE ===
        action_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_buttons_box.set_halign(Gtk.Align.END)
        stats_container.pack_end(action_buttons_box, False, False, 0)
        
        # Bouton "Appliquer la conversion" (initialement désactivé)
        self.apply_conversion_btn = Gtk.Button("Appliquer")
        self.apply_conversion_btn.connect("clicked", self._on_apply_conversion)
        self.apply_conversion_btn.set_sensitive(False)
        self.apply_conversion_btn.set_tooltip_text("Appliquer la conversion de chemins")
        action_buttons_box.pack_start(self.apply_conversion_btn, False, False, 0)
        
        # Bouton "Annuler" (initialement désactivé)
        self.cancel_conversion_btn = Gtk.Button("Annuler")
        self.cancel_conversion_btn.connect("clicked", self._on_cancel_conversion)
        self.cancel_conversion_btn.set_sensitive(False)
        self.cancel_conversion_btn.set_tooltip_text("Annuler la conversion en cours")
        action_buttons_box.pack_start(self.cancel_conversion_btn, False, False, 0)
    
    def _on_import_playlists(self, button):
        """Callback du bouton d'import - ouvre le navigateur de dossiers"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier contenant des playlists",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder_path = dialog.get_filename()
            if folder_path:
                # Scanner automatiquement le dossier sélectionné
                self.playlist_manager.add_scan_directory(folder_path)
                self._scan_playlists_in_folder(folder_path)
                self.logger.info(f"Dossier scanné: {folder_path}")
        
        dialog.destroy()
    
    def _scan_playlists_in_folder(self, folder_path):
        """Scanne les playlists dans un dossier et met à jour l'affichage"""
        try:
            # Réinitialiser les playlists
            self.playlists_store.clear()
            
            # Scanner le dossier
            self.playlist_manager._scan_playlists()
            
            # Récupérer les playlists scannées
            self.current_playlists = self.playlist_manager.playlists
            
            # Mettre à jour l'affichage
            self._update_playlists_display()
            self._update_stats_display()
            
        except Exception as e:
            self.logger.error(f"Erreur lors du scan: {e}")
    
    def _on_refresh_playlists(self, button):
        """Actualise la liste des playlists"""
        self.playlist_manager._scan_playlists()
        
        # Récupérer les playlists scannées
        self.current_playlists = self.playlist_manager.playlists
        
        self._update_playlists_display()
        self._update_stats_display()
    
    def _on_open_folder(self, button):
        """Ouvre le dossier de la playlist sélectionnée"""
        selection = self.playlists_view.get_selection()
        model, iter = selection.get_selected()
        if iter:
            folder_path = model[iter][1]  # Colonne répertoire
            if folder_path and os.path.exists(folder_path):
                os.system(f'xdg-open "{folder_path}"')
    
    
    def _create_playlists_table_block(self, parent_box):
        """BLOC 3 : Tableau des playlists trouvées"""
        frame = Gtk.Frame(label="Playlists trouvées")
        parent_box.pack_start(frame, True, True, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Scrolled window pour le tableau
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(250)
        vbox.pack_start(scrolled, True, True, 0)
        
        # TreeStore : Nom, Répertoire, Pistes, Valides, Manquantes, Durée, Type, Chemin complet
        self.playlists_store = Gtk.ListStore(str, str, int, int, int, str, str, str)
        self.playlists_view = Gtk.TreeView(model=self.playlists_store)
        
        # Colonnes du tableau
        columns_config = [
            ("Nom", 0, 200, True),
            ("Répertoire", 1, 250, True),
            ("Pistes", 2, 80, True),
            ("Valides", 3, 80, True),
            ("Manquantes", 4, 80, True),
            ("Durée", 5, 100, False),
            ("Type", 6, 80, True)
        ]
        
        for title, col_id, width, sortable in columns_config:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            if sortable:
                column.set_sort_column_id(col_id)
            self.playlists_view.append_column(column)
        
        # Sélection simple
        selection = self.playlists_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect("changed", self._on_playlist_selection_changed)
        
        # Double-clic pour ouvrir
        self.playlists_view.connect("row-activated", self._on_playlist_activated)
        
        scrolled.add(self.playlists_view)
        
        # Boutons actions playlist
        playlist_actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        refresh_btn = Gtk.Button("Actualiser")
        refresh_btn.connect("clicked", self._on_refresh_playlist)
        playlist_actions_box.pack_start(refresh_btn, False, False, 0)
        
        open_folder_btn = Gtk.Button("Ouvrir le dossier")
        open_folder_btn.connect("clicked", self._on_open_playlist_folder)
        playlist_actions_box.pack_start(open_folder_btn, False, False, 0)
        
        vbox.pack_start(playlist_actions_box, False, False, 0)
    
    def _create_playlist_details_block(self, parent_box):
        """BLOC 2 : Détails de la playlist sélectionnée (partie basse du paned)"""
        frame = Gtk.Frame(label="Détails de la playlist")
        parent_box.pack_start(frame, True, True, 0)  # Prend tout l'espace disponible
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Label nom playlist
        self.playlist_name_label = Gtk.Label("Aucune playlist sélectionnée")
        self.playlist_name_label.set_markup("<b>Aucune playlist sélectionnée</b>")
        self.playlist_name_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.playlist_name_label, False, False, 0)
        
        # === PANNEAUX AVANT/APRÈS CÔTE À CÔTE ===
        comparison_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(comparison_box, True, True, 0)
        
        # === PARTIE 1 : AVANT CONVERSION ===
        before_frame = Gtk.Frame(label="État actuel")
        comparison_box.pack_start(before_frame, True, True, 0)
        
        before_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        before_vbox.set_margin_left(10)
        before_vbox.set_margin_right(10)
        before_vbox.set_margin_top(10)
        before_vbox.set_margin_bottom(10)
        before_frame.add(before_vbox)
        
        # Scrolled window pour les pistes actuelles
        scrolled_before = Gtk.ScrolledWindow()
        scrolled_before.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_before.set_min_content_height(120)
        before_vbox.pack_start(scrolled_before, True, True, 0)
        
        # TreeStore AVANT : État, Piste, Type chemin, Chemin original, Chemin résolu
        self.tracks_before_store = Gtk.ListStore(str, str, str, str, str, str)  # +1 pour file_path complet
        self.tracks_before_view = Gtk.TreeView(model=self.tracks_before_store)
        
        # Colonnes tableau AVANT (plus compactes)
        before_columns_config = [
            ("✓", 0, 30, False),
            ("Piste", 1, 120, True),
            ("Type", 2, 60, True),
            ("Chemin", 3, 180, True),
        ]
        
        for title, col_id, width, sortable in before_columns_config:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            if sortable:
                column.set_sort_column_id(col_id)
            self.tracks_before_view.append_column(column)
        
        scrolled_before.add(self.tracks_before_view)
        
        # === PARTIE 2 : APRÈS CONVERSION ===
        after_frame = Gtk.Frame(label="Aperçu après conversion")
        comparison_box.pack_start(after_frame, True, True, 0)
        
        after_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        after_vbox.set_margin_left(10)
        after_vbox.set_margin_right(10)
        after_vbox.set_margin_top(10)
        after_vbox.set_margin_bottom(10)
        after_frame.add(after_vbox)
        
        # Scrolled window pour l'aperçu
        scrolled_after = Gtk.ScrolledWindow()
        scrolled_after.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_after.set_min_content_height(120)
        after_vbox.pack_start(scrolled_after, True, True, 0)
        
        # TreeStore APRÈS : même structure
        self.tracks_after_store = Gtk.ListStore(str, str, str, str, str, str)
        self.tracks_after_view = Gtk.TreeView(model=self.tracks_after_store)
        
        # Colonnes tableau APRÈS (identiques)
        after_columns_config = [
            ("✓", 0, 30, False),
            ("Piste", 1, 120, True),
            ("Type", 2, 60, True),
            ("Chemin", 3, 180, True),
        ]
        
        for title, col_id, width, sortable in after_columns_config:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            if sortable:
                column.set_sort_column_id(col_id)
            self.tracks_after_view.append_column(column)
        
        scrolled_after.add(self.tracks_after_view)
        # Variables de conversion
        self.current_conversion_type = None  # 'relative' ou 'absolute'
        self.current_playlist = None
    
    # === CALLBACKS CONTRÔLES ===
    
    def _on_add_directory(self, button):
        """Ajoute un répertoire à scanner"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un répertoire",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            directory = dialog.get_filename()
            if directory:
                self.playlist_manager.add_scan_directory(directory)
                self.dirs_store.append([directory])
                self.logger.info(f"Répertoire ajouté: {directory}")
        
        dialog.destroy()
    
    def _on_remove_directory(self, button):
        """Supprime le répertoire sélectionné"""
        selection = self.dirs_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            directory = model[tree_iter][0]
            self.playlist_manager.remove_scan_directory(directory)
            model.remove(tree_iter)
            self.logger.info(f"Répertoire supprimé: {directory}")
    
    def _on_scan_playlists(self, button):
        """Lance le scan des playlists"""
        if not self.playlist_manager.scan_directories:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Aucun répertoire configuré"
            )
            dialog.format_secondary_text("Veuillez ajouter au moins un répertoire à scanner.")
            dialog.run()
            dialog.destroy()
            return
        
        # Désactiver le bouton et démarrer le scan
        self.scan_btn.set_sensitive(False)
        self.scan_btn.set_label("Scan en cours...")
        self.progress_bar.set_text("Initialisation du scan...")
        self.progress_bar.pulse()
        
        # Démarrer le timer de mise à jour de la barre de progression
        self.progress_timer = GLib.timeout_add(100, self._pulse_progress)
        
        # Lancer le scan
        self.playlist_manager.scan_playlists_async()
    
    def _on_create_playlist(self, button):
        """Ouvre le dialog de création de playlist"""
        dialog = PlaylistCreationDialog(self)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            directory = dialog.get_directory()
            name = dialog.get_playlist_name()
            recursive = dialog.get_recursive()
            
            if directory and name:
                # Créer la playlist
                self._create_playlist_async(directory, name, recursive)
        
        dialog.destroy()
    
    def _create_playlist_async(self, directory, name, recursive):
        """Crée une playlist en arrière-plan"""
        def create_worker():
            try:
                playlist = self.playlist_manager.create_playlist_from_directory(
                    directory, name, recursive
                )
                if playlist:
                    GLib.idle_add(self._on_playlist_creation_success, playlist)
                else:
                    GLib.idle_add(self._on_playlist_creation_error, "Aucun fichier audio trouvé")
            except Exception as e:
                GLib.idle_add(self._on_playlist_creation_error, str(e))
        
        thread = threading.Thread(target=create_worker, daemon=True)
        thread.start()
    
    def _on_playlist_creation_success(self, playlist):
        """Callback succès création playlist"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Playlist créée avec succès"
        )
        dialog.format_secondary_text(f"Playlist '{playlist.name}' créée avec {len(playlist.tracks)} pistes.")
        dialog.run()
        dialog.destroy()
        
        # Actualiser l'affichage
        self._update_playlists_display()
        self._update_stats_display()
    
    def _on_playlist_creation_error(self, error_msg):
        """Callback erreur création playlist"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Erreur création playlist"
        )
        dialog.format_secondary_text(error_msg)
        dialog.run()
        dialog.destroy()
    
    # === CALLBACKS SCAN ===
    
    def _on_scan_progress(self, message):
        """Mise à jour progression scan"""
        GLib.idle_add(self._update_scan_progress, message)
    
    def _update_scan_progress(self, message):
        """Met à jour l'affichage de progression (pas d'interface - juste logger)"""
        self.logger.info(f"Scan en cours: {message}")
        return False
    
    def _on_scan_complete(self, playlists):
        """Callback fin de scan"""
        GLib.idle_add(self._finalize_scan, playlists)
    
    def _finalize_scan(self, playlists):
        """Finalise le scan dans le thread principal"""
        # Arrêter le timer de progression
        if hasattr(self, 'progress_timer'):
            GLib.source_remove(self.progress_timer)
        
        # Mettre à jour l'affichage
        self.current_playlists = playlists
        self._update_playlists_display()
        self._update_stats_display()
        
        # Message de fin dans les logs
        self.logger.info(f"Scan terminé - {len(playlists)} playlist{'s' if len(playlists) > 1 else ''} trouvée{'s' if len(playlists) > 1 else ''}")
        
        return False
    
    def _pulse_progress(self):
        """Anime la barre de progression"""
        self.progress_bar.pulse()
        return True
    
    def _on_playlist_created(self, playlist):
        """Callback nouvelle playlist créée"""
        # Déjà géré par _on_playlist_creation_success
        pass
    
    # === CALLBACKS PLAYLISTS ===
    
    def _on_playlist_selection_changed(self, selection):
        """Playlist sélectionnée"""
        model, tree_iter = selection.get_selected()
        if tree_iter:
            playlist_path = model[tree_iter][9]  # Chemin complet (maintenant index 9 avec les nouvelles colonnes)
            playlist = self._find_playlist_by_path(playlist_path)
            if playlist:
                self._display_playlist_details(playlist)
        else:
            self._clear_playlist_details()
    
    def _on_playlist_activated(self, tree_view, path, column):
        """Double-clic sur une playlist"""
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        playlist_path = model[tree_iter][9]  # Chemin complet (maintenant index 9 avec les nouvelles colonnes)
        
        # Ouvrir le fichier playlist avec l'application par défaut
        try:
            import subprocess
            subprocess.run(['xdg-open', playlist_path], check=True)
        except Exception as e:
            self.logger.error(f"Erreur ouverture playlist: {e}")
    
    def _on_refresh_playlist(self, button):
        """Actualise la playlist sélectionnée"""
        selection = self.playlists_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            playlist_path = model[tree_iter][7]  # Chemin complet (maintenant index 7)
            playlist = self._find_playlist_by_path(playlist_path)
            if playlist:
                refreshed = self.playlist_manager.refresh_playlist(playlist)
                if refreshed:
                    self._update_playlists_display()
                    self._display_playlist_details(refreshed)
    
    def _on_open_playlist_folder(self, button):
        """Ouvre le dossier contenant la playlist"""
        selection = self.playlists_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            playlist_path = model[tree_iter][7]  # Chemin complet (maintenant index 7)
            folder = os.path.dirname(playlist_path)
            try:
                import subprocess
                subprocess.run(['xdg-open', folder], check=True)
            except Exception as e:
                self.logger.error(f"Erreur ouverture dossier: {e}")
    
    # === MÉTHODES UTILITAIRES ===
    
    def _update_playlists_display(self):
        """Met à jour l'affichage des playlists"""
        self.playlists_store.clear()
        
        for playlist in self.current_playlists:
            directory = os.path.dirname(playlist.file_path)
            self.playlists_store.append([
                playlist.name,
                directory,
                str(len(playlist.tracks)),  # Convertir en string
                str(playlist.valid_tracks),  # Convertir en string
                str(playlist.invalid_tracks),  # Convertir en string
                playlist.get_formatted_duration(),
                playlist.get_path_type(),
                "🔄",  # Colonne bouton "Relatif"
                "🔄",  # Colonne bouton "Absolu"
                playlist.file_path  # Path (dernière colonne cachée)
            ])
    
    def _update_stats_display(self):
        """Met à jour l'affichage des statistiques"""
        stats = self.playlist_manager.get_playlist_statistics()
        
        # Durée formatée
        total_seconds = stats['total_duration']
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        duration_str = f"{hours}h{minutes:02d}m" if hours > 0 else f"{minutes}m"
        
        # Mise à jour des labels
        updates = {
            '🎵': f"<b>{stats['total_playlists']}</b>",
            '🎶': f"<b>{stats['total_tracks']}</b>",
            '✅': f"<b>{stats['valid_tracks']}</b>",
            '❌': f"<b>{stats['invalid_tracks']}</b>"
        }
        
        for key, value in updates.items():
            if key in self.stats_values:
                self.stats_values[key].set_markup(value)
    
    def _display_playlist_details(self, playlist):
        """Affiche les détails d'une playlist avec état actuel"""
        self.current_playlist = playlist
        
        # Échapper les caractères spéciaux HTML
        import html
        escaped_name = html.escape(playlist.name)
        escaped_summary = html.escape(playlist.get_summary())
        self.playlist_name_label.set_markup(f"<b>{escaped_name}</b> - {escaped_summary}")
        
        # Vider et remplir le tableau AVANT (état actuel)
        self.tracks_before_store.clear()
        self.tracks_after_store.clear()
        
        for track in playlist.tracks:
            status = "✅" if track.exists else "❌"
            filename = os.path.basename(track.file_path)
            
            # Déterminer le type de chemin original
            path_type = "Absolu" if track.is_original_path_absolute() else "Relatif"
            
            self.tracks_before_store.append([
                status,
                filename,
                path_type,
                track.original_path,
                track.file_path,  # Chemin résolu (caché)
                track.file_path   # Pour référence
            ])
        
        # Réinitialiser l'état de conversion
        self._reset_conversion_state()
    
    def _clear_playlist_details(self):
        """Vide les détails de playlist"""
        self.playlist_name_label.set_markup("<b>Aucune playlist sélectionnée</b>")
        self.tracks_before_store.clear()
        self.tracks_after_store.clear()
        self.current_playlist = None
        
        # Désactiver les boutons d'action (les boutons de conversion sont maintenant dans le tableau)
        self.apply_conversion_btn.set_sensitive(False)
        self.cancel_conversion_btn.set_sensitive(False)
        
        self._reset_conversion_state()
    
    def _find_playlist_by_path(self, path):
        """Trouve une playlist par son chemin"""
        for playlist in self.current_playlists:
            if playlist.file_path == path:
                return playlist
        return None
    
    # === MÉTHODES DE CONVERSION ===
    
    def _reset_conversion_state(self):
        """Remet à zéro l'état de conversion"""
        self.current_conversion_type = None
        self.apply_conversion_btn.set_sensitive(False)
        self.cancel_conversion_btn.set_sensitive(False)
    
    def _on_playlist_table_clicked(self, tree_view, event):
        """Gère les clics sur le tableau des playlists (pour les boutons de conversion)"""
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:  # Clic gauche
            path_info = tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, column, cell_x, cell_y = path_info
                
                # Vérifier sur quelle colonne on a cliqué
                columns = tree_view.get_columns()
                col_index = columns.index(column)
                
                if col_index == 7:  # Colonne "Relatif"
                    # Sélectionner la playlist
                    selection = tree_view.get_selection()
                    selection.select_path(path)
                    # Déclencher la conversion relative
                    GLib.idle_add(lambda: self._convert_selected_playlist("relative"))
                    return True
                elif col_index == 8:  # Colonne "Absolu"
                    # Sélectionner la playlist
                    selection = tree_view.get_selection()
                    selection.select_path(path)
                    # Déclencher la conversion absolue
                    GLib.idle_add(lambda: self._convert_selected_playlist("absolute"))
                    return True
        
        return False
    
    def _convert_selected_playlist(self, conversion_type):
        """Convertit la playlist sélectionnée au type spécifié"""
        if not self.current_playlist:
            return
        
        self.current_conversion_type = conversion_type
        self._preview_conversion()
        
        # Activer les boutons d'application
        self.apply_conversion_btn.set_sensitive(True)
        self.cancel_conversion_btn.set_sensitive(True)
        
        # Message informatif
        type_name = "relatifs" if conversion_type == "relative" else "absolus"
        self.logger.info(f"Aperçu de conversion en chemins {type_name} pour {self.current_playlist.name}")

    def _on_convert_to_relative(self, button):
        """Convertir la playlist en chemins relatifs"""
        if not self.current_playlist:
            return
        
        self.current_conversion_type = 'relative'
        self._preview_conversion()
        
        # Activer les boutons d'application
        self.apply_conversion_btn.set_sensitive(True)
        self.cancel_conversion_btn.set_sensitive(True)
    
    def _on_convert_to_absolute(self, button):
        """Convertir la playlist en chemins absolus"""
        if not self.current_playlist:
            return
        
        self.current_conversion_type = 'absolute'
        self._preview_conversion()
        
        # Activer les boutons d'application
        self.apply_conversion_btn.set_sensitive(True)
        self.cancel_conversion_btn.set_sensitive(True)
    
    def _preview_conversion(self):
        """Affiche un aperçu de la conversion dans le tableau APRÈS"""
        if not self.current_playlist or not self.current_conversion_type:
            return
            
        # Vérification supplémentaire pour s'assurer que file_path existe
        if not hasattr(self.current_playlist, 'file_path') or not self.current_playlist.file_path:
            return
        
        # Vider le tableau APRÈS
        self.tracks_after_store.clear()
        
        playlist_dir = os.path.dirname(self.current_playlist.file_path)
        
        for track in self.current_playlist.tracks:
            status = "✅" if track.exists else "❌"
            filename = os.path.basename(track.file_path)
            
            if self.current_conversion_type == 'relative':
                # Convertir vers relatif
                try:
                    if os.path.isabs(track.original_path):
                        # Chemin absolu -> relatif
                        new_path = os.path.relpath(track.file_path, playlist_dir)
                        new_type = "Relatif"
                    else:
                        # Déjà relatif, garder tel quel
                        new_path = track.original_path
                        new_type = "Relatif"
                except ValueError:
                    # Impossible de créer un chemin relatif (disques différents sur Windows)
                    new_path = track.original_path
                    new_type = "Absolu (impossible de convertir)"
                    
            else:  # absolute
                # Convertir vers absolu
                if os.path.isabs(track.original_path):
                    # Déjà absolu, garder tel quel
                    new_path = track.original_path
                else:
                    # Relatif -> absolu
                    new_path = track.file_path  # Le chemin résolu est déjà absolu
                new_type = "Absolu"
            
            self.tracks_after_store.append([
                status,
                filename,
                new_type,
                new_path,
                track.file_path,  # Pour référence (colonne 4)
                track.original_path  # Chemin original (colonne 5)
            ])
    
    def _on_apply_conversion(self, button):
        """Applique la conversion et sauvegarde la playlist"""
        if not self.current_playlist or not self.current_conversion_type:
            return
        
        # Confirmer l'action
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirmer la conversion"
        )
        dialog.format_secondary_text(
            f"Voulez-vous vraiment convertir la playlist '{self.current_playlist.name}' "
            f"en chemins {'relatifs' if self.current_conversion_type == 'relative' else 'absolus'} ?\n\n"
            "Cette action modifiera le fichier M3U sur le disque."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            if not self.current_playlist:
                self.logger.error("Aucune playlist sélectionnée pour la conversion")
                return
                
            success = self._perform_conversion()
            if success:
                # Actualiser l'affichage
                self.playlist_manager._scan_playlists()
                self._update_playlists_display()
                
                # Recharger les détails de la playlist si elle existe encore
                if self.current_playlist and hasattr(self.current_playlist, 'file_path'):
                    updated_playlist = self._find_playlist_by_path(self.current_playlist.file_path)
                    if updated_playlist:
                        self._display_playlist_details(updated_playlist)
                
                # Message de succès
                success_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Conversion réussie"
                )
                success_dialog.format_secondary_text(
                    f"La playlist a été convertie avec succès en chemins "
                    f"{'relatifs' if self.current_conversion_type == 'relative' else 'absolus'}."
                )
                success_dialog.run()
                success_dialog.destroy()
            else:
                # Message d'erreur
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Erreur de conversion"
                )
                error_dialog.format_secondary_text("Une erreur s'est produite lors de la conversion.")
                error_dialog.run()
                error_dialog.destroy()
    
    def _perform_conversion(self):
        """Effectue la conversion et sauvegarde le fichier M3U"""
        try:
            # Vérification de sécurité
            if not self.current_playlist or not hasattr(self.current_playlist, 'file_path') or not self.current_playlist.file_path:
                print("Erreur: Aucune playlist valide sélectionnée")
                return False
                
            playlist_path = self.current_playlist.file_path
            playlist_dir = os.path.dirname(playlist_path)
            
            # Lire le fichier M3U existant pour préserver les commentaires
            with open(playlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Créer le nouveau contenu
            new_lines = []
            track_index = 0
            
            for line in lines:
                line_stripped = line.strip()
                
                # Garder les lignes de commentaires et EXTINF
                if line_stripped.startswith('#') or not line_stripped:
                    new_lines.append(line)
                else:
                    # C'est un chemin de fichier, le convertir
                    if track_index < len(self.current_playlist.tracks):
                        track = self.current_playlist.tracks[track_index]
                        
                        if self.current_conversion_type == 'relative':
                            # Convertir vers relatif
                            try:
                                if os.path.isabs(track.original_path):
                                    new_path = os.path.relpath(track.file_path, playlist_dir)
                                else:
                                    new_path = track.original_path
                            except ValueError:
                                new_path = track.original_path
                        else:  # absolute
                            # Convertir vers absolu
                            if os.path.isabs(track.original_path):
                                new_path = track.original_path
                            else:
                                new_path = track.file_path
                        
                        new_lines.append(new_path + '\n')
                        track_index += 1
                    else:
                        # Garder la ligne telle quelle si on n'a plus de tracks
                        new_lines.append(line)
            
            # Sauvegarder le fichier
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            self.logger.info(f"Playlist convertie: {playlist_path} -> {self.current_conversion_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur conversion playlist: {e}")
            return False
    
    def _on_cancel_conversion(self, button):
        """Annule la conversion"""
        self.tracks_after_store.clear()
        self._reset_conversion_state()
    
    def _set_initial_paned_position(self):
        """Définit la position initiale du séparateur à 50/50"""
        # Obtenir la hauteur totale du paned
        allocation = self.paned.get_allocation()
        if allocation.height > 100:  # S'assurer que la fenêtre est bien dimensionnée
            # Position à 50% de la hauteur
            position = allocation.height // 2
            self.paned.set_position(position)
            self.logger.info(f"Position du séparateur définie à {position}px (50/50)")
        return False  # N'exécuter qu'une fois

class PlaylistCreationDialog(Gtk.Dialog):
    """Dialog pour créer une nouvelle playlist"""
    
    def __init__(self, parent):
        super().__init__(
            title="📝 Créer une nouvelle playlist",
            transient_for=parent,
            flags=0
        )
        
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Créer", Gtk.ResponseType.OK
        )
        
        self.set_default_size(500, 300)
        
        content_area = self.get_content_area()
        content_area.set_spacing(15)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)
        
        # Sélection du répertoire
        dir_label = Gtk.Label("Répertoire source:")
        dir_label.set_halign(Gtk.Align.START)
        content_area.pack_start(dir_label, False, False, 0)
        
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_placeholder_text("Sélectionner un répertoire...")
        self.dir_entry.set_editable(False)
        dir_box.pack_start(self.dir_entry, True, True, 0)
        
        browse_btn = Gtk.Button("Parcourir")
        browse_btn.connect("clicked", self._on_browse_directory)
        dir_box.pack_start(browse_btn, False, False, 0)
        
        content_area.pack_start(dir_box, False, False, 0)
        
        # Nom de la playlist
        name_label = Gtk.Label("Nom de la playlist :")
        name_label.set_halign(Gtk.Align.START)
        content_area.pack_start(name_label, False, False, 0)
        
        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("Ma Playlist")
        content_area.pack_start(self.name_entry, False, False, 0)
        
        # Option récursive
        self.recursive_check = Gtk.CheckButton("Inclure les sous-dossiers")
        self.recursive_check.set_active(True)
        content_area.pack_start(self.recursive_check, False, False, 0)
        
        # Info
        info_label = Gtk.Label()
        info_label.set_markup("<i>La playlist sera créée dans le répertoire sélectionné</i>")
        content_area.pack_start(info_label, False, False, 0)
        
        self.show_all()
    
    def _on_browse_directory(self, button):
        """Sélection du répertoire"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner le répertoire source",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            directory = dialog.get_filename()
            self.dir_entry.set_text(directory)
            
            # Proposer un nom basé sur le dossier
            if not self.name_entry.get_text():
                folder_name = os.path.basename(directory)
                self.name_entry.set_text(folder_name)
        
        dialog.destroy()
    
    def get_directory(self):
        """Retourne le répertoire sélectionné"""
        return self.dir_entry.get_text()
    
    def get_playlist_name(self):
        """Retourne le nom de la playlist"""
        return self.name_entry.get_text().strip()
    
    def get_recursive(self):
        """Retourne si le scan doit être récursif"""
        return self.recursive_check.get_active()
