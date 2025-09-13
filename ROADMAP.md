# ROADMAP - Application Nonotags

## Vue d'ensemble
Cette roadmap détaille toutes les étapes nécessaires pour développer l'application de gestion de métadonnées MP3 "Nonotags".

---

## PHASE 1 : FONDATIONS ET ARCHITECTURE (Semaines 1-2)

### 1.1 Configuration de l'environnement de développement
- [x] Installation des dépendances Python (mutagen, PyGObject, GTK) ✅
- [x] Configuration de l'environnement de développement sur Fedora 41 ✅
- [x] Création de la structure de projet ✅
- [x] Configuration des outils de développement (linter, formatter) ✅

### 1.2 Architecture du projet
- [x] Création de l'arborescence des modules ✅
  ```
  nonotags/
  ├── main.py
  ├── core/
  │   ├── __init__.py
  │   ├── file_cleaner.py           # Module 1
  │   ├── metadata_processor.py     # Modules 2-3
  │   ├── rules_engine.py           # Module 4
  │   ├── exceptions_manager.py     # Module 5
  │   └── sync_manager.py           # Module 6
  ├── ui/
  │   ├── __init__.py
  │   ├── main_window.py            # Module 9
  │   ├── album_card.py             # Module 11
  │   ├── edit_window.py            # Module 9
  │   └── exceptions_window.py      # Module 9
  ├── database/
  │   ├── __init__.py
  │   ├── db_manager.py             # Module 10
  │   └── models.py                 # Module 10
  ├── services/
  │   ├── __init__.py
  │   ├── cover_search.py           # Module 7
  │   ├── playlist_creator.py       # Module 8
  │   └── audio_player.py           # Module 12
  ├── support/
  │   ├── __init__.py
  │   ├── validator.py              # Module 13 - Validation
  │   ├── logger.py                 # Module 14 - Logging
  │   ├── config_manager.py         # Module 15 - Configuration
  │   └── state_manager.py          # Module 16 - Gestion d'état
  └── tests/
  ```

### 1.3 Modules de support (nouvelle priorité)
- [x] **Module 14 - Logging** : Système de journalisation centralisé ✅
  - Configuration des niveaux de log ✅
  - Rotation des fichiers de log ✅
  - Formatage standardisé des messages ✅
- [x] **Module 15 - Configuration** : Gestionnaire de configuration ✅
  - Chargement/sauvegarde des paramètres ✅
  - Valeurs par défaut ✅
  - Validation des configurations ✅
- [x] **Module 16 - Gestion d'état** : État global de l'application ✅
  - Centralisation de l'état ✅
  - Événements inter-modules ✅
  - Coordination des opérations ✅
- [x] **Module 13 - Validation** : Validation des données ✅
  - Validation des fichiers MP3 ✅
  - Contrôle d'intégrité des métadonnées ✅
  - Validation des saisies utilisateur ✅

### 1.4 Base de données (étendue)
- [x] Création du schéma SQLite étendu ✅
- [x] Implémentation de la table `case_exceptions` ✅
- [x] Implémentation de la table `app_config` ✅
- [x] Implémentation de la table `import_history` ✅
- [x] Scripts d'initialisation de la base ✅
- [x] Tests de connexion et CRUD basique ✅
- [x] Intégration avec le module de configuration ✅

---

## PHASE 2 : MOTEUR DE RÈGLES ET TRAITEMENT (Semaines 3-5)

### 2.1 Module de nettoyage des fichiers (GROUPE 1)
- [x] **Intégration avec modules de support** :
  - Validation des permissions et formats (Module 13) ✅
  - Logging des opérations de nettoyage (Module 14) ✅
- [x] Suppression des fichiers indésirables (.DS_Store, Thumbs.db, etc.) ✅
- [x] Suppression des sous-dossiers ✅
- [x] Renommage des fichiers de pochettes (front.jpg → cover.jpg) ✅
- [x] Tests unitaires du module avec logging intégré ✅

### 2.2 Module de nettoyage des métadonnées (GROUPE 2)
- [x] **Intégration avec modules de support** : ✅
  - Validation de l'intégrité des métadonnées (Module 13) ✅
  - Logging des modifications (Module 14) ✅
  - Historique des changements (base import_history) ✅
- [x] Suppression des commentaires ✅
- [x] Suppression des parenthèses et contenu ✅
- [x] Nettoyage des espaces en trop ✅
- [x] Suppression des caractères spéciaux ✅
- [x] Normalisation " and " et " et " → " & " ✅
- [x] Tests unitaires du module ✅

