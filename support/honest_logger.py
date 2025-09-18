"""
SYSTÈME DE LOGS HONNÊTE - Fini les mensonges !
Ce logger dit la vérité sur ce qui se passe vraiment.
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class LogLevel(Enum):
    DEBUG = "🔍 DEBUG"
    INFO = "ℹ️  INFO"
    SUCCESS = "✅ SUCCESS"
    WARNING = "⚠️  WARNING"
    ERROR = "❌ ERROR"
    CRITICAL = "💥 CRITICAL"
    REALITY_CHECK = "🎯 REALITY"

@dataclass
class ProcessingResult:
    """Résultat HONNÊTE d'une opération"""
    operation: str
    success: bool
    files_affected: int = 0
    files_expected: int = 0
    errors: List[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.details is None:
            self.details = {}
    
    @property
    def is_real_success(self) -> bool:
        """Vrai succès = pas d'erreur ET quelque chose de fait"""
        return self.success and len(self.errors) == 0 and self.files_affected > 0
    
    @property
    def success_rate(self) -> float:
        """Taux de réussite réel"""
        if self.files_expected == 0:
            return 0.0
        return self.files_affected / self.files_expected

class HonestLogger:
    """Logger qui dit la VÉRITÉ"""
    
    def __init__(self, component_name: str = "NonoTags"):
        # Si c'est juste un nom de composant, créer le chemin complet
        if "/" not in component_name and "." not in component_name:
            self.log_file = f"logs/honest_{component_name.lower()}.log"
        else:
            self.log_file = component_name
            
        self.ensure_log_dir()
        self.session_start = time.time()
        self.total_lies_detected = 0
        
        # Vider le fichier de log au démarrage
        with open(self.log_file, 'w') as f:
            f.write(f"🎯 SESSION HONNÊTE DÉMARRÉE - {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
    
    def ensure_log_dir(self):
        """Crée le répertoire de logs si nécessaire"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir:  # Seulement si le répertoire n'est pas vide
            os.makedirs(log_dir, exist_ok=True)
    
    def _write_log(self, level: LogLevel, message: str):
        """Écrit dans le fichier de log (silencieux)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level.value} {message}\n"
        
        # Écriture dans le fichier seulement
        with open(self.log_file, 'a') as f:
            f.write(log_line)
        
        # Affichage console SEULEMENT pour les erreurs critiques
        if level in [LogLevel.CRITICAL]:
            print(log_line.strip())
    
    def reality_check(self, operation: str, result: ProcessingResult):
        """CONTRÔLE DE RÉALITÉ - Version silencieuse"""
        
        # Log simple dans le fichier uniquement
        if result.is_real_success:
            self._write_log(LogLevel.INFO, 
                f"{operation} - Réussi: {result.files_affected} fichiers traités")
        
        elif result.success and result.files_affected == 0:
            self.total_lies_detected += 1
            self._write_log(LogLevel.WARNING, 
                f"{operation} - Aucun fichier traité")
        
        elif len(result.errors) > 0:
            self._write_log(LogLevel.ERROR, 
                f"{operation} - Échec: {len(result.errors)} erreurs")
        
        else:
            self._write_log(LogLevel.WARNING, 
                f"{operation} - Résultat douteux")
        
        # Détails supplémentaires
        if result.details:
            for key, value in result.details.items():
                self._write_log(LogLevel.DEBUG, f"   {key}: {value}")
    
    def file_operation(self, operation: str, file_path: str, success: bool, error: str = None):
        """Log d'opération sur fichier (silencieux)"""
        if success:
            self._write_log(LogLevel.DEBUG, f"{operation}: {os.path.basename(file_path)}")
        else:
            self._write_log(LogLevel.ERROR, f"{operation} échec: {os.path.basename(file_path)} - {error}")
    
    def folder_scan(self, folder: str, before_files: List[str], after_files: List[str]):
        """Compare l'état du dossier avant/après (silencieux)"""
        deleted = set(before_files) - set(after_files)
        added = set(after_files) - set(before_files)
        
        if len(deleted) > 0 or len(added) > 0:
            self._write_log(LogLevel.DEBUG, f"Dossier {folder}: {len(deleted)} supprimés, {len(added)} ajoutés")
        else:
            self._write_log(LogLevel.DEBUG, f"Dossier {folder}: aucun changement")
    
    def pipeline_step(self, step_name: str, album_path: str, result: ProcessingResult):
        """Log d'étape du pipeline (silencieux)"""
        self._write_log(LogLevel.DEBUG, f"Étape: {step_name} - {os.path.basename(album_path)}")
        self.reality_check(f"{step_name}", result)
    
    def session_summary(self):
        """Résumé de la session (silencieux)"""
        duration = time.time() - self.session_start
        self._write_log(LogLevel.DEBUG, 
            f"Session terminée: {duration:.1f}s - {self.total_lies_detected} problèmes détectés")
    
    def error(self, message: str):
        """Log d'erreur"""
        self._write_log(LogLevel.ERROR, message)
    
    def success(self, message: str):
        """Log de succès (silencieux)"""
        self._write_log(LogLevel.DEBUG, message)
    
    def warning(self, message: str):
        """Log d'avertissement"""
        self._write_log(LogLevel.WARNING, message)
    
    def info(self, message: str):
        """Log d'information"""
        self._write_log(LogLevel.INFO, message)
    
    def debug(self, message: str):
        """Log de debug"""
        self._write_log(LogLevel.DEBUG, message)

# Instance globale
honest_logger = HonestLogger()
