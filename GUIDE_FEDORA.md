# Guide de lancement Nonotags sur Fedora

## 🚀 Lancement rapide

```bash
# 1. Rendre les scripts exécutables
chmod +x *.sh

# 2. Diagnostic du système (optionnel)
./check_system.sh

# 3. Installation des dépendances (si nécessaire)
./install_deps_fedora.sh

# 4. Lancement de l'application
./run_nonotags.sh
```

## 📋 Scripts disponibles

### `run_nonotags.sh` - Script principal de lancement
- ✅ Vérifie automatiquement les dépendances
- ✅ Configure l'environnement optimal
- ✅ Lance l'application avec gestion d'erreurs
- ✅ Génère des logs de diagnostic
- ✅ Interface colorée et informative

### `install_deps_fedora.sh` - Installation des dépendances
- 📦 Installe automatiquement Python3, GTK3, et les outils de développement
- 🐍 Configure pip et les modules Python requis
- 🎨 Vérifie l'accès à GTK3 depuis Python
- ✅ Test de fonctionnement des modules Nonotags

### `check_system.sh` - Diagnostic système
- 🔍 Analyse complète de l'environnement
- 📊 Rapport détaillé des dépendances
- 🛠️ Recommandations de correction
- 📝 Informations système utiles

### `launch_gtk3.py` - Launcher Python compatible
- 🎨 Version GTK3 compatible avec tous les systèmes
- 💫 Style CSS moderne intégré
- 🚀 Point d'entrée optimisé pour Fedora

## 🎯 Fonctionnalités de l'application

### Interface principale
- **📱 Design moderne** : Interface épurée avec GTK3
- **📀 Gestion d'albums** : Cartes visuelles 250×250px
- **📁 Import/Scanner** : Dialogue de sélection de fichiers/dossiers
- **⚙️ Paramètres** : Configuration de l'application

### Fenêtre d'édition (conforme au cahier des charges)
- **🖼️ Bloc 12.1** : Pochette 250×250 + recherche
- **📝 Bloc 12.2** : Champs Album/Artiste/Année/Genre
- **📊 Bloc 12.3** : Tableau 9 colonnes avec tri et édition
- **🎵 Bloc 12.4** : Lecteur audio avec contrôles et égaliseur

## 🔧 Dépannage

### Problèmes courants

**❌ "command not found: sudo"**
```bash
# Solution : utilisez su ou installez sudo
su -c "dnf install sudo"
```

**❌ "GTK3 non accessible"**
```bash
sudo dnf install python3-gobject gtk3-devel cairo-gobject-devel
```

**❌ "Module mutagen manquant"**
```bash
pip3 install --user mutagen PyGObject pycairo
```

**❌ "Problème X11/Display"**
```bash
# Pour SSH avec X11 forwarding
ssh -X utilisateur@serveur

# Ou définir manuellement
export DISPLAY=:0
```

### Variables d'environnement utiles

```bash
# Configuration GTK3 optimale
export GTK_THEME=Adwaita
export GDK_SCALE=1
export NO_AT_BRIDGE=1

# Configuration Python
export PYTHONPATH="/chemin/vers/Nonotags:$PYTHONPATH"
```

### Logs et diagnostic

```bash
# Voir les logs en temps réel
tail -f /tmp/nonotags_*.log

# Diagnostic complet
./check_system.sh

# Test des modules Python
python3 -c "
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
print('GTK3 OK:', Gtk.get_major_version())
"
```

## 📦 Installation manuelle des dépendances

### Fedora/RHEL/CentOS
```bash
# Packages système essentiels
sudo dnf install python3 python3-pip python3-devel gtk3-devel

# Bindings Python pour GTK
sudo dnf install python3-gobject python3-cairo cairo-gobject-devel

# Outils de développement
sudo dnf install gcc redhat-rpm-config pkg-config

# Modules Python spécialisés
pip3 install --user mutagen requests Pillow
```

### Packages optionnels pour multimédia
```bash
sudo dnf install gstreamer1-plugins-base gstreamer1-plugins-good
```

## 🎉 Utilisation

Une fois lancée, l'application présente :

1. **📱 Interface principale** avec albums d'exemple
2. **✏️ Bouton "Éditer"** sur chaque album → ouvre la fenêtre d'édition 4 blocs
3. **📁 Scanner dossiers** → sélection de répertoires musicaux
4. **📂 Importer fichiers** → sélection de fichiers MP3
5. **⚙️ Paramètres** → configuration de l'application

### Navigation dans l'édition
- **Double-clic** sur le nom de fichier → lecture audio
- **Double-clic** sur le titre → édition inline
- **Tri des colonnes** → clic sur les en-têtes avec ⇅
- **Égaliseur** → 10 presets disponibles (Jazz, Rock, Pop, etc.)

## 🆘 Support

En cas de problème :

1. **Diagnostic** : `./check_system.sh`
2. **Logs** : Consultez `/tmp/nonotags_*.log`
3. **Réinstallation** : `./install_deps_fedora.sh`
4. **Test manuel** : `python3 launch_gtk3.py`

L'application est conçue pour être **robuste** et **compatible** avec les systèmes Fedora standard.
