#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de playlists M3U pour Nonotags
Permet de scanner, créer et gérer des playlists .m3u
"""

import os
import re
import threading
from pathlib import Path
from typing import List, Dict, Optional, Callable
from urllib.parse import unquote
from mutagen import File as MutagenFile
from support.honest_logger import HonestLogger

class PlaylistTrack:
    """Représente une piste dans une playlist"""
    
    def __init__(self, file_path: str, title: str = "", artist: str = "", duration: int = 0, original_path: str = None):
        self.file_path = file_path  # Chemin résolu (peut être absolu)
        self.original_path = original_path or file_path  # Chemin original du fichier M3U
        self.title = title
        self.artist = artist
        self.duration = duration  # en secondes
        self.exists = os.path.exists(file_path)
    
    def is_original_path_absolute(self) -> bool:
        """Retourne True si le chemin original était absolu"""
        return os.path.isabs(self.original_path)
    
    def __str__(self):
        return f"{self.artist} - {self.title}" if self.artist and self.title else os.path.basename(self.file_path)

class Playlist:
    """Représente une playlist M3U"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.name = os.path.splitext(os.path.basename(file_path))[0]
        self.tracks: List[PlaylistTrack] = []
        self.total_duration = 0
        self.valid_tracks = 0
        self.invalid_tracks = 0
    
    def add_track(self, track: PlaylistTrack):
        """Ajoute une piste à la playlist"""
        self.tracks.append(track)
        if track.exists:
            self.valid_tracks += 1
            self.total_duration += track.duration
        else:
            self.invalid_tracks += 1
    
    def get_formatted_duration(self) -> str:
        """Retourne la durée totale formatée"""
        hours = self.total_duration // 3600
        minutes = (self.total_duration % 3600) // 60
        if hours > 0:
            return f"{hours}h{minutes:02d}m"
        else:
            return f"{minutes}m"
    
    def get_summary(self) -> str:
        """Retourne un résumé de la playlist"""
        total = len(self.tracks)
        if total == 0:
            return "Vide"
        
        summary = f"{total} piste{'s' if total > 1 else ''}"
        if self.invalid_tracks > 0:
            summary += f" ({self.invalid_tracks} manquante{'s' if self.invalid_tracks > 1 else ''})"
        summary += f" - {self.get_formatted_duration()}"
        return summary
    
    def get_path_type(self) -> str:
        """Retourne le type de chemin des pistes (Absolu/Relatif/Mixte)"""
        if not self.tracks:
            return "Vide"
        
        absolute_count = 0
        relative_count = 0
        
        for track in self.tracks:
            if track.is_original_path_absolute():
                absolute_count += 1
            else:
                relative_count += 1
        
        if absolute_count > 0 and relative_count > 0:
            return "Mixte"
        elif absolute_count > 0:
            return "Absolu"
        else:
            return "Relatif"

