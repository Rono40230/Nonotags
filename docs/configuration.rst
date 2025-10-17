Configuration
==============

Fichiers de configuration
-------------------------

**ConfigManager** (``support/config_manager.py``)
   Gestion centralisée de tous les paramètres applicatifs.

**Emplacements** :
   - Configuration utilisateur : ``~/.config/nonotags/``
   - Logs : ``logs/`` (dossier local)
   - Base de données : ``nonotags.db`` (SQLite)

Paramètres disponibles
----------------------

**Interface utilisateur** :

- ``ui.theme`` : Thème GTK (clair/sombre)
- ``ui.language`` : Langue de l'interface (fr/en)
- ``ui.lazy_loading_batch`` : Nombre d'albums par lot (défaut: 20)
- ``ui.show_previews`` : Afficher les aperçus d'album

**Performance** :

- ``performance.cache_ttl`` : Durée de vie du cache LRU (secondes)
- ``performance.thread_pool_workers`` : Nombre de workers pour les tâches parallèles
- ``performance.enable_profiling`` : Activer le profiling automatique

**Corrections** :

- ``corrections.auto_apply`` : Appliquer automatiquement les corrections (défaut: oui)
- ``corrections.backup_files`` : Créer des sauvegardes avant modification
- ``corrections.case_rules`` : Règles de correction de casse activées

**Base de données** :

- ``database.path`` : Chemin vers le fichier SQLite
- ``database.backup_interval`` : Intervalle de sauvegarde automatique (jours)

Configuration par défaut
-------------------------

.. code-block:: python

   DEFAULT_CONFIG = {
       'ui': {
           'theme': 'system',
           'language': 'fr',
           'lazy_loading_batch': 20,
           'show_previews': True,
       },
       'performance': {
           'cache_ttl': 3600,  # 1 heure
           'thread_pool_workers': 4,
           'enable_profiling': False,
       },
       'corrections': {
           'auto_apply': True,
           'backup_files': True,
           'case_rules': True,
       },
       'database': {
           'path': 'nonotags.db',
           'backup_interval': 7,
       }
   }

Modification de la configuration
--------------------------------

**Via l'interface** :
   Menu Configuration → Paramètres

**Via fichier** :
   Éditer ``~/.config/nonotags/config.json``

**Programmatiquement** :

.. code-block:: python

   from support.config_manager import ConfigManager

   config = ConfigManager()
   config.set('ui.lazy_loading_batch', 50)
   config.save()

Logs et débogage
-----------------

**Niveaux de log** :
   - ``DEBUG`` : Informations détaillées pour le développement
   - ``INFO`` : Informations générales d'exécution
   - ``WARNING`` : Avertissements non-bloquants
   - ``ERROR`` : Erreurs nécessitant attention
   - ``CRITICAL`` : Erreurs critiques

**Fichiers de log** :
   - ``logs/nonotags.log`` : Log principal
   - ``logs/performance.log`` : Métriques de performance
   - ``logs/metadata_changes.log`` : Changements de métadonnées

**Rotation automatique** :
   Les logs sont automatiquement archivés quand ils dépassent 10MB.