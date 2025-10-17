# Application de gestion de métadonnées MP3

## Introduction
L'application de gestion de métadonnées MP3 est conçue pour gérer les métadonnées des fichiers MP3. Elle importera des dossiers d'album en appliquant automatiquement des corrections en fonction de règles hardcodées et d'exceptions définies par l'utilisateur, puis permettra aux utilisateurs de corriger manuellement les métadonnées des fichiers MP3.

## Fonctionnalités

L'application de gestion de métadonnées MP3 aura les fonctionnalités suivantes :

1. Suppression automatique des fichiers indésirables dans le dossier "Album".
2. Renommage du nom du dossier d'origine.
3. Correction automatique des métadonnées : L'application permettra de corriger les métadonnées des fichiers MP3 en fonction de règles et d'exceptions définies.
4. Correction manuelle des métadonnées : L'application permettra aux utilisateurs de corriger les métadonnées des fichiers MP3 qui nécessitent des corrections après la correction automatique.
5. Gestion des exceptions : L'application permettra aux utilisateurs de définir des exceptions pour la correction des métadonnées. Les exceptions seront stockées dans une base de données SQLite.
6. Interface utilisateur : L'application aura une interface utilisateur graphique développée en utilisant PyGObject avec GTK. L'interface utilisateur permettra aux utilisateurs de corriger les métadonnées des fichiers MP3, de définir les exceptions, et de gérer la correction manuelle des métadonnées des fichiers MP3.
7. Base de données : L'application utilisera une base de données SQLite pour stocker les exceptions de casse.

## Exigences fonctionnelles

1. **Importation d'album MP3** :
   - L'application doit analyser et trier automatiquement les fichiers et dossiers dans le dossier importé.
   - L'application doit supprimer automatiquement les fichiers et dossiers indésirables dans le dossier importé.
   - L'application doit renommer automatiquement certains fichiers dans le dossier importé.
   - L'application doit appliquer les règles hardcodées de corrections des métadonnées.
   - L'application doit corriger le nom du dossier importé.

2. **Correction manuelle des métadonnées** :
   - L'application doit permettre aux utilisateurs d'ajouter des exceptions au fil du temps. Les exceptions devront être ajoutées aux règles d'importation automatique.
   - L'application doit permettre aux utilisateurs d'accéder aux métadonnées affichées sous forme de tableau pour pouvoir les corriger manuellement.

3. **Interface utilisateur** :
   - L'application doit avoir une interface utilisateur graphique développée en utilisant PyGObject avec GTK.
   - L'application doit afficher les imports sous la forme de cards avec pochette de l'album et informations.
   - Le clic sur les cards choisies doit ouvrir une fenêtre d'édition avec un tableau affichant les métadonnées (pour les corrections manuelles) et des champs de saisie pour généraliser les corrections manuelles.

4. **Synchronisation** :
   - Le tableau de la fenêtre d'édition doit être synchronisé en temps réel avec les métadonnées.

5. **Base de données** :
   - L'application doit utiliser une base de données SQLite pour stocker les exceptions de casse définies par l'utilisateur.
   - L'application doit permettre aux utilisateurs de gérer les exceptions de casse via l'interface graphique.

## Exigences non fonctionnelles

1. **Performances** : L'application doit être performante et réagir rapidement aux entrées de l'utilisateur.
2. **Sécurité** : L'application doit être sécurisée et protéger les données des utilisateurs.
3. **Compatibilité** : L'application doit être compatible avec les différentes versions de Linux (priorité sur Fedora 41).
4. **Utilisabilité** : L'application doit être facile à utiliser et avoir une interface utilisateur claire et intuitive.

## Architecture