class PlaylistManager:
    """Gestionnaire principal des playlists M3U"""
    
    def __init__(self):
        self.logger = HonestLogger("PlaylistManager")
        self.playlists: List[Playlist] = []
        self.scan_directories: List[str] = []
        self.supported_extensions = {'.mp3', '.flac', '.m4a', '.mp4', '.ogg', '.wav'}
        
        # Callbacks pour l'interface
        self.on_scan_progress: Optional[Callable] = None
        self.on_scan_complete: Optional[Callable] = None
        self.on_playlist_created: Optional[Callable] = None
    
    def add_scan_directory(self, directory: str):
        """Ajoute un répertoire à scanner"""
        if os.path.exists(directory) and directory not in self.scan_directories:
            self.scan_directories.append(directory)
            self.logger.info(f"Répertoire ajouté pour scan: {directory}")
    
    def remove_scan_directory(self, directory: str):
        """Supprime un répertoire du scan"""
        if directory in self.scan_directories:
            self.scan_directories.remove(directory)
            self.logger.info(f"Répertoire supprimé du scan: {directory}")
    
    def scan_playlists_async(self):
        """Lance le scan des playlists en arrière-plan"""
        def scan_worker():
            try:
                self._scan_playlists()
            except Exception as e:
                self.logger.error(f"Erreur lors du scan des playlists: {e}")
        
        thread = threading.Thread(target=scan_worker, daemon=True)
        thread.start()
    
    def _scan_playlists(self):
        """Scanne tous les répertoires pour trouver les playlists M3U"""
        self.playlists.clear()
        total_found = 0
        
        self.logger.info("Début du scan des playlists...")
        
        for directory in self.scan_directories:
            if not os.path.exists(directory):
                continue
            
            self.logger.info(f"Scan du répertoire: {directory}")
            
            # Rechercher récursivement tous les fichiers .m3u
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.m3u'):
                        playlist_path = os.path.join(root, file)
                        
                        if self.on_scan_progress:
                            self.on_scan_progress(f"Analyse: {os.path.basename(playlist_path)}")
                        
                        playlist = self._parse_playlist(playlist_path)
                        if playlist:
                            self.playlists.append(playlist)
                            total_found += 1
                            self.logger.info(f"Playlist trouvée: {playlist.name} ({playlist.get_summary()})")
        
        # Trier les playlists par nom
        self.playlists.sort(key=lambda p: p.name.lower())
        
        self.logger.info(f"Scan terminé: {total_found} playlist{'s' if total_found > 1 else ''} trouvée{'s' if total_found > 1 else ''}")
        
        if self.on_scan_complete:
            self.on_scan_complete(self.playlists)
    
    def _parse_playlist(self, playlist_path: str) -> Optional[Playlist]:
        """Parse un fichier de playlist M3U"""
        try:
            playlist = Playlist(playlist_path)
            current_track_info = {}
            
            with open(playlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('#') and not line.startswith('#EXTINF'):
                    continue
                
                # Parse des informations de piste EXTINF
                if line.startswith('#EXTINF:'):
                    # Format: #EXTINF:duration,artist - title
                    match = re.match(r'#EXTINF:(\d+),(.+)', line)
                    if match:
                        duration = int(match.group(1))
                        info = match.group(2).strip()
                        
                        # Essayer de séparer artiste et titre
                        if ' - ' in info:
                            artist, title = info.split(' - ', 1)
                            current_track_info = {
                                'duration': duration,
                                'artist': artist.strip(),
                                'title': title.strip()
                            }
                        else:
                            current_track_info = {
                                'duration': duration,
                                'title': info
                            }
                
                # Chemin de fichier
                elif line and not line.startswith('#'):
                    original_path = line  # Garder le chemin original du M3U
                    file_path = self._resolve_track_path(line, playlist_path)
                    
                    # Créer la piste avec les infos disponibles
                    track = PlaylistTrack(
                        file_path=file_path,
                        title=current_track_info.get('title', ''),
                        artist=current_track_info.get('artist', ''),
                        duration=current_track_info.get('duration', 0),
                        original_path=original_path
                    )
                    
                    # Si pas d'infos M3U, essayer d'extraire des métadonnées
                    if not track.title and track.exists:
                        self._extract_track_metadata(track)
                    
                    playlist.add_track(track)
                    current_track_info = {}  # Reset pour la piste suivante
            
            return playlist if playlist.tracks else None
            
        except Exception as e:
            self.logger.error(f"Erreur lecture playlist {playlist_path}: {e}")
            return None
    
    def _resolve_track_path(self, track_line: str, playlist_path: str) -> str:
        """Résout le chemin d'une piste par rapport à la playlist"""
        track_path = track_line.strip()
        
        # Gérer les URLs
        if track_path.startswith(('http://', 'https://', 'file://')):
            if track_path.startswith('file://'):
                track_path = unquote(track_path[7:])
            else:
                return track_path  # URL web, garder tel quel
        
        # Chemin absolu
        if os.path.isabs(track_path):
            return track_path
        
        # Chemin relatif par rapport à la playlist
        playlist_dir = os.path.dirname(playlist_path)
        return os.path.normpath(os.path.join(playlist_dir, track_path))
    
    def _extract_track_metadata(self, track: PlaylistTrack):
        """Extrait les métadonnées d'une piste si possible"""
        try:
            audio_file = MutagenFile(track.file_path)
            if audio_file is None:
                return
            
            # Extraire titre
            if not track.title:
                title = None
                if hasattr(audio_file, 'tags') and audio_file.tags:
                    # MP3
                    title = (audio_file.tags.get('TIT2') or 
                            audio_file.tags.get('TITLE') or
                            [None])[0]
                    if hasattr(title, 'text'):
                        title = str(title.text[0]) if title.text else None
                
                if not title and hasattr(audio_file, '__getitem__'):
                    # FLAC, MP4, etc.
                    title = (audio_file.get('TITLE') or 
                            audio_file.get('title') or
                            [None])[0]
                
                track.title = str(title) if title else os.path.splitext(os.path.basename(track.file_path))[0]
            
            # Extraire artiste
            if not track.artist:
                artist = None
                if hasattr(audio_file, 'tags') and audio_file.tags:
                    # MP3
                    artist = (audio_file.tags.get('TPE1') or 
                             audio_file.tags.get('ARTIST') or
                             [None])[0]
                    if hasattr(artist, 'text'):
                        artist = str(artist.text[0]) if artist.text else None
                
                if not artist and hasattr(audio_file, '__getitem__'):
                    # FLAC, MP4, etc.
                    artist = (audio_file.get('ARTIST') or 
                             audio_file.get('artist') or
                             [None])[0]
                
                track.artist = str(artist) if artist else ""
            
            # Extraire durée si pas déjà définie
            if track.duration == 0 and hasattr(audio_file, 'info'):
                track.duration = int(audio_file.info.length) if audio_file.info.length else 0
                
        except Exception as e:
            self.logger.debug(f"Impossible d'extraire métadonnées de {track.file_path}: {e}")
    
    def create_playlist_from_directory(self, directory: str, playlist_name: str, 
                                     recursive: bool = True) -> Optional[Playlist]:
        """Crée une nouvelle playlist à partir d'un répertoire"""
        try:
            if not os.path.exists(directory):
                self.logger.error(f"Répertoire inexistant: {directory}")
                return None
            
            # Collecter tous les fichiers audio
            audio_files = []
            
            if recursive:
                for root, dirs, files in os.walk(directory):
                    for file in sorted(files):
                        if any(file.lower().endswith(ext) for ext in self.supported_extensions):
                            audio_files.append(os.path.join(root, file))
            else:
                for file in sorted(os.listdir(directory)):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in self.supported_extensions):
                        audio_files.append(file_path)
            
            if not audio_files:
                self.logger.warning(f"Aucun fichier audio trouvé dans {directory}")
                return None
            
            # Créer le fichier de playlist
            playlist_path = os.path.join(directory, f"{playlist_name}.m3u")
            
            # Créer l'objet playlist
            playlist = Playlist(playlist_path)
            
            # Générer le contenu M3U
            m3u_content = ["#EXTM3U"]
            
            for file_path in audio_files:
                track = PlaylistTrack(file_path, original_path=file_path)
                self._extract_track_metadata(track)
                playlist.add_track(track)
                
                # Ajouter l'entrée M3U
                if track.duration > 0:
                    track_info = f"{track.artist} - {track.title}" if track.artist else track.title
                    m3u_content.append(f"#EXTINF:{track.duration},{track_info}")
                
                # Utiliser un chemin relatif si possible
                rel_path = os.path.relpath(file_path, directory)
                m3u_content.append(rel_path)
            
            # Sauvegarder le fichier
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(m3u_content))
            
            self.logger.info(f"Playlist créée: {playlist_path} ({len(audio_files)} pistes)")
            
            if self.on_playlist_created:
                self.on_playlist_created(playlist)
            
            return playlist
            
        except Exception as e:
            self.logger.error(f"Erreur création playlist: {e}")
            return None
    
    def get_playlists_by_directory(self, directory: str) -> List[Playlist]:
        """Retourne toutes les playlists d'un répertoire donné"""
        directory = os.path.normpath(directory)
        return [p for p in self.playlists if os.path.normpath(os.path.dirname(p.file_path)) == directory]
    
    def get_all_playlists(self) -> List[Playlist]:
        """Retourne toutes les playlists trouvées"""
        return self.playlists.copy()
    
    def get_playlist_statistics(self) -> Dict[str, int]:
        """Retourne des statistiques sur les playlists"""
        total_playlists = len(self.playlists)
        total_tracks = sum(len(p.tracks) for p in self.playlists)
        total_valid_tracks = sum(p.valid_tracks for p in self.playlists)
        total_invalid_tracks = sum(p.invalid_tracks for p in self.playlists)
        total_duration = sum(p.total_duration for p in self.playlists)
        
        return {
            'total_playlists': total_playlists,
            'total_tracks': total_tracks,
            'valid_tracks': total_valid_tracks,
            'invalid_tracks': total_invalid_tracks,
            'total_duration': total_duration
        }
    
    def refresh_playlist(self, playlist: Playlist):
        """Actualise une playlist spécifique"""
        if os.path.exists(playlist.file_path):
            refreshed = self._parse_playlist(playlist.file_path)
            if refreshed:
                # Remplacer dans la liste
                for i, p in enumerate(self.playlists):
                    if p.file_path == playlist.file_path:
                        self.playlists[i] = refreshed
                        break
                self.logger.info(f"Playlist actualisée: {refreshed.name}")
                return refreshed
        return None
    
    def convert_playlist_paths(self, playlist: Playlist, to_relative: bool = True) -> bool:
        """
        Convertit une playlist entre chemins absolus et relatifs
        
        Args:
            playlist: La playlist à convertir
            to_relative: True pour convertir vers relatif, False pour absolu
            
        Returns:
            bool: True si la conversion a réussi
        """
        try:
            playlist_path = playlist.file_path
            playlist_dir = os.path.dirname(playlist_path)
            
            # Lire le fichier M3U existant
            with open(playlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Créer le nouveau contenu
            new_lines = []
            track_index = 0
            
            for line in lines:
                line_stripped = line.strip()
                
                # Garder les lignes de commentaires et EXTINF
                if line_stripped.startswith('#') or not line_stripped:
                    new_lines.append(line)
                else:
                    # C'est un chemin de fichier, le convertir
                    if track_index < len(playlist.tracks):
                        track = playlist.tracks[track_index]
                        
                        if to_relative:
                            # Convertir vers relatif
                            try:
                                if os.path.isabs(track.original_path):
                                    new_path = os.path.relpath(track.file_path, playlist_dir)
                                else:
                                    new_path = track.original_path
                            except ValueError:
                                # Impossible de créer un chemin relatif
                                new_path = track.original_path
                        else:
                            # Convertir vers absolu
                            if os.path.isabs(track.original_path):
                                new_path = track.original_path
                            else:
                                new_path = track.file_path  # Déjà résolu en absolu
                        
                        new_lines.append(new_path + '\n')
                        track_index += 1
                    else:
                        # Garder la ligne telle quelle
                        new_lines.append(line)
            
            # Sauvegarder le fichier
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            conversion_type = "relatifs" if to_relative else "absolus"
            self.logger.info(f"Playlist convertie en chemins {conversion_type}: {playlist.name}")
            
            # Actualiser la playlist
            self.refresh_playlist(playlist)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur conversion playlist {playlist.name}: {e}")
            return False
