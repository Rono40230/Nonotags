"""
Gestionnaire d'erreurs unifié
Utilise ErrorType pour standardiser les messages d'erreur dans toute l'application
"""

from typing import Optional, Dict, Any
from support.error_types import ErrorType
from support.logger import AppLogger

class ErrorHandler:
    """Gestionnaire centralisé des erreurs"""

    def __init__(self):
        self.logger = AppLogger()
        self._error_history: list[Dict[str, Any]] = []

    def create_error(self, error_type: ErrorType, context: str = "",
                    details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Crée une erreur structurée"""
        error_info = {
            'type': error_type,
            'message': error_type.get_description(),
            'severity': error_type.get_severity(),
            'context': context,
            'details': details or {},
            'timestamp': self._get_timestamp()
        }

        # Log l'erreur selon sa sévérité
        log_message = f"[{error_type.name}] {error_type.value}"
        if context:
            log_message += f" - Contexte: {context}"

        if error_info['severity'] == 'CRITICAL':
            self.logger.error(log_message)
        elif error_info['severity'] == 'HIGH':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Garde l'historique
        self._error_history.append(error_info)

        return error_info

    def get_user_message(self, error_info: Dict[str, Any]) -> str:
        """Retourne un message d'erreur adapté à l'utilisateur"""
        base_message = error_info['message']

        if error_info['context']:
            base_message += f" ({error_info['context']})"

        # Messages plus détaillés pour certains types
        if error_info['type'] == ErrorType.FILE_NOT_FOUND:
            if 'file_path' in error_info['details']:
                base_message += f"\nFichier: {error_info['details']['file_path']}"

        elif error_info['type'] == ErrorType.CONVERSION_FAILED:
            if 'source_format' in error_info['details'] and 'target_format' in error_info['details']:
                base_message += f"\nDe {error_info['details']['source_format']} vers {error_info['details']['target_format']}"

        return base_message

    def get_error_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur les erreurs"""
        stats = {}
        for error in self._error_history:
            error_type = error['type'].name
            stats[error_type] = stats.get(error_type, 0) + 1
        return stats

    def clear_history(self):
        """Efface l'historique des erreurs"""
        self._error_history.clear()

    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté"""
        from datetime import datetime
        return datetime.now().isoformat()

# Instance globale
_error_handler_instance = None

def get_error_handler() -> ErrorHandler:
    """Retourne l'instance globale du gestionnaire d'erreurs"""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler()
    return _error_handler_instance