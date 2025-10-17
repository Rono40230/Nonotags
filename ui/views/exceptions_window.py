"""
Fenêtre de gestion des exceptions de casse
Interface CRUD pour les exceptions de correction de casse
"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
from database.db_manager import DatabaseManager
from database.models import CaseExceptionModel
from support.logger import AppLogger
from support.validator import Validator

class ExceptionsWindow(Gtk.Window):
    """Fenêtre de gestion des exceptions de casse"""
    
    def __init__(self, parent=None):
        super().__init__(title="Gestion des exceptions de casse")
        
        self.parent = parent
        self.logger = AppLogger()
        self.db_manager = DatabaseManager()
        self.validator = Validator()
        
        # Configuration de la fenêtre
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        
        if parent:
            self.set_transient_for(parent)
            self.set_modal(True)
        
        # Styles CSS
        self._setup_styles()
        
        # Interface
        self._setup_ui()
        
        # Charger les données
        self._load_exceptions()
        
        self.logger.info("Fenêtre d'exceptions initialisée")
    
    def _setup_styles(self):
        """Configure les styles CSS"""
        css = """
        .exception-header {
            background: linear-gradient(to right, #2196F3, #1976D2);
            color: white;
            font-weight: bold;
            padding: 10px;
        }
        
        .exception-toolbar {
            background: #f5f5f5;
            border-bottom: 1px solid #ddd;
            padding: 5px;
        }
        
        .exception-button {
            padding: 8px 15px;
            margin: 2px;
        }
        
        .exception-button:hover {
            background: #e3f2fd;
        }
        
        .exception-entry {
            padding: 5px;
            margin: 2px;
        }
        
        .exception-row:nth-child(even) {
            background: #f9f9f9;
        }
        
        .exception-row:hover {
            background: #e3f2fd;
        }
        
        .exception-status {
            font-weight: bold;
            padding: 5px;
        }
        
        .status-info {
            color: #2196F3;
        }
        
        .status-success {
            color: #4CAF50;
        }
        
        .status-warning {
            color: #FF9800;
        }
        
        .status-error {
            color: #f44336;
        }
        """
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        # Conteneur principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_box)
        
        # En-tête
        self._create_header(main_box)
        
        # Barre d'outils
        self._create_toolbar(main_box)
        
        # Zone principale avec liste et formulaire
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(content_paned, True, True, 0)
        
        # Liste des exceptions (gauche)
        self._create_exceptions_list(content_paned)
        
        # Formulaire d'édition (droite)
        self._create_edit_form(content_paned)
        
        # Barre de statut
        self._create_status_bar(main_box)
    
    def _create_header(self, parent):
        """Crée l'en-tête"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.get_style_context().add_class("exception-header")
        parent.pack_start(header_box, False, False, 0)
        
        # Titre et description
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header_box.pack_start(title_box, True, True, 10)
        
        title_label = Gtk.Label("Gestion des exceptions de casse")
        title_label.set_markup("<span size='large' weight='bold'>Gestion des exceptions de casse</span>")
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        desc_label = Gtk.Label("Gérez les mots qui ne doivent pas suivre les règles de casse automatiques")
        desc_label.set_halign(Gtk.Align.START)
        title_box.pack_start(desc_label, False, False, 0)

    def _create_toolbar(self, parent):
        """Crée la barre d'outils"""
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        toolbar_box.get_style_context().add_class("exception-toolbar")
        toolbar_box.set_margin_left(10)
        toolbar_box.set_margin_right(10)
        toolbar_box.set_margin_top(5)
        toolbar_box.set_margin_bottom(5)
        parent.pack_start(toolbar_box, False, False, 0)
        
        # Boutons d'action
        self.new_button = Gtk.Button("Nouveau")
        self.new_button.get_style_context().add_class("exception-button")
        self.new_button.connect("clicked", self.on_new_clicked)
        toolbar_box.pack_start(self.new_button, False, False, 0)
        
        self.edit_button = Gtk.Button("Modifier")
        self.edit_button.get_style_context().add_class("exception-button")
        self.edit_button.connect("clicked", self.on_edit_clicked)
        self.edit_button.set_sensitive(False)
        toolbar_box.pack_start(self.edit_button, False, False, 0)
        
        self.delete_button = Gtk.Button("Supprimer")
        self.delete_button.get_style_context().add_class("exception-button")
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.delete_button.set_sensitive(False)
        toolbar_box.pack_start(self.delete_button, False, False, 0)
        
        # Séparateur
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar_box.pack_start(separator, False, False, 5)
        
        # Recherche
        search_label = Gtk.Label("Recherche:")
        toolbar_box.pack_start(search_label, False, False, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Tapez pour filtrer...")
        self.search_entry.get_style_context().add_class("exception-entry")
        self.search_entry.connect("changed", self.on_search_changed)
        toolbar_box.pack_start(self.search_entry, False, False, 0)
        
        # Bouton actualiser
        toolbar_box.pack_end(Gtk.Box(), True, True, 0)  # Espaceur
        
        refresh_button = Gtk.Button("Actualiser")
        refresh_button.get_style_context().add_class("exception-button")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        toolbar_box.pack_end(refresh_button, False, False, 0)
    
    def _create_exceptions_list(self, parent):
        """Crée la liste des exceptions"""
        # Conteneur pour la liste
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        parent.pack1(left_box, True, False)
        
        # Titre de la liste
        list_label = Gtk.Label("Liste des exceptions")
        list_label.set_markup("<span weight='bold'>Liste des exceptions</span>")
        list_label.set_halign(Gtk.Align.START)
        list_label.set_margin_left(10)
        list_label.set_margin_top(5)
        left_box.pack_start(list_label, False, False, 0)
        
        # ScrolledWindow pour la liste
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_width(350)
        left_box.pack_start(scrolled, True, True, 5)
        
        # TreeView pour les exceptions
        self.exceptions_store = Gtk.ListStore(int, str, str, str, str)  # ID, Word, Type, Category, Result
        self.exceptions_view = Gtk.TreeView(model=self.exceptions_store)
        
        # Colonnes simplifiées
        columns = [
            ("Avant", 1, True),
            ("Après", 4, False)
        ]
        
        for title, col_id, editable in columns:
            renderer = Gtk.CellRendererText()
            if editable:
                renderer.set_property("editable", True)
                renderer.connect("edited", self.on_cell_edited, col_id)
            
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_sort_column_id(col_id)
            self.exceptions_view.append_column(column)
        
        # Sélection
        self.exceptions_selection = self.exceptions_view.get_selection()
        self.exceptions_selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.exceptions_selection.connect("changed", self.on_selection_changed)
        
        # Double-clic pour édition
        self.exceptions_view.connect("row-activated", self.on_row_activated)
        
        scrolled.add(self.exceptions_view)
        
        # Informations sur la sélection
        self.selection_info_label = Gtk.Label("")
        self.selection_info_label.set_halign(Gtk.Align.START)
        self.selection_info_label.set_margin_left(10)
        left_box.pack_start(self.selection_info_label, False, False, 5)
    
    def _create_edit_form(self, parent):
        """Crée le formulaire d'édition"""
        # Conteneur pour le formulaire
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        parent.pack2(right_box, False, False)
        
        # Titre du formulaire
        form_label = Gtk.Label("Ajouter/Modifier une exception")
        form_label.set_markup("<span weight='bold'>Ajouter/Modifier une exception</span>")
        form_label.set_halign(Gtk.Align.START)
        form_label.set_margin_left(10)
        form_label.set_margin_top(5)
        right_box.pack_start(form_label, False, False, 0)
        
        # Formulaire dans un frame
        form_frame = Gtk.Frame()
        form_frame.set_margin_left(10)
        form_frame.set_margin_right(10)
        form_frame.set_margin_top(5)
        right_box.pack_start(form_frame, False, False, 0)
        
        form_grid = Gtk.Grid()
        form_grid.set_row_spacing(10)
        form_grid.set_column_spacing(10)
        form_grid.set_margin_left(15)
        form_grid.set_margin_right(15)
        form_grid.set_margin_top(15)
        form_grid.set_margin_bottom(15)
        form_frame.add(form_grid)
        
        # Champ Avant (mot original)
        form_grid.attach(Gtk.Label("Avant:"), 0, 0, 1, 1)
        self.before_entry = Gtk.Entry()
        self.before_entry.set_placeholder_text("Mot original (ex: dj, paris, new york)")
        self.before_entry.get_style_context().add_class("exception-entry")
        self.before_entry.connect("changed", self.on_entry_changed)
        form_grid.attach(self.before_entry, 1, 0, 2, 1)
        
        # Champ Après (mot avec casse corrigée)
        form_grid.attach(Gtk.Label("Après:"), 0, 1, 1, 1)
        self.after_entry = Gtk.Entry()
        self.after_entry.set_placeholder_text("Mot avec la bonne casse (ex: DJ, Paris, New York)")
        self.after_entry.get_style_context().add_class("exception-entry")
        self.after_entry.connect("changed", self.on_entry_changed)
        form_grid.attach(self.after_entry, 1, 1, 2, 1)
        
        # Boutons de formulaire
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        form_grid.attach(button_box, 1, 2, 2, 1)
        
        self.save_button = Gtk.Button("Sauvegarder")
        self.save_button.get_style_context().add_class("exception-button")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.save_button.set_sensitive(False)
        button_box.pack_start(self.save_button, False, False, 0)
        
        self.cancel_button = Gtk.Button("Annuler")
        self.cancel_button.get_style_context().add_class("exception-button")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        self.cancel_button.set_sensitive(False)
        button_box.pack_start(self.cancel_button, False, False, 0)
        
        # État du formulaire
        self.current_exception_id = None
        self.form_mode = None  # None, 'new', 'edit'
    
    def _create_status_bar(self, parent):
        """Crée la barre de statut"""
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.status_bar.get_style_context().add_class("exception-toolbar")
        parent.pack_start(self.status_bar, False, False, 0)
        
        self.status_label = Gtk.Label("Prêt")
        self.status_label.get_style_context().add_class("exception-status")
        self.status_label.get_style_context().add_class("status-info")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_margin_left(10)
        self.status_bar.pack_start(self.status_label, True, True, 0)
        
        # Compteur d'exceptions
        self.count_label = Gtk.Label("0 exceptions")
        self.count_label.set_margin_right(10)
        self.status_bar.pack_end(self.count_label, False, False, 0)
    
    def _load_exceptions(self):
        """Charge les exceptions depuis la base de données"""
        try:
            self.exceptions_store.clear()
            exceptions_dict = self.db_manager.get_all_case_exceptions()
            
            exception_id = 1  # Compteur pour ID numérique
            for word, preserved_case in exceptions_dict.items():
                # Affichage simplifié: "avant" et "après" uniquement
                self.exceptions_store.append([
                    exception_id,  # ID numérique requis par GTK
                    word,          # Mot original (avant)
                    "",            # Colonne inutilisée
                    "",            # Colonne inutilisée
                    preserved_case # Mot avec casse préservée (après)
                ])
                exception_id += 1
            
            self._update_count_label()
            self._update_status("Exceptions chargées", "success")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement exceptions: {e}")
            self._update_status(f"Erreur: {e}", "error")
    
    def _update_status(self, message, status_type="info"):
        """Met à jour la barre de statut"""
        self.status_label.set_text(message)
        
        # Supprimer les anciennes classes de statut
        style_context = self.status_label.get_style_context()
        for cls in ["status-info", "status-success", "status-warning", "status-error"]:
            style_context.remove_class(cls)
        
        # Ajouter la nouvelle classe
        style_context.add_class(f"status-{status_type}")
    
    # === MÉTHODES UTILITAIRES SUPPRIMÉES ===
    # Les méthodes de gestion des types et catégories ont été supprimées 
    # car l'interface est maintenant simplifiée avec uniquement "Avant" et "Après"
    
    def _update_count_label(self):
        """Met à jour le compteur d'exceptions"""
        count = len(self.exceptions_store)
        text = f"{count} exception{'s' if count != 1 else ''}"
        self.count_label.set_text(text)
    
    def _clear_form(self):
        """Vide le formulaire"""
        self.before_entry.set_text("")
        self.after_entry.set_text("")
        self.current_exception_id = None
        self.form_mode = None
        self.save_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)
    
    def _load_form_from_selection(self):
        """Charge le formulaire avec la sélection actuelle"""
        model, iter = self.exceptions_selection.get_selected()
        if not iter:
            return
        
        word = model.get_value(iter, 1)  # Le mot original (avant)
        preserved_case = model.get_value(iter, 4)  # Le mot avec casse préservée (après)
        
        # Charger dans les champs simplifiés
        self.before_entry.set_text(word)
        self.after_entry.set_text(preserved_case)
        self.current_exception_id = word  # Utiliser le mot comme ID
    
    def _validate_form(self):
        """Valide le formulaire"""
        before = self.before_entry.get_text().strip().lower()
        after = self.after_entry.get_text().strip()
        
        if not before:
            self.logger.warning("DEBUG - Validation: mot 'avant' vide")
            self._update_status("Le mot 'Avant' est requis", "warning")
            return False
        
        if not after:
            self.logger.warning("DEBUG - Validation: mot 'après' vide")
            self._update_status("Le mot 'Après' est requis", "warning")
            return False
        
        if not self.validator.input_validator.validate_exception_word(before).is_valid:
            self.logger.warning(f"DEBUG - Validation: mot avant invalide '{before}'")
            self._update_status("Mot 'Avant' invalide (caractères spéciaux non autorisés)", "warning")
            return False
        
        self.logger.info("DEBUG - Validation réussie")
        return True

    # === CALLBACKS ===
    
    def on_entry_changed(self, entry):
        """Callback appelé quand un champ texte change"""
        # Activer les boutons si on est en mode création/édition et que les champs ne sont pas vides
        if self.form_mode in ['new', 'edit']:
            before_text = self.before_entry.get_text().strip()
            after_text = self.after_entry.get_text().strip()
            
            # Activer le bouton sauvegarder si les deux champs ont du contenu
            has_content = bool(before_text and after_text)
            self.save_button.set_sensitive(has_content)
    
    def on_new_clicked(self, button):
        """Nouveau exception"""
        self._clear_form()
        self.form_mode = 'new'
        self.save_button.set_sensitive(False)  # Désactivé jusqu'à ce que l'utilisateur tape
        self.cancel_button.set_sensitive(True)
        self.before_entry.grab_focus()
        self._update_status("Mode création - Tapez 'Avant' et 'Après' pour activer la sauvegarde", "info")
    
    def on_edit_clicked(self, button):
        """Modifier l'exception sélectionnée"""
        model, iter = self.exceptions_selection.get_selected()
        if not iter:
            return
        
        self._load_form_from_selection()
        self.form_mode = 'edit'
        
        # Vérifier si les champs sont remplis pour activer le bouton
        before_text = self.before_entry.get_text().strip()
        after_text = self.after_entry.get_text().strip()
        self.save_button.set_sensitive(bool(before_text and after_text))
        
        self.cancel_button.set_sensitive(True)
        self.before_entry.grab_focus()
        self._update_status("Mode édition", "info")
    
    def on_delete_clicked(self, button):
        """Supprimer l'exception sélectionnée"""
        model, iter = self.exceptions_selection.get_selected()
        if not iter:
            return
        
        exception_id = model.get_value(iter, 0)
        word = model.get_value(iter, 1)
        
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Supprimer l'exception '{word}' ?"
        )
        
        dialog.format_secondary_text("Cette action est irréversible.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                self.db_manager.remove_case_exception(word)
                self._load_exceptions()
                self._clear_form()
                self._update_status(f"Exception '{word}' supprimée", "success")
                
            except Exception as e:
                self.logger.error(f"Erreur suppression exception: {e}")
                self._update_status(f"Erreur suppression: {e}", "error")
    
    def on_save_clicked(self, button):
        """Sauvegarder l'exception"""
        self.logger.info(f"DEBUG - Début sauvegarde, form_mode: {self.form_mode}")
        
        if not self._validate_form():
            self.logger.warning("DEBUG - Validation formulaire échouée")
            return
        
        before = self.before_entry.get_text().strip().lower()  # Toujours en minuscules pour la clé
        after = self.after_entry.get_text().strip()  # Garder la casse telle que saisie
        
        self.logger.info(f"📝 DEBUG - Données: before='{before}', after='{after}'")
        
        try:
            if self.form_mode == 'new':
                self.logger.info(f"💾 DEBUG - Mode nouveau: before='{before}', after='{after}'")
                success = self.db_manager.add_case_exception(before, after)
                self.logger.info(f"💾 DEBUG - Résultat add_case_exception: {success}")
                if success:
                    self._update_status(f"Exception '{before} → {after}' créée", "success")
                else:
                    self._update_status(f"Erreur lors de la création de '{before}'", "error")
                    return
                
            elif self.form_mode == 'edit' and self.current_exception_id:
                self.logger.info(f"DEBUG - Mode édition: current_id='{self.current_exception_id}'")
                # Pour l'édition, on supprime l'ancienne et on recrée
                self.db_manager.remove_case_exception(self.current_exception_id)
                success = self.db_manager.add_case_exception(before, after)
                if success:
                    self._update_status(f"Exception '{before} → {after}' modifiée", "success")
                else:
                    self._update_status(f"Erreur lors de la modification de '{before}'", "error")
                    return
            else:
                self.logger.warning(f"⚠️ DEBUG - Mode non reconnu: form_mode='{self.form_mode}', current_id='{self.current_exception_id}'")
                self._update_status("Mode de formulaire non valide", "error")
                return
            
            self._load_exceptions()
            self._clear_form()
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde exception: {e}")
            self._update_status(f"Erreur sauvegarde: {e}", "error")
    
    def on_cancel_clicked(self, button):
        """Annuler l'édition"""
        self._clear_form()
        self._update_status("Édition annulée", "info")
    
    def on_refresh_clicked(self, button):
        """Actualiser la liste"""
        self._load_exceptions()
    
    def on_search_changed(self, entry):
        """Filtrer la liste selon la recherche"""
        search_text = entry.get_text().lower()
        
        # TODO: Implémenter le filtrage
        # Pour l'instant, simple reload
        if not search_text:
            self._load_exceptions()
    
    def on_selection_changed(self, selection):
        """Gestion du changement de sélection"""
        model, iter = selection.get_selected()
        has_selection = iter is not None
        
        self.edit_button.set_sensitive(has_selection)
        self.delete_button.set_sensitive(has_selection)
        
        if has_selection:
            word = model.get_value(iter, 1)
            after = model.get_value(iter, 4)
            
            info_text = f"Sélectionné: '{word}' → '{after}'"
            self.selection_info_label.set_text(info_text)
        else:
            self.selection_info_label.set_text("")
    
    def on_row_activated(self, treeview, path, column):
        """Double-clic sur une ligne"""
        self.on_edit_clicked(None)
    
    def on_cell_edited(self, renderer, path, new_text, column_id):
        """Édition directe dans la liste"""
        if not new_text.strip():
            return
        
        iter = self.exceptions_store.get_iter(path)
        exception_id = self.exceptions_store.get_value(iter, 0)
        
        try:
            if column_id == 1:  # Colonne Mot
                # Valider le nouveau mot
                if not self.validator.is_valid_case_exception_word(new_text.strip()):
                    self._update_status("Mot invalide", "warning")
                    return
                
                # Mettre à jour en base
                exception = self.db_manager.get_case_exception(exception_id)
                if exception:
                    self.db_manager.update_case_exception(
                        exception_id, new_text.strip(), 
                        exception.exception_type, exception.category, exception.description
                    )
                    
                    # Mettre à jour l'affichage
                    self.exceptions_store.set_value(iter, column_id, new_text.strip())
                    self._update_status(f"Mot modifié: '{new_text}'", "success")
        
        except Exception as e:
            self.logger.error(f"Erreur édition cellule: {e}")
            self._update_status(f"Erreur: {e}", "error")