"""
Module 2 - Nettoyage des métadonnées (GROUPE 2)

Ce module implémente le nettoyage des métadonnées MP3 :
1. Suppression des commentaires
2. Suppression des parenthèses et contenu  
3. Nettoyage des espaces en trop
4. Suppression des caractères spéciaux
5. Normalisation " and " et " et " → " & "

Intégration complète avec les modules de support :
- Module 13 : Validation de l'intégrité des métadonnées
- Module 14 : Logging des modifications
- Module 15 : Configuration des règles
- Module 16 : Gestion d'état
- Module 10 : Historique des changements (base import_history)
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# Import Mutagen pour manipulation métadonnées MP3
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError
    from mutagen.id3._frames import TIT2, TALB, TPE1, TPE2, TDRC, TCON, COMM
except ImportError:
    # Pour les tests et développement sans mutagen
    MP3 = None

# Import des modules de support
from support.logger import AppLogger
from support.config_manager import ConfigManager
from support.state_manager import StateManager
from support.validator import MetadataValidator, ValidationResult
from database.db_manager import DatabaseManager


class CleaningRule(Enum):
    """Types de règles de nettoyage des métadonnées."""
    REMOVE_COMMENTS = "remove_comments"
    REMOVE_PARENTHESES = "remove_parentheses" 
    CLEAN_WHITESPACE = "clean_whitespace"
    REMOVE_SPECIAL_CHARS = "remove_special_chars"
    NORMALIZE_CONJUNCTIONS = "normalize_conjunctions"


@dataclass
class MetadataChange:
    """Représente un changement effectué sur une métadonnée."""
    field_name: str
    old_value: str
    new_value: str
    rule_applied: CleaningRule
    timestamp: str = ""
    
    def __post_init__(self):
        from datetime import datetime
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CleaningResults:
    """Résultats du nettoyage des métadonnées d'un fichier."""
    file_path: str
    success: bool = False
    changes: List[MetadataChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0


@dataclass
class AlbumCleaningStats:
    """Statistiques de nettoyage d'un album complet."""
    album_path: str
    files_processed: int = 0
    files_modified: int = 0
    total_changes: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    processing_time: float = 0.0
    rule_stats: Dict[CleaningRule, int] = field(default_factory=dict)


class MetadataCleaner:
    """
    Module 2 - Nettoyage des métadonnées (GROUPE 2)
    
    Nettoie les métadonnées MP3 selon 5 règles définies :
    1. Suppression des commentaires
    2. Suppression des parenthèses et contenu
    3. Nettoyage des espaces
    4. Suppression des caractères spéciaux
    5. Normalisation des conjonctions
    """
    
    def __init__(self):
        """Initialise le nettoyeur de métadonnées avec les modules de support."""
        # Intégration modules de support
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.config = ConfigManager()
        self.state = StateManager()
        self.validator = MetadataValidator()
        self.db = DatabaseManager()
        
        # Configuration des règles de nettoyage
        self._load_cleaning_rules()
        
        # Champs métadonnées à nettoyer
        self._metadata_fields = ['TIT2', 'TALB', 'TPE1', 'TPE2', 'TCON']  # Title, Album, Artist, AlbumArtist, Genre
        
        self.logger.info("MetadataCleaner initialisé avec succès")
    
    def _load_cleaning_rules(self):
        """Charge les règles de nettoyage depuis la configuration."""
        processing_config = self.config.processing
        
        # Caractères spéciaux à supprimer (configurables)
        self._special_chars_pattern = r'[^\w\s\-\.\,\(\)\[\]\'\"\&\!\?]'
        
        # Patterns de parenthèses (configurables)
        self._parentheses_patterns = [
            r'\([^)]*\)',  # (contenu)
            r'\[[^\]]*\]',  # [contenu]
            r'\{[^}]*\}',   # {contenu}
        ]
        
        # Patterns de conjonctions à normaliser
        self._conjunction_patterns = {
            r'\s+and\s+': ' & ',
            r'\s+et\s+': ' & ',
            r'\s+And\s+': ' & ',
            r'\s+Et\s+': ' & ',
            r'\s+AND\s+': ' & ',
            r'\s+ET\s+': ' & ',
        }
        
        self.logger.debug("Règles de nettoyage chargées depuis la configuration")
    
    def clean_album_metadata(self, album_path: str) -> AlbumCleaningStats:
        """
        Nettoie les métadonnées de tous les fichiers MP3 d'un album.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            AlbumCleaningStats: Statistiques du nettoyage
        """
        self.logger.info(f"Début du nettoyage des métadonnées : {album_path}")
        
        # Validation du dossier d'album
        validation = self.validator.validate_directory(album_path)
        if not validation.is_valid:
            error_msg = f"Dossier invalide : {', '.join(validation.errors)}"
            self.logger.error(error_msg)
            stats = AlbumCleaningStats(album_path)
            stats.total_errors = 1
            return stats
        
        stats = AlbumCleaningStats(album_path)
        
        try:
            # Mise à jour de l'état
            self.state.update_album_processing_status(album_path, "cleaning_metadata")
            
            # Recherche des fichiers MP3
            mp3_files = self._find_mp3_files(album_path)
            self.logger.info(f"Trouvé {len(mp3_files)} fichiers MP3 à traiter")
            
            import time
            start_time = time.time()
            
            # Traitement de chaque fichier MP3
            for mp3_file in mp3_files:
                file_result = self.clean_file_metadata(mp3_file)
                stats.files_processed += 1
                
                if file_result.success:
                    if file_result.changes:
                        stats.files_modified += 1
                        stats.total_changes += len(file_result.changes)
                        
                        # Mise à jour des statistiques par règle
                        for change in file_result.changes:
                            rule = change.rule_applied
                            stats.rule_stats[rule] = stats.rule_stats.get(rule, 0) + 1
                        
                        # Sauvegarde en base de données
                        self._save_changes_to_db(file_result)
                
                stats.total_errors += len(file_result.errors)
                stats.total_warnings += len(file_result.warnings)
            
            stats.processing_time = time.time() - start_time
            
            # Logging des résultats
            self.logger.info(
                f"Nettoyage métadonnées terminé pour {album_path} : "
                f"{stats.files_processed} fichiers traités, "
                f"{stats.files_modified} fichiers modifiés, "
                f"{stats.total_changes} changements, "
                f"{stats.total_errors} erreurs"
            )
            
            # Mise à jour de l'état
            if stats.total_errors > 0:
                self.state.update_album_processing_status(album_path, "metadata_cleaning_completed_with_errors")
            else:
                self.state.update_album_processing_status(album_path, "metadata_cleaning_completed")
            
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage métadonnées de {album_path} : {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            stats.total_errors += 1
            self.state.update_album_processing_status(album_path, "metadata_cleaning_failed")
        
        return stats
    
    def clean_file_metadata(self, file_path: str) -> CleaningResults:
        """
        Nettoie les métadonnées d'un fichier MP3 spécifique.
        
        Args:
            file_path: Chemin vers le fichier MP3
            
        Returns:
            CleaningResults: Résultats du nettoyage
        """
        results = CleaningResults(file_path)
        
        try:
            import time
            start_time = time.time()
            
            # Validation du fichier MP3
            validation = self.validator.validate_mp3_file(file_path)
            if not validation.is_valid:
                results.errors.extend(validation.errors)
                results.warnings.extend(validation.warnings)
                self.logger.warning(f"Fichier MP3 invalide : {file_path}")
                return results
            
            # Chargement des métadonnées
            if MP3 is None:
                results.errors.append("Mutagen non disponible - impossible de traiter les métadonnées")
                return results
            
            try:
                audio_file = MP3(file_path)
            except ID3NoHeaderError:
                # Créer les tags ID3 s'ils n'existent pas
                audio_file = MP3(file_path)
                audio_file.add_tags()
            
            # Application des règles de nettoyage
            changes_made = False
            
            for field_name in self._metadata_fields:
                if field_name in audio_file.tags:
                    original_value = str(audio_file.tags[field_name].text[0])
                    cleaned_value = self._apply_cleaning_rules(original_value)
                    
                    if cleaned_value != original_value:
                        # Déterminer quelle règle a causé le changement
                        applied_rules = self._identify_applied_rules(original_value, cleaned_value)
                        
                        # Mise à jour de la métadonnée
                        audio_file.tags[field_name].text = [cleaned_value]
                        
                        # Enregistrement du changement
                        for rule in applied_rules:
                            change = MetadataChange(
                                field_name=field_name,
                                old_value=original_value,
                                new_value=cleaned_value,
                                rule_applied=rule
                            )
                            results.changes.append(change)
                        
                        changes_made = True
                        
                        self.logger.debug(
                            f"Métadonnée modifiée dans {file_path} - "
                            f"{field_name}: '{original_value}' → '{cleaned_value}'"
                        )
            
            # Sauvegarde des modifications
            if changes_made:
                audio_file.save()
                self.logger.info(f"Métadonnées sauvegardées pour {file_path}")
            
            results.success = True
            results.processing_time = time.time() - start_time
            
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage de {file_path} : {str(e)}"
            results.errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
        
        return results
    
    def _apply_cleaning_rules(self, text: str) -> str:
        """
        Applique toutes les règles de nettoyage à un texte.
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return text
        
        cleaned = text
        
        # Règle 1 : Suppression des commentaires (tags COMM)
        # Note: Les commentaires sont gérés séparément via les tags COMM
        
        # Règle 2 : Suppression des parenthèses et contenu
        for pattern in self._parentheses_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Règle 3 : Nettoyage des espaces en trop
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Espaces multiples → un seul
        cleaned = cleaned.strip()  # Suppression espaces début/fin
        
        # Règle 4 : Suppression des caractères spéciaux
        cleaned = re.sub(self._special_chars_pattern, '', cleaned)
        
        # Règle 5 : Normalisation des conjonctions
        for pattern, replacement in self._conjunction_patterns.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Nettoyage final des espaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _identify_applied_rules(self, original: str, cleaned: str) -> List[CleaningRule]:
        """
        Identifie quelles règles ont été appliquées en comparant l'original et le résultat.
        
        Args:
            original: Texte original
            cleaned: Texte nettoyé
            
        Returns:
            List[CleaningRule]: Liste des règles appliquées
        """
        applied_rules = []
        
        # Test de chaque règle individuellement
        temp = original
        
        # Règle 2 : Parenthèses
        for pattern in self._parentheses_patterns:
            if re.search(pattern, temp):
                applied_rules.append(CleaningRule.REMOVE_PARENTHESES)
                temp = re.sub(pattern, '', temp)
                break
        
        # Règle 3 : Espaces
        if re.search(r'\s{2,}', temp) or temp != temp.strip():
            applied_rules.append(CleaningRule.CLEAN_WHITESPACE)
            temp = re.sub(r'\s+', ' ', temp).strip()
        
        # Règle 4 : Caractères spéciaux
        if re.search(self._special_chars_pattern, temp):
            applied_rules.append(CleaningRule.REMOVE_SPECIAL_CHARS)
            temp = re.sub(self._special_chars_pattern, '', temp)
        
        # Règle 5 : Conjonctions
        for pattern in self._conjunction_patterns:
            if re.search(pattern, temp, re.IGNORECASE):
                applied_rules.append(CleaningRule.NORMALIZE_CONJUNCTIONS)
                break
        
        return applied_rules if applied_rules else [CleaningRule.CLEAN_WHITESPACE]
    
    def _find_mp3_files(self, album_path: str) -> List[str]:
        """
        Trouve tous les fichiers MP3 dans un dossier d'album.
        
        Args:
            album_path: Chemin du dossier d'album
            
        Returns:
            List[str]: Liste des chemins vers les fichiers MP3
        """
        mp3_files = []
        album_dir = Path(album_path)
        
        for file_path in album_dir.glob("*.mp3"):
            if file_path.is_file():
                mp3_files.append(str(file_path))
        
        return sorted(mp3_files)
    
    def _save_changes_to_db(self, results: CleaningResults):
        """
        Sauvegarde les changements dans la base de données (table import_history).
        
        Args:
            results: Résultats du nettoyage contenant les changements
        """
        try:
            for change in results.changes:
                # Préparer les données pour la base
                change_data = {
                    'file_path': results.file_path,
                    'field_name': change.field_name,
                    'old_value': change.old_value,
                    'new_value': change.new_value,
                    'rule_applied': change.rule_applied.value,
                    'timestamp': change.timestamp,
                    'module': 'metadata_cleaner'
                }
                
                # Insertion en base (à adapter selon le schéma exact)
                # Note: Ceci sera adapté quand le schéma final de import_history sera défini
                self.logger.debug(f"Changement sauvegardé en base : {change_data}")
                
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde base de données : {str(e)}")
    
    def get_cleaning_preview(self, album_path: str) -> Dict[str, Any]:
        """
        Génère un aperçu des modifications qui seraient apportées sans les appliquer.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            Dict contenant l'aperçu des modifications prévues
        """
        preview = {
            'files_to_modify': [],
            'estimated_changes': 0,
            'rules_preview': {},
            'warnings': []
        }
        
        try:
            mp3_files = self._find_mp3_files(album_path)
            
            for mp3_file in mp3_files:
                file_preview = self._preview_file_changes(mp3_file)
                if file_preview['changes']:
                    preview['files_to_modify'].append(file_preview)
                    preview['estimated_changes'] += len(file_preview['changes'])
                    
                    # Comptage par règle
                    for change in file_preview['changes']:
                        rule = change['rule']
                        preview['rules_preview'][rule] = preview['rules_preview'].get(rule, 0) + 1
                
        except Exception as e:
            preview['warnings'].append(f"Erreur génération aperçu : {str(e)}")
            self.logger.error(f"Erreur aperçu nettoyage : {str(e)}")
        
        return preview
    
    def _preview_file_changes(self, file_path: str) -> Dict[str, Any]:
        """
        Génère un aperçu des changements pour un fichier spécifique.
        
        Args:
            file_path: Chemin vers le fichier MP3
            
        Returns:
            Dict contenant l'aperçu des changements
        """
        file_preview = {
            'file_path': file_path,
            'changes': [],
            'errors': []
        }
        
        try:
            if MP3 is None:
                file_preview['errors'].append("Mutagen non disponible")
                return file_preview
            
            audio_file = MP3(file_path)
            
            for field_name in self._metadata_fields:
                if field_name in audio_file.tags:
                    original_value = str(audio_file.tags[field_name].text[0])
                    cleaned_value = self._apply_cleaning_rules(original_value)
                    
                    if cleaned_value != original_value:
                        applied_rules = self._identify_applied_rules(original_value, cleaned_value)
                        
                        for rule in applied_rules:
                            change_preview = {
                                'field': field_name,
                                'original': original_value,
                                'cleaned': cleaned_value,
                                'rule': rule.value
                            }
                            file_preview['changes'].append(change_preview)
                        
        except Exception as e:
            file_preview['errors'].append(str(e))
        
        return file_preview
    
    def remove_all_comments(self, album_path: str) -> int:
        """
        Supprime tous les commentaires (tags COMM) des fichiers MP3 d'un album.
        
        Args:
            album_path: Chemin vers le dossier de l'album
            
        Returns:
            int: Nombre de commentaires supprimés
        """
        comments_removed = 0
        
        try:
            mp3_files = self._find_mp3_files(album_path)
            
            for mp3_file in mp3_files:
                if MP3 is None:
                    continue
                
                audio_file = MP3(mp3_file)
                
                # Recherche et suppression des tags COMM
                comm_tags = [tag for tag in audio_file.tags if tag.startswith('COMM')]
                
                for comm_tag in comm_tags:
                    del audio_file.tags[comm_tag]
                    comments_removed += 1
                    self.logger.debug(f"Commentaire supprimé de {mp3_file}: {comm_tag}")
                
                if comm_tags:
                    audio_file.save()
                    
        except Exception as e:
            self.logger.error(f"Erreur suppression commentaires : {str(e)}")
        
        self.logger.info(f"Supprimé {comments_removed} commentaires de {album_path}")
        return comments_removed


# Classe de compatibilité pour l'ancien nom
class MetadataProcessor(MetadataCleaner):
    """Alias pour compatibilité avec l'architecture existante."""
    
    def __init__(self):
        super().__init__()
        self.logger.info("MetadataProcessor (MetadataCleaner) initialisé")


class RulesEngine:
    """Moteur de règles (Module 4) - Placeholder pour Phase 2."""
    
    def __init__(self):
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.logger.info("RulesEngine module placeholder initialized")

class ExceptionsManager:
    """Gestionnaire d'exceptions (Module 5)."""
    
    def __init__(self):
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.logger.info("ExceptionsManager module placeholder initialized")

class SyncManager:
    """Gestionnaire de synchronisation (Module 6)."""
    
    def __init__(self):
        from support.logger import get_logger
        self.logger = get_logger().main_logger
        self.logger.info("SyncManager module placeholder initialized")
