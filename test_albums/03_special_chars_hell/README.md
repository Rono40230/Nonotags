# ALBUM 3 - Caractères Spéciaux Extrêmes
# Test résistance aux caractères Unicode et spéciaux

# Métadonnées avec caractères complexes
Artiste: "Café Del Mar & Les Amis"
Album: "Été à Saint-Tropez (Édition Spéciale™)"
Année: "2020"
Genre: "Chill-Out/Lounge"

# Fichiers avec caractères Unicode
01 - Café du Matin (Müller Remix).mp3
02 - Señorita María José.mp3
03 - Nöël à Prague & Vienne.mp3
04 - Øresund Bridge (Göteborg Mix).mp3
05 - Naïve Mélodies d'Été.mp3
06 - Zürich to São Paulo.mp3

# Caractères spéciaux dans noms
Track with $pecial Ch@rs!.mp3
Song #2 w/ Symbols %.mp3
File [with] {brackets} & (parens).mp3
Music★Song✓Test♪.mp3

# Accents et ligatures
Æon Flux Thème.mp3
Résumé de l'année.mp3
Coeur de Pirate.mp3
Naïve Mélanie.mp3

# Problèmes de casse complexes
TOUT EN MAJUSCULES.mp3
tout en minuscules.mp3
CamelCaseNightmare.mp3
mIxEd_CaSe_HoRrOr.mp3

# Espaces et caractères invisibles
Track   with    multiple     spaces.mp3
	Tab-separated	Title.mp3
No-Break Space Title.mp3    # Espaces insécables

# Fichiers système avec caractères spéciaux
._metadata.xml               # Fichier Mac avec point-underscore
Caché.tmp                   # Fichier temporaire
#recycle.bin                # Corbeille avec #

# Règles testées principalement:
# GROUPE 2: Nettoyage caractères spéciaux extrêmes
# GROUPE 3: Standardisation casse complexe, gestion accents
# GROUPE 5: Renommage avec caractères Unicode
# Tous: Résistance aux caractères non-ASCII
