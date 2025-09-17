#!/bin/bash

# 🧪 SCRIPT DE CRÉATION DES ALBUMS TEST
# Génère 4 albums de test avec fichiers MP3 factices pour validation pipeline

echo "🎵 Création des albums de test NonoTags..."

# Fonction pour créer un fichier MP3 factice avec métadonnées
create_fake_mp3() {
    local file_path="$1"
    local title="$2"
    local artist="$3"
    local album="$4"
    local year="$5"
    local track="$6"
    local comment="$7"
    
    # Créer un fichier MP3 minimal (header MP3 valide mais vide)
    echo -e "\xFF\xFB\x90\x00" > "$file_path"
    # Ajouter du contenu pour faire un fichier de taille réaliste
    dd if=/dev/zero bs=1024 count=100 >> "$file_path" 2>/dev/null
    
    echo "✅ Créé: $file_path"
}

# Fonction pour créer une image de pochette factice
create_fake_cover() {
    local file_path="$1"
    local width="$2"
    local height="$3"
    
    # Créer une image JPG factice (header JPEG valide)
    echo -e "\xFF\xD8\xFF\xE0\x00\x10JFIF" > "$file_path"
    dd if=/dev/zero bs=1024 count=50 >> "$file_path" 2>/dev/null
    echo -e "\xFF\xD9" >> "$file_path"
    
    echo "🖼️ Créé: $file_path"
}

# ALBUM 1 - Standard Simple
echo "📁 Création Album 1 - Standard Simple..."
mkdir -p "01_album_standard"
cd "01_album_standard"

create_fake_mp3 "01 - Come Together.mp3" "Come Together" "The Beatles  " "Abbey Road (Original)" "1969" "1" "Ripped from original CD // Quality: 320kbps"
create_fake_mp3 "02 - Something.mp3" "Something" "The Beatles  " "Abbey Road (Original)" "1969" "2" ""
create_fake_mp3 "3 - Maxwell's Silver Hammer.mp3" "Maxwell's Silver Hammer" "The Beatles  " "Abbey Road (Original)" "1969" "3" ""
create_fake_mp3 "04 - Oh! Darling.mp3" "Oh! Darling" "The Beatles  " "Abbey Road (Original)" "1969" "4" ""
create_fake_mp3 "05 - Octopus's Garden.mp3" "Octopus's Garden" "The Beatles  " "Abbey Road (Original)" "1969" "5" ""

# Fichiers problématiques
touch "Thumbs.db"
touch "desktop.ini"
touch ".DS_Store"
create_fake_cover "folder.jpg" 500 500

cd ..

# ALBUM 2 - Compilation Multi-Années
echo "📁 Création Album 2 - Compilation Complex..."
mkdir -p "02_compilation_complex"
cd "02_compilation_complex"

create_fake_mp3 "01 - Song One (1995).mp3" "Song One" "Various Artists" "Greatest Hits Collection 1995-2005" "1995" "1" ""
create_fake_mp3 "02 - Hit Two (1998).mp3" "Hit Two" "Various Artists" "Greatest Hits Collection 1995-2005" "1998" "2" ""
create_fake_mp3 "03 - Track Three (2001).mp3" "Track Three" "Various Artists" "Greatest Hits Collection 1995-2005" "2001" "3" ""
create_fake_mp3 "04 - Number Four (2003).mp3" "Number Four" "Various Artists" "Greatest Hits Collection 1995-2005" "2003" "4" ""
create_fake_mp3 "05 - Final Five (2005).mp3" "Final Five" "Various Artists" "Greatest Hits Collection 1995-2005" "2005" "5" ""

# Sous-dossiers problématiques
mkdir -p "logs"
touch "logs/temp.log"
mkdir -p "backup"
mkdir -p ".git"
touch "info.txt"
touch "tracklist.doc"
touch "liner_notes.pdf"

# Pochette PNG
create_fake_cover "artwork.png" 600 600

# Dossier avec nom long
mkdir -p "Very_Long_Folder_Name_That_Should_Be_Simplified_According_To_Rules"
create_fake_mp3 "Very_Long_Folder_Name_That_Should_Be_Simplified_According_To_Rules/Extremely_Long_File_Name_With_Many_Underscores_And_Details.mp3" "Long Song" "Test Artist" "Test Album" "2020" "1" ""

cd ..

# ALBUM 3 - Caractères Spéciaux
echo "📁 Création Album 3 - Caractères Spéciaux..."
mkdir -p "03_special_chars_hell"
cd "03_special_chars_hell"

