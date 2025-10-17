Guide d'utilisation
===================

Démarrage rapide
-----------------

1. **Lancer l'application** :

   .. code-block:: bash

      ./run_nonotags.sh
      # ou directement
      python main.py

2. **Interface principale** :
   - Bouton "Importer des albums" pour ajouter de la musique
   - Bouton "Ajouter des exceptions" pour gérer les corrections personnalisées
   - Grille d'albums avec aperçu des métadonnées

Import d'albums
---------------

**Via l'explorateur de fichiers** :

1. Cliquer sur "Importer des albums"
2. Sélectionner un ou plusieurs dossiers contenant des MP3
3. L'application analyse automatiquement et applique les corrections

**Traitement automatique** :

- Suppression des fichiers indésirables
- Correction des métadonnées selon les règles hardcodées
- Application des exceptions utilisateur
- Affichage des cards d'album avec statuts

Correction manuelle
-------------------

**Édition des métadonnées** :

1. Cliquer sur une card d'album
2. Fenêtre d'édition avec tableau des pistes
3. Modifier les champs (titre, artiste, album, etc.)
4. Sauvegarder les changements

**Gestion des exceptions** :

1. Bouton "Ajouter des exceptions d'importation"
2. Définir des règles personnalisées de correction
3. Les exceptions sont sauvegardées en base de données

Fonctionnalités avancées
-------------------------

**Lazy loading** :
   - Chargement progressif des albums (20 par lot)
   - Scroll automatique pour charger plus de contenu
   - Optimisé pour les grandes bibliothèques

**Cache de performance** :
   - Cache LRU automatique pour les métadonnées fréquentes
   - Traitement par lots pour les gros volumes
   - Profiling intégré pour l'optimisation

**Synchronisation temps réel** :
   - Modifications du tableau synchronisées avec les fichiers
   - Prévisualisation des changements avant sauvegarde
   - Rollback possible en cas d'erreur

Raccourcis clavier
-------------------

- **Ctrl+O** : Ouvrir l'explorateur d'import
- **Ctrl+E** : Ouvrir la gestion des exceptions
- **Ctrl+Q** : Quitter l'application
- **F5** : Actualiser l'affichage

Dépannage
----------

**Albums non importés** :
   - Vérifier les permissions du dossier
   - Consulter les logs dans ``logs/``
   - Vérifier le format des fichiers MP3

**Corrections non appliquées** :
   - Vérifier les exceptions dans la base de données
   - Consulter les règles hardcodées dans ``core/``

**Interface lente** :
   - Activer le lazy loading (paramètre par défaut)
   - Vérifier l'utilisation mémoire
   - Utiliser le profiling pour identifier les goulots