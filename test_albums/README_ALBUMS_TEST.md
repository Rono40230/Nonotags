# 🧪 ALBUMS DE TEST - VALIDATION COMPLÈTE DU PIPELINE

## 📋 VUE D'ENSEMBLE

4 albums de test créés pour valider toutes les 21 règles automatiques du pipeline NonoTags.

### 🎯 Objectifs de Test
- **Couverture complète** : Chaque règle doit être testée au moins une fois
- **Cas limites** : Situations complexes et edge cases
- **Validation robustesse** : Résistance aux données corrompues
- **Performance** : Mesure des temps de traitement

---

## 📂 STRUCTURE DES ALBUMS TEST

### 🟡 **ALBUM 1 : Standard Simple**
**Dossier :** `01_album_standard/`  
**Objectif :** Test de base, métadonnées légèrement "sales"  
**Règles testées :** 4-8, 13-14, 19-20

### 🟠 **ALBUM 2 : Compilation Multi-Années** 
**Dossier :** `02_compilation_complex/`  
**Objectif :** Test compilation avec plage d'années  
**Règles testées :** 17, 21, 15-16

### 🔴 **ALBUM 3 : Caractères Spéciaux Extrêmes**
**Dossier :** `03_special_chars_hell/`  
**Objectif :** Test résistance caractères spéciaux  
**Règles testées :** 6-7, 9-12, 18

### 🟣 **ALBUM 4 : Métadonnées Très Sales**
**Dossier :** `04_dirty_metadata_nightmare/`  
**Objectif :** Test robustesse avec données corrompues  
**Règles testées :** Toutes les 21 règles

---

## 🎵 DÉTAIL DES ALBUMS

### **ALBUM 1 - Standard Simple**
```
Artiste: "The Beatles"
Album: "Abbey Road"
Année: "1969"
Genre: "Rock"
Problèmes intentionnels:
- Espaces multiples
- Commentaires dans tags
- Numéros piste sans zero-padding
- Pochette mal nommée
```

### **ALBUM 2 - Compilation Multi-Années**
```
Artiste: "Various Artists"
Album: "Greatest Hits 1995-2005"
Années: Multiple (1995, 1998, 2001, 2005)
Problèmes intentionnels:
- Années multiples à gérer
- Noms fichiers/dossiers longs
- Fichiers indésirables
```

### **ALBUM 3 - Caractères Spéciaux**
```
Artiste: "Café Del Mar & Friends"
Album: "Été à Saint-Tropez (Édition Spéciale)"
Problèmes intentionnels:
- Accents et caractères Unicode
- Symboles spéciaux (&, -, (), etc.)
- Cas de casse complexes
```

### **ALBUM 4 - Métadonnées Sales**
```
Artiste: "  EMINEM   (feat. Dr. Dre) "
Album: "THE MARSHALL MATHERS LP [Deluxe Edition] {2000}"
Problèmes intentionnels:
- TOUT EN MAJUSCULES
- Espaces et parenthèses multiples
- Commentaires longs et sales
- Sous-dossiers parasites
- Formats image incorrects
```

---

## ✅ VALIDATION ATTENDUE

### **Après traitement, chaque album devrait avoir :**
- ✅ Fichiers indésirables supprimés
- ✅ Métadonnées nettoyées et formatées
- ✅ Casse standardisée (Title Case)
- ✅ Numéros piste formatés (01, 02, 03...)
- ✅ Noms fichiers/dossiers conformes
- ✅ Pochettes correctement associées
- ✅ Tags ID3 synchronisés

### **Métriques de succès :**
- **21/21 règles appliquées** sans erreur
- **Temps traitement** < 30s par album
- **Logs détaillés** pour chaque transformation
- **Résultat reproductible** à 100%

---

## 🚀 UTILISATION

1. **Copier albums** vers dossier d'import NonoTags
2. **Lancer traitement** via interface ou script
3. **Analyser logs** pour identifier problèmes
4. **Comparer avant/après** pour validation
5. **Mesurer performance** et stabilité

Ces albums test garantissent une validation exhaustive du pipeline NonoTags.
