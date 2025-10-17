# Services modules - Services métier

from typing import Optional
from support.logger import AppLogger

class BaseService:
    """Classe de base pour tous les services métier

    Fournit logging et gestion d'erreurs commune à tous les services.
    """

    def __init__(self):
        self.logger = AppLogger()
        self._errors: list[str] = []

    def log_info(self, message: str) -> None:
        """Log un message d'information"""
        self.logger.info(f"[{self.__class__.__name__}] {message}")

    def log_warning(self, message: str) -> None:
        """Log un avertissement"""
        self.logger.warning(f"[{self.__class__.__name__}] {message}")

    def log_error(self, message: str) -> None:
        """Log une erreur"""
        self.logger.error(f"[{self.__class__.__name__}] {message}")
        self._errors.append(message)

    def get_last_error(self) -> Optional[str]:
        """Retourne la dernière erreur"""
        return self._errors[-1] if self._errors else None

    def clear_errors(self) -> None:
        """Efface l'historique des erreurs"""
        self._errors.clear()

    def has_errors(self) -> bool:
        """Vérifie s'il y a des erreurs"""
        return len(self._errors) > 0
