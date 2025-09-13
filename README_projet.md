# Nonotags - Gestionnaire de métadonnées MP3

## Vue d'ensemble

Nonotags est une application Linux de gestion et correction automatique des métadonnées MP3, développée avec une architecture modulaire robuste pour une maintenance facile et un débogage efficace.

## 🏗️ Architecture

### Modules de base (12 modules principaux)
- **Module 1** : Nettoyage des fichiers indésirables
- **Module 2-3** : Correction automatique et manuelle des métadonnées  
- **Module 4** : Moteur de règles hardcodées
- **Module 5** : Gestion des exceptions utilisateur
- **Module 6** : Synchronisation temps réel
- **Module 7** : Recherche de pochettes en ligne
- **Module 8** : Création de playlists M3U
- **Module 9** : Interface utilisateur GTK
- **Module 10** : Base de données SQLite
- **Module 11** : Gestion des cards d'albums
- **Module 12** : Lecteur audio intégré

### Modules de support (4 modules pour la maintenabilité)
- **Module 13** : Validation des données et formats
- **Module 14** : Système de logging centralisé
- **Module 15** : Gestionnaire de configuration
- **Module 16** : Gestion d'état global

## 🗂️ Structure du projet

```
nonotags/
├── main.py                    # Point d'entrée principal
├── requirements.txt           # Dépendances Python
├── core/                      # Modules métier
│   ├── file_cleaner.py       # Module 1
│   ├── metadata_processor.py # Modules 2-3
│   ├── rules_engine.py       # Module 4 
│   ├── exceptions_manager.py # Module 5
│   └── sync_manager.py       # Module 6
├── ui/                       # Interface utilisateur
│   ├── main_window.py        # Module 9
│   ├── album_card.py         # Module 11
│   ├── edit_window.py        # Fenêtre d'édition
│   └── exceptions_window.py  # Fenêtre des exceptions
├── database/                 # Base de données
│   ├── db_manager.py         # Module 10
│   └── models.py             # Modèles de données
├── services/                 # Services métier
│   ├── cover_search.py       # Module 7
│   ├── playlist_creator.py   # Module 8
│   └── audio_player.py       # Module 12
├── support/                  # Modules de support
│   ├── validator.py          # Module 13
│   ├── logger.py             # Module 14
│   ├── config_manager.py     # Module 15
│   └── state_manager.py      # Module 16
└── tests/                    # Tests unitaires
```

## ⚡ Installation et lancement

### Prérequis
- Python 3.12+
- Linux (testé sur Fedora 41)
- GTK 3.0
- Dépendances système : `python3-dev`, `libgtk-3-dev`, `libgirepository1.0-dev`

### Installation

```bash
# Cloner le repository
git clone <repository-url>
cd Nonotags

# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Lancement

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer l'application
python main.py
```

## 🧪 Tests

### Tests des modules de support
```bash
python test_phase1.py
```

### Rapport de Phase 1
```bash
python rapport_phase1.py
```

## 📊 État actuel - Phase 1 Complétée ✅

### ✅ Réalisé
- **Architecture modulaire** : 16 modules (12 base + 4 support)
- **Modules de support** : Logging, Configuration, État, Validation
- **Base de données étendue** : 3 tables SQLite (exceptions, config, historique)
- **Environnement de développement** : Configuré et testé
- **Tests automatisés** : 5 tests des modules de support
- **Documentation** : Structure et utilisation

### 📝 Statistiques
- **Fichiers Python** : 18 fichiers
- **Lignes de code** : 2672 lignes
- **Tests** : 5 tests automatisés (100% succès)
- **Couverture** : Modules de support entièrement testés

## 🎯 Prochaines phases

### Phase 2 : Moteur de règles (Semaines 3-5)
- Implémentation des 21 règles hardcodées
- Organisation en 6 groupes logiques
- Intégration avec modules de support

### Phase 3 : Interface utilisateur (Semaines 6-8)
- Fenêtres GTK complètes
- Cards d'albums avec statuts
- Fenêtre d'édition avec tableau

### Phase 4 : Fonctionnalités avancées (Semaines 9-10)
- Recherche de pochettes (APIs externes)
- Lecteur audio intégré
- Création de playlists

## 🔧 Technologies utilisées

- **Python 3.12** : Langage principal
- **GTK 3.0 / PyGObject** : Interface utilisateur
- **SQLite** : Base de données
- **Mutagen** : Manipulation métadonnées MP3
- **Pillow** : Traitement d'images
- **Requests** : Appels d'APIs

## 📋 Fonctionnalités principales

### Traitement automatique
- 21 règles de correction organisées en 6 groupes
- Nettoyage des fichiers indésirables
- Correction des métadonnées (casse, format, caractères)
- Gestion des exceptions utilisateur

### Interface utilisateur
- Cards d'albums avec aperçu et statuts
- Fenêtre d'édition avec tableau interactif
- Gestionnaire d'exceptions intuitif
- Lecteur audio intégré

### Robustesse
- Validation de toutes les données d'entrée
- Logging centralisé pour le débogage
- Configuration flexible et persistante
- Gestion d'état centralisée

## 🛠️ Développement

### Modules de support pour la maintenabilité

Le code est conçu pour être **facilement maintenable** et **débogable** grâce aux modules de support :

1. **Validation (Module 13)** : Prévient les erreurs en amont
2. **Logging (Module 14)** : Traçabilité complète des opérations
3. **Configuration (Module 15)** : Paramètres centralisés et flexibles
4. **État (Module 16)** : Coordination entre modules sans couplage

### Ajout de nouvelles fonctionnalités

1. Créer le module dans le répertoire approprié
2. Intégrer avec les modules de support
3. Ajouter la validation des données d'entrée
4. Implémenter le logging des opérations
5. Créer les tests unitaires
6. Mettre à jour la documentation

## 📄 Licence

[À définir selon vos préférences]

## 👥 Contribution

[Instructions de contribution si open source]

---

**Status actuel** : Phase 1 complétée ✅ | **Prochaine étape** : Phase 2 - Moteur de règles
