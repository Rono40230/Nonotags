# 📋 LISTE COMPLÈTE DES RÈGLES AUTOMATIQUES À L'IMPORT

*Date d'analyse : 17 septembre 2025*
*Basé sur l'analyse du code source et du README.md*

## 🔄 **ORDRE D'EXÉCUTION AUTOMATIQUE**

L'application applique automatiquement **6 groupes de règles** dans l'ordre séquentiel suivant :

### **GROUPE 1 → GROUPE 2 → GROUPE 3 → GROUPE 4 → GROUPE 5 → GROUPE 6**

---

## 📁 **GROUPE 1 : NETTOYAGE FICHIERS** (file_cleaner.py)
**Module** : `core/file_cleaner.py` → méthode `clean_album_folder()`
**Étape orchestre** : `ProcessingStep.FILE_CLEANING`

### **Règle 1** : Suppression fichiers indésirables 🗑️
**Types supprimés** : `.DS_Store, Thumbs.db, PNG, NFO, TXT, M3U, bs.db`
**Action** : Suppression automatique de tous ces fichiers du dossier d'album

### **Règle 2** : Suppression sous-dossiers 📂
**Action** : Suppression de tous les sous-dossiers dans le dossier d'album
**Exception** : Seuls les dossiers vides ou sans MP3 sont supprimés

### **Règle 3** : Renommage fichiers pochette 🖼️
**Cibles** : `front.jpg, Front.jpg, Cover.jpg`
**Action** : Renommage automatique vers `cover.jpg`

---

## 🏷️ **GROUPE 2 : NETTOYAGE MÉTADONNÉES** (metadata_processor.py)
**Module** : `core/metadata_processor.py` → méthode `clean_album_metadata()`
**Étape orchestre** : `ProcessingStep.METADATA_CLEANING`

### **Règle 4** : Suppression commentaires 💬
**Champs** : Suppression de tous les commentaires dans les métadonnées
**Implémentation** : `CleaningRule.REMOVE_COMMENTS`

### **Règle 5** : Suppression parenthèses 📝
**Champs** : Titres, Artistes, Albums
**Action** : Suppression des parenthèses et de leur contenu : `(texte)`
**Implémentation** : `CleaningRule.REMOVE_PARENTHESES`

### **Règle 6** : Nettoyage espaces ␣
**Champs** : Titres, Artistes, Albums
**Action** : Suppression des espaces en trop (début, fin, doubles espaces)
**Implémentation** : `CleaningRule.CLEAN_WHITESPACE`

### **Règle 7** : Suppression caractères spéciaux 🚫
**Champs** : Titres, Artistes, Albums
**Caractères supprimés** : `!, ", #, $, %, &', *, +, ,, -, ., :, ;, <, =, >, ?, @, [, \, ], ^, _, {, |, }, ~`
**Implémentation** : `CleaningRule.REMOVE_SPECIAL_CHARS`

### **Règle 8** : Normalisation conjonctions 🔗
**Champs** : Titres, Artistes, Albums
**Action** : `" and "` et `" et "` → `" & "`
**Implémentation** : `CleaningRule.NORMALIZE_CONJUNCTIONS`

---

## 🔤 **GROUPE 3 : CORRECTIONS CASSE** (case_corrector.py)
**Module** : `core/case_corrector.py` → méthode `correct_album_metadata()`
**Étape orchestre** : `ProcessingStep.CASE_CORRECTION`

### **Règle 9** : Casse propre - Titres 📖
**Action** : Première lettre majuscule, reste en minuscule
**Exemple** : `"hello WORLD"` → `"Hello world"`

### **Règle 10** : Casse propre - Albums 💿
**Action** : Première lettre majuscule, reste en minuscule
**Exemple** : `"THE BEST album"` → `"The best album"`

### **Règle 11** : Exception villes et chiffres romains 🏛️
**Action** : Préservation de la casse pour villes et chiffres romains
**Exemples** : `"Paris"`, `"III"`, `"XIV"` → gardent leur casse originale

### **Règle 12** : Exception artiste dans album 👤
**Condition** : Si nom artiste présent dans titre album
**Action** : Le nom artiste ne subit pas la correction de casse
**Exemple** : Album "Best of MADONNA" → "MADONNA" garde sa casse

### **Règle 18** : Préservation " I " 🔺
**Action** : " I " reste " I " (pronom anglais)
**Exemple** : `"i love you"` → `"I love you"`

**🛡️ SYSTÈME D'EXCEPTIONS** : Consultation de la base `case_exceptions` avant application

---

