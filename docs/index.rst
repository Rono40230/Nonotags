.. Nonotags documentation master file, created by
   sphinx-quickstart on Thu Oct 16 15:52:08 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Nonotags - Gestionnaire de métadonnées MP3
===========================================

**Nonotags** est une application GTK3 pour la gestion et correction automatique des métadonnées de fichiers MP3.
Elle offre une interface utilisateur moderne pour importer, corriger et synchroniser les métadonnées musicales.

Fonctionnalités principales
---------------------------

- **Import automatique** : Analyse et correction des métadonnées lors de l'import
- **Correction intelligente** : Règles hardcodées + exceptions utilisateur
- **Interface moderne** : GTK3 avec cards responsives et lazy loading
- **Base de données** : SQLite pour persister les exceptions
- **Performance optimisée** : Cache LRU, traitement par lots, profiling intégré

Guide d'utilisation
-------------------

.. toctree::
   :maxdepth: 2
   :caption: Guide utilisateur:

   installation
   utilisation
   configuration

API Reference
-------------

.. toctree::
   :maxdepth: 3
   :caption: API Reference:

   api_core
   api_services
   api_ui
   api_support
   api_database

Modules
-------

.. toctree::
   :maxdepth: 2
   :caption: Modules détaillés:

   modules

Indices et tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

