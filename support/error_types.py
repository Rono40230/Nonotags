"""
Types d'erreurs standardisés pour l'application
Centralise tous les types d'erreurs pour uniformiser les messages et statuts
"""

from enum import Enum

class ErrorType(Enum):
    """Types d'erreurs standardisés"""

    # Erreurs de fichiers
    FILE_NOT_FOUND = "Fichier introuvable"
    FILE_PERMISSION_DENIED = "Permission refusée"
    FILE_CORRUPTED = "Fichier corrompu"
    FILE_FORMAT_UNSUPPORTED = "Format de fichier non supporté"

    # Erreurs de métadonnées
    METADATA_MISSING = "Métadonnées manquantes"
    METADATA_CORRUPTED = "Métadonnées corrompues"
    METADATA_WRITE_FAILED = "Échec écriture métadonnées"

    # Erreurs de validation
    VALIDATION_FAILED = "Validation échouée"
    INVALID_PATH = "Chemin invalide"
    INVALID_FORMAT = "Format invalide"

    # Erreurs réseau/API
    NETWORK_ERROR = "Erreur réseau"
    API_ERROR = "Erreur API"
    COVER_DOWNLOAD_FAILED = "Téléchargement pochette échoué"

    # Erreurs de conversion
    CONVERSION_FAILED = "Conversion échouée"
    FFMPEG_NOT_FOUND = "FFmpeg non trouvé"
    AUDIO_FORMAT_UNSUPPORTED = "Format audio non supporté"

    # Erreurs système
    DATABASE_ERROR = "Erreur base de données"
    CONFIG_ERROR = "Erreur configuration"
    MEMORY_ERROR = "Erreur mémoire"

    # Erreurs génériques
    UNKNOWN_ERROR = "Erreur inconnue"
    OPERATION_CANCELLED = "Opération annulée"

    def get_description(self) -> str:
        """Retourne la description de l'erreur"""
        return self.value

    def get_severity(self) -> str:
        """Retourne la sévérité de l'erreur"""
        critical_errors = {
            ErrorType.FILE_CORRUPTED,
            ErrorType.METADATA_CORRUPTED,
            ErrorType.DATABASE_ERROR
        }

        if self in critical_errors:
            return "CRITICAL"
        elif self in {ErrorType.FILE_NOT_FOUND, ErrorType.FILE_PERMISSION_DENIED}:
            return "HIGH"
        else:
            return "MEDIUM"