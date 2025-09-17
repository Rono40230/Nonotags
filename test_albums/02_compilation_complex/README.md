# ALBUM 2 - Compilation Multi-Années
# Test des règles de compilation et gestion années multiples

# Métadonnées complexes
Artiste: "Various Artists"
Album: "Greatest Hits Collection 1995-2005"
Années: 1995, 1998, 2001, 2003, 2005  # Plage à gérer
Genre: "Pop/Rock"

# Structure avec années multiples dans noms
01 - Song One (1995).mp3
02 - Hit Two (1998).mp3  
03 - Track Three (2001).mp3
04 - Number Four (2003).mp3
05 - Final Five (2005).mp3

# Fichiers indésirables variés
.git/                         # Dossier système
logs/                         # Sous-dossier vide
    temp.log                  # Fichier temporaire
backup/                       # Sous-dossier à nettoyer
info.txt                      # Fichier texte à supprimer
tracklist.doc                 # Document à supprimer
artwork.png                   # Pochette format PNG
liner_notes.pdf               # Document à supprimer

# Noms longs et complexes à tester renommage
Very_Long_Folder_Name_That_Should_Be_Simplified_According_To_Rules/
    Extremely_Long_File_Name_With_Many_Underscores_And_Details.mp3

# Problèmes de métadonnées:
- Années multiples: "1995, 1998, 2001, 2003, 2005"
- Noms fichiers/dossiers trop longs
- Sous-dossiers parasites avec fichiers temporaires
- Format pochette PNG au lieu de JPG

# Règles testées principalement:
# GROUPE 1: Nettoyage sous-dossiers complexes, renommage pochette PNG
# GROUPE 4: Gestion années compilation (1995-2005)
# GROUPE 5: Renommage fichiers/dossiers longs, gestion multi-années
# GROUPE 6: Association pochette PNG