### 2.3 Module de corrections de casse (GROUPE 3)
- [x] **Intégration avec modules de support** : ✅
  - Validation des exceptions avant application (Module 13) ✅
  - Logging détaillé des corrections de casse (Module 14) ✅
  - Configuration des règles personnalisables (Module 15) ✅
- [x] Implémentation des règles de casse pour titres/albums ✅
- [x] Gestion des exceptions (villes, chiffres romains, " I ") ✅
- [x] Protection artiste dans titre d'album ✅
- [x] Intégration avec les exceptions utilisateur (base de données) ✅
- [x] Tests unitaires du module avec traçabilité complète ✅

### 2.4 Module de formatage (GROUPE 4)
- [x] **Intégration avec modules de support** : ✅
  - Validation des champs et valeurs (Module 13) ✅
  - Logging détaillé du formatage (Module 14) ✅
  - Configuration des règles de formatage (Module 15) ✅
- [x] Copie artiste → interprète ✅
- [x] Formatage numéro de piste (01, 02, 03...) ✅
- [x] Gestion année compilation ✅
- [x] Normalisation des genres ✅
- [x] Validation des champs requis ✅
- [x] Tests unitaires du module ✅

### 2.5 Module de renommage (GROUPE 5)
- [x] **Intégration avec modules de support** : ✅
  - Validation des chemins et formats (Module 13) ✅
  - Logging détaillé du renommage (Module 14) ✅
  - Configuration des règles de renommage (Module 15) ✅
- [x] Renommage fichiers : "(N° piste) - Titre" ✅
- [x] Renommage dossier : "(Année) Album" ✅
- [x] Gestion multi-années : "(année1-année2) Album" ✅
- [x] Tests unitaires du module ✅

### 2.6 Module de finalisation (GROUPE 6)
- [x] **Intégration avec modules de support** : ✅
  - Validation des métadonnées et images (Module 13) ✅
  - Logging détaillé des synchronisations (Module 14) ✅
  - Configuration des paramètres de synchronisation (Module 15) ✅
  - Gestion d'état pour les opérations de finalisation (Module 16) ✅
- [x] Association cover.jpg aux métadonnées ✅
- [x] Mise à jour temps réel des tags physiques ✅
- [x] Validation et formatage des pochettes (200x200 minimum) ✅
- [x] Sauvegarde et restauration des originaux ✅
- [x] Gestion des erreurs et statuts détaillés ✅
- [x] Tests unitaires du module (33 tests passent) ✅

### 2.7 Moteur d'orchestration
- [x] **PHASE 2 COMPLÉTÉE À 100%** ✅
  - **6 modules principaux** implémentés et testés ✅
  - **123 tests unitaires** - Tous passent ✅
  - **Pipeline complet** : Import → Nettoyage → Correction → Format → Renommage → Finalisation ✅
  - **Intégration support** : Validation, Logging, Configuration, État ✅
- [ ] Coordinateur d'exécution des 6 groupes
- [ ] Gestion d'erreurs et continuité de traitement
- [ ] Logging des opérations
- [ ] Tests d'intégration

---

## PHASE 3 : INTERFACE UTILISATEUR (Semaines 6-8)

> **🎯 STATUT :** Phase 2 terminée à 100% - Prêt pour l'UI
> 
> **📦 FONDATIONS DISPONIBLES :**
> - ✅ Pipeline de traitement complet (6 modules core)
> - ✅ Modules de support intégrés (validation, logging, config, état)
> - ✅ Base de données opérationnelle
> - ✅ 123 tests unitaires validés
> 
> **🔧 ARCHITECTURE UI :** GTK4 + PyGObject avec pattern MVVM

### 3.0 STRATÉGIE DE CONSTRUCTION UI

#### 3.0.1 Architecture technique UI
```
ui/
├── __init__.py
├── app_controller.py         # Contrôleur principal
├── views/
│   ├── __init__.py
│   ├── startup_view.py       # Fenêtre de démarrage
│   ├── main_view.py          # Fenêtre principale
│   ├── album_card_view.py    # Card d'album
│   ├── edit_view.py          # Fenêtre d'édition
│   └── exceptions_view.py    # Fenêtre exceptions
├── components/
│   ├── __init__.py
│   ├── album_grid.py         # Grille d'albums
│   ├── metadata_table.py     # Tableau métadonnées
│   ├── cover_selector.py     # Sélecteur de pochette
│   └── audio_player.py       # Lecteur audio
├── models/
│   ├── __init__.py
│   ├── album_model.py        # Modèle d'album
│   └── ui_state_model.py     # État de l'interface
└── resources/
    ├── ui/                   # Fichiers .ui (Glade)
    ├── css/                  # Styles CSS
    └── icons/                # Icônes de l'application
```

