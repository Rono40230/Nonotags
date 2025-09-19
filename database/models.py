"""
Modèles de base de données pour Nonotags
"""

import os
import sqlite3
from typing import List, Dict, Optional

class CaseExceptionModel:
    """Modèle pour gérer les exceptions de casse"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'nonotags.db')
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS case_exceptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_text TEXT NOT NULL UNIQUE,
                        corrected_text TEXT NOT NULL,
                        exception_type TEXT NOT NULL DEFAULT 'custom',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"Erreur initialisation base de données: {e}")
    
    def add_exception(self, original: str, corrected: str, exception_type: str = 'custom') -> bool:
        """Ajoute une exception de casse"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO case_exceptions 
                    (original_text, corrected_text, exception_type)
                    VALUES (?, ?, ?)
                ''', (original, corrected, exception_type))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur ajout exception: {e}")
            return False
    
    def get_all_exceptions(self) -> List[Dict]:
        """Récupère toutes les exceptions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, original_text, corrected_text, exception_type, created_at
                    FROM case_exceptions
                    ORDER BY created_at DESC
                ''')
                
                exceptions = []
                for row in cursor.fetchall():
                    exceptions.append({
                        'id': row[0],
                        'original': row[1],
                        'corrected': row[2],
                        'type': row[3],
                        'created_at': row[4]
                    })
                return exceptions
        except Exception as e:
            print(f"Erreur récupération exceptions: {e}")
            return []
    
    def delete_exception(self, exception_id: int) -> bool:
        """Supprime une exception"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM case_exceptions WHERE id = ?', (exception_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Erreur suppression exception: {e}")
            return False
    
    def get_correction(self, text: str) -> Optional[str]:
        """Récupère la correction pour un texte donné"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT corrected_text FROM case_exceptions 
                    WHERE original_text = ? LIMIT 1
                ''', (text,))
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Erreur récupération correction: {e}")
            return None