"""
Pool de threads limité pour les opérations I/O
Évite la surcharge système lors des scans et conversions massives
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional
from dataclasses import dataclass
from support.logger import AppLogger

@dataclass
class ThreadPoolConfig:
    """Configuration du pool de threads"""
    max_workers: int = 4  # Nombre max de threads simultanés
    thread_name_prefix: str = "NonotagsWorker"
    timeout: int = 300  # Timeout par défaut en secondes

class LimitedThreadPool:
    """Pool de threads avec limites pour éviter la surcharge"""

    def __init__(self, config: Optional[ThreadPoolConfig] = None):
        self.config = config or ThreadPoolConfig()
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix=self.config.thread_name_prefix
        )
        self.logger = AppLogger()
        self._active_tasks = 0
        self._lock = threading.Lock()

    def submit_task(self, fn: Callable, *args, **kwargs) -> Future:
        """Soumet une tâche au pool de threads"""
        with self._lock:
            if self._active_tasks >= self.config.max_workers:
                self.logger.warning(f"Pool saturé ({self._active_tasks}/{self.config.max_workers} tâches)")
                # Attendre qu'un slot se libère
                time.sleep(0.1)

            self._active_tasks += 1

        def task_wrapper():
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.error(f"Erreur dans tâche threadée: {e}")
                raise
            finally:
                with self._lock:
                    self._active_tasks -= 1

        future = self.executor.submit(task_wrapper)
        return future

    def submit_with_timeout(self, fn: Callable, timeout: Optional[int] = None, *args, **kwargs) -> Any:
        """Soumet une tâche avec timeout"""
        future = self.submit_task(fn, *args, **kwargs)
        timeout = timeout or self.config.timeout

        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            self.logger.error(f"Tâche timeout après {timeout}s")
            future.cancel()
            raise

    def shutdown(self, wait: bool = True):
        """Arrête le pool de threads"""
        self.executor.shutdown(wait=wait)
        self.logger.info("Pool de threads arrêté")

    def get_active_count(self) -> int:
        """Retourne le nombre de tâches actives"""
        with self._lock:
            return self._active_tasks

    def get_pool_status(self) -> dict:
        """Retourne le statut du pool"""
        with self._lock:
            return {
                "active_tasks": self._active_tasks,
                "max_workers": self.config.max_workers,
                "utilization_percent": (self._active_tasks / self.config.max_workers) * 100
            }

# Instance globale du pool (singleton)
_thread_pool_instance = None
_thread_pool_lock = threading.Lock()

def get_thread_pool() -> LimitedThreadPool:
    """Retourne l'instance globale du pool de threads"""
    global _thread_pool_instance

    if _thread_pool_instance is None:
        with _thread_pool_lock:
            if _thread_pool_instance is None:
                _thread_pool_instance = LimitedThreadPool()

    return _thread_pool_instance