### Modules principaux (12 modules de base)
1. **Module de suppression des dossiers indésirables** : Nettoyage des fichiers et dossiers indésirables.
2. **Module de correction automatique des métadonnées** : Application des règles hardcodées de correction.
3. **Module de correction manuelle des métadonnées** : Interface et logique pour les corrections manuelles.
4. **Module de gestion des règles** : Gestion et exécution des règles hardcodées organisées par groupes.
5. **Module de gestion des exceptions** : Gestion des exceptions de casse définies par l'utilisateur.
6. **Module de synchronisation** : Synchronisation temps réel entre métadonnées et interface.
7. **Module de recherche de pochette** : Recherche et téléchargement de pochettes depuis internet.
8. **Module de création de playlist** : Génération de playlists M3U avec chemins relatifs.
9. **Module d'interface utilisateur** : Gestion des fenêtres et interfaces GTK.
10. **Module de base de données** : Gestion de la base de données SQLite.
11. **Module de gestion des cards** : Affichage et gestion des cards d'albums.
12. **Module de lecteur audio** : Lecteur audio intégré avec contrôles et égaliseur.

### Modules de support pour la maintenabilité (4 modules supplémentaires)
13. **Module de validation** : Validation des données d'entrée, formats de fichiers et intégrité des métadonnées.
14. **Module de logging** : Système de journalisation centralisé pour le débogage et le suivi d'erreurs.
15. **Module de configuration** : Gestion centralisée des paramètres d'application et préférences utilisateur.
16. **Module de gestion d'état** : Centralisation de l'état de l'application et coordination entre modules.

### Détail des modules de support

#### Module 13 : Validation
**Responsabilités** :
- Validation des formats de fichiers MP3 avant traitement
- Vérification de l'intégrité des métadonnées existantes
- Validation des chemins de fichiers et permissions d'accès
- Contrôle de la cohérence des données saisies par l'utilisateur
- Validation des exceptions avant ajout en base de données

**Avantages pour la maintenabilité** :
- Centralisation des contrôles de validité
- Prévention des erreurs en amont
- Messages d'erreur cohérents et informatifs

#### Module 14 : Logging
**Responsabilités** :
- Journalisation centralisée de toutes les opérations
- Gestion des niveaux de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Rotation automatique des fichiers de log
- Formatage standardisé des messages de log
- Traçabilité des modifications de métadonnées

**Avantages pour le débogage** :
- Historique complet des opérations
- Identification rapide des problèmes
- Suivi des performances et goulots d'étranglement
- Audit trail pour les modifications

#### Module 15 : Configuration
**Responsabilités** :
- Gestion centralisée des paramètres d'application
- Sauvegarde/restauration des préférences utilisateur
- Configuration des règles d'import personnalisables
- Gestion des chemins par défaut (dossiers, exports)
- Paramètres de performance et optimisation

**Avantages pour la maintenabilité** :
- Point unique de configuration
- Facilité d'ajout de nouveaux paramètres
- Cohérence des valeurs par défaut
- Portabilité des configurations

#### Module 16 : Gestion d'état
**Responsabilités** :
- Centralisation de l'état global de l'application
- Coordination entre les différents modules
- Gestion des événements inter-modules
- Suivi de l'état des imports en cours
- Synchronisation des données partagées

**Avantages pour la maintenabilité** :
- Réduction du couplage entre modules
- Facilitation des tests unitaires
- Cohérence de l'état applicatif
- Debugging centralisé de l'état

## Règles hardcodées - Organisation par groupes logiques

### GROUPE 1 : NETTOYAGE FICHIERS
1. Suppression des fichiers indésirables dans le dossier d'album original : .DS_Store, Thumbs.db, PNG, NFO, TXT, M3U (et autre format de playlists), bs.db.
2. Suppression des sous-dossiers dans le dossier de l'album original.
3. Renommage automatique des fichiers front.jpg, Front.jpg et Cover.jpg en cover.jpg.

### GROUPE 2 : NETTOYAGE MÉTADONNÉES
4. Suppression des commentaires dans les métadonnées.
5. Suppression des parenthèses et leur contenu dans Titres, Artistes et albums.
6. Nettoyage des espaces en trop dans Titres, Artistes et albums.
7. Suppression des caractères spéciaux suivants dans Titres, Artistes et albums : !, ", #, $, %, &', *, +, ,, -, ., :, ;, <, =, >, ?, @, [, \, ], ^, _, {, |, }, ~.
8. Normaliser " and " et " et " dans Titres, Artistes et albums en les remplaçant par " & ".

