# 🎨 ARCHITECTURE INTERFACE UTILISATEUR - NONOTAGS

## 📋 Vue d'ensemble

Maintenant que la **Phase 2 est terminée à 100%** avec tous les modules core implémentés et testés, nous allons construire l'interface utilisateur en **réutilisant intelligemment** tous les composants existants.

### 🎯 Objectifs de l'UI

1. **Réutilisation maximale** : Exploiter les 6 modules core + 4 modules support
2. **Architecture MVVM** : Séparation claire entre logique et présentation  
3. **GTK4 moderne** : Interface native Linux avec design contemporain
4. **Performance** : Responsive même avec de gros volumes d'albums
5. **Extensibilité** : Architecture modulaire pour évolutions futures

---

## 🏗️ ARCHITECTURE TECHNIQUE

### Structure des dossiers UI
```
ui/
├── __init__.py
├── app.py                    # Application GTK principale
├── controllers/
│   ├── __init__.py
│   ├── app_controller.py     # Contrôleur principal
│   ├── startup_controller.py # Fenêtre de démarrage
│   ├── main_controller.py    # Fenêtre principale
│   ├── edit_controller.py    # Fenêtre d'édition
│   └── exceptions_controller.py # Fenêtre exceptions
├── views/
│   ├── __init__.py
│   ├── startup_view.py       # Vue démarrage
│   ├── main_view.py          # Vue principale
│   ├── edit_view.py          # Vue édition
│   └── exceptions_view.py    # Vue exceptions
├── components/
│   ├── __init__.py
│   ├── album_card.py         # Card d'album réutilisable
│   ├── album_grid.py         # Grille d'albums
│   ├── metadata_table.py     # Tableau métadonnées éditable
│   ├── cover_viewer.py       # Visualiseur de pochette
│   ├── status_indicator.py   # Indicateur de statut
│   └── progress_bar.py       # Barre de progression
├── models/
│   ├── __init__.py
│   ├── album_model.py        # Modèle d'album UI
│   ├── ui_state.py          # État global de l'UI
│   └── selection_model.py    # Gestion des sélections
├── resources/
│   ├── ui/                   # Fichiers .ui (Glade)
│   │   ├── startup.ui
│   │   ├── main_window.ui
│   │   ├── edit_window.ui
│   │   ├── exceptions.ui
│   │   └── album_card.ui
│   ├── css/
│   │   ├── main.css         # Styles principaux
│   │   ├── cards.css        # Styles des cards
│   │   └── forms.css        # Styles des formulaires
│   ├── icons/               # Icônes SVG
│   └── gresource.xml        # Définition des ressources
└── utils/
    ├── __init__.py
    ├── gtk_helpers.py       # Utilitaires GTK
    ├── threading_utils.py   # Gestion async
    └── image_utils.py       # Manipulation d'images
```

---

## 🔄 PATTERN MVVM AVEC INTÉGRATION MODULES EXISTANTS

### Modèle d'intégration

```python
# Exemple: EditController utilisant les modules Phase 2
class EditController:
    def __init__(self, album_path: str):
        # === RÉUTILISATION MODULES EXISTANTS ===
        self.metadata_processor = MetadataProcessor()  # Module 2-3
        self.metadata_formatter = MetadataFormatter()  # Module 4
        self.file_renamer = FileRenamer()             # Module 5
        self.tag_synchronizer = TagSynchronizer()     # Module 6
        
        # Modules de support
        self.validator = MetadataValidator()          # Module 13
        self.logger = AppLogger(__name__)             # Module 14
        self.config = ConfigManager()                 # Module 15
        self.state_manager = StateManager()           # Module 16
        
        # === MODÈLES UI ===
        self.album_model = AlbumModel(album_path)
        self.ui_state = UIState()
        
        # === VUE GTK ===
        self.view = EditView()
        self.setup_bindings()
    
    def setup_bindings(self):
        """Lie les événements UI aux actions métier."""
        # Validation en temps réel
        self.view.on_field_changed.connect(self.validate_field)
        
        # Sauvegarde automatique
        self.view.on_metadata_changed.connect(self.auto_save)
        
        # Synchronisation avec fichiers
        self.view.on_save_requested.connect(self.synchronize_tags)
    
    def validate_field(self, field_name: str, value: str):
        """Validation temps réel avec feedback visuel."""
        validation = self.validator.validate_field(field_name, value)
        
        if validation.is_valid:
            self.view.set_field_valid(field_name)
            self.album_model.update_field(field_name, value)
        else:
            self.view.set_field_error(field_name, validation.errors[0])
        
        self.logger.debug(f"Validation {field_name}: {validation.is_valid}")
    
    def synchronize_tags(self):
        """Synchronise les modifications avec les fichiers MP3."""
        try:
            # Utilisation du Module 6 pour la synchronisation
            result = self.tag_synchronizer.synchronize_album(
                self.album_model.path,
                apply_metadata=True
            )
            
            if result.errors:
                self.view.show_errors(result.errors)
            else:
                self.view.show_success(f"{result.files_processed} fichiers synchronisés")
                
            self.logger.info(f"Synchronisation terminée: {result.files_processed} fichiers")
            
        except Exception as e:
            self.logger.error(f"Erreur synchronisation: {e}")
            self.view.show_error(f"Erreur: {e}")
```

