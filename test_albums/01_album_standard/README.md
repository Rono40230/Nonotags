# ALBUM 1 - Standard Simple
# Problèmes intentionnels légers pour test de base

# Métadonnées originales (sales mais pas extrêmes)
Artiste: "The Beatles  "  # Espaces en fin
Album: "Abbey Road (Original)"  # Parenthèses à nettoyer
Année: "1969"
Genre: "Rock"

# Structure fichiers avec problèmes mineurs
01 - Come Together.mp3        # Pas de zero-padding
02 - Something.mp3
3 - Maxwell's Silver Hammer.mp3  # Numéro sans zero
04 - Oh! Darling.mp3
05 - Octopus's Garden.mp3

# Fichiers problématiques
Thumbs.db                     # Fichier système à supprimer
desktop.ini                   # Fichier système à supprimer
folder.jpg                    # Pochette mal nommée → cover.jpg
.DS_Store                     # Fichier système Mac

# Métadonnées sales dans les tags
- Commentaires: "Ripped from original CD // Quality: 320kbps"
- Espaces multiples dans artiste: "The Beatles  "
- Parenthèses inutiles: "Abbey Road (Original)"
- Zero-padding manquant: pistes "1", "3" au lieu de "01", "03"

# Règles testées principalement:
# GROUPE 1: Suppression fichiers indésirables, renommage pochette
# GROUPE 2: Nettoyage commentaires, parenthèses, espaces
# GROUPE 4: Zero-padding pistes, copie artiste
# GROUPE 6: Association pochette, synchronisation tags
