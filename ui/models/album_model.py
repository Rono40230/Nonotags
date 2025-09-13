"""
Modèle de données pour les albums
Représentation moderne des métadonnées d'albums
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import os
from pathlib import Path

class AlbumStatus(Enum):
    """États possibles d'un album"""
    PENDING = "pending"      # En attente de traitement
    PROCESSING = "processing" # En cours de traitement
    SUCCESS = "success"      # Traitement réussi
    ERROR = "error"          # Erreur de traitement
    WARNING = "warning"      # Traitement avec avertissements

@dataclass
class TrackModel:
    """Modèle pour une piste audio"""
    number: int
    title: str
    artist: str = ""
    duration: Optional[int] = None  # en secondes
    file_path: str = ""
    has_issues: bool = False
    issues: List[str] = field(default_factory=list)

@dataclass
class AlbumModel:
    """
    Modèle moderne pour un album avec toutes ses métadonnées
    """
    title: str
    artist: str
    year: str = ""
    genre: str = ""
    track_count: int = 0
    folder_path: str = ""
    cover_path: Optional[str] = None
    
    # Métadonnées étendues
    album_artist: str = ""
    compilation: bool = False
    disc_number: int = 1
    total_discs: int = 1
    
    # État et traitement
    status: AlbumStatus = AlbumStatus.PENDING
    is_selected: bool = False
    processing_progress: float = 0.0
    
    # Pistes
    tracks: List[TrackModel] = field(default_factory=list)
    
    # Historique et métadonnées techniques
    last_modified: Optional[str] = None
    import_date: Optional[str] = None
    issues: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialisation après création"""
        if not self.album_artist:
            self.album_artist = self.artist
        
        # Trouve automatiquement la pochette si pas spécifiée
        if not self.cover_path and self.folder_path:
            self._find_cover_image()
        
        # Charge les pistes si le dossier existe
        if self.folder_path and os.path.exists(self.folder_path):
            self._load_tracks()
    
    @property
    def display_title(self) -> str:
        """Titre d'affichage formaté"""
        if self.year:
            return f"({self.year}) {self.title}"
        return self.title
    
    @property
    def display_artist(self) -> str:
        """Artiste d'affichage formaté"""
        if self.compilation:
            return "Various Artists"
        return self.artist
    
    @property
    def has_cover(self) -> bool:
        """Vérifie si l'album a une pochette"""
        return self.cover_path is not None and os.path.exists(self.cover_path)
    
    @property
    def has_issues(self) -> bool:
        """Vérifie si l'album a des problèmes"""
        return len(self.issues) > 0 or any(track.has_issues for track in self.tracks)
    
    @property
    def total_duration(self) -> int:
        """Durée totale en secondes"""
        return sum(track.duration or 0 for track in self.tracks)
    
    @property
    def status_emoji(self) -> str:
        """Emoji correspondant au statut"""
        emoji_map = {
            AlbumStatus.PENDING: "⏳",
            AlbumStatus.PROCESSING: "🔄",
            AlbumStatus.SUCCESS: "✅",
            AlbumStatus.ERROR: "❌",
            AlbumStatus.WARNING: "⚠️"
        }
        return emoji_map.get(self.status, "❓")
    
    @property
    def status_text(self) -> str:
        """Texte du statut"""
        text_map = {
            AlbumStatus.PENDING: "En attente",
            AlbumStatus.PROCESSING: "Traitement",
            AlbumStatus.SUCCESS: "Traité",
            AlbumStatus.ERROR: "Erreur",
            AlbumStatus.WARNING: "Attention"
        }
        return text_map.get(self.status, "Inconnu")
    
    @property
    def status_css_class(self) -> str:
        """Classe CSS pour le statut"""
        return f"status-{self.status.value}"
    
    def _find_cover_image(self):
        """Trouve l'image de pochette dans le dossier"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            return
        
        # Noms de fichiers de pochette courants
        cover_names = [
            "cover.jpg", "cover.jpeg", "cover.png",
            "folder.jpg", "folder.jpeg", "folder.png",
            "front.jpg", "front.jpeg", "front.png",
            "album.jpg", "album.jpeg", "album.png"
        ]
        
        for cover_name in cover_names:
            cover_path = os.path.join(self.folder_path, cover_name)
            if os.path.exists(cover_path):
                self.cover_path = cover_path
                break
    
    def _load_tracks(self):
        """Charge les pistes depuis le dossier"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            return
        
        # Extensions audio supportées
        audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav'}
        
        tracks = []
        for file_name in sorted(os.listdir(self.folder_path)):
            file_path = os.path.join(self.folder_path, file_name)
            
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file_name.lower())
                
                if ext in audio_extensions:
                    # Extrait le numéro de piste (basique pour l'instant)
                    track_number = len(tracks) + 1
                    
                    # Extrait le titre (retire l'extension et numéro éventuel)
                    title = Path(file_name).stem
                    
                    track = TrackModel(
                        number=track_number,
                        title=title,
                        artist=self.artist,
                        file_path=file_path
                    )
                    
                    tracks.append(track)
        
        self.tracks = tracks
        self.track_count = len(tracks)
    
    def add_issue(self, issue: str):
        """Ajoute un problème à l'album"""
        if issue not in self.issues:
            self.issues.append(issue)
    
    def clear_issues(self):
        """Efface tous les problèmes"""
        self.issues.clear()
        for track in self.tracks:
            track.issues.clear()
            track.has_issues = False
    
    def update_status(self, new_status: AlbumStatus, progress: float = 0.0):
        """Met à jour le statut de l'album"""
        self.status = new_status
        self.processing_progress = progress
    
    def create_playlist(self) -> str:
        """Crée une playlist M3U avec chemins relatifs dans le dossier de l'album"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            raise ValueError("Dossier de l'album non trouvé")
        
        # Nom du fichier playlist
        playlist_filename = f"{self.title}.m3u"
        # Nettoie le nom de fichier des caractères non autorisés
        safe_filename = "".join(c for c in playlist_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        playlist_path = os.path.join(self.folder_path, safe_filename)
        
        # Contenu de la playlist
        playlist_content = ["#EXTM3U"]
        
        # Trie les pistes par numéro
        sorted_tracks = sorted(self.tracks, key=lambda t: t.number if t.number else 0)
        
        for track in sorted_tracks:
            if track.file_path and os.path.exists(track.file_path):
                # Chemin relatif depuis le dossier de l'album
                rel_path = os.path.relpath(track.file_path, self.folder_path)
                
                # Informations étendues M3U
                duration_seconds = self._parse_duration_to_seconds(track.duration)
                playlist_content.append(f"#EXTINF:{duration_seconds},{track.artist} - {track.title}")
                playlist_content.append(rel_path)
        
        # Écrit le fichier playlist
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(playlist_content))
        
        return playlist_path
    
    def _parse_duration_to_seconds(self, duration_str: str) -> int:
        """Convertit une durée format 'mm:ss' en secondes"""
        if not duration_str or ':' not in duration_str:
            return -1  # Durée inconnue en M3U
        
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            pass
        
        return -1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour serialisation"""
        return {
            'title': self.title,
            'artist': self.artist,
            'year': self.year,
            'genre': self.genre,
            'track_count': self.track_count,
            'folder_path': self.folder_path,
            'cover_path': self.cover_path,
            'album_artist': self.album_artist,
            'compilation': self.compilation,
            'status': self.status.value,
            'issues': self.issues,
            'tracks': [
                {
                    'number': track.number,
                    'title': track.title,
                    'artist': track.artist,
                    'duration': track.duration,
                    'file_path': track.file_path,
                    'has_issues': track.has_issues,
                    'issues': track.issues
                }
                for track in self.tracks
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlbumModel':
        """Crée une instance depuis un dictionnaire"""
        # Extrait les données des pistes
        tracks_data = data.pop('tracks', [])
        
        # Crée l'album
        album = cls(
            status=AlbumStatus(data.pop('status', 'pending')),
            **data
        )
        
        # Recrée les pistes
        album.tracks = [
            TrackModel(**track_data)
            for track_data in tracks_data
        ]
        
        return album
    
    def __str__(self) -> str:
        """Représentation textuelle"""
        return f"{self.display_artist} - {self.display_title} ({self.track_count} pistes)"
    
    def __repr__(self) -> str:
        """Représentation pour debug"""
        return f"AlbumModel(title='{self.title}', artist='{self.artist}', status={self.status})"
