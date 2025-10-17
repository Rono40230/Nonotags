#!/bin/bash
# Script de déploiement AppImage pour Nonotags
# Génère une AppImage autonome pour Linux

set -e

echo "🚀 Construction de l'AppImage Nonotags..."

# Variables
APP_NAME="Nonotags"
VERSION="1.0.0"
BUILD_DIR="appimage-build"
APP_DIR="$BUILD_DIR/$APP_NAME.AppDir"
OUTPUT_FILE="$APP_NAME-$VERSION-x86_64.AppImage"

# Nettoyer les builds précédents
rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_FILE"

# Créer la structure AppDir
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/lib"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/share/metainfo"

# Copier l'application
echo "📦 Copie des fichiers de l'application..."
cp -r core/ "$APP_DIR/usr/bin/"
cp -r services/ "$APP_DIR/usr/bin/"
cp -r ui/ "$APP_DIR/usr/bin/"
cp -r support/ "$APP_DIR/usr/bin/"
cp -r database/ "$APP_DIR/usr/bin/"
cp main.py "$APP_DIR/usr/bin/"
cp requirements.txt "$APP_DIR/usr/bin/"
cp -r logs/ "$APP_DIR/usr/bin/" 2>/dev/null || true

# Créer l'exécutable principal
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
# AppRun script for Nonotags

export PYTHONPATH="${APPDIR}/usr/bin:${PYTHONPATH}"
export PATH="${APPDIR}/usr/bin:${PATH}"

# Vérifier si Python est disponible
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Erreur: Python n'est pas installé sur ce système"
    exit 1
fi

# Lancer l'application
cd "${APPDIR}/usr/bin"
exec "$PYTHON_CMD" main.py "$@"
EOF

chmod +x "$APP_DIR/AppRun"

# Créer le fichier .desktop
cat > "$APP_DIR/usr/share/applications/nonotags.desktop" << EOF
[Desktop Entry]
Name=Nonotags
Exec=nonotags
Icon=nonotags
Type=Application
Categories=AudioVideo;Audio;Utility;
Comment=Gestionnaire de métadonnées MP3
Terminal=false
StartupWMClass=Nonotags
EOF

# Copier l'icône (si elle existe)
if [ -f "ui/resources/icon.png" ]; then
    cp "ui/resources/icon.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/nonotags.png"
else
    # Créer une icône par défaut
    echo "⚠️  Aucune icône trouvée, création d'une icône par défaut..."
    # Ici on pourrait générer une icône simple ou utiliser une icône système
fi

# Créer le fichier metainfo
cat > "$APP_DIR/usr/share/metainfo/nonotags.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>io.github.rono40230.nonotags</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0</project_license>
  <name>Nonotags</name>
  <summary>Gestionnaire de métadonnées MP3</summary>
  <description>
    <p>
      Nonotags est une application GTK3 moderne pour la gestion et correction automatique
      des métadonnées de fichiers MP3. Elle offre une interface utilisateur intuitive
      pour importer, corriger et synchroniser les métadonnées musicales.
    </p>
    <p>Fonctionnalités principales :</p>
    <ul>
      <li>Import automatique avec correction intelligente</li>
      <li>Interface utilisateur moderne avec lazy loading</li>
      <li>Gestion des exceptions utilisateur</li>
      <li>Base de données SQLite intégrée</li>
      <li>Optimisations de performance avancées</li>
    </ul>
  </description>
  <launchable type="desktop-id">nonotags.desktop</launchable>
  <screenshots>
    <screenshot type="default">
      <caption>Interface principale avec grille d'albums</caption>
    </screenshot>
  </screenshots>
  <categories>
    <category>AudioVideo</category>
    <category>Audio</category>
  </categories>
  <keywords>
    <keyword>MP3</keyword>
    <keyword>metadata</keyword>
    <keyword>music</keyword>
    <keyword>tags</keyword>
  </keywords>
  <url type="homepage">https://github.com/Rono40230/Nonotags</url>
  <provides>
    <binary>nonotags</binary>
  </provides>
</component>
EOF

# Télécharger et utiliser appimagetool
echo "📥 Téléchargement d'appimagetool..."
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

echo "🔨 Construction de l'AppImage..."
./appimagetool-x86_64.AppImage "$APP_DIR" "$OUTPUT_FILE"

# Nettoyer
rm -rf "$BUILD_DIR"
rm appimagetool-x86_64.AppImage

echo "✅ AppImage créée : $OUTPUT_FILE"
echo "📏 Taille : $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "🚀 Pour tester :"
echo "  chmod +x $OUTPUT_FILE"
echo "  ./$OUTPUT_FILE"