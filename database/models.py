"""
Module 10 - Modèles de données
Définit les structures de données pour la base de données.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class CaseException:
    """Modèle pour les exceptions de casse."""
    id: Optional[int] = None
    word: str = ""
    preserved_case: str = ""
    created_date: Optional[datetime] = None

@dataclass
class AppConfig:
    """Modèle pour la configuration de l'application."""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    category: str = "general"
    description: str = ""
    updated_date: Optional[datetime] = None

@dataclass
class ImportRecord:
    """Modèle pour l'historique des imports."""
    id: Optional[int] = None
    album_path: str = ""
    import_date: Optional[datetime] = None
    status: str = ""  # 'success', 'error', 'partial'
    error_message: str = ""
    files_processed: int = 0
    rules_applied: Optional[List[str]] = None
