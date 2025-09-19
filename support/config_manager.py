"""
Module 15 - Gestionnaire de configuration centralisé
Gère tous les paramètres de l'application avec sauvegarde/restauration automatique.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from support.logger import get_logger

@dataclass
class UIConfig:
    """Configuration de l'interface utilisateur."""
    window_width: int = 1200
    window_height: int = 800
    card_size: int = 200
    show_tooltips: bool = True
    theme: str = "default"
    language: str = "fr"

@dataclass
class ProcessingConfig:
    """Configuration du traitement des métadonnées."""
    auto_apply_rules: bool = True
    backup_original_files: bool = True
    max_parallel_imports: int = 4
    timeout_per_file: int = 30  # secondes
    
    # Configuration FileRenamer (Module 5)
    rename_folders: bool = True  # Activer le renommage des dossiers d'albums
    
    # Configuration FileCleaner (Module 1)
    unwanted_files: List[str] = None
    cover_rename_patterns: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialise les valeurs par défaut des listes et dictionnaires."""
        if self.unwanted_files is None:
            self.unwanted_files = [
                '.ds_store', 'thumbs.db', 'desktop.ini', '.fuse_hidden',
                'folder.jpg', 'albumartsmall.jpg', 'albumart_{*}_large.jpg',
                'albumart_{*}_small.jpg', '.nomedia', '._*', '.sync',
                'ehthumbs.db', 'ehthumbs_vista.db', 'image.db'
            ]
        
        if self.cover_rename_patterns is None:
            self.cover_rename_patterns = {
                'front': 'cover',
                'folder': 'cover',
                'album': 'cover',
                'albumart': 'cover',
                'artwork': 'cover'
            }
    
@dataclass
class LoggingConfig:
    """Configuration du logging."""
    level: str = "INFO"
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_performance_logging: bool = False

@dataclass
class PathsConfig:
    """Configuration des chemins."""
    default_import_dir: str = ""
    default_export_dir: str = ""
    temp_dir: str = ""
    cache_dir: str = ""

@dataclass
class APIConfig:
    """Configuration des APIs externes."""
    musicbrainz_enabled: bool = True
    discogs_enabled: bool = True
    itunes_enabled: bool = True
    search_timeout: int = 10  # secondes
    max_cover_size_mb: int = 5

class ConfigManager:
    """Gestionnaire centralisé de la configuration de l'application."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_dir: Répertoire de configuration (par défaut: ~/.config/nonotags)
        """
        self.logger = get_logger()
        
        # Configuration des répertoires
        if config_dir is None:
            home = Path.home()
            config_dir = home / ".config" / "nonotags"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        
        # Configuration par défaut
        self.ui = UIConfig()
        self.processing = ProcessingConfig()
        self.logging = LoggingConfig()
        self.paths = PathsConfig()
        self.api = APIConfig()
        
        # Chargement de la configuration existante
        self.load()
        
        self.logger.info("Configuration manager initialized")
    
    def load(self) -> bool:
        """
        Charge la configuration depuis le fichier.
        
        Returns:
            True si la configuration a été chargée, False sinon
        """
        try:
            if not self.config_file.exists():
                self.logger.info("No configuration file found, using defaults")
                self._create_default_paths()
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Chargement des sections de configuration
            if 'ui' in data:
                self.ui = UIConfig(**data['ui'])
            if 'processing' in data:
                self.processing = ProcessingConfig(**data['processing'])
            if 'logging' in data:
                self.logging = LoggingConfig(**data['logging'])
            if 'paths' in data:
                self.paths = PathsConfig(**data['paths'])
            if 'api' in data:
                self.api = APIConfig(**data['api'])
            
            self.logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._create_default_paths()
            return False
    
    def save(self) -> bool:
        """
        Sauvegarde la configuration dans le fichier.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            config_data = {
                'ui': asdict(self.ui),
                'processing': asdict(self.processing),
                'logging': asdict(self.logging),
                'paths': asdict(self.paths),
                'api': asdict(self.api)
            }
            
            # Sauvegarde avec indentation pour lisibilité
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _create_default_paths(self):
        """Crée les chemins par défaut."""
        home = Path.home()
        
        # Répertoires par défaut
        self.paths.default_import_dir = str(home / "Music")
        self.paths.default_export_dir = str(home / "Music" / "Nonotags_Export")
        self.paths.temp_dir = str(self.config_dir / "temp")
        self.paths.cache_dir = str(self.config_dir / "cache")
        
        # Création des répertoires
        for path in [self.paths.temp_dir, self.paths.cache_dir]:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration.
        
        Args:
            section: Section de configuration ('ui', 'processing', etc.)
            key: Clé de configuration
            default: Valeur par défaut si non trouvée
            
        Returns:
            Valeur de configuration ou valeur par défaut
        """
        try:
            section_obj = getattr(self, section)
            return getattr(section_obj, key, default)
        except AttributeError:
            self.logger.warning(f"Configuration key not found: {section}.{key}")
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Définit une valeur de configuration.
        
        Args:
            section: Section de configuration
            key: Clé de configuration
            value: Nouvelle valeur
            
        Returns:
            True si la valeur a été définie, False sinon
        """
        try:
            section_obj = getattr(self, section)
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
                self.logger.debug(f"Configuration updated: {section}.{key} = {value}")
                return True
            else:
                self.logger.warning(f"Configuration key not found: {section}.{key}")
                return False
        except AttributeError:
            self.logger.warning(f"Configuration section not found: {section}")
            return False
    
    def reset_section(self, section: str) -> bool:
        """
        Remet une section à ses valeurs par défaut.
        
        Args:
            section: Section à remettre à zéro
            
        Returns:
            True si la remise à zéro a réussi, False sinon
        """
        try:
            if section == 'ui':
                self.ui = UIConfig()
            elif section == 'processing':
                self.processing = ProcessingConfig()
            elif section == 'logging':
                self.logging = LoggingConfig()
            elif section == 'paths':
                self.paths = PathsConfig()
                self._create_default_paths()
            elif section == 'api':
                self.api = APIConfig()
            else:
                self.logger.warning(f"Unknown configuration section: {section}")
                return False
            
            self.logger.info(f"Configuration section reset: {section}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration section {section}: {e}")
            return False
    
    def reset_all(self) -> bool:
        """
        Remet toute la configuration aux valeurs par défaut.
        
        Returns:
            True si la remise à zéro a réussi, False sinon
        """
        try:
            self.ui = UIConfig()
            self.processing = ProcessingConfig()
            self.logging = LoggingConfig()
            self.paths = PathsConfig()
            self.api = APIConfig()
            self._create_default_paths()
            
            self.logger.info("All configuration reset to defaults")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset all configuration: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """
        Exporte la configuration vers un fichier.
        
        Args:
            export_path: Chemin du fichier d'export
            
        Returns:
            True si l'export a réussi, False sinon
        """
        try:
            from datetime import datetime
            
            config_data = {
                'ui': asdict(self.ui),
                'processing': asdict(self.processing),
                'logging': asdict(self.logging),
                'paths': asdict(self.paths),
                'api': asdict(self.api),
                'export_info': {
                    'version': "1.0.0",
                    'export_date': datetime.now().isoformat()
                }
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        Importe la configuration depuis un fichier.
        
        Args:
            import_path: Chemin du fichier d'import
            
        Returns:
            True si l'import a réussi, False sinon
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validation et import des sections
            if 'ui' in data:
                self.ui = UIConfig(**data['ui'])
            if 'processing' in data:
                self.processing = ProcessingConfig(**data['processing'])
            if 'logging' in data:
                self.logging = LoggingConfig(**data['logging'])
            if 'paths' in data:
                self.paths = PathsConfig(**data['paths'])
            if 'api' in data:
                self.api = APIConfig(**data['api'])
            
            self.logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne un résumé de la configuration actuelle.
        
        Returns:
            Dictionnaire avec toutes les sections de configuration
        """
        return {
            'ui': asdict(self.ui),
            'processing': asdict(self.processing),
            'logging': asdict(self.logging),
            'paths': asdict(self.paths),
            'api': asdict(self.api)
        }