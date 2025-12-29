# Cahier des Charges : Migration Nonotags (Python/GTK vers Rust/Vue)

## 1. Objectif et Architecture
Refonte complète de l'application Nonotags pour améliorer les performances, la sécurité (typage fort) et la modernité de l'interface. L'objectif est de passer d'une application purement Linux/GTK à une application moderne, potentiellement multi-plateforme, tout en conservant la logique métier stricte de nettoyage.

**Stack Technique Cible :**
*   **Framework Application :** [Tauri](https://tauri.app/) (v2). Permet d'avoir un backend Rust performant et un frontend Web moderne, produisant un binaire natif très léger (contrairement à Electron).
*   **Backend (Core) :** Rust.
*   **Frontend (UI) :** Vue.js 3 + TypeScript + TailwindCSS (ou PrimeVue).
*   **Base de données :** SQLite (via `rusqlite` ou `sqlx`).
*   **Gestion Audio :** Crate `lofty` (recommandé pour la performance et le support large) ou `rust-id3`.

## 2. Phasage du Développement (Par ordre de priorité)

### Phase 1 : Fondations et Backend Core (Rust)
*Objectif : Mettre en place l'environnement et les capacités de base de lecture de fichiers sans UI.*
1.  **Initialisation du projet Tauri** : Configuration de l'espace de travail Rust + Vue.
2.  **Module `Scanner` (Rust)** :
    *   Portage de `music_scanner.py`.
    *   Parcours récursif performant (crate `walkdir`).
    *   Filtrage des extensions (.mp3).
    *   *Amélioration :* Scan asynchrone pour ne pas bloquer le thread principal.
3.  **Module `MetadataReader` (Rust)** :
    *   Lecture des tags ID3 (Artiste, Album, Titre, Année, Piste, Genre, Cover).
    *   Gestion robuste des erreurs de lecture (fichiers corrompus).

### Phase 2 : Base de Données et Configuration
*Objectif : Persistance des données et gestion des exceptions.*
1.  **Gestionnaire SQLite (Rust)** :
    *   Portage de `db_manager.py`.
    *   Création des schémas (Tables `exceptions`, `history`, `import_rules`).
    *   Migration des données existantes si nécessaire.
2.  **Système de Configuration** :
    *   Gestion des fichiers de config (TOML ou JSON) pour les préférences utilisateur (chemins par défaut, thèmes).

### Phase 3 : Interface Utilisateur Basique (Vue.js)
*Objectif : Avoir une fenêtre qui affiche les données du backend.*
1.  **Communication Tauri (Commands)** :
    *   Création des commandes Rust `scan_directory`, `get_metadata`, `save_config`.
2.  **Vue Principale (Dashboard)** :
    *   Composant "Sélecteur de dossier" (dialogue natif OS via Tauri API).
    *   Composant "Grille d'albums" (Portage de `AlbumCard`).
    *   Affichage des données brutes remontées par Rust.
    *   Gestion de l'état global (Pinia) pour stocker la liste des albums chargés.

### Phase 4 : Logique Métier Avancée (Le "Cerveau")
*Objectif : Porter l'intelligence de nettoyage de Python vers Rust. C'est la partie la plus critique.*
1.  **Module `MetadataProcessor` (Rust)** :
    *   Portage de `metadata_processor.py`.
    *   Implémentation des Regex de nettoyage (suppression commentaires, urls, tags parasites).
    *   Normalisation des séparateurs (" feat. ", " & ").
2.  **Module `CaseCorrector` (Rust)** :
    *   Portage de `case_corrector.py`.
    *   Algorithme de "Title Case" intelligent (gestion des exceptions grammaticales : "le", "la", "de", "du"...).
3.  **Intégration des Exceptions DB** :
    *   Avant d'appliquer une correction auto, vérifier si une exception existe en base (ex: "AC/DC").

### Phase 5 : Opérations sur Fichiers (Écriture)
*Objectif : Rendre l'application capable de modifier le disque.*
1.  **Module `TagWriter` (Rust)** :
    *   Écriture des métadonnées modifiées dans les fichiers MP3.
    *   Sauvegarde atomique pour éviter la corruption.
2.  **Module `FileRenamer` (Rust)** :
    *   Portage de `file_renamer.py`.
    *   Renommage physique des fichiers selon le pattern défini (ex: `{track} - {title}.mp3`).
    *   Renommage des dossiers albums.
3.  **Module `FileCleaner` (Rust)** :
    *   Suppression des fichiers indésirables (.txt, .nfo, images < X px).

### Phase 6 : Interface d'Édition et UX
*Objectif : Permettre l'interaction utilisateur complète.*
1.  **Vue Édition (Détail Album)** :
    *   Tableau éditable des pistes (Data Grid).
    *   Champs globaux (Artiste Album, Année, Genre) avec application en masse.
    *   Comparaison visuelle "Avant / Après" correction.
2.  **Gestion des Exceptions (UI)** :
    *   Interface pour ajouter/modifier des règles d'exception (Portage de `exceptions_window.py`).
    *   Bouton "Ajouter aux exceptions" directement depuis la vue d'édition.
3.  **Feedback Visuel** :
    *   Indicateurs de chargement, barres de progression (Scan).
    *   Notifications (Toasts) pour les succès/erreurs.

### Phase 7 : Fonctionnalités Annexes et Finalisation
1.  **Recherche de Pochettes** :
    *   Appels API (MusicBrainz/iTunes/Discogs) via `reqwest` (Rust).
    *   Interface de sélection de pochette (Drag & Drop).
2.  **Tests et CI/CD** :
    *   Tests unitaires Rust (`cargo test`) pour la logique de correction.
    *   Tests E2E basiques.
    *   Packaging (AppImage, .deb, .rpm).

## 3. Correspondance des Modules (Python -> Rust)

| Module Python | Module Rust (Suggéré) | Crate Recommandée |
| :--- | :--- | :--- |
| `music_scanner.py` | `scanner.rs` | `walkdir` |
| `metadata_processor.py` | `processor.rs` | `regex`, `lazy_static` |
| `case_corrector.py` | `corrector.rs` | - |
| `db_manager.py` | `database.rs` | `rusqlite` ou `sqlx` |
| `mutagen` (lib) | `audio.rs` | `lofty` (ou `rust-id3`) |
| `requests` | `api.rs` | `reqwest` |
| `ui/` (GTK) | `src/` (Vue) | `tauri-plugin-dialog`, `tauri-plugin-fs` |