create_fake_mp3 "01 - Café du Matin (Müller Remix).mp3" "Café du Matin" "Café Del Mar & Les Amis" "Été à Saint-Tropez (Édition Spéciale™)" "2020" "1" ""
create_fake_mp3 "02 - Señorita María José.mp3" "Señorita María José" "Café Del Mar & Les Amis" "Été à Saint-Tropez (Édition Spéciale™)" "2020" "2" ""
create_fake_mp3 "03 - Nöël à Prague & Vienne.mp3" "Nöël à Prague & Vienne" "Café Del Mar & Les Amis" "Été à Saint-Tropez (Édition Spéciale™)" "2020" "3" ""
create_fake_mp3 "04 - Øresund Bridge (Göteborg Mix).mp3" "Øresund Bridge" "Café Del Mar & Les Amis" "Été à Saint-Tropez (Édition Spéciale™)" "2020" "4" ""
create_fake_mp3 "05 - Naïve Mélodies d'Été.mp3" "Naïve Mélodies d'Été" "Café Del Mar & Les Amis" "Été à Saint-Tropez (Édition Spéciale™)" "2020" "5" ""

# Fichiers avec caractères spéciaux
create_fake_mp3 "Track with \$pecial Ch@rs!.mp3" "Special Chars" "Test Artist" "Test Album" "2020" "6" ""
create_fake_mp3 "Song #2 w/ Symbols %.mp3" "Song with Symbols" "Test Artist" "Test Album" "2020" "7" ""
create_fake_mp3 "TOUT EN MAJUSCULES.mp3" "Majuscules" "Test Artist" "Test Album" "2020" "8" ""
create_fake_mp3 "tout en minuscules.mp3" "minuscules" "Test Artist" "Test Album" "2020" "9" ""

# Fichiers problématiques
touch "._metadata.xml"
touch "Caché.tmp"
touch "#recycle.bin"

cd ..

# ALBUM 4 - Métadonnées Sales (NIGHTMARE)
echo "📁 Création Album 4 - Nightmare..."
mkdir -p "04_dirty_metadata_nightmare"
cd "04_dirty_metadata_nightmare"

# Structure complexe
mkdir -p "Eminem/THE MARSHALL MATHERS LP/Disc 1"
mkdir -p "Eminem/THE MARSHALL MATHERS LP/Disc 2 - Bonus Tracks"
mkdir -p "Eminem/THE MARSHALL MATHERS LP/Extras"
mkdir -p "Eminem/THE MARSHALL MATHERS LP/Backup"
mkdir -p "Eminem/THE MARSHALL MATHERS LP/temp"

# Fichiers MP3 avec métadonnées très sales
create_fake_mp3 "Eminem/THE MARSHALL MATHERS LP/Disc 1/01 - The Real Slim Shady (Radio Edit) [feat. various].mp3" "The Real Slim Shady" "  EMINEM   (feat. Dr. Dre & 50 Cent) [Explicit Version]  " "THE MARSHALL MATHERS LP [Deluxe Remastered Edition] {2000} (DIRTY VERSION!!!) **EXPLICIT**" "2000, 1999, 2001, 2020" "1" "Ripped from original CD by DJ_PIRATE_2000 // Quality: 320kbps VBR // Source: Official Release + Bonus Tracks + Leaked Demos // Uploaded: 2020-03-15 // Tags fixed by MetadataEditor v2.1 // PLEASE SEED!!! // Contact: pirate@example.com // This is a very long comment that should be removed entirely"

create_fake_mp3 "Eminem/THE MARSHALL MATHERS LP/Disc 1/2 - The Way I Am.MP3" "The Way I Am" "  EMINEM   (feat. Dr. Dre & 50 Cent) [Explicit Version]  " "THE MARSHALL MATHERS LP [Deluxe Remastered Edition] {2000} (DIRTY VERSION!!!) **EXPLICIT**" "2000, 1999, 2001, 2020" "2" ""

create_fake_mp3 "Eminem/THE MARSHALL MATHERS LP/Disc 1/03-Kill_You_(Explicit_Version).mp3" "Kill You" "  EMINEM   (feat. Dr. Dre & 50 Cent) [Explicit Version]  " "THE MARSHALL MATHERS LP [Deluxe Remastered Edition] {2000} (DIRTY VERSION!!!) **EXPLICIT**" "2000, 1999, 2001, 2020" "3" ""

# Fichiers indésirables extrêmes
touch "desktop.ini"
touch "Thumbs.db"
touch ".DS_Store"
touch "._metadata"
touch "folder.jpg"
touch "AlbumArtSmall.jpg"
touch "Folder.jpg"
touch "info.nfo"
touch "readme.txt"
touch "tracklist.doc"
touch ".torrent"

# Sous-dossiers profonds
mkdir -p "deep/nested/folder/structure/another/level"
touch "deep/nested/folder/structure/empty_file.tmp"
touch "deep/nested/folder/structure/another/level/final.log"

# Images variées
create_fake_cover "cover.png" 300 300
create_fake_cover "artwork.gif" 800 800
create_fake_cover "front.jpeg" 1200 1200

cd ..

echo ""
echo "🎉 Création terminée!"
echo ""
echo "📊 Albums créés:"
echo "   📁 01_album_standard/ - Test de base"
echo "   📁 02_compilation_complex/ - Test compilation"
echo "   📁 03_special_chars_hell/ - Test caractères spéciaux"
echo "   📁 04_dirty_metadata_nightmare/ - Test ultime"
echo ""
echo "🚀 Prêt pour les tests du pipeline NonoTags!"
