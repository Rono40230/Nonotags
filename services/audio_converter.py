"""
Service de conversion audio
Convertit les fichiers audio entre différents formats
"""

import os
import subprocess
import threading
from enum import Enum
from dataclasses import dataclass
from typing import List, Callable, Optional
import shutil

class ConversionStatus(Enum):
    """États de conversion"""
    PENDING = "En attente"
    CONVERTING = "Conversion..."
    COMPLETED = "Terminé"
    ERROR = "Erreur"
    CANCELLED = "Annulé"

class AudioFormat(Enum):
    """Formats audio supportés"""
    MP3 = "mp3"
    FLAC = "flac"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"

@dataclass
class ConversionJob:
    """Tâche de conversion"""
    source_path: str
    target_path: str
    source_format: str
    target_format: str
    quality: str = "standard"  # Nouveau: qualité de conversion
    delete_source: bool = False  # Nouveau: supprimer le fichier source après conversion
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0
    error_message: str = ""

class AudioConverter:
    """Service de conversion audio utilisant FFmpeg"""
    
    def __init__(self):
        self.conversion_queue: List[ConversionJob] = []
        self.is_converting = False
        self.current_job: Optional[ConversionJob] = None
        self.stop_flag = False
        
        # Callbacks
        self.on_job_started: Optional[Callable[[ConversionJob], None]] = None
        self.on_job_progress: Optional[Callable[[ConversionJob, float], None]] = None
        self.on_job_completed: Optional[Callable[[ConversionJob], None]] = None
        self.on_job_error: Optional[Callable[[ConversionJob, str], None]] = None
        self.on_queue_finished: Optional[Callable[[], None]] = None
        
        # Vérifier la disponibilité de FFmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Vérifie si FFmpeg est disponible"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Retourne la liste des formats supportés"""
        return [fmt.value for fmt in AudioFormat]
    
    def detect_format(self, file_path: str) -> str:
        """Détecte le format d'un fichier audio"""
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.')
    
    def add_conversion_job(self, source_path: str, target_format: str, output_dir: str, quality: str = "standard", delete_source: bool = False) -> ConversionJob:
        """Ajoute une tâche de conversion à la queue"""
        source_format = self.detect_format(source_path)
        filename = os.path.splitext(os.path.basename(source_path))[0]
        target_path = os.path.join(output_dir, f"{filename}.{target_format}")
        
        # Éviter les doublons dans le nom si le fichier existe déjà
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(output_dir, f"{filename}_{counter}.{target_format}")
            counter += 1
        
        job = ConversionJob(
            source_path=source_path,
            target_path=target_path,
            source_format=source_format,
            target_format=target_format,
            quality=quality,
            delete_source=delete_source
        )
        
        self.conversion_queue.append(job)
        return job
    
    def remove_job(self, job: ConversionJob):
        """Supprime une tâche de la queue"""
        if job in self.conversion_queue and job.status == ConversionStatus.PENDING:
            self.conversion_queue.remove(job)
    
    def clear_queue(self):
        """Vide la queue de conversion"""
        if not self.is_converting:
            self.conversion_queue.clear()
    
    def start_conversion(self):
        """Démarre la conversion de la queue"""
        if self.is_converting or not self.conversion_queue:
            return
        
        if not self.ffmpeg_available:
            print("❌ FFmpeg n'est pas disponible. Installation requise.")
            return
        
        self.is_converting = True
        self.stop_flag = False
        
        # Lancer la conversion dans un thread séparé
        thread = threading.Thread(target=self._process_queue, daemon=True)
        thread.start()
    
    def stop_conversion(self):
        """Arrête la conversion en cours"""
        self.stop_flag = True
    
    def _process_queue(self):
        """Traite la queue de conversion"""
        try:
            while self.conversion_queue and not self.stop_flag:
                self.current_job = self.conversion_queue.pop(0)
                self.current_job.status = ConversionStatus.CONVERTING
                
                # Notifier le début de la tâche
                if self.on_job_started:
                    self.on_job_started(self.current_job)
                
                # Effectuer la conversion
                success = self._convert_file(self.current_job)
                
                if success and not self.stop_flag:
                    self.current_job.status = ConversionStatus.COMPLETED
                    self.current_job.progress = 100.0
                    if self.on_job_completed:
                        self.on_job_completed(self.current_job)
                elif self.stop_flag:
                    self.current_job.status = ConversionStatus.CANCELLED
                else:
                    self.current_job.status = ConversionStatus.ERROR
                    if self.on_job_error:
                        self.on_job_error(self.current_job, self.current_job.error_message)
            
        finally:
            self.is_converting = False
            self.current_job = None
            if self.on_queue_finished:
                self.on_queue_finished()
    
    def _convert_file(self, job: ConversionJob) -> bool:
        """Convertit un fichier audio"""
        try:
            # Créer le dossier de destination si nécessaire
            os.makedirs(os.path.dirname(job.target_path), exist_ok=True)
            
            # Construire la commande FFmpeg
            cmd = self._build_ffmpeg_command(job)
            
            print(f"🔄 Conversion: {os.path.basename(job.source_path)} → {job.target_format.upper()}")
            
            # Exécuter FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Surveiller le processus et la progression
            while process.poll() is None:
                if self.stop_flag:
                    process.terminate()
                    return False
                
                # Simulation simple de progression (FFmpeg n'expose pas facilement la progression)
                if job.progress < 90:
                    job.progress += 10
                    if self.on_job_progress:
                        self.on_job_progress(job, job.progress)
                
                # Attendre un peu avant la prochaine vérification
                import time
                time.sleep(0.5)
            
            # Vérifier le résultat
            if process.returncode == 0:
                job.progress = 100.0
                if self.on_job_progress:
                    self.on_job_progress(job, job.progress)
                print(f"✅ Conversion réussie: {job.target_path}")
                
                # Supprimer le fichier source si demandé
                if job.delete_source:
                    try:
                        os.remove(job.source_path)
                        print(f"🗑️ Fichier source supprimé: {job.source_path}")
                    except OSError as e:
                        print(f"⚠️ Impossible de supprimer le fichier source {job.source_path}: {e}")
                        # Note: on ne considère pas cela comme un échec de conversion
                
                return True
            else:
                _, stderr = process.communicate()
                job.error_message = stderr.strip()
                print(f"❌ Erreur conversion: {job.error_message}")
                return False
                
        except Exception as e:
            job.error_message = str(e)
            print(f"❌ Exception durant conversion: {e}")
            return False
    
    def _build_ffmpeg_command(self, job: ConversionJob) -> List[str]:
        """Construit la commande FFmpeg selon le format cible et la qualité"""
        cmd = ['ffmpeg', '-i', job.source_path, '-y']  # -y pour écraser le fichier de sortie
        
        if job.target_format == 'mp3':
            # MP3 avec différentes qualités
            if job.quality == "low":
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '128k'])
            elif job.quality == "standard":
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k'])
            elif job.quality == "high":
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '256k'])
            elif job.quality == "maximum":
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '320k'])
                
        elif job.target_format == 'flac':
            # FLAC sans perte (la qualité n'affecte que la compression)
            if job.quality == "low":
                cmd.extend(['-codec:a', 'flac', '-compression_level', '0'])
            elif job.quality == "standard":
                cmd.extend(['-codec:a', 'flac', '-compression_level', '5'])
            elif job.quality == "high":
                cmd.extend(['-codec:a', 'flac', '-compression_level', '8'])
            elif job.quality == "maximum":
                cmd.extend(['-codec:a', 'flac', '-compression_level', '12'])
                
        elif job.target_format == 'wav':
            # WAV non compressé (la qualité affecte la résolution)
            if job.quality == "low":
                cmd.extend(['-codec:a', 'pcm_s16le', '-ar', '22050'])
            elif job.quality == "standard":
                cmd.extend(['-codec:a', 'pcm_s16le', '-ar', '44100'])
            elif job.quality == "high":
                cmd.extend(['-codec:a', 'pcm_s24le', '-ar', '48000'])
            elif job.quality == "maximum":
                cmd.extend(['-codec:a', 'pcm_s32le', '-ar', '96000'])
                
        elif job.target_format == 'ogg':
            # OGG Vorbis avec différentes qualités
            if job.quality == "low":
                cmd.extend(['-codec:a', 'libvorbis', '-q:a', '2'])
            elif job.quality == "standard":
                cmd.extend(['-codec:a', 'libvorbis', '-q:a', '5'])
            elif job.quality == "high":
                cmd.extend(['-codec:a', 'libvorbis', '-q:a', '7'])
            elif job.quality == "maximum":
                cmd.extend(['-codec:a', 'libvorbis', '-q:a', '10'])
                
        elif job.target_format == 'm4a':
            # AAC dans conteneur M4A
            if job.quality == "low":
                cmd.extend(['-codec:a', 'aac', '-b:a', '128k'])
            elif job.quality == "standard":
                cmd.extend(['-codec:a', 'aac', '-b:a', '192k'])
            elif job.quality == "high":
                cmd.extend(['-codec:a', 'aac', '-b:a', '256k'])
            elif job.quality == "maximum":
                cmd.extend(['-codec:a', 'aac', '-b:a', '320k'])
        
        # Préserver les métadonnées
        cmd.extend(['-map_metadata', '0'])
        
        cmd.append(job.target_path)
        return cmd
    
    def get_queue_status(self) -> dict:
        """Retourne l'état de la queue"""
        pending = len([j for j in self.conversion_queue if j.status == ConversionStatus.PENDING])
        return {
            'total_jobs': len(self.conversion_queue),
            'pending_jobs': pending,
            'is_converting': self.is_converting,
            'current_job': self.current_job.source_path if self.current_job else None
        }
