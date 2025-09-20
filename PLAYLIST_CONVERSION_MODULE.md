# 🎵 Module de Gestion et Conversion de Playlists

## 📋 Description

Le module de gestion de playlists permet de :
- **Scanner** et **analyser** les playlists M3U existantes
- **Créer** de nouvelles playlists depuis des répertoires
- **Convertir** les playlists entre chemins absolus et relatifs
- **Gérer** les métadonnées et la validation des pistes

## 🏗️ Architecture

```
services/
├── playlist_manager.py     # Backend de gestion des playlists
ui/views/
├── playlist_manager_window.py  # Interface GTK+ avec conversion
```

## ⚡ Fonctionnalités principales

### 🔍 **Analyse des playlists**
- Parsing complet des fichiers M3U/M3U8
- Extraction des métadonnées EXTINF
- Détection du type de chemins (Absolu/Relatif/Mixte)
- Validation de l'existence des fichiers

### 🔄 **Conversion de chemins**
- **Absolu → Relatif** : Convertit `/home/music/song.mp3` vers `../music/song.mp3`
- **Relatif → Absolu** : Convertit `./song.mp3` vers `/home/user/playlist/song.mp3`
- **Aperçu avant application** : Visualisation des changements avant sauvegarde
- **Sauvegarde sécurisée** : Préservation des commentaires et métadonnées

### 📊 **Interface utilisateur**
- **4 blocs** conformes au cahier des charges :
  1. **Contrôles** : Ajout répertoires, scan, création
  2. **Statistiques** : Nombre playlists, pistes, durée totale  
  3. **Tableau playlists** : 7 colonnes avec type de chemin
  4. **Détails conversion** : Avant/Après avec boutons

## 🎯 Utilisation

### Interface graphique

```python
from ui.views.playlist_manager_window import PlaylistManagerWindow

# Lancer l'interface complète
window = PlaylistManagerWindow()
window.show_all()
```

### Utilisation programmatique

```python
from services.playlist_manager import PlaylistManager

manager = PlaylistManager()

# Scanner un répertoire
manager.add_scan_directory("/path/to/playlists")
manager.scan_playlists_async()

# Convertir une playlist
playlist = manager.get_all_playlists()[0]
success = manager.convert_playlist_paths(playlist, to_relative=True)
```

## 📝 Formats supportés

- **M3U** : Playlists simples avec chemins
- **M3U8** : Playlists avec métadonnées EXTINF
- **Chemins supportés** :
  - Absolus : `/home/music/song.mp3`
  - Relatifs : `./song.mp3`, `../music/song.mp3`
  - URLs : `http://`, `https://`, `file://`

## 🔧 Configuration

### Types de chemins détectés :
- **"Absolu"** : Tous les chemins sont absolus
- **"Relatif"** : Tous les chemins sont relatifs  
- **"Mixte"** : Mélange de chemins absolus et relatifs
- **"Vide"** : Playlist sans pistes

### Extensions audio supportées :
- MP3, FLAC, M4A, MP4, OGG, WAV

## 🧪 Tests disponibles

```bash
# Test des conversions
python test_conversion.py

# Test interface complète  
python test_conversion_interface.py

# Test conversion complète avec sauvegarde
python test_full_conversion.py
```

## 📊 Exemples de conversion

### Playlist absolue → relative

**Avant :**
```m3u
#EXTM3U
#EXTINF:245,Rock Band - Rock Song 1
/home/music/rock/song1.mp3
#EXTINF:198,Rock Band - Rock Song 2  
/home/music/rock/song2.mp3
```

**Après :**
```m3u
#EXTM3U
#EXTINF:245,Rock Band - Rock Song 1
../../music/rock/song1.mp3
#EXTINF:198,Rock Band - Rock Song 2
../../music/rock/song2.mp3
```

### Playlist relative → absolue

**Avant :**
```m3u
#EXTM3U
#EXTINF:180,Artiste Test - Titre Test 1
./test_audio1.mp3
#EXTINF:187,Artiste Test - Titre Test 2
./test_audio2.mp3
```

**Après :**
```m3u
#EXTM3U
#EXTINF:180,Artiste Test - Titre Test 1
/home/rono/Nonotags/test_audio1.mp3
#EXTINF:187,Artiste Test - Titre Test 2
/home/rono/Nonotags/test_audio2.mp3
```

## ✅ Statut

- ✅ **Parsing M3U complet** : TERMINÉ
- ✅ **Création de playlists** : TERMINÉ  
- ✅ **Interface GTK+** : TERMINÉ
- ✅ **Conversion absolue/relative** : TERMINÉ
- ✅ **Aperçu avant/après** : TERMINÉ
- ✅ **Sauvegarde sécurisée** : TERMINÉ
- ✅ **Tests complets** : TERMINÉ

Le module est **100% fonctionnel** et prêt pour l'intégration dans Nonotags ! 🎉
