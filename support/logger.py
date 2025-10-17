"""
Module 14 - Système de journalisation centralisé
Gère tous les logs de l'application avec différents niveaux et rotation automatique.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path

class AppLogger:
    """Gestionnaire centralisé des logs de l'application."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialise le système de logging.
        
        Args:
            log_dir: Répertoire des logs (par défaut: ./logs)
        """
        # Configuration des répertoires
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuration des niveaux de log
        self.levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # Initialisation des loggers
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Configure tous les loggers de l'application."""
        # Logger principal
        self.main_logger = self._create_logger(
            'nonotags',
            self.log_dir / 'nonotags.log',
            level=logging.INFO
        )
        
        # Logger spécialisé pour les erreurs d'import
        self.import_logger = self._create_logger(
            'nonotags.import',
            self.log_dir / 'import_errors.log',
            level=logging.WARNING
        )
        
        # Logger pour les modifications de métadonnées
        self.metadata_logger = self._create_logger(
            'nonotags.metadata',
            self.log_dir / 'metadata_changes.log',
            level=logging.INFO
        )
        
        # Logger pour les performances
        self.performance_logger = self._create_logger(
            'nonotags.performance',
            self.log_dir / 'performance.log',
            level=logging.DEBUG
        )
    
    def _create_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """
        Crée un logger configuré avec rotation.
        
        Args:
            name: Nom du logger
            log_file: Fichier de log
            level: Niveau de log minimum
            
        Returns:
            Logger configuré
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Éviter la duplication des handlers
        if logger.handlers:
            return logger
        
        # Handler avec rotation (10MB max, 5 fichiers de backup)
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Format des messages
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        # Handler console pour les erreurs importantes
        if level >= logging.WARNING:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    # Méthodes du logger principal
    def debug(self, message: str):
        """Log niveau DEBUG."""
        self.main_logger.debug(message)
    
    def info(self, message: str):
        """Log niveau INFO."""
        self.main_logger.info(message)
    
    def warning(self, message: str):
        """Log niveau WARNING."""
        self.main_logger.warning(message)
    
    def error(self, message: str):
        """Log niveau ERROR."""
        self.main_logger.error(message)
    
    def critical(self, message: str):
        """Log niveau CRITICAL."""
        self.main_logger.critical(message)
    
    # Méthodes des loggers spécialisés
    def log_import_error(self, album_path: str, error: str):
        """Log spécifique pour les erreurs d'import."""
        self.import_logger.error(f"Import failed for {album_path}: {error}")
    
    def log_metadata_change(self, file_path: str, field: str, old_value: str, new_value: str):
        """Log spécifique pour les modifications de métadonnées."""
        self.metadata_logger.info(
            f"Metadata changed - File: {file_path}, Field: {field}, "
            f"Old: '{old_value}' -> New: '{new_value}'"
        )
    
    def log_performance(self, operation: str, duration: float, details: str = "",
                       memory_usage: Optional[float] = None, cpu_usage: Optional[float] = None):
        """
        Log spécifique pour les performances avec métriques système.
        
        Args:
            operation: Nom de l'opération
            duration: Durée en secondes
            details: Détails supplémentaires
            memory_usage: Utilisation mémoire en MB (optionnel)
            cpu_usage: Utilisation CPU en % (optionnel)
        """
        perf_message = f"Performance - Operation: {operation}, Duration: {duration:.3f}s"
        
        if memory_usage is not None:
            perf_message += f", Memory: {memory_usage:.1f}MB"
        
        if cpu_usage is not None:
            perf_message += f", CPU: {cpu_usage:.1f}%"
        
        if details:
            perf_message += f", Details: {details}"
        
        self.performance_logger.info(perf_message)
    
    def set_level(self, level: str):
        """
        Change le niveau de logging global.
        
        Args:
            level: Niveau ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        if level.upper() in self.levels:
            new_level = self.levels[level.upper()]
            self.main_logger.setLevel(new_level)
            self.info(f"Log level changed to {level.upper()}")
        else:
            self.warning(f"Invalid log level: {level}")
    
    def get_log_files(self) -> dict:
        """
        Retourne la liste des fichiers de log disponibles.
        
        Returns:
            Dictionnaire des fichiers de log avec leurs tailles
        """
        log_files = {}
        for log_file in self.log_dir.glob("*.log"):
            if log_file.is_file():
                size = log_file.stat().st_size
                log_files[log_file.name] = {
                    'path': str(log_file),
                    'size': size,
                    'size_mb': round(size / (1024*1024), 2)
                }
        return log_files


# Instance globale pour faciliter l'utilisation
_logger_instance = None

def get_logger() -> AppLogger:
    """Retourne l'instance globale du logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger()
    return _logger_instance