#### 3.0.2 Pattern architectural : MVVM avec GTK
- **Model** : Classes de données + modules core existants
- **View** : Fichiers .ui (Glade) + composants GTK
- **ViewModel** : Contrôleurs qui font le lien model ↔ view
- **Services** : Réutilisation des modules de support existants

#### 3.0.3 Intégration avec les modules existants
```python
# Exemple d'intégration dans un contrôleur UI
class AlbumEditController:
    def __init__(self):
        # Réutilisation des modules Phase 2
        self.metadata_processor = MetadataProcessor()
        self.validator = MetadataValidator()
        self.logger = AppLogger(__name__)
        self.state_manager = StateManager()
        
    def update_metadata(self, field, value):
        # Validation en temps réel
        validation = self.validator.validate_field(field, value)
        if validation.is_valid:
            # Mise à jour avec logging
            self.metadata_processor.update_field(field, value)
            self.logger.info(f"Métadonnée mise à jour: {field}={value}")
            # Notification de changement d'état
            self.state_manager.notify_change("metadata_updated")
```

#### 3.0.4 Outils de développement UI
- **Glade** : Design visuel des interfaces (.ui)
- **GTK Inspector** : Debug et test des interfaces
- **CSS GTK** : Stylisation personnalisée
- **GResource** : Packaging des ressources

---

### 3.1 Fenêtre de démarrage
- [ ] **Architecture et design** :
  - Création du fichier .ui avec Glade ✅ (design visuel)
  - Intégration CSS pour le style moderne
  - Contrôleur StartupController avec pattern MVVM
- [ ] **Intégration avec modules de support** :
  - Configuration de l'interface depuis le module 15 ✅
  - Gestion d'état pour la navigation (Module 16) ✅
  - Logging des actions utilisateur (Module 14) ✅
- [ ] **Fonctionnalités** :
  - Interface minimale avec 3 boutons
  - "Importer des albums" → navigateur système (GtkFileChooserDialog)
  - "Ajouter des exceptions d'importation" → fenêtre exceptions
  - "Ouvrir l'application" → fenêtre principale
- [ ] **Tests** :
  - Tests unitaires du contrôleur
  - Tests d'intégration avec modules support

### 3.2 Fenêtre principale
- [ ] **Architecture et design** :
  - Création du fichier .ui principal avec header bar GTK4
  - Layout responsif avec GtkScrolledWindow
  - Contrôleur MainController avec gestion d'état
- [ ] **Intégration avec modules de support** :
  - État centralisé des albums importés (Module 16) ✅
  - Configuration de l'affichage (Module 15) ✅
  - Validation des sélections (Module 13) ✅
- [ ] **Composants** :
  - Header bar avec boutons de navigation
  - Grille d'albums avec GtkFlowBox
  - Barre de statut avec progression
  - Menu hamburger avec préférences
- [ ] **Fonctionnalités** :
  - Affichage en damier des cards d'albums
  - Gestion de la sélection multiple
  - Bouton "Traiter les albums sélectionnés"
  - Recherche et filtrage des albums
- [ ] **Tests** :
  - Tests de performance avec gros volumes
  - Tests de responsivité

### 3.3 Cards d'albums (Composant réutilisable)
- [ ] **Architecture et design** :
  - Composant AlbumCardView réutilisable
  - Template .ui pour une card type
  - CSS pour les différents états (normal, sélectionné, erreur)
- [ ] **Intégration avec modules de support** :
  - Système de statut renforcé avec validation (Module 13) ✅
  - Logging des erreurs de cards (Module 14) ✅
  - Coordination d'état pour synchronisation (Module 16) ✅
- [ ] **Éléments visuels** :
  - Affichage pochette (ou placeholder SVG)
  - Informations album (titre, artiste, nb morceaux)
  - Système de statut avec icônes colorées
  - Case à cocher pour sélection
  - Boutons contextuels (playlist, retirer)
- [ ] **Interactions** :
  - Double-clic → fenêtre d'édition
  - Clic droit → menu contextuel
  - Drag & drop pour réorganisation
