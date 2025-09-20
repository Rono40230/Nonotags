"""
Fenêtre de conversion audio
Interface pour convertir des fichiers audio entre différents formats
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, GdkPixbuf
import os
import threading
from services.audio_converter import AudioConverter, ConversionStatus, AudioFormat

class AudioConverterWindow(Gtk.Window):
    """Fenêtre de conversion audio avec layout 4 blocs"""
    
    def __init__(self):
        super().__init__(title="🔄 Convertisseur Audio")
        
        # Configuration de la fenêtre
        self.set_default_size(1000, 700)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Service de conversion
        self.converter = AudioConverter()
        self._setup_converter_callbacks()
        
        # Variables d'état
        self.selected_files = []
        
        # Conteneur principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)
        
        # Conteneur haut pour les blocs 1 et 2 (côte à côte)
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.pack_start(top_box, True, True, 0)
        
        # BLOC 1 : Sélection des fichiers (haut gauche)
        self._create_file_selection_block(top_box)
        
        # BLOC 2 : Paramètres de conversion (haut droite)
        self._create_settings_block(top_box)
        
        # BLOC 3 : Queue de conversion (toute la largeur)
        self._create_conversion_queue_block(main_box)
        
        # BLOC 4 : Contrôles et progression (toute la largeur)
        self._create_controls_block(main_box)
        
        # Vérification initiale de FFmpeg
        self._check_ffmpeg_availability()
    
    def _create_file_selection_block(self, parent_box):
        """BLOC 1 : Sélection des fichiers sources"""
        frame = Gtk.Frame(label="📁 Fichiers sources")
        frame.set_size_request(450, 350)
        parent_box.pack_start(frame, True, True, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Boutons d'ajout
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        add_files_btn = Gtk.Button("➕ Ajouter fichiers")
        add_files_btn.connect("clicked", self.on_add_files)
        buttons_box.pack_start(add_files_btn, True, True, 0)
        
        add_folder_btn = Gtk.Button("📂 Ajouter dossier")
        add_folder_btn.connect("clicked", self.on_add_folder)
        buttons_box.pack_start(add_folder_btn, True, True, 0)
        
        clear_btn = Gtk.Button("🗑️ Vider")
        clear_btn.connect("clicked", self.on_clear_files)
        buttons_box.pack_start(clear_btn, False, False, 0)
        
        vbox.pack_start(buttons_box, False, False, 0)
        
        # Liste des fichiers sélectionnés
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)
        
        # TreeStore : Nom, Format, Taille, Chemin
        self.files_store = Gtk.ListStore(str, str, str, str)
        self.files_view = Gtk.TreeView(model=self.files_store)
        
        # Colonnes
        columns_config = [
            ("Fichier", 0, 200),
            ("Format", 1, 60),
            ("Taille", 2, 80)
        ]
        
        for title, col_id, width in columns_config:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            self.files_view.append_column(column)
        
        scrolled.add(self.files_view)
        
        # Label d'information
        self.files_info_label = Gtk.Label("Aucun fichier sélectionné")
        self.files_info_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.files_info_label, False, False, 0)
    
    def _create_settings_block(self, parent_box):
        """BLOC 2 : Paramètres de conversion"""
        frame = Gtk.Frame(label="⚙️ Paramètres de conversion")
        frame.set_size_request(450, 350)
        parent_box.pack_start(frame, True, True, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_margin_left(20)
        vbox.set_margin_right(20)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        frame.add(vbox)
        
        # Format de sortie
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        format_label = Gtk.Label("🎵 Format de sortie:")
        format_label.set_size_request(150, -1)
        format_box.pack_start(format_label, False, False, 0)
        
        self.format_combo = Gtk.ComboBoxText()
        formats = [
            ("MP3", "mp3"),
            ("FLAC", "flac"),
            ("WAV", "wav"),
            ("OGG Vorbis", "ogg"),
            ("M4A (AAC)", "m4a")
        ]
        for display_name, format_code in formats:
            self.format_combo.append(format_code, display_name)
        self.format_combo.set_active_id("mp3")  # MP3 par défaut
        self.format_combo.connect("changed", self.on_format_changed)
        format_box.pack_start(self.format_combo, True, True, 0)
        
        vbox.pack_start(format_box, False, False, 0)
        
        # Qualité de conversion
        quality_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        quality_label = Gtk.Label("🎚️ Qualité:")
        quality_label.set_size_request(150, -1)
        quality_box.pack_start(quality_label, False, False, 0)
        
        self.quality_combo = Gtk.ComboBoxText()
        qualities = [
            ("Basse (plus rapide, fichiers plus petits)", "low"),
            ("Standard (équilibre qualité/taille)", "standard"),
            ("Haute (meilleure qualité)", "high"),
            ("Maximum (qualité maximale)", "maximum")
        ]
        for display_name, quality_code in qualities:
            self.quality_combo.append(quality_code, display_name)
        self.quality_combo.set_active_id("standard")  # Standard par défaut
        quality_box.pack_start(self.quality_combo, True, True, 0)
        
        vbox.pack_start(quality_box, False, False, 0)
        
        # Informations
        info_frame = Gtk.Frame(label="ℹ️ Information")
        info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_vbox.set_margin_left(10)
        info_vbox.set_margin_right(10)
        info_vbox.set_margin_top(10)
        info_vbox.set_margin_bottom(10)
        
        self.ffmpeg_status_label = Gtk.Label()
        info_vbox.pack_start(self.ffmpeg_status_label, False, False, 0)
        
        format_info = Gtk.Label("""• MP3: Format compressé universel
