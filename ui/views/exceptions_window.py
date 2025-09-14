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
        super().__init__(title="⚙️ Gestion des exceptions de casse")
        
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
        
        title_label = Gtk.Label("⚙️ Gestion des exceptions de casse")
        title_label.set_markup("<span size='large' weight='bold'>⚙️ Gestion des exceptions de casse</span>")
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        desc_label = Gtk.Label("Gérez les mots qui ne doivent pas suivre les règles de casse automatiques")
        desc_label.set_halign(Gtk.Align.START)
        title_box.pack_start(desc_label, False, False, 0)
        
        # Bouton aide
        help_button = Gtk.Button("❓")
        help_button.set_tooltip_text("Aide sur les exceptions")
        help_button.connect("clicked", self.on_help_clicked)
        header_box.pack_end(help_button, False, False, 10)
    
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
        self.new_button = Gtk.Button("➕ Nouveau")
        self.new_button.get_style_context().add_class("exception-button")
        self.new_button.connect("clicked", self.on_new_clicked)
        toolbar_box.pack_start(self.new_button, False, False, 0)
        
        self.edit_button = Gtk.Button("✏️ Modifier")
        self.edit_button.get_style_context().add_class("exception-button")
        self.edit_button.connect("clicked", self.on_edit_clicked)
        self.edit_button.set_sensitive(False)
        toolbar_box.pack_start(self.edit_button, False, False, 0)
        
        self.delete_button = Gtk.Button("🗑️ Supprimer")
        self.delete_button.get_style_context().add_class("exception-button")
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.delete_button.set_sensitive(False)
        toolbar_box.pack_start(self.delete_button, False, False, 0)
        
        # Séparateur
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar_box.pack_start(separator, False, False, 5)
        
        # Recherche
        search_label = Gtk.Label("🔍 Recherche:")
        toolbar_box.pack_start(search_label, False, False, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Tapez pour filtrer...")
        self.search_entry.get_style_context().add_class("exception-entry")
        self.search_entry.connect("changed", self.on_search_changed)
        toolbar_box.pack_start(self.search_entry, False, False, 0)
        
        # Bouton actualiser
        toolbar_box.pack_end(Gtk.Box(), True, True, 0)  # Espaceur
        
        refresh_button = Gtk.Button("🔄 Actualiser")
        refresh_button.get_style_context().add_class("exception-button")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        toolbar_box.pack_end(refresh_button, False, False, 0)
    
    def _create_exceptions_list(self, parent):
        """Crée la liste des exceptions"""
        # Conteneur pour la liste
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        parent.pack1(left_box, True, False)
        
        # Titre de la liste
        list_label = Gtk.Label("📋 Liste des exceptions")
        list_label.set_markup("<span weight='bold'>📋 Liste des exceptions</span>")
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
        self.exceptions_store = Gtk.ListStore(int, str, str, str, str)  # ID, Word, Type, Category, Created
        self.exceptions_view = Gtk.TreeView(model=self.exceptions_store)
        
        # Colonnes
        columns = [
            ("Mot", 1, True),
            ("Type", 2, False),
            ("Catégorie", 3, False),
            ("Créé le", 4, False)
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
        form_label = Gtk.Label("✏️ Détails de l'exception")
        form_label.set_markup("<span weight='bold'>✏️ Détails de l'exception</span>")
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
        
        # Champ Mot
        form_grid.attach(Gtk.Label("Mot:"), 0, 0, 1, 1)
        self.word_entry = Gtk.Entry()
        self.word_entry.set_placeholder_text("Mot à conserver (ex: I, II, III)")
        self.word_entry.get_style_context().add_class("exception-entry")
        form_grid.attach(self.word_entry, 1, 0, 2, 1)
        
        # Type d'exception
        form_grid.attach(Gtk.Label("Type:"), 0, 1, 1, 1)
        self.type_combo = Gtk.ComboBoxText()
        exception_types = ["uppercase", "lowercase", "titlecase", "preserve"]
        for ex_type in exception_types:
            self.type_combo.append_text(ex_type)
        form_grid.attach(self.type_combo, 1, 1, 2, 1)
        
        # Catégorie
        form_grid.attach(Gtk.Label("Catégorie:"), 0, 2, 1, 1)
        self.category_combo = Gtk.ComboBoxText()
        categories = ["Chiffres romains", "Prépositions", "Conjonctions", "Acronymes", "Noms propres", "Autre"]
        for category in categories:
            self.category_combo.append_text(category)
        form_grid.attach(self.category_combo, 1, 2, 2, 1)
        
        # Description
        form_grid.attach(Gtk.Label("Description:"), 0, 3, 1, 1)
        self.description_entry = Gtk.Entry()
        self.description_entry.set_placeholder_text("Description optionnelle")
        self.description_entry.get_style_context().add_class("exception-entry")
        form_grid.attach(self.description_entry, 1, 3, 2, 1)
        
        # Boutons de formulaire
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        form_grid.attach(button_box, 1, 4, 2, 1)
        
        self.save_button = Gtk.Button("💾 Sauvegarder")
        self.save_button.get_style_context().add_class("exception-button")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.save_button.set_sensitive(False)
        button_box.pack_start(self.save_button, False, False, 0)
        
        self.cancel_button = Gtk.Button("❌ Annuler")
        self.cancel_button.get_style_context().add_class("exception-button")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        self.cancel_button.set_sensitive(False)
        button_box.pack_start(self.cancel_button, False, False, 0)
        
        # Zone d'aide
        help_frame = Gtk.Frame(label="💡 Aide")
        help_frame.set_margin_left(10)
        help_frame.set_margin_right(10)
        help_frame.set_margin_top(10)
        right_box.pack_start(help_frame, True, True, 0)
        
        help_text = """
<b>Types d'exceptions :</b>
• <b>uppercase</b> : Force en MAJUSCULES (ex: USA, DJ)
• <b>lowercase</b> : Force en minuscules (ex: and, of, the)
• <b>titlecase</b> : Force la première lettre en majuscule
• <b>preserve</b> : Conserve la casse exacte (ex: eMule, iPhone)

<b>Exemples courants :</b>
• Chiffres romains : I, II, III, IV, V, VI, VII, VIII, IX, X
• Prépositions : of, in, on, at, by, for, with, from
• Articles : a, an, the
• Conjonctions : and, or, but, nor, yet, so
• Acronymes : USA, UK, DJ, MC, TV, CD, LP, EP
        """
        
        help_label = Gtk.Label()
        help_label.set_markup(help_text.strip())
        help_label.set_line_wrap(True)
        help_label.set_halign(Gtk.Align.START)
        help_label.set_valign(Gtk.Align.START)
        help_label.set_margin_left(10)
        help_label.set_margin_right(10)
        help_label.set_margin_top(5)
        help_label.set_margin_bottom(10)
        help_frame.add(help_label)
        
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
            exceptions = self.db_manager.get_all_case_exceptions()
            
            for exception in exceptions:
                self.exceptions_store.append([
                    exception.id,
                    exception.word,
                    exception.exception_type,
                    exception.category or "Non classé",
                    exception.created_at.strftime("%d/%m/%Y") if exception.created_at else ""
                ])
            
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
    
    def _update_count_label(self):
        """Met à jour le compteur d'exceptions"""
        count = len(self.exceptions_store)
        text = f"{count} exception{'s' if count != 1 else ''}"
        self.count_label.set_text(text)
    
    def _clear_form(self):
        """Vide le formulaire"""
        self.word_entry.set_text("")
        self.type_combo.set_active(-1)
        self.category_combo.set_active(-1)
        self.description_entry.set_text("")
        self.current_exception_id = None
        self.form_mode = None
        self.save_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)
    
    def _load_form_from_selection(self):
        """Charge le formulaire avec la sélection actuelle"""
        model, iter = self.exceptions_selection.get_selected()
        if not iter:
            return
        
        exception_id = model.get_value(iter, 0)
        
        try:
            exception = self.db_manager.get_case_exception(exception_id)
            if exception:
                self.word_entry.set_text(exception.word)
                
                # Sélectionner le type
                type_model = self.type_combo.get_model()
                for i in range(len(type_model)):
                    if type_model[i][0] == exception.exception_type:
                        self.type_combo.set_active(i)
                        break
                
                # Sélectionner la catégorie
                if exception.category:
                    category_model = self.category_combo.get_model()
                    for i in range(len(category_model)):
                        if category_model[i][0] == exception.category:
                            self.category_combo.set_active(i)
                            break
                
                self.description_entry.set_text(exception.description or "")
                self.current_exception_id = exception_id
                
        except Exception as e:
            self.logger.error(f"Erreur chargement exception {exception_id}: {e}")
    
    def _validate_form(self):
        """Valide le formulaire"""
        word = self.word_entry.get_text().strip()
        exception_type = self.type_combo.get_active_text()
        
        if not word:
            self._update_status("Le mot est requis", "warning")
            return False
        
        if not exception_type:
            self._update_status("Le type est requis", "warning")
            return False
        
        if not self.validator.is_valid_case_exception_word(word):
            self._update_status("Mot invalide (caractères spéciaux non autorisés)", "warning")
            return False
        
        return True
    
    # === CALLBACKS ===
    
    def on_help_clicked(self, button):
        """Affiche l'aide"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Aide - Exceptions de casse"
        )
        
        help_text = """
Les exceptions de casse permettent de définir des mots qui ne suivent pas les règles automatiques de formatage.

Types d'exceptions :
• uppercase : Force en MAJUSCULES (ex: USA, DJ, MC)
• lowercase : Force en minuscules (ex: and, of, the, in)  
• titlecase : Force la première lettre en majuscule
• preserve : Conserve la casse exacte (ex: iPhone, eMule)

Exemples courants :
• Chiffres romains : I, II, III, IV, V, VI, VII, VIII, IX, X
• Articles et prépositions : a, an, the, of, in, on, at, by, for
• Conjonctions : and, or, but, nor, yet, so
• Acronymes : USA, UK, DJ, MC, TV, CD, LP, EP

Les exceptions s'appliquent lors du formatage automatique des titres et albums.
        """
        
        dialog.format_secondary_text(help_text)
        dialog.run()
        dialog.destroy()
    
    def on_new_clicked(self, button):
        """Nouveau exception"""
        self._clear_form()
        self.form_mode = 'new'
        self.save_button.set_sensitive(True)
        self.cancel_button.set_sensitive(True)
        self.word_entry.grab_focus()
        self._update_status("Mode création", "info")
    
    def on_edit_clicked(self, button):
        """Modifier l'exception sélectionnée"""
        model, iter = self.exceptions_selection.get_selected()
        if not iter:
            return
        
        self._load_form_from_selection()
        self.form_mode = 'edit'
        self.save_button.set_sensitive(True)
        self.cancel_button.set_sensitive(True)
        self.word_entry.grab_focus()
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
                self.db_manager.delete_case_exception(exception_id)
                self._load_exceptions()
                self._clear_form()
                self._update_status(f"Exception '{word}' supprimée", "success")
                
            except Exception as e:
                self.logger.error(f"Erreur suppression exception: {e}")
                self._update_status(f"Erreur suppression: {e}", "error")
    
    def on_save_clicked(self, button):
        """Sauvegarder l'exception"""
        if not self._validate_form():
            return
        
        word = self.word_entry.get_text().strip()
        exception_type = self.type_combo.get_active_text()
        category = self.category_combo.get_active_text()
        description = self.description_entry.get_text().strip() or None
        
        try:
            if self.form_mode == 'new':
                self.db_manager.add_case_exception(word, exception_type, category, description)
                self._update_status(f"Exception '{word}' créée", "success")
                
            elif self.form_mode == 'edit' and self.current_exception_id:
                self.db_manager.update_case_exception(
                    self.current_exception_id, word, exception_type, category, description
                )
                self._update_status(f"Exception '{word}' modifiée", "success")
            
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
            ex_type = model.get_value(iter, 2)
            category = model.get_value(iter, 3)
            
            info_text = f"Sélectionné: '{word}' ({ex_type}, {category})"
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