## 📊 **GROUPE 4 : FORMATAGE** (metadata_formatter.py)
**Module** : `core/metadata_formatter.py` → méthode `format_album_metadata()`
**Étape orchestre** : `ProcessingStep.FORMATTING`

### **Règle 13** : Copie artiste vers interprète 👥
**Action** : Champ "Artiste" copié automatiquement vers "Interprète"

### **Règle 14** : Format numéro piste 🔢
**Format cible** : `01, 02, 03` (avec zéro initial)
**Depuis** : `1, 2, 3` ou `1/3, 2/3` ou `01/03, 02/03`
**Vers** : `01, 02, 03`

### **Règle 21** : Format année compilation 📅
**Format cible** : `(1970)` (année unique entre parenthèses)
**Action** : Normalisation des années en format standardisé

---

## 📝 **GROUPE 5 : RENOMMAGE** (file_renamer.py)
**Module** : `core/file_renamer.py` → méthode `rename_album_files()`
**Étape orchestre** : `ProcessingStep.RENAMING`

### **Règle 15** : Format nom fichier 🎵
**Format cible** : `(N° piste) - Titre.mp3`
**Exemple** : `01 - Hello World.mp3`

### **Règle 16** : Renommage dossier album 📁
**Format cible** : `(Année) Album`
**Exemple** : `(1990) Best Hits`

### **Règle 17** : Gestion années multiples 📅
**Condition** : Plusieurs années dans les titres d'un album
**Format** : `(année_ancienne - 2_derniers_chiffres_récente) Album`
**Exemple** : `(1990-95) Greatest Hits`

---

## 🎯 **GROUPE 6 : FINALISATION** (tag_synchronizer.py)
**Module** : `core/tag_synchronizer.py` → méthode `synchronize_album_tags()`
**Étape orchestre** : `ProcessingStep.SYNCHRONIZATION`

### **Règle 19** : Association pochette automatique 🖼️
**Condition** : Présence de `cover.jpg` dans le dossier
**Action** : Association automatique de la pochette à tous les titres dans les métadonnées

### **Règle 20** : Synchronisation tags physiques 💾
**Action** : Mise à jour temps réel des métadonnées dans les fichiers MP3
**Timing** : Après application de toutes les autres règles

---

## ⚙️ **RÉSUMÉ EXÉCUTION AUTOMATIQUE**

### **DÉCLENCHEMENT** : 
- ✅ **Automatique** lors de l'import d'un dossier d'album
- ✅ **Immédiat** après scan et détection des MP3
- ✅ **Sequential** : Chaque groupe attend la fin du précédent

### **ORDRE CHRONOLOGIQUE** :
```
1. SCAN ALBUM 
   ↓
2. GROUPE 1 : Nettoyage fichiers (Règles 1-3)
   ↓ 
3. GROUPE 2 : Nettoyage métadonnées (Règles 4-8)
   ↓
4. GROUPE 3 : Corrections casse (Règles 9-12, 18) + Exceptions
   ↓
5. GROUPE 4 : Formatage (Règles 13-14, 21)
   ↓
6. GROUPE 5 : Renommage (Règles 15-17)
   ↓
7. GROUPE 6 : Finalisation (Règles 19-20)
   ↓
8. ✅ IMPORT TERMINÉ
```

### **CONTRÔLE QUALITÉ** :
- 🔍 **HonestLogger** : Suivi en temps réel de chaque règle appliquée
- 📊 **Statistiques** : Nombre de modifications par groupe
- ⚠️ **Gestion erreurs** : Poursuite même en cas d'échec partiel
- 💾 **Historique** : Sauvegarde des modifications en base

### **EXCEPTIONS UTILISATEUR** :
- 🛡️ **Case exceptions** : Préservation de casse personnalisée (Groupe 3)
- 📋 **Base SQLite** : `case_exceptions` table pour mots à préserver

---

## 📈 **STATUT IMPLÉMENTATION**

```
✅ GROUPE 1 : 100% implémenté (3/3 règles)
✅ GROUPE 2 : 100% implémenté (5/5 règles) 
✅ GROUPE 3 : 100% implémenté (5/5 règles)
✅ GROUPE 4 : 100% implémenté (3/3 règles)
✅ GROUPE 5 : 100% implémenté (3/3 règles)
✅ GROUPE 6 : 100% implémenté (2/2 règles)

🎯 TOTAL : 21/21 règles automatiques opérationnelles
```

**L'application applique automatiquement et de façon séquentielle les 21 règles hardcodées à chaque import d'album !** ✨
