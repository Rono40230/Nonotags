"""
Système de cache LRU pour optimiser les accès aux métadonnées fréquentes
"""

import time
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from functools import wraps
import hashlib

class LRUCache:
    """Cache LRU (Least Recently Used) thread-safe pour métadonnées"""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        """
        Args:
            max_size: Taille maximale du cache
            ttl: Time To Live en secondes (0 = pas d'expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}

    def _get_key(self, *args, **kwargs) -> str:
        """Génère une clé unique pour les arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if key not in self.cache:
            return None

        # Vérifier expiration
        if self.ttl > 0:
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None

        # Déplacer en fin (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        """Ajoute une valeur dans le cache"""
        if key in self.cache:
            # Mettre à jour et déplacer en fin
            self.cache[key] = value
            self.cache.move_to_end(key)
        else:
            # Ajouter nouveau
            self.cache[key] = value
            if len(self.cache) > self.max_size:
                # Supprimer le moins récemment utilisé
                oldest_key, _ = self.cache.popitem(last=False)
                if oldest_key in self.timestamps:
                    del self.timestamps[oldest_key]

        self.timestamps[key] = time.time()

    def clear(self) -> None:
        """Vide le cache"""
        self.cache.clear()
        self.timestamps.clear()

    def size(self) -> int:
        """Retourne la taille actuelle du cache"""
        return len(self.cache)

    def stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_ratio": 0,  # À implémenter si nécessaire
            "ttl": self.ttl
        }

# Instance globale pour métadonnées
metadata_cache = LRUCache(max_size=200, ttl=600)  # 200 entrées, 10 minutes TTL

def cached_metadata(func):
    """Décorateur pour cacher les résultats des fonctions de métadonnées"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = metadata_cache._get_key(func.__name__, *args, **kwargs)
        cached_result = metadata_cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        # Calculer et cacher
        result = func(*args, **kwargs)
        metadata_cache.put(cache_key, result)
        return result

    return wrapper