• FLAC: Sans perte, fichiers plus volumineux
• WAV: Non compressé, très volumineux
• OGG: Alternative libre au MP3
• M4A: Format Apple, bonne qualité

Qualités disponibles:
• Basse: Plus rapide, fichiers plus petits
• Standard: Équilibre qualité/taille optimal
• Haute: Meilleure qualité audio
• Maximum: Qualité maximale disponible""")
        format_info.set_halign(Gtk.Align.START)
        format_info.set_line_wrap(True)
        info_vbox.pack_start(format_info, False, False, 0)
        
        info_frame.add(info_vbox)
        vbox.pack_start(info_frame, True, True, 0)
    
    def _create_conversion_queue_block(self, parent_box):
        """BLOC 3 : Queue de conversion"""
        frame = Gtk.Frame(label="📋 Queue de conversion")
        parent_box.pack_start(frame, True, True, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        frame.add(vbox)
        
        # Boutons de gestion de la queue
        queue_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        add_to_queue_btn = Gtk.Button("➕ Ajouter à la queue")
        add_to_queue_btn.connect("clicked", self.on_add_to_queue)
        queue_buttons_box.pack_start(add_to_queue_btn, False, False, 0)
        
        remove_from_queue_btn = Gtk.Button("➖ Supprimer sélection")
        remove_from_queue_btn.connect("clicked", self.on_remove_from_queue)
        queue_buttons_box.pack_start(remove_from_queue_btn, False, False, 0)
        
        clear_queue_btn = Gtk.Button("🗑️ Vider la queue")
        clear_queue_btn.connect("clicked", self.on_clear_queue)
        queue_buttons_box.pack_start(clear_queue_btn, False, False, 0)
        
        # Spacer pour pousser les autres boutons à droite
        queue_buttons_box.pack_start(Gtk.Box(), True, True, 0)
        
        vbox.pack_start(queue_buttons_box, False, False, 0)
        
        # Liste de la queue
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        vbox.pack_start(scrolled, True, True, 0)
        
        # TreeStore : Source, Format cible, Destination, Statut, Progression
        self.queue_store = Gtk.ListStore(str, str, str, str, str, object)  # +object pour le job
        self.queue_view = Gtk.TreeView(model=self.queue_store)
        
        # Colonnes de la queue
        queue_columns_config = [
            ("Fichier source", 0, 250),
            ("→", 1, 40),
            ("Destination", 2, 250),
            ("Statut", 3, 100),
            ("Progression", 4, 100)
        ]
        
        for title, col_id, width in queue_columns_config:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            self.queue_view.append_column(column)
        
        scrolled.add(self.queue_view)
    
    def _create_controls_block(self, parent_box):
        """BLOC 4 : Contrôles et progression globale"""
        frame = Gtk.Frame(label="🎛️ Contrôles")
        parent_box.pack_start(frame, False, False, 0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        hbox.set_margin_left(20)
        hbox.set_margin_right(20)
        hbox.set_margin_top(15)
        hbox.set_margin_bottom(15)
        frame.add(hbox)
        
        # Boutons de contrôle
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.start_btn = Gtk.Button("▶️ Démarrer")
        self.start_btn.connect("clicked", self.on_start_conversion)
        controls_box.pack_start(self.start_btn, False, False, 0)
        
        self.stop_btn = Gtk.Button("⏹️ Arrêter")
        self.stop_btn.connect("clicked", self.on_stop_conversion)
        self.stop_btn.set_sensitive(False)
        controls_box.pack_start(self.stop_btn, False, False, 0)
        
        hbox.pack_start(controls_box, False, False, 0)
        
        # Progression globale
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.progress_label = Gtk.Label("Prêt à convertir")
        self.progress_label.set_halign(Gtk.Align.START)
        progress_box.pack_start(self.progress_label, False, False, 0)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        progress_box.pack_start(self.progress_bar, False, False, 0)
        
        hbox.pack_start(progress_box, True, True, 0)
        
        # Statistiques
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.stats_label = Gtk.Label("0 tâches en queue")
        self.stats_label.set_halign(Gtk.Align.END)
        stats_box.pack_start(self.stats_label, False, False, 0)
        
        self.time_label = Gtk.Label("")
        self.time_label.set_halign(Gtk.Align.END)
        stats_box.pack_start(self.time_label, False, False, 0)
        
        hbox.pack_start(stats_box, False, False, 0)
    
    def _setup_converter_callbacks(self):
        """Configure les callbacks du convertisseur"""
        self.converter.on_job_started = self._on_job_started
        self.converter.on_job_progress = self._on_job_progress
        self.converter.on_job_completed = self._on_job_completed
        self.converter.on_job_error = self._on_job_error
        self.converter.on_queue_finished = self._on_queue_finished
    
    def _check_ffmpeg_availability(self):
        """Vérifie la disponibilité de FFmpeg"""
        if self.converter.ffmpeg_available:
            self.ffmpeg_status_label.set_text("✅ FFmpeg disponible")
            self.ffmpeg_status_label.set_name("success-label")
        else:
            self.ffmpeg_status_label.set_text("❌ FFmpeg requis (sudo apt install ffmpeg)")
            self.ffmpeg_status_label.set_name("error-label")
    
    # === CALLBACKS INTERFACE ===
    
    def on_add_files(self, button):
        """Ajouter des fichiers individuels"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner des fichiers audio",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Ouvrir", Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        
        # Filtres pour les fichiers audio
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Fichiers audio")
        audio_filter.add_pattern("*.mp3")
        audio_filter.add_pattern("*.flac")
        audio_filter.add_pattern("*.wav")
        audio_filter.add_pattern("*.ogg")
        audio_filter.add_pattern("*.m4a")
        audio_filter.add_pattern("*.aac")
        dialog.add_filter(audio_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            self._add_files_to_list(files)
        
        dialog.destroy()
    
    def on_add_folder(self, button):
        """Ajouter tous les fichiers audio d'un dossier"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Sélectionner", Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            audio_files = []
            
            # Parcourir le dossier pour trouver les fichiers audio
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac')):
                        audio_files.append(os.path.join(root, file))
            
            self._add_files_to_list(audio_files)
        
        dialog.destroy()
    
    def on_clear_files(self, button):
        """Vider la liste des fichiers"""
        self.selected_files.clear()
        self.files_store.clear()
        self._update_files_info()
    
    def on_add_to_queue(self, button):
        """Ajouter les fichiers sélectionnés à la queue de conversion"""
        if not self.selected_files:
            self._show_message("Aucun fichier sélectionné", "Veuillez d'abord sélectionner des fichiers à convertir.")
            return
        
        target_format = self.format_combo.get_active_id()
        if not target_format:
            self._show_message("Format non sélectionné", "Veuillez choisir un format de sortie.")
            return
        
        target_quality = self.quality_combo.get_active_id()
        if not target_quality:
            target_quality = "standard"  # Valeur par défaut
        
        # Ajouter les fichiers à la queue (utilise le dossier source de chaque fichier)
        added_count = 0
        for file_path in self.selected_files:
            # Utiliser le dossier du fichier source comme destination
            source_directory = os.path.dirname(file_path)
            job = self.converter.add_conversion_job(file_path, target_format, source_directory, target_quality)
            self._add_job_to_queue_display(job)
            added_count += 1
        
        self._update_stats()
        print(f"✅ {added_count} fichiers ajoutés à la queue de conversion avec qualité {target_quality}")
    
    def on_remove_from_queue(self, button):
        """Supprimer les éléments sélectionnés de la queue"""
        selection = self.queue_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            job = model[tree_iter][5]  # L'objet job est dans la dernière colonne
            self.converter.remove_job(job)
            model.remove(tree_iter)
            self._update_stats()
    
    def on_clear_queue(self, button):
        """Vider la queue de conversion"""
        if not self.converter.is_converting:
            self.converter.clear_queue()
            self.queue_store.clear()
            self._update_stats()
    
    def on_start_conversion(self, button):
        """Démarrer la conversion"""
        if not self.converter.conversion_queue:
            self._show_message("Queue vide", "Ajoutez des fichiers à la queue avant de démarrer.")
            return
        
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.converter.start_conversion()
    
    def on_stop_conversion(self, button):
        """Arrêter la conversion"""
        self.converter.stop_conversion()
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
    
    def on_format_changed(self, combo):
        """Met à jour les informations de qualité selon le format sélectionné"""
        format_selected = combo.get_active_id()
        
        # Informations détaillées sur les qualités par format
        quality_info = {
            "mp3": "MP3 - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps",
            "flac": "FLAC - Qualités (niveau de compression):\n• Basse: Rapide, fichiers plus gros\n• Standard: Équilibré\n• Haute: Compression élevée\n• Maximum: Compression maximale",
            "wav": "WAV - Qualités (fréquence d'échantillonnage):\n• Basse: 22 kHz, 16-bit\n• Standard: 44.1 kHz, 16-bit\n• Haute: 48 kHz, 24-bit\n• Maximum: 96 kHz, 32-bit",
            "ogg": "OGG Vorbis - Qualités:\n• Basse: Qualité 2\n• Standard: Qualité 5\n• Haute: Qualité 7\n• Maximum: Qualité 10",
            "m4a": "M4A/AAC - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps"
        }
        
        # Afficher les informations détaillées pour le format sélectionné
        if hasattr(self, 'format_specific_info'):
            info_text = quality_info.get(format_selected, "Sélectionnez un format pour voir les détails")
            self.format_specific_info.set_text(info_text)
    
    # === CALLBACKS DE L'INTERFACE ===
    
    def on_add_files(self, button):
        """Ajouter des fichiers individuels"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner des fichiers audio",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Ouvrir", Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        
        # Filtres pour les fichiers audio
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Fichiers audio")
        audio_filter.add_pattern("*.mp3")
        audio_filter.add_pattern("*.flac")
        audio_filter.add_pattern("*.wav")
        audio_filter.add_pattern("*.ogg")
        audio_filter.add_pattern("*.m4a")
        audio_filter.add_pattern("*.aac")
        dialog.add_filter(audio_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            self._add_files_to_list(files)
        
        dialog.destroy()
    
    def on_add_folder(self, button):
        """Ajouter tous les fichiers audio d'un dossier"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Sélectionner", Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            audio_files = []
            
            # Parcourir le dossier pour trouver les fichiers audio
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac')):
                        audio_files.append(os.path.join(root, file))
            
            self._add_files_to_list(audio_files)
        
        dialog.destroy()
    
    def on_clear_files(self, button):
        """Vider la liste des fichiers"""
        self.selected_files.clear()
        self.files_store.clear()
        self._update_files_info()
    
    def on_add_to_queue(self, button):
        """Ajouter les fichiers sélectionnés à la queue de conversion"""
        if not self.selected_files:
            self._show_message("Aucun fichier sélectionné", "Veuillez d'abord sélectionner des fichiers à convertir.")
            return
        
        target_format = self.format_combo.get_active_id()
        if not target_format:
            self._show_message("Format non sélectionné", "Veuillez choisir un format de sortie.")
            return
        
        target_quality = self.quality_combo.get_active_id()
        if not target_quality:
            target_quality = "standard"  # Valeur par défaut
        
        # Ajouter les fichiers à la queue (utilise le dossier source de chaque fichier)
        added_count = 0
        for file_path in self.selected_files:
            # Utiliser le dossier du fichier source comme destination
            source_directory = os.path.dirname(file_path)
            job = self.converter.add_conversion_job(file_path, target_format, source_directory, target_quality)
            self._add_job_to_queue_display(job)
            added_count += 1
        
        self._update_stats()
        print(f"✅ {added_count} fichiers ajoutés à la queue de conversion avec qualité {target_quality}")
    
    def on_remove_from_queue(self, button):
        """Supprimer les éléments sélectionnés de la queue"""
        selection = self.queue_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            job = model[tree_iter][5]  # L'objet job est dans la dernière colonne
            self.converter.remove_job(job)
            model.remove(tree_iter)
            self._update_stats()
    
    def on_clear_queue(self, button):
        """Vider la queue de conversion"""
        if not self.converter.is_converting:
            self.converter.clear_queue()
            self.queue_store.clear()
            self._update_stats()
    
    def on_start_conversion(self, button):
        """Démarrer la conversion"""
        if not self.converter.conversion_queue:
            self._show_message("Queue vide", "Ajoutez des fichiers à la queue avant de démarrer.")
            return
        
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.converter.start_conversion()
    
    def on_stop_conversion(self, button):
        """Arrêter la conversion"""
        self.converter.stop_conversion()
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
    
    def on_format_changed(self, combo):
        """Met à jour les informations de qualité selon le format sélectionné"""
        format_selected = combo.get_active_id()
        
        # Informations détaillées sur les qualités par format
        quality_info = {
            "mp3": "MP3 - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps",
            "flac": "FLAC - Qualités (niveau de compression):\n• Basse: Rapide, fichiers plus gros\n• Standard: Équilibré\n• Haute: Compression élevée\n• Maximum: Compression maximale",
            "wav": "WAV - Qualités (fréquence d'échantillonnage):\n• Basse: 22 kHz, 16-bit\n• Standard: 44.1 kHz, 16-bit\n• Haute: 48 kHz, 24-bit\n• Maximum: 96 kHz, 32-bit",
            "ogg": "OGG Vorbis - Qualités:\n• Basse: Qualité 2\n• Standard: Qualité 5\n• Haute: Qualité 7\n• Maximum: Qualité 10",
            "m4a": "M4A/AAC - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps"
        }
        
        # Afficher les informations détaillées pour le format sélectionné
        if hasattr(self, 'format_specific_info'):
            info_text = quality_info.get(format_selected, "Sélectionnez un format pour voir les détails")
            self.format_specific_info.set_text(info_text)
    
    # === CALLBACKS DE L'INTERFACE ===
    
    def on_add_files(self, button):
        """Ajouter des fichiers individuels"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner des fichiers audio",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Ouvrir", Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        
        # Filtres pour les fichiers audio
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Fichiers audio")
        audio_filter.add_pattern("*.mp3")
        audio_filter.add_pattern("*.flac")
        audio_filter.add_pattern("*.wav")
        audio_filter.add_pattern("*.ogg")
        audio_filter.add_pattern("*.m4a")
        audio_filter.add_pattern("*.aac")
        dialog.add_filter(audio_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            self._add_files_to_list(files)
        
        dialog.destroy()
    
    def on_add_folder(self, button):
        """Ajouter tous les fichiers audio d'un dossier"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Sélectionner", Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            audio_files = []
            
            # Parcourir le dossier pour trouver les fichiers audio
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac')):
                        audio_files.append(os.path.join(root, file))
            
            self._add_files_to_list(audio_files)
        
        dialog.destroy()
    
    def on_clear_files(self, button):
        """Vider la liste des fichiers"""
        self.selected_files.clear()
        self.files_store.clear()
        self._update_files_info()
    
    def on_add_to_queue(self, button):
        """Ajouter les fichiers sélectionnés à la queue de conversion"""
        if not self.selected_files:
            self._show_message("Aucun fichier sélectionné", "Veuillez d'abord sélectionner des fichiers à convertir.")
            return
        
        target_format = self.format_combo.get_active_id()
        if not target_format:
            self._show_message("Format non sélectionné", "Veuillez choisir un format de sortie.")
            return
        
        target_quality = self.quality_combo.get_active_id()
        if not target_quality:
            target_quality = "standard"  # Valeur par défaut
        
        # Ajouter les fichiers à la queue (utilise le dossier source de chaque fichier)
        added_count = 0
        for file_path in self.selected_files:
            # Utiliser le dossier du fichier source comme destination
            source_directory = os.path.dirname(file_path)
            job = self.converter.add_conversion_job(file_path, target_format, source_directory, target_quality)
            self._add_job_to_queue_display(job)
            added_count += 1
        
        self._update_stats()
        print(f"✅ {added_count} fichiers ajoutés à la queue de conversion avec qualité {target_quality}")
    
    def on_remove_from_queue(self, button):
        """Supprimer les éléments sélectionnés de la queue"""
        selection = self.queue_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            job = model[tree_iter][5]  # L'objet job est dans la dernière colonne
            self.converter.remove_job(job)
            model.remove(tree_iter)
            self._update_stats()
    
    def on_clear_queue(self, button):
        """Vider la queue de conversion"""
        if not self.converter.is_converting:
            self.converter.clear_queue()
            self.queue_store.clear()
            self._update_stats()
    
    def on_start_conversion(self, button):
        """Démarrer la conversion"""
        if not self.converter.conversion_queue:
            self._show_message("Queue vide", "Ajoutez des fichiers à la queue avant de démarrer.")
            return
        
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.converter.start_conversion()
    
    def on_stop_conversion(self, button):
        """Arrêter la conversion"""
        self.converter.stop_conversion()
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
    
    def on_format_changed(self, combo):
        """Met à jour les informations de qualité selon le format sélectionné"""
        format_selected = combo.get_active_id()
        
        # Informations détaillées sur les qualités par format
        quality_info = {
            "mp3": "MP3 - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps",
            "flac": "FLAC - Qualités (niveau de compression):\n• Basse: Rapide, fichiers plus gros\n• Standard: Équilibré\n• Haute: Compression élevée\n• Maximum: Compression maximale",
            "wav": "WAV - Qualités (fréquence d'échantillonnage):\n• Basse: 22 kHz, 16-bit\n• Standard: 44.1 kHz, 16-bit\n• Haute: 48 kHz, 24-bit\n• Maximum: 96 kHz, 32-bit",
            "ogg": "OGG Vorbis - Qualités:\n• Basse: Qualité 2\n• Standard: Qualité 5\n• Haute: Qualité 7\n• Maximum: Qualité 10",
            "m4a": "M4A/AAC - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps"
        }
        
        # Afficher les informations détaillées pour le format sélectionné
        if hasattr(self, 'format_specific_info'):
            info_text = quality_info.get(format_selected, "Sélectionnez un format pour voir les détails")
            self.format_specific_info.set_text(info_text)
    
    # === CALLBACKS DE L'INTERFACE ===
    
    def on_add_files(self, button):
        """Ajouter des fichiers individuels"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner des fichiers audio",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Ouvrir", Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        
        # Filtres pour les fichiers audio
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Fichiers audio")
        audio_filter.add_pattern("*.mp3")
        audio_filter.add_pattern("*.flac")
        audio_filter.add_pattern("*.wav")
        audio_filter.add_pattern("*.ogg")
        audio_filter.add_pattern("*.m4a")
        audio_filter.add_pattern("*.aac")
        dialog.add_filter(audio_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            self._add_files_to_list(files)
        
        dialog.destroy()
    
    def on_add_folder(self, button):
        """Ajouter tous les fichiers audio d'un dossier"""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un dossier",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Sélectionner", Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            audio_files = []
            
            # Parcourir le dossier pour trouver les fichiers audio
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac')):
                        audio_files.append(os.path.join(root, file))
            
            self._add_files_to_list(audio_files)
        
        dialog.destroy()
    
    def on_clear_files(self, button):
        """Vider la liste des fichiers"""
        self.selected_files.clear()
        self.files_store.clear()
        self._update_files_info()
    
    def on_add_to_queue(self, button):
        """Ajouter les fichiers sélectionnés à la queue de conversion"""
        if not self.selected_files:
            self._show_message("Aucun fichier sélectionné", "Veuillez d'abord sélectionner des fichiers à convertir.")
            return
        
        target_format = self.format_combo.get_active_id()
        if not target_format:
            self._show_message("Format non sélectionné", "Veuillez choisir un format de sortie.")
            return
        
        target_quality = self.quality_combo.get_active_id()
        if not target_quality:
            target_quality = "standard"  # Valeur par défaut
        
        # Ajouter les fichiers à la queue (utilise le dossier source de chaque fichier)
        added_count = 0
        for file_path in self.selected_files:
            # Utiliser le dossier du fichier source comme destination
            source_directory = os.path.dirname(file_path)
            job = self.converter.add_conversion_job(file_path, target_format, source_directory, target_quality)
            self._add_job_to_queue_display(job)
            added_count += 1
        
        self._update_stats()
        print(f"✅ {added_count} fichiers ajoutés à la queue de conversion avec qualité {target_quality}")
    
    def on_remove_from_queue(self, button):
        """Supprimer les éléments sélectionnés de la queue"""
        selection = self.queue_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            job = model[tree_iter][5]  # L'objet job est dans la dernière colonne
            self.converter.remove_job(job)
            model.remove(tree_iter)
            self._update_stats()
    
    def on_clear_queue(self, button):
        """Vider la queue de conversion"""
        if not self.converter.is_converting:
            self.converter.clear_queue()
            self.queue_store.clear()
            self._update_stats()
    
    def on_start_conversion(self, button):
        """Démarrer la conversion"""
        if not self.converter.conversion_queue:
            self._show_message("Queue vide", "Ajoutez des fichiers à la queue avant de démarrer.")
            return
        
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.converter.start_conversion()
    
    def on_stop_conversion(self, button):
        """Arrêter la conversion"""
        self.converter.stop_conversion()
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
    
    def on_format_changed(self, combo):
        """Met à jour les informations de qualité selon le format sélectionné"""
        format_selected = combo.get_active_id()
        
        # Informations détaillées sur les qualités par format
        quality_info = {
            "mp3": "MP3 - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps",
            "flac": "FLAC - Qualités (niveau de compression):\n• Basse: Rapide, fichiers plus gros\n• Standard: Équilibré\n• Haute: Compression élevée\n• Maximum: Compression maximale",
            "wav": "WAV - Qualités (fréquence d'échantillonnage):\n• Basse: 22 kHz, 16-bit\n• Standard: 44.1 kHz, 16-bit\n• Haute: 48 kHz, 24-bit\n• Maximum: 96 kHz, 32-bit",
            "ogg": "OGG Vorbis - Qualités:\n• Basse: Qualité 2\n• Standard: Qualité 5\n• Haute: Qualité 7\n• Maximum: Qualité 10",
            "m4a": "M4A/AAC - Qualités:\n• Basse: 128 kbps\n• Standard: 192 kbps\n• Haute: 256 kbps\n• Maximum: 320 kbps"
        }
        
        # Afficher les informations détaillées pour le format sélectionné
        if hasattr(self, 'format_specific_info'):
            info_text = quality_info.get(format_selected, "Sélectionnez un format pour voir les détails")
            self.format_specific_info.set_text(info_text)
    
    # === CALLBACKS CONVERTISSEUR ===
    
    def _on_job_started(self, job):
        """Callback: job démarré"""
        GLib.idle_add(self._update_job_in_queue, job, job.status.value, "0%")
        GLib.idle_add(self._update_progress_label, f"Conversion: {os.path.basename(job.source_path)}")
    
    def _on_job_progress(self, job, progress):
        """Callback: progression du job"""
        GLib.idle_add(self._update_job_in_queue, job, job.status.value, f"{progress:.0f}%")
        GLib.idle_add(self._update_progress_bar, progress / 100.0)
    
    def _on_job_completed(self, job):
        """Callback: job terminé"""
        GLib.idle_add(self._update_job_in_queue, job, "✅ " + job.status.value, "100%")
        GLib.idle_add(self._update_stats)
    
    def _on_job_error(self, job, error_message):
        """Callback: erreur de job"""
        GLib.idle_add(self._update_job_in_queue, job, "❌ " + job.status.value, "Erreur")
        GLib.idle_add(self._update_stats)
    
    def _on_queue_finished(self):
        """Callback: queue terminée"""
        GLib.idle_add(self._conversion_finished)
    
    def _update_job_in_queue(self, job, status, progress):
        """Met à jour un job dans l'affichage de la queue"""
        iter = self.queue_store.get_iter_first()
        while iter:
            if self.queue_store[iter][5] == job:  # Comparer l'objet job
                self.queue_store[iter][3] = status
                self.queue_store[iter][4] = progress
                break
            iter = self.queue_store.iter_next(iter)
    
    def _update_progress_label(self, text):
        """Met à jour le label de progression"""
        self.progress_label.set_text(text)
    
    def _update_progress_bar(self, fraction):
        """Met à jour la barre de progression"""
        self.progress_bar.set_fraction(fraction)
    
    def _conversion_finished(self):
        """Conversion terminée"""
        self.progress_label.set_text("Conversion terminée")
        self.progress_bar.set_fraction(0.0)
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self._update_stats()