---

## 🎨 DESIGN SYSTEM ET COMPOSANTS

### 1. Cards d'albums (Composant principal)

```python
class AlbumCard(Gtk.Box):
    """Card d'album réutilisable avec états dynamiques."""
    
    # Signaux GTK personnalisés
    __gsignals__ = {
        'album-selected': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'album-edit': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'album-remove': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }
    
    def __init__(self, album_model: AlbumModel):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.album_model = album_model
        self.build_ui()
        self.setup_styling()
        self.connect_signals()
    
    def build_ui(self):
        """Construit l'interface de la card."""
        # Header avec checkbox et menu
        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.checkbox = Gtk.CheckButton()
        self.menu_button = Gtk.MenuButton()
        
        # Zone pochette
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(200, 200)
        
        # Informations album
        self.title_label = Gtk.Label()
        self.artist_label = Gtk.Label() 
        self.tracks_label = Gtk.Label()
        
        # Indicateur de statut
        self.status_indicator = StatusIndicator()
        
        # Assembly
        self.header.append(self.checkbox)
        self.header.append(self.menu_button)
        
        self.append(self.header)
        self.append(self.cover_image)
        self.append(self.title_label)
        self.append(self.artist_label)
        self.append(self.tracks_label)
        self.append(self.status_indicator)
    
    def update_from_model(self):
        """Met à jour l'affichage selon le modèle."""
        # Mise à jour des textes
        self.title_label.set_text(self.album_model.album)
        self.artist_label.set_text(self.album_model.artist)
        self.tracks_label.set_text(f"{self.album_model.track_count} pistes")
        
        # Mise à jour de la pochette
        if self.album_model.cover_path:
            self.cover_image.set_filename(self.album_model.cover_path)
        else:
            self.cover_image.set_icon_name("media-optical-symbolic")
        
        # Mise à jour du statut
        self.status_indicator.set_status(self.album_model.status)
        
        # Application du style selon l'état
        self.update_styling()
```

### 2. Tableau métadonnées éditable

```python
class MetadataTable(Gtk.TreeView):
    """Tableau de métadonnées avec édition en ligne."""
    
    def __init__(self, album_model: AlbumModel):
        super().__init__()
        self.album_model = album_model
        self.validator = MetadataValidator()
        
        self.setup_model()
        self.setup_columns()
        self.setup_editing()
    
    def setup_columns(self):
        """Configure les colonnes éditables."""
        columns = [
            ("Fichier", "filename", False),  # Non éditable
            ("Titre", "title", True),        # Éditable
            ("Artiste", "artist", True),
            ("Album", "album", True),
            ("Numéro", "track_number", True),
            ("Année", "year", True),
            ("Genre", "genre", True),
            ("Statut", "status", False)      # Non éditable
        ]
        
        for title, field, editable in columns:
            column = Gtk.TreeViewColumn(title)
            
            if editable:
                cell = Gtk.CellRendererText()
                cell.set_property("editable", True)
                cell.connect("edited", self.on_cell_edited, field)
            else:
                cell = Gtk.CellRendererText()
            
            column.pack_start(cell, True)
            column.add_attribute(cell, "text", columns.index((title, field, editable)))
            self.append_column(column)
    
    def on_cell_edited(self, cell, path, new_text, field):
        """Gère l'édition d'une cellule avec validation."""
        # Validation en temps réel
        validation = self.validator.validate_field(field, new_text)
        
        if validation.is_valid:
            # Mise à jour du modèle
            iter = self.get_model().get_iter(path)
            self.get_model().set_value(iter, self.get_column_index(field), new_text)
            
            # Notification du changement
            self.album_model.update_track_field(path, field, new_text)
            
            # Style de validation réussie
            self.set_cell_style(path, field, "valid")
        else:
            # Affichage de l'erreur
            self.show_validation_error(path, field, validation.errors[0])
            self.set_cell_style(path, field, "error")
```

---

## 🔄 FLUX DE DONNÉES ET ÉTATS

### États de l'application

```python
class UIState:
    """Gestion centralisée de l'état de l'interface."""
    
    def __init__(self):
        self.current_view = "startup"
        self.selected_albums = []
        self.processing_status = "idle"
        self.last_error = None
        
        # Intégration avec StateManager (Module 16)
        self.state_manager = StateManager()
        self.setup_state_sync()
    
    def setup_state_sync(self):
        """Synchronise avec le StateManager global."""
        self.state_manager.subscribe("processing_status", self.on_processing_status_changed)
        self.state_manager.subscribe("album_updated", self.on_album_updated)
    
    def set_processing_status(self, status: str):
        """Met à jour le statut de traitement."""
        self.processing_status = status
        self.state_manager.set_status(status)
        self.notify_observers("processing_status_changed", status)
    
    def select_album(self, album_path: str):
        """Sélectionne un album."""
        if album_path not in self.selected_albums:
            self.selected_albums.append(album_path)
            self.notify_observers("selection_changed", self.selected_albums)
    
    def notify_observers(self, event: str, data):
        """Notifie les observateurs d'un changement."""
        # Pattern Observer pour mettre à jour les vues
        for observer in self.observers:
            observer.on_state_changed(event, data)
```