- [ ] **États dynamiques** :
  ```python
  # Gestion des états de card
  CARD_STATES = {
      'PENDING': ('⏳', 'En attente', 'card-pending'),
      'PROCESSING': ('🔄', 'Traitement', 'card-processing'),
      'SUCCESS': ('✅', 'Traité', 'card-success'),
      'ERROR': ('❌', 'Erreur', 'card-error'),
      'WARNING': ('⚠️', 'Attention', 'card-warning')
  }
  ```

### 3.4 Fenêtre d'édition (Interface complexe)
- [ ] **Architecture et design** :
  - Interface divisée en 3 panneaux principaux
  - Layout adaptatif avec GtkPaned
  - Contrôleur EditController avec validation temps réel
- [ ] **Intégration avec modules de support** :
  - Validation en temps réel des modifications (Module 13) ✅
  - Logging de toutes les modifications (Module 14) ✅
  - Configuration personnalisable de l'interface (Module 15) ✅
  - Synchronisation d'état avec autres fenêtres (Module 16) ✅
- [ ] **Panneau gauche - Pochette et infos générales** :
  - Widget pochette (300x300) avec zoom
  - Bouton recherche pochette (intégration Module 7)
  - Champs de saisie : Album, Artiste, Année, Genre
  - Menu déroulant genres (25 genres hardcodés)
  - Validation en temps réel avec indicateurs visuels
- [ ] **Panneau central - Tableau métadonnées** :
  - GtkTreeView avec colonnes ajustables/triables
  - Édition cellules par double-clic
  - Validation instantanée avec surlignage erreurs
  - Synchronisation bidirectionnelle avec fichiers MP3
  - Undo/Redo avec historique
- [ ] **Panneau droit - Outils et actions** :
  - Lecteur audio intégré (Module 12)
  - Historique des modifications
  - Actions rapides (corriger tout, réinitialiser)
  - Prévisualisation des changements
- [ ] **Fonctionnalités avancées** :
  - Auto-sauvegarde toutes les 30 secondes
  - Mode "aperçu" avant validation finale
  - Export/Import des métadonnées en JSON
  - Raccourcis clavier pour actions fréquentes

### 3.5 Fenêtre des exceptions (Interface de gestion)
- [ ] **Architecture et design** :
  - Interface de gestion CRUD des exceptions
  - Recherche et filtrage avancé
  - Contrôleur ExceptionsController
- [ ] **Intégration avec modules de support** :
  - Validation des exceptions avant ajout (Module 13) ✅
  - Logging des modifications d'exceptions (Module 14) ✅
  - Configuration avancée des règles (Module 15) ✅
- [ ] **Sections de l'interface** :
  - **Bloc test et ajout** (haut) :
    - Zone de test avec aperçu en temps réel
    - Formulaire d'ajout avec validation
    - Suggestions basées sur l'historique
  - **Bloc affichage règles** (gauche) :
    - Liste hiérarchique des règles
    - Recherche et filtrage
    - Import/Export des règles
  - **Bloc gestion** (droite) :
    - Édition des règles sélectionnées
    - Suppression avec confirmation
    - Statistiques d'utilisation
- [ ] **Fonctionnalités** :
  - Preview en temps réel des règles
  - Validation avec feedback visuel
  - Backup automatique avant modifications
  - Mode expert pour règles regex

---

### 🔧 PLAN DE DÉVELOPPEMENT UI - PHASE 3

#### Semaine 6 : Fondations UI
1. **Configuration environnement GTK4**
   - Installation GTK4-devel sur Fedora
   - Configuration PyGObject avec GTK4
   - Setup Glade pour design d'interfaces

2. **Structure de base**
   - Création de l'arborescence ui/
   - AppController principal
   - Integration avec modules existants

3. **Fenêtre de démarrage**
   - Design avec Glade
   - Implémentation StartupController
   - Navigation basique

#### Semaine 7 : Interfaces principales
1. **Fenêtre principale**
   - Layout principal avec header bar
   - Intégration AlbumGrid
   - Gestion de la navigation

2. **Cards d'albums**
   - Composant réutilisable
   - États dynamiques
   - Interactions de base

3. **Tests et debug**
   - Tests unitaires des contrôleurs
   - Debug avec GTK Inspector

#### Semaine 8 : Interfaces avancées
1. **Fenêtre d'édition**
   - Interface complexe multi-panneaux
   - Tableau métadonnées éditable
   - Synchronisation temps réel

