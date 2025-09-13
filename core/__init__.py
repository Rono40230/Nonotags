"""
Core modules pour le traitement des métadonnées MP3.

Ce package contient les modules principaux de traitement :
- Module 1 : Nettoyage des fichiers (file_cleaner.py)
- Modules 2-3 : Traitement des métadonnées (metadata_processor.py)
- Module 4 : Moteur de règles (rules_engine.py)
- Module 5 : Gestionnaire d'exceptions (exceptions_manager.py)
- Module 6 : Gestionnaire de synchronisation (sync_manager.py)
"""

__version__ = "1.0.0"
__author__ = "Nonotags"

# Import des modules principaux
try:
    from .file_cleaner import FileCleaner
except ImportError:
    FileCleaner = None

try:
    from .metadata_processor import MetadataCleaner, MetadataProcessor
except ImportError:
    MetadataCleaner = None
    MetadataProcessor = None

try:
    from .case_corrector import CaseCorrector, MetadataCaseCorrector
except ImportError:
    CaseCorrector = None
    MetadataCaseCorrector = None

try:
    from .metadata_formatter import MetadataFormatter
except ImportError:
    MetadataFormatter = None

try:
    from .file_renamer import FileRenamer
except ImportError:
    FileRenamer = None

# Exports publics
__all__ = [
    "FileCleaner",
    "MetadataCleaner", 
    "MetadataProcessor",
    "CaseCorrector",
    "MetadataCaseCorrector",
    "MetadataFormatter",
    "FileRenamer",
]