### Synchronisation temps réel

```python
class RealTimeSync:
    """Synchronisation temps réel entre UI et fichiers."""
    
    def __init__(self, edit_controller):
        self.controller = edit_controller
        self.sync_timer = None
        self.pending_changes = {}
    
    def schedule_sync(self, field: str, value: str):
        """Programme une synchronisation différée."""
        self.pending_changes[field] = value
        
        # Annule le timer précédent
        if self.sync_timer:
            GLib.source_remove(self.sync_timer)
        
        # Programme la synchronisation dans 2 secondes
        self.sync_timer = GLib.timeout_add_seconds(2, self.perform_sync)
    
    def perform_sync(self):
        """Effectue la synchronisation des modifications."""
        if not self.pending_changes:
            return False
        
        try:
            # Utilisation des modules Phase 2 pour la synchronisation
            for field, value in self.pending_changes.items():
                self.controller.metadata_processor.update_field(field, value)
            
            # Synchronisation physique avec TagSynchronizer
            self.controller.tag_synchronizer.synchronize_file(
                self.controller.album_model.current_file,
                self.pending_changes
            )
            
            self.pending_changes.clear()
            self.controller.view.show_sync_success()
            
        except Exception as e:
            self.controller.logger.error(f"Erreur synchronisation: {e}")
            self.controller.view.show_sync_error(str(e))
        
        return False  # Ne pas répéter le timer
```

---

## 🛠️ OUTILS DE DÉVELOPPEMENT

### 1. Design avec Glade

```xml
<!-- resources/ui/album_card.ui -->
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <template class="AlbumCard" parent="GtkBox">
    <property name="orientation">vertical</property>
    <property name="spacing">8</property>
    <style>
      <class name="album-card"/>
    </style>
    
    <child>
      <object class="GtkBox" id="header">
        <property name="orientation">horizontal</property>
        <child>
          <object class="GtkCheckButton" id="checkbox"/>
        </child>
        <child>
          <object class="GtkMenuButton" id="menu_button">
            <property name="icon-name">view-more-symbolic</property>
          </object>
        </child>
      </object>
    </child>
    
    <child>
      <object class="GtkPicture" id="cover_image">
        <property name="width-request">200</property>
        <property name="height-request">200</property>
        <style>
          <class name="album-cover"/>
        </style>
      </object>
    </child>
    
    <!-- Autres éléments... -->
  </template>
</interface>
```

### 2. Styles CSS

```css
/* resources/css/cards.css */
.album-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  margin: 8px;
  transition: all 0.2s ease;
}

.album-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.album-card.selected {
  border: 2px solid #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.album-card.processing {
  opacity: 0.7;
  pointer-events: none;
}

.album-card.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.album-cover {
  border-radius: 8px;
  object-fit: cover;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
}

.status-indicator.success {
  color: #10b981;
}

.status-indicator.error {
  color: #ef4444;
}

.status-indicator.warning {
  color: #f59e0b;
}
```

### 3. Gestion des ressources

```xml
<!-- resources/gresource.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/com/nonotags/ui">
    <!-- Fichiers UI -->
    <file>ui/startup.ui</file>
    <file>ui/main_window.ui</file>
    <file>ui/edit_window.ui</file>
    <file>ui/album_card.ui</file>
    
    <!-- Styles CSS -->
    <file>css/main.css</file>
    <file>css/cards.css</file>
    <file>css/forms.css</file>
    
    <!-- Icônes -->
    <file>icons/album-placeholder.svg</file>
    <file>icons/status-success.svg</file>
    <file>icons/status-error.svg</file>
  </gresource>
</gresources>
```

---

## 🚀 STRATÉGIE DE DÉVELOPPEMENT

### Phase 3A : Fondations (Semaine 6)
1. **Setup environnement GTK4**
2. **Architecture de base** avec contrôleurs
3. **Fenêtre de démarrage** simple
4. **Intégration modules existants**

### Phase 3B : Interfaces principales (Semaine 7)  
1. **Fenêtre principale** avec grille d'albums
2. **Cards d'albums** réutilisables
3. **Navigation et états**
4. **Tests d'intégration**

### Phase 3C : Interfaces complexes (Semaine 8)
1. **Fenêtre d'édition** multi-panneaux
2. **Tableau métadonnées** éditable
3. **Synchronisation temps réel**
4. **Fenêtre exceptions**

### Avantages de cette approche

✅ **Réutilisation maximale** : Tous les modules Phase 2 sont exploités
✅ **Architecture solide** : MVVM avec séparation claire des responsabilités  
✅ **Performance** : Pas de duplication de logique métier
✅ **Maintenabilité** : Code UI séparé de la logique existante
✅ **Extensibilité** : Facile d'ajouter de nouvelles vues
✅ **Tests** : Interface testable indépendamment de la logique

Cette architecture garantit une interface utilisateur moderne et performante tout en capitalisant sur le travail déjà réalisé en Phase 2.