2. **Fenêtre exceptions**
   - Interface de gestion CRUD
   - Validation avancée
   - Tests d'intégration

3. **Finalisation**
   - CSS et thème global
   - Tests utilisateur
   - Optimisations performance

---

### 🎨 DESIGN SYSTEM

#### Palette de couleurs
```css
:root {
  /* Couleurs principales */
  --primary-color: #2563eb;     /* Bleu principal */
  --secondary-color: #64748b;   /* Gris secondaire */
  --accent-color: #f59e0b;      /* Orange accent */
  
  /* États */
  --success-color: #10b981;     /* Vert succès */
  --warning-color: #f59e0b;     /* Orange avertissement */
  --error-color: #ef4444;       /* Rouge erreur */
  
  /* Interface */
  --background-color: #f8fafc;  /* Fond principal */
  --surface-color: #ffffff;     /* Fond cards */
  --border-color: #e2e8f0;      /* Bordures */
}
```

#### Composants standardisés
- **Boutons** : Primary, Secondary, Outline, Ghost
- **Cards** : Avec ombres et états hover
- **Tables** : Alternance de couleurs, tri visuel
- **Inputs** : Validation visuelle, placeholders
- **Icons** : Set cohérent (Lucide ou Phosphor)

#### Responsive design
- Adaptation tablette (768px+)
- Adaptation desktop (1024px+)
- Grid system flexible
- Typography scale harmonieuse

---

## PHASE 4 : FONCTIONNALITÉS AVANCÉES (Semaines 9-10)

## PHASE 4 : FONCTIONNALITÉS AVANCÉES (Semaines 9-10)

### 4.1 Recherche de pochettes
- [ ] **Intégration avec modules de support** :
  - Validation des API et formats d'images (Module 13)
  - Logging des recherches et téléchargements (Module 14)
  - Configuration des sources de recherche (Module 15)
- [ ] Intégration APIs (MusicBrainz, Discogs, iTunes)
- [ ] Fenêtre de recherche avec résultats
- [ ] Validation taille minimale (250x250)
- [ ] Téléchargement et intégration pochettes
- [ ] Gestion cache temporaire avec logging

### 4.2 Lecteur audio
- [ ] **Intégration avec modules de support** :
  - Validation des formats audio supportés (Module 13)
  - Logging des opérations de lecture (Module 14)
  - Configuration audio personnalisable (Module 15)
  - État centralisé du lecteur (Module 16)
- [ ] Contrôles de base (play, pause, stop, suivant, précédent)
- [ ] Curseur de progression
- [ ] Égaliseur basique
- [ ] Intégration avec double-clic nom fichier
- [ ] Gestion formats audio supportés avec validation

### 4.3 Création de playlists
- [ ] **Intégration avec modules de support** :
  - Validation des chemins et formats (Module 13)
  - Logging de la création de playlists (Module 14)
  - Configuration des formats de playlist (Module 15)
- [ ] Génération format M3U
- [ ] Chemins relatifs
- [ ] Sauvegarde dans dossier album
- [ ] Validation et tests avec traçabilité complète

---

## PHASE 5 : INTÉGRATION ET TESTS (Semaines 11-12)

### 5.1 Tests d'intégration avec modules de support
- [ ] **Tests de validation** :
  - Validation de tous les formats supportés
  - Tests de validation des saisies utilisateur
  - Validation de l'intégrité des données
- [ ] **Tests de logging** :
  - Vérification de la journalisation complète
  - Tests des différents niveaux de log
  - Validation de la rotation des logs
- [ ] **Tests de configuration** :
  - Chargement/sauvegarde des paramètres
  - Tests des valeurs par défaut
  - Migration de configuration
- [ ] **Tests de gestion d'état** :
  - Synchronisation entre modules
  - Cohérence de l'état global
  - Recovery après erreur
- [ ] Tests workflow complet d'import avec traçabilité
- [ ] Tests gestion d'erreurs avec logging détaillé
- [ ] Tests performances sur gros volumes
- [ ] Tests interface utilisateur
- [ ] Jeu de données de test standardisé

### 5.2 Gestion d'erreurs robuste avec modules de support
- [ ] **Système de statut enrichi** :
  - Intégration validation → statuts détaillés
  - Logs centralisés pour toutes les erreurs
  - Configuration des seuils d'alerte
- [ ] Système de statut des cards
- [ ] Messages d'erreur détaillés avec logging
- [ ] Icônes et tooltips informatifs
- [ ] Historique des erreurs en base (import_history)
- [ ] Recovery automatique quand possible avec logging

