"""
Module 10 - Gestionnaire de base de données
Gère la base de données SQLite avec les tables étendues.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from support.logger import get_logger
from support.config_manager import ConfigManager

class DatabaseManager:
    """Gestionnaire principal de la base de données SQLite."""
    
    def __init__(self, db_path: Optional[str] = None, config: Optional[ConfigManager] = None):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path: Chemin de la base de données (optionnel)
            config: Gestionnaire de configuration (optionnel)
        """
        self.logger = get_logger()
        self.config = config
        
        # Définition du chemin de la base
        if db_path is None:
            if config:
                db_dir = Path(config.config_dir)
            else:
                db_dir = Path.home() / ".config" / "nonotags"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "nonotags.db"
        
        self.db_path = str(db_path)
        self.connection = None
        
        # Initialisation de la base
        self._initialize_database()
        
        self.logger.info(f"Database initialized: {self.db_path}")
    
    def _initialize_database(self):
        """Initialise la base de données avec toutes les tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table des exceptions de casse
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS case_exceptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL UNIQUE,
                        preserved_case TEXT NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table de configuration
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL UNIQUE,
                        value TEXT NOT NULL,
                        category TEXT NOT NULL DEFAULT 'general',
                        description TEXT,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table d'historique des imports
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS import_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        album_path TEXT NOT NULL,
                        import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        files_processed INTEGER DEFAULT 0,
                        rules_applied TEXT
                    )
                """)
                
                # Index pour optimiser les requêtes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_exceptions_word ON case_exceptions(word)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_config_key ON app_config(key)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_history_date ON import_history(import_date)")
                
                conn.commit()
                self.logger.info("Database tables initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Retourne une connexion à la base de données."""
        return sqlite3.connect(self.db_path)
    
    # === Gestion des exceptions de casse ===
    
    def add_case_exception(self, word: str, preserved_case: str) -> bool:
        """
        Ajoute une exception de casse.
        
        Args:
            word: Mot en version normalisée (minuscules)
            preserved_case: Casse à préserver
            
        Returns:
            True si ajouté avec succès, False sinon
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO case_exceptions (word, preserved_case) VALUES (?, ?)",
                    (word.lower(), preserved_case)
                )
                conn.commit()
                
                self.logger.info(f"Case exception added: {word} -> {preserved_case}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add case exception: {e}")
            return False
    
    def get_case_exception(self, word: str) -> Optional[str]:
        """
        Récupère l'exception de casse pour un mot.
        
        Args:
            word: Mot à rechercher
            
        Returns:
            Casse préservée ou None si non trouvé
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT preserved_case FROM case_exceptions WHERE word = ?",
                    (word.lower(),)
                )
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            self.logger.error(f"Failed to get case exception: {e}")
            return None
    
    def get_all_case_exceptions(self) -> Dict[str, str]:
        """
        Récupère toutes les exceptions de casse.
        
        Returns:
            Dictionnaire {mot_normalisé: casse_préservée}
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT word, preserved_case FROM case_exceptions")
                results = cursor.fetchall()
                return {word: preserved_case for word, preserved_case in results}
                
        except Exception as e:
            self.logger.error(f"Failed to get case exceptions: {e}")
            return {}
    
    def remove_case_exception(self, word: str) -> bool:
        """
        Supprime une exception de casse.
        
        Args:
            word: Mot à supprimer
            
        Returns:
            True si supprimé avec succès, False sinon
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM case_exceptions WHERE word = ?",
                    (word.lower(),)
                )
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    self.logger.info(f"Case exception removed: {word}")
                return deleted
                
        except Exception as e:
            self.logger.error(f"Failed to remove case exception: {e}")
            return False
    
    def get_case_exceptions(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les exceptions de casse dans un format structuré.
        Compatible avec le module CaseCorrector.
        
        Returns:
            Liste de dictionnaires avec les exceptions
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT word, preserved_case FROM case_exceptions")
                results = cursor.fetchall()
                
                exceptions = []
                for word, preserved_case in results:
                    exceptions.append({
                        'original': word,
                        'corrected': preserved_case,
                        'type': 'custom',
                        'case_sensitive': True
                    })
                
                return exceptions
                
        except Exception as e:
            self.logger.error(f"Failed to get case exceptions: {e}")
            return []

    # === Gestion de la configuration ===
    
    def set_config_value(self, key: str, value: Any, category: str = "general", description: str = "") -> bool:
        """
        Définit une valeur de configuration.
        
        Args:
            key: Clé de configuration
            value: Valeur à stocker
            category: Catégorie de la configuration
            description: Description de la configuration
            
        Returns:
            True si défini avec succès, False sinon
        """
        try:
            # Conversion en JSON pour les types complexes
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO app_config (key, value, category, description, updated_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value_str, category, description, datetime.now().isoformat()))
                conn.commit()
                
                self.logger.debug(f"Config value set: {key} = {value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set config value: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration.
        
        Args:
            key: Clé de configuration
            default: Valeur par défaut si non trouvé
            
        Returns:
            Valeur de configuration ou valeur par défaut
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
                result = cursor.fetchone()
                
                if result:
                    value_str = result[0]
                    # Tentative de désérialisation JSON
                    try:
                        return json.loads(value_str)
                    except json.JSONDecodeError:
                        return value_str
                else:
                    return default
                    
        except Exception as e:
            self.logger.error(f"Failed to get config value: {e}")
            return default
    
    def get_config_by_category(self, category: str) -> Dict[str, Any]:
        """
        Récupère toutes les configurations d'une catégorie.
        
        Args:
            category: Catégorie à récupérer
            
        Returns:
            Dictionnaire des configurations
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM app_config WHERE category = ?", (category,))
                results = cursor.fetchall()
                
                config_dict = {}
                for key, value_str in results:
                    try:
                        config_dict[key] = json.loads(value_str)
                    except json.JSONDecodeError:
                        config_dict[key] = value_str
                
                return config_dict
                
        except Exception as e:
            self.logger.error(f"Failed to get config by category: {e}")
            return {}
    
    # === Gestion de l'historique des imports ===
    
    def add_import_record(self, album_path: str, status: str, error_message: str = "", 
                         files_processed: int = 0, rules_applied: List[str] = None) -> bool:
        """
        Ajoute un enregistrement d'import.
        
        Args:
            album_path: Chemin de l'album importé
            status: Statut de l'import ('success', 'error', 'partial')
            error_message: Message d'erreur si applicable
            files_processed: Nombre de fichiers traités
            rules_applied: Liste des règles appliquées
            
        Returns:
            True si ajouté avec succès, False sinon
        """
        try:
            rules_json = json.dumps(rules_applied) if rules_applied else None
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO import_history 
                    (album_path, status, error_message, files_processed, rules_applied)
                    VALUES (?, ?, ?, ?, ?)
                """, (album_path, status, error_message, files_processed, rules_json))
                conn.commit()
                
                self.logger.info(f"Import record added: {album_path} - {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add import record: {e}")
            return False
    
    def get_import_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des imports.
        
        Args:
            limit: Nombre maximum d'enregistrements
            
        Returns:
            Liste des enregistrements d'import
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, album_path, import_date, status, error_message, 
                           files_processed, rules_applied
                    FROM import_history 
                    ORDER BY import_date DESC 
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                history = []
                
                for row in results:
                    record = {
                        'id': row[0],
                        'album_path': row[1],
                        'import_date': row[2],
                        'status': row[3],
                        'error_message': row[4],
                        'files_processed': row[5],
                        'rules_applied': json.loads(row[6]) if row[6] else []
                    }
                    history.append(record)
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get import history: {e}")
            return []
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """
        Récupère des statistiques sur les imports.
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Statistiques générales
                cursor.execute("SELECT COUNT(*) FROM import_history")
                total_imports = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM import_history WHERE status = 'success'")
                successful_imports = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM import_history WHERE status = 'error'")
                failed_imports = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(files_processed) FROM import_history")
                total_files = cursor.fetchone()[0] or 0
                
                # Statistiques par jour (7 derniers jours)
                cursor.execute("""
                    SELECT DATE(import_date) as day, COUNT(*) as count
                    FROM import_history 
                    WHERE import_date >= date('now', '-7 days')
                    GROUP BY DATE(import_date)
                    ORDER BY day
                """)
                daily_stats = {day: count for day, count in cursor.fetchall()}
                
                return {
                    'total_imports': total_imports,
                    'successful_imports': successful_imports,
                    'failed_imports': failed_imports,
                    'total_files_processed': total_files,
                    'success_rate': successful_imports / total_imports if total_imports > 0 else 0,
                    'daily_stats_7days': daily_stats
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get import statistics: {e}")
            return {}
    
    # === Méthodes utilitaires ===
    
    def cleanup_old_records(self, days: int = 30) -> int:
        """
        Nettoie les anciens enregistrements d'import.
        
        Args:
            days: Nombre de jours à conserver
            
        Returns:
            Nombre d'enregistrements supprimés
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM import_history 
                    WHERE import_date < date('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old import records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
            return 0
    
    def vacuum_database(self) -> bool:
        """
        Optimise la base de données.
        
        Returns:
            True si l'optimisation a réussi, False sinon
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                self.logger.info("Database vacuumed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Retourne des informations sur la base de données.
        
        Returns:
            Dictionnaire des informations
        """
        try:
            db_path = Path(self.db_path)
            file_size = db_path.stat().st_size if db_path.exists() else 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Comptage des enregistrements
                cursor.execute("SELECT COUNT(*) FROM case_exceptions")
                case_exceptions_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM app_config")
                config_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM import_history")
                import_history_count = cursor.fetchone()[0]
                
                return {
                    'database_path': self.db_path,
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'tables': {
                        'case_exceptions': case_exceptions_count,
                        'app_config': config_count,
                        'import_history': import_history_count
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {}