### GROUPE 3 : CORRECTIONS CASSE
9. Casse propre - Titres = Première lettre en majuscule, puis tout le reste en minuscule.
10. Casse propre - Albums = Première lettre en majuscule, puis tout le reste en minuscule.
11. Ne pas appliquer les règles de casse sur les noms de villes et les chiffres romains.
12. Si le nom de l'artiste est présent dans le titre de l'album, le nom de l'artiste ne doit pas subir la correction de casse.
18. Si " I " est détecté dans Titres, Artistes ou Album il doit rester " I ".

### GROUPE 4 : FORMATAGE
13. Copier artiste vers interprète.
14. Format numéro de piste = 01, 02, 03 au lieu de 1, 2, 3 ou 1/3, 2/3, 3/3 ou 01/03, 02/03, 03/03.
21. Année compilation à une seule année : format (1970).

### GROUPE 5 : RENOMMAGE
15. Nom de fichier doit respecter le format : (N° de piste) - Titre.
16. Renommage du nom de dossier d'origine au format : (Année) Album.
17. Dans le cas où plusieurs années sont présentes pour les titres d'un même album, le renommage du nom de dossier de l'album doit être : (année la plus ancienne - 2 derniers nombres de l'année la plus récente) Album (pour normaliser les données).

### GROUPE 6 : FINALISATION
19. Si à la fin de l'import il y a un fichier cover.jpg dans le dossier, la cover doit être automatiquement associée à tous les titres de l'album dans les métadonnées.
20. Mise à jour en temps réel des métadonnées des tags physiques après que les règles d'importation ont été appliquées.

### Ordre d'exécution
Les groupes sont exécutés dans l'ordre séquentiel (1 → 6), et au sein de chaque groupe, les règles sont appliquées dans l'ordre numérique. Les exceptions utilisateur sont vérifiées avant l'application des règles de casse (GROUPE 3).

### Système d'exceptions utilisateur - Préservation de casse
**Objectif** : Permettre aux utilisateurs de définir des mots qui doivent conserver leur casse d'origine au lieu de subir les règles de casse automatiques (règles 9-10).

**Fonctionnement** :
- **Type** : Exceptions positives uniquement (forcer une casse spécifique)
- **Portée** : Globale (s'applique à tous les futurs imports)
- **Granularité** : Par album entier ou par titre individuel
- **Règles concernées** : Uniquement les règles de casse (9-10) du GROUPE 3

**Interface utilisateur** :
- **Liste de mots à préserver** : Interface simple avec liste des mots et leur casse à conserver
- **Champ de saisie** : Zone de texte pour ajouter manuellement des mots (format : "iPhone, AC/DC, iTunes")
- **Gestion** : Possibilité d'ajouter, modifier et supprimer des exceptions via la fenêtre des exceptions

**Exemples d'usage** :
- "iPhone" → conserve "iPhone" au lieu de "Iphone"
- "AC/DC" → conserve "AC/DC" au lieu de "Ac/dc"  
- "iTunes" → conserve "iTunes" au lieu de "Itunes"
- "McDonald's" → conserve "McDonald's" au lieu de "Mcdonald's"

**Stockage** : Base de données SQLite avec table dédiée aux exceptions de casse.

## Technologies

1. Python : Langage de programmation utilisé pour le développement de l'application.
2. mutagen : Bibliothèque utilisée pour la manipulation des métadonnées MP3.
3. PyGObject avec GTK : Bibliothèque utilisée pour l'interface utilisateur de l'application.
4. SQLite : Base de données utilisée pour stocker les exceptions de casse définies par l'utilisateur.

## Structure de la base de données

L'application utilise une base de données SQLite pour stocker les exceptions de casse et la configuration de l'application.

### Table : case_exceptions
```sql
CREATE TABLE case_exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    preserved_case TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table : app_config (nouveau)
```sql
CREATE TABLE app_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    description TEXT,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table : import_history (nouveau)
```sql
CREATE TABLE import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_path TEXT NOT NULL,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL, -- 'success', 'error', 'partial'
    error_message TEXT,
    files_processed INTEGER DEFAULT 0,
    rules_applied TEXT -- JSON des règles appliquées
);
```

**Description des nouvelles tables :**

**app_config** :
- Stockage centralisé de la configuration de l'application
- Paramètres par catégorie (UI, performance, chemins, etc.)
- Facilite l'ajout de nouveaux paramètres configurables

**import_history** :
- Historique des imports pour le débogage
- Traçabilité des erreurs récurrentes
- Statistiques d'utilisation et performance

**Description des colonnes :**
- `id` : Identifiant unique de l'exception
- `word` : Le mot en version normalisée (minuscules) pour la recherche
- `preserved_case` : La casse exacte à préserver
- `created_date` : Date de création de l'exception

**Exemples de données :**
```sql
INSERT INTO case_exceptions (word, preserved_case) VALUES 
('iphone', 'iPhone'),
('ac/dc', 'AC/DC'),
('itunes', 'iTunes'),
('mcdonald''s', 'McDonald''s');
```

**Logique d'utilisation :**
1. Avant l'application des règles de casse (9-10), consultation de cette table
2. Si un mot est trouvé, application de la `preserved_case`
3. Sinon, application des règles de casse standard

### Liste des genres musicaux hardcodés

L'application utilise une liste fixe de genres musicaux disponibles dans le menu déroulant de l'interface d'édition :

**Genres disponibles :**
1. Acid Jazz
2. B.O. de Films
3. Blues
4. Chansons Française
5. Disco
6. Electronique
7. Flamenco
8. Folk
9. Funk
10. Jazz
11. Musique Afriquaine
12. Musique Andine
13. Musique Brésilienne
14. Musique Classique
15. Musique Cubaine
16. Musique Franco-Hispanique
17. New-Wave
18. Pop
19. Rap
20. Reggae
21. Rock
22. Soul
23. Top 50
24. Trip-Hop
25. Zouk

**Stockage :** Liste hardcodée dans le code source (aucun stockage en base de données requis)
**Interface :** Menu déroulant dans la fenêtre d'édition permettant la sélection d'un genre pour l'album entier

## Déploiement

L'application de gestion de métadonnées MP3 sera déployée sur les plates-formes suivantes :

1. Linux Fedora 41.

## Tests et validation

1. Tests unitaires : Les tests unitaires seront effectués pour vérifier que chaque module de l'application fonctionne correctement.
2. Tests d'intégration : Les tests d'intégration seront effectués pour vérifier que les modules de l'application fonctionnent correctement ensemble.
3. Tests de validation : Les tests de validation seront effectués pour vérifier que l'application répond aux exigences fonctionnelles et non fonctionnelles.

## Spécifications techniques supplémentaires

### Gestion des erreurs avec modules de support

Le système de gestion d'erreurs est renforcé par les modules de support :

- **Module de validation (13)** : Prévention des erreurs par validation préalable
- **Module de logging (14)** : Traçabilité complète des erreurs et historique des opérations
- **Module de gestion d'état (16)** : Coordination des statuts d'erreur entre modules

Les statuts des cards doivent s'afficher sous la forme d'icônes modernes et de messages toolkits indiquant :
  - **Problème de pochette** :
    - Absence de pochette dans le dossier album.
    - Absence de pochette dans les métadonnées des titres.
  - **Problème d'import** :
    - Préciser le problème rencontré (ex. : fichier manquant, format incorrect).
  - **Problème de métadonnées** :
    - Métadonnées manquantes.
    - Métadonnées cassées ou corrompues.
  - **Problème de synchronisation** :
    - Échec de mise à jour des métadonnées dans les fichiers physiques après modification.
  - **Problème de validation** :
    - Erreurs détectées par le module de validation (format incorrect, permissions, etc.).
  - **Problème inconnu** :
    - Statut générique pour les erreurs non catégorisées.

### Journalisation et débogage

**Fichiers de log** :
- `nonotags.log` : Log principal avec toutes les opérations
- `import_errors.log` : Log spécialisé pour les erreurs d'import
- `metadata_changes.log` : Historique des modifications de métadonnées
- `performance.log` : Métriques de performance pour optimisation

**Niveaux de logging configurables** :
- **PRODUCTION** : WARNING et ERROR uniquement
- **DEVELOPMENT** : DEBUG, INFO, WARNING, ERROR
- **VERBOSE** : Tous les niveaux avec détails techniques

### Compatibilité des fichiers
- L'application est destinée à traiter uniquement les fichiers MP3.

### Performances
- Pas de taille maximale pour les dossiers d'album à traiter.
- Aucun benchmark de performance n'est nécessaire.

### Optimisations de performance implémentées

#### Cache LRU pour les métadonnées
- **Composant** : `support/cache.py` - Classe `LRUCache` avec TTL (Time To Live)
- **Fonctionnalité** : Cache thread-safe avec expiration automatique des entrées
- **Bénéfices** : Réduction significative des accès disque pour les métadonnées fréquemment consultées
- **Configuration** : TTL configurable, taille maximale ajustable

#### Traitement par lots avec ThreadPoolExecutor
- **Composant** : `services/music_scanner.py` - Méthode `_process_album_batch()`
- **Fonctionnalité** : Analyse parallèle des albums avec pool de threads limité
- **Bénéfices** : Amélioration des performances pour les grandes bibliothèques musicales
- **Configuration** : Nombre de workers configurable pour éviter la surcharge système

#### Lazy loading de l'interface utilisateur
- **Composant** : `ui/views/main_window.py` - Méthodes `_display_next_batch()` et `_on_scroll_value_changed()`
- **Fonctionnalité** : Chargement progressif des albums (20 par lot) déclenché par le scroll
- **Bénéfices** : Réduction de la mémoire utilisée et amélioration de la réactivité pour les grandes collections
- **Configuration** : Taille des lots configurable via `lazy_loading_batch`

#### Profilage de performance intégré
- **Composant** : `profile_performance.py`
- **Fonctionnalité** : Analyse cProfile des goulots d'étranglement avec rapports détaillés
- **Bénéfices** : Identification précise des zones nécessitant des optimisations
- **Utilisation** : `python profile_performance.py` pour analyser les performances

#### Métriques de performance étendues
- **Composant** : `support/logger.py` - Extension avec métriques CPU et mémoire
- **Fonctionnalité** : Suivi en temps réel de l'utilisation des ressources
- **Bénéfices** : Détection précoce des problèmes de performance
- **Logs** : `logs/performance.log` pour analyse historique

**Objectifs de performance atteints** :
- Import de bibliothèques < 5 secondes
- Utilisation mémoire optimisée pour les grandes collections
- Interface réactive même avec des milliers d'albums
- Traitement parallèle sans surcharge système

## Détails sur l'interface utilisateur

### Workflow d'importation
**Processus d'import automatique** :
1. L'utilisateur sélectionne un ou plusieurs dossiers d'albums via le navigateur système
2. Les règles hardcodées s'appliquent **immédiatement** sur chaque album sélectionné
3. Les cards apparaissent directement avec les métadonnées **déjà corrigées**
4. En cas d'erreur (fichier corrompu, permissions, etc.) :
   - L'import continue pour les autres albums
   - L'album problématique est affiché avec un **statut d'erreur** sur sa card
   - L'utilisateur peut consulter le détail de l'erreur via l'icône de statut
   - Aucune interruption du processus global d'import

**Gestion d'erreurs durant l'import** :
- **Continuité** : L'échec d'un album n'affecte pas le traitement des autres
- **Traçabilité** : Chaque erreur est enregistrée et visible via le système de statut des cards
- **Flexibilité** : L'utilisateur peut choisir de réessayer l'import d'un album en erreur plus tard

### Navigation
1. L'application s'ouvre sur une petite fenêtre avec les boutons suivants : "Importer des albums", "Ajouter des exceptions d'importation" et "Ouvrir l'application".
2. "Importer des albums" ouvre le navigateur système pour choisir les dossiers.
3. "Ajouter des exceptions d'importation" ouvre la fenêtre des exceptions.
4. "Ouvrir l'application" ouvre la fenêtre principale.
5. La fenêtre des exceptions se décompose en trois parties :
   - En haut : bloc de test et d'ajout des nouvelles exceptions.
   - À gauche : bloc affichant toutes les règles et exceptions hardcodées dans l'ordre d'exécution.
   - À droite : bloc permettant de supprimer une règle ou une exception.
6. La fenêtre principale affiche en damier les cards des albums importés et comporte un header avec les boutons : "Importer des albums", "Ajouter des exceptions d'importation", "Afficher les albums sélectionnés".
7. Les cards affichent : pochette, titre de l'album, artiste, nombre de morceaux, statut, une case à cocher, un bouton "Créer la playlist de l'album" et un bouton "Retirer de la liste".
8. Un double clic sur une card ouvre la fenêtre d'édition de l'album.
9. "Retirer de la liste" supprime la card de la liste des albums affichés.
10. "Créer la playlist de l'album" génère une playlist au format M3U avec chemins relatifs et l'enregistre dans le dossier de l'album.
11. Si plusieurs albums sont sélectionnés, "Afficher les albums sélectionnés" ouvre la fenêtre d'édition avec tous les albums affichés à la volée.
12. la fenetre d'édition comporte 4 blocs qui affichent les métadonnées ou les moyens de modifier instantanément les métadonnées.
		12.1 - en haut à gauche, le bloc qui affiche la pochette de l'album au format 250 x 250 et le bouton "Chercher une pochette".
			11.1.1 Un clique sur "Chercher une pochette" ouvre une fenetre de recherche de pochettes sur internet avec un bouton "Télécharger" sous chaque pochette trouvée. La pochette doit faire au mois 250x250 pour être sélectionnée (tri de qualité)
			11.1.2 Un clique sur "Télécharger" enregistre la pochette dans le dossier de l'album au format : cover.jpg et applique la pochette automatiquement à toutes les métadonnées des titres de l'album
		12.2 - en haut à droite le bloc qui affiche 4 champs de saisie : Album, Artiste, Année, Genre.
			11.2.1 Si l'utilisateur saisie une correction dans un de ces champs c'est pour corriger en même temps TOUTES les lignes du tableau correspondantes à la colonne concernée.
			11.2.2 le champs "Genre" sera un menu déroulant avec les genres suivants : Acid Jazz, B.O. de Films, Blues, Chansons Française, Disco, Electronique, Flamenco, Folk, Funk, Jazz, Musique Afriquaine, Musique Andine, Musique Brésilienne, Musique Classique, Musique Cubaine, Musique Franco-Hispanique, New-Wave, Pop, Rap, Reggae, Rock, Soul, Top 50, Trip-Hop, Zouk 
		12.3 - En dessous des 2 premiers champs, sur toute la largeur de la fenetre, le bloc du tableau qui affiche les métadonnées.
			11.3.1 Le tableau comporte les colonnes suivantes dans cet ordre : Cover (indique par une coche verte ou une croix rouge si la pochette est associée au titre), nom de fichier, titre, interprète, artiste, album, année, N°de piste et genre
			11.3.2 Les colonne du tableau doivent être ajustables en largeur
			11.3.3 Les colonnes : titre, années et N°de piste doivent proposer un système de tri croissant/décroissant
			11.3.4 Les cellules de la colonne titre doivent être dynamique. Un double clic sur la cellule doit permettre à l'utilisateur de modifier le titre.
			11.3.5 Un double clic sur le nom du fichier déclenche la lecture du titre dans le lecteur audio
			11.3.6 Le titre en lecture dans le lecteur audio doit toujours être surligné en bleu dans le tableau.
		12.4 - En dessous du tableau des métadonnées, sur toute la largeur de la fenetre, le bloc fin qui affiche le lecteur audio
			11.4.1 sur la gauche, le lecteur comprend les boutons : play, précédent, suivant et stop. 
			11.4.2 au centre, le lecteur comprend un curseur de progression de lecture qui affiche le début et la fin (en mn) du morceau
			11.4.3 à droite, le lecteur comprend un bouton sous la forme déroulante pour choisir entre 5 et 10 de pré-réglages d'équalizer.

### Personnalisation
- Pas de personnalisation de l'apparence (thèmes, couleurs).

## Déploiement AppImage

Nonotags peut être déployé sous forme d'AppImage pour une distribution facile sur Linux.

### Construction de l'AppImage

```bash
# Depuis le répertoire racine du projet
./build_appimage.sh
```

Ce script :
- Crée une structure AppDir complète
- Copie tous les fichiers nécessaires
- Télécharge automatiquement appimagetool
- Génère l'AppImage finale

### Utilisation de l'AppImage

```bash
# Rendre exécutable
chmod +x Nonotags-1.0.0-x86_64.AppImage

# Lancer l'application
./Nonotags-1.0.0-x86_64.AppImage
```

### Avantages de l'AppImage

- **Autonome** : Contient toutes les dépendances
- **Portable** : Fonctionne sur toute distribution Linux
- **Sandbox** : N'affecte pas le système hôte
- **Mises à jour** : Remplacement simple du fichier

### Structure de l'AppImage

```
Nonotags.AppDir/
├── AppRun              # Script de lancement
├── nonotags.desktop    # Fichier .desktop
├── nonotags.png        # Icône de l'application
└── usr/
    ├── bin/            # Code Python et ressources
    ├── share/
    │   ├── applications/
    │   ├── icons/
    │   └── metainfo/
    └── lib/            # Dépendances (si nécessaire)
```

### Dépannage AppImage

**Problème** : "Fusermount not found"
```bash
# Installer fuse
sudo apt install fuse  # Ubuntu/Debian
sudo dnf install fuse  # Fedora
```

**Problème** : Interface GTK ne s'affiche pas
```bash
# Variables d'environnement nécessaires
export DISPLAY=:0
export XDG_SESSION_TYPE=x11
```

**Problème** : Permissions refusées
```bash
# Vérifier les permissions
chmod +x Nonotags-*.AppImage
```

### Distribution

L'AppImage peut être distribuée via :
- GitHub Releases
- Site web personnel
- AppImageHub (community)
- Flathub (via Flatpak si souhaité)

### Alternatives de déploiement

- **Flatpak** : Intégration système plus poussée
- **Snap** : Support multi-distributions
- **PyInstaller** : Exécutable Python natif
- **Docker** : Conteneurisation complète

### Accessibilité
- Pas de fonctionnalités spécifiques d'accessibilité.

## Déploiement et distribution

### Installation
- L'application sera distribuée sous forme d'AppImage pour Fedora.

### Mises à jour
- Les albums affichés sous forme de cards restent visibles après l'import de nouveaux albums durant la session en cours.
- **Persistance** : Les cards ne sont pas sauvegardées entre les sessions (disparaissent à la fermeture de l'application).
- **Gestion des cards** : Possibilité de retirer définitivement un album de l'affichage via le bouton "Retirer de la liste" sur chaque card.

### Documentation utilisateur
- Pas de documentation ou guide utilisateur prévu.

## Tests et validation

### Tests automatisés
- Pas de réponse spécifique concernant les outils ou frameworks pour les tests unitaires et d'intégration.

### Scénarios de test
- Un dossier d'album test sera utilisé pour les tests.

### Beta testing
- Pas de phase de beta testing prévue.

## Sécurité

### Protection des données
- Aucun accès non autorisé : l'application sera installée uniquement sur le PC de l'utilisateur.

### Sauvegarde
- Pas de mécanisme de sauvegarde/restauration des données nécessaire.

## Fonctionnalités futures (évolutivité)

### Support multi-plateforme
- L'application est destinée uniquement à Linux.

### Intégration avec des services en ligne
- Récupération des pochettes via MusicBrainz, Discogs et iTunes.

### Support multilingue
- Pas de traduction prévue.

## Organisation du projet

### Planification détaillée
- Pas de calendrier ou estimation du temps nécessaire pour chaque module.

### Collaboration
- Pas de collaboration prévue, ni de conventions de codage ou système de gestion de version.

### Améliorations possibles
- Ajouter des maquettes ou des croquis pour visualiser les interfaces utilisateur.
- Ajouter des tests automatisés pour les règles hardcodées et les exceptions.