### 5.3 Optimisations avec support du logging
- [ ] **Monitoring des performances** :
  - Métriques de performance loggées
  - Identification des goulots via logs
  - Configuration optimale automatique
- [ ] Optimisation performances traitement
- [ ] Optimisation interface (réactivité)
- [ ] Gestion mémoire pour gros albums
- [ ] Optimisation base de données

---

## PHASE 6 : PACKAGING ET DÉPLOIEMENT (Semaines 13-14)

### 6.1 Packaging AppImage
- [ ] **Intégration finale des modules de support** :
  - Configuration de production (Module 15)
  - Logs de déploiement (Module 14)
  - Validation de l'environnement (Module 13)
- [ ] Configuration AppImage pour Fedora
- [ ] Inclusion de toutes les dépendances
- [ ] Tests sur différentes versions Linux
- [ ] Script de build automatisé avec logging

### 6.2 Documentation technique et maintenance
- [ ] **Documentation des modules de support** :
  - Guide de configuration avancée
  - Documentation des logs et débogage
  - Procédures de validation et maintenance
- [ ] Documentation du code avec exemples de logging
- [ ] Guide d'utilisation avec section dépannage
- [ ] Documentation de débogage avec logs
- [ ] Tests de validation finale

### 6.3 Préparation maintenance future
- [ ] **Outils de maintenance** :
  - Scripts de diagnostic avec logging
  - Utilitaires de validation de configuration
  - Outils de migration de base de données
- [ ] Structure pour mises à jour
- [ ] Système de monitoring des erreurs
- [ ] Backup et restauration configuration utilisateur
- [ ] Guide d'installation
- [ ] Guide de contribution (si open source)
- [ ] Documentation API interne

### 6.3 Tests finaux
- [ ] Tests sur environnement propre
- [ ] Tests de régression
- [ ] Validation cahier des charges
- [ ] Tests utilisateur final

---

## PHASE 7 : LIVRAISON ET MAINTENANCE (Semaine 15+)

### 7.1 Release
- [ ] Version finale 1.0.0
- [ ] Publication AppImage
- [ ] Documentation utilisateur finale
- [ ] Communication release

### 7.2 Post-release
- [ ] Monitoring bugs utilisateurs
- [ ] Patches critiques si nécessaires
- [ ] Planification évolutions futures
- [ ] Retours d'expérience

---

## ESTIMATION GLOBALE

**Durée totale estimée :** 15 semaines (3-4 mois)

**Architecture modulaire :** 16 modules (12 modules de base + 4 modules de support pour la maintenabilité)

**Répartition effort :**
- Backend/Logique métier : 35%
- Modules de support (validation, logging, config, état) : 15%
- Interface utilisateur : 30%
- Tests et intégration : 12%
- Packaging et déploiement : 8%

**Jalons critiques :**
- ✅ Fin Phase 1 : Modules de support opérationnels (fondation solide)
- ✅ Fin Phase 2 : Moteur de règles fonctionnel avec logging/validation
- ✅ Fin Phase 3 : Interface utilisateur complète avec support centralisé
- ✅ Fin Phase 5 : Application stable et testée avec traçabilité complète
- ✅ Fin Phase 6 : Application packagée et déployable avec outils de maintenance

---

## RISQUES ET MITIGATION

### Risques techniques
- **Complexité GTK/PyGObject :** Prévoir formation et prototypage précoce
- **Performance sur gros volumes :** Tests et optimisations dès la Phase 2
- **Intégration APIs pochettes :** Prévoir fallbacks et gestion limite de taux

### Risques projet
- **Scope creep :** S'en tenir strictement au cahier des charges validé
- **Perfectionnisme :** Définir MVP et critères d'acceptation clairs
- **Tests insuffisants :** Intégrer tests dès le début, pas à la fin

---

## OUTILS ET RESSOURCES

### Développement
- **IDE :** VS Code avec extensions Python/GTK
- **Version control :** Git
- **Tests :** pytest
- **Documentation :** Sphinx

### APIs externes
- **MusicBrainz API :** https://musicbrainz.org/doc/MusicBrainz_API
- **Discogs API :** https://www.discogs.com/developers/
- **iTunes API :** https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/

### Resources GTK
- **PyGObject Documentation :** https://pygobject.readthedocs.io/
- **GTK Documentation :** https://docs.gtk.org/

---

*Cette roadmap sera mise à jour au fur et à mesure de l'avancement du projet.*
