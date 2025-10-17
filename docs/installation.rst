Installation de Nonotags
========================

Prérequis système
------------------

**Système d'exploitation**
   - Linux (testé sur Fedora 41)
   - GTK3 et PyGObject installés

**Python**
   - Version 3.12 ou supérieure
   - pip pour l'installation des dépendances

Installation depuis les sources
--------------------------------

1. **Cloner le dépôt** :

   .. code-block:: bash

      git clone https://github.com/Rono40230/Nonotags.git
      cd Nonotags

2. **Installer les dépendances** :

   .. code-block:: bash

      pip install -r requirements.txt

3. **Vérifier l'installation** :

   .. code-block:: bash

      python main.py --help

Dépendances principales
-----------------------

- **PyGObject** : Interface GTK3
- **Mutagen** : Manipulation des métadonnées MP3
- **SQLite3** : Base de données locale
- **GStreamer** : Lecture audio (optionnel)

Configuration système
---------------------

**Sur Fedora/Ubuntu** :

.. code-block:: bash

   # GTK3 et PyGObject
   sudo dnf install gtk3 python3-gobject  # Fedora
   # ou
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0  # Ubuntu

   # GStreamer pour la lecture audio
   sudo dnf install gstreamer1-plugins-good gstreamer1-plugins-bad-free

Dépannage
----------

**Erreur d'import GTK** :
   Vérifier que ``python3-gobject`` est installé et que la variable d'environnement ``DISPLAY`` est définie.

**Problèmes de permissions** :
   S'assurer que l'utilisateur a les droits de lecture/écriture sur les dossiers musicaux.

**Performance** :
   Pour les grandes bibliothèques, utiliser le lazy loading (activé par défaut) et le cache LRU.