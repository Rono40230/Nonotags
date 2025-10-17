"""
Service de scan des dossiers musicaux
Détecte automatiquement les albums et extrait les métadonnées
"""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
try:
    from mutagen.flac import FLAC
except ImportError:
    FLAC = None
try:
    from mutagen.mp4 import MP4
except ImportError:
    MP4 = None
try:
    from mutagen.wav import WAV
except ImportError:
    WAV = None
from services.metadata_backup import metadata_backup
from support.thread_pool import get_thread_pool

class MusicScanner:
    """Service de scan des dossiers musicaux"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.flac', '.ogg', '.m4a', '.wav']
        self.albums_found = []
        
    def scan_directory(self, directory_path: str, progress_callback=None) -> List[Dict]:
        """
        Scanne un dossier et retourne la liste des albums détectés
        
        Args:
            directory_path: Chemin du dossier à scanner
            progress_callback: Fonction appelée pour indiquer le progrès
            
        Returns:
            Liste des albums avec leurs métadonnées
        """
        self.albums_found = []
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Le dossier {directory_path} n'existe pas")
            
        # Parcours récursif des dossiers
        for root, dirs, files in os.walk(directory_path):
            music_files = self._filter_music_files(files)
            
            if music_files:
                album_data = self._analyze_folder(root, music_files)
                if album_data:
                    # Sauvegarder les métadonnées originales avant toute correction
                    try:
                        metadata_backup.backup_album_metadata(root)
                        print(f"✅ Métadonnées sauvegardées pour {os.path.basename(root)}")
                    except Exception as e:
                        print(f"⚠️ Erreur sauvegarde métadonnées {root}: {e}")
                    
                    self.albums_found.append(album_data)
                    if progress_callback:
                        progress_callback(len(self.albums_found), album_data['title'])
        
        return self.albums_found
    
    def _process_album_batch(self, root: str, music_files: List[str]) -> Optional[Dict]:
        """Traite un album dans un contexte threadé (pour batch processing)"""
        album_data = self._analyze_folder(root, music_files)
        return album_data
    
    def _filter_music_files(self, files: List[str]) -> List[str]:
        """Filtre les fichiers musicaux supportés"""
        return [f for f in files if any(f.lower().endswith(ext) for ext in self.supported_formats)]
    
    def _analyze_folder(self, folder_path: str, music_files: List[str]) -> Optional[Dict]:
        """
        Analyse un dossier contenant des fichiers musicaux
        Essaie de déterminer s'il s'agit d'un album cohérent
        """
        if not music_files:
            return None
            
        # Analyse le premier fichier pour obtenir les métadonnées de base
        first_file = os.path.join(folder_path, music_files[0])
        base_metadata = self._extract_metadata(first_file)
        
        if not base_metadata:
            # Si pas de métadonnées, utilise le nom du dossier
            folder_name = os.path.basename(folder_path)
            base_metadata = self._guess_metadata_from_folder(folder_name)
        
        # Analyse tous les fichiers pour détecter la cohérence
        tracks_info = []
        for music_file in music_files:
            file_path = os.path.join(folder_path, music_file)
            track_metadata = self._extract_metadata(file_path)
            if track_metadata:
                tracks_info.append(track_metadata)
        
        # Vérifie la cohérence (même artiste/album pour la majorité des pistes)
        if self._is_coherent_album(tracks_info):
            # Met à jour les métadonnées avec les infos les plus fréquentes
            refined_metadata = self._refine_album_metadata(base_metadata, tracks_info)
            refined_metadata.update({
                'tracks': len(music_files),
                'folder_path': folder_path,
                'files': music_files,
                'emoji': self._get_genre_emoji(refined_metadata.get('genre', '')),
                'color': self._get_genre_color(refined_metadata.get('genre', ''))
            })
            return refined_metadata
            
        return None
    
    def _extract_metadata(self, file_path: str) -> Optional[Dict]:
        """Extrait les métadonnées d'un fichier musical"""
        try:
            file_ext = file_path.lower().endswith
            
            if file_ext('.mp3'):
                # Support MP3 avec tags ID3
                audio = MP3(file_path, ID3=mutagen.id3.ID3)
                return {
                    'title': self._get_tag_value(audio, 'TIT2') or self._guess_title_from_filename(file_path),
                    'artist': self._get_tag_value(audio, 'TPE1') or 'Artiste Inconnu',
                    'album': self._get_tag_value(audio, 'TALB') or 'Album Inconnu',
                    'year': self._extract_year(audio),
                    'genre': self._get_tag_value(audio, 'TCON') or 'Genre Inconnu',
                    'track_number': self._get_tag_value(audio, 'TRCK')
                }
            
            elif file_ext('.flac') and FLAC:
                # Support FLAC
                audio = FLAC(file_path)
                return {
                    'title': audio.get('title', [self._guess_title_from_filename(file_path)])[0],
                    'artist': audio.get('artist', ['Artiste Inconnu'])[0],
                    'album': audio.get('album', ['Album Inconnu'])[0],
                    'year': audio.get('date', ['----'])[0][:4] if audio.get('date') else '----',
                    'genre': audio.get('genre', ['Genre Inconnu'])[0],
                    'track_number': audio.get('tracknumber', [None])[0]
                }
            
            elif (file_ext('.m4a') or file_ext('.mp4')) and MP4:
                # Support M4A/MP4
                audio = MP4(file_path)
                return {
                    'title': audio.get('\xa9nam', [self._guess_title_from_filename(file_path)])[0],
                    'artist': audio.get('\xa9ART', ['Artiste Inconnu'])[0],
                    'album': audio.get('\xa9alb', ['Album Inconnu'])[0],
                    'year': audio.get('\xa9day', ['----'])[0][:4] if audio.get('\xa9day') else '----',
                    'genre': audio.get('\xa9gen', ['Genre Inconnu'])[0],
                    'track_number': audio.get('trkn', [(None,)])[0][0]
                }
            
            elif file_ext('.ogg'):
                # Support OGG (métadonnées basiques)
                try:
                    from mutagen.oggvorbis import OggVorbis
                    audio = OggVorbis(file_path)
                    return {
                        'title': audio.get('title', [self._guess_title_from_filename(file_path)])[0],
                        'artist': audio.get('artist', ['Artiste Inconnu'])[0],
                        'album': audio.get('album', ['Album Inconnu'])[0],
                        'year': audio.get('date', ['----'])[0][:4] if audio.get('date') else '----',
                        'genre': audio.get('genre', ['Genre Inconnu'])[0],
                        'track_number': audio.get('tracknumber', [None])[0]
                    }
                except ImportError:
                    # Fallback si mutagen.oggvorbis n'est pas disponible
                    pass
            
            elif file_ext('.wav') and WAV:
                # Support WAV (métadonnées limitées)
                audio = WAV(file_path)
                # WAV a très peu de métadonnées, on utilise le nom de fichier
                return self._guess_metadata_from_filename(file_path)
        
        except (ID3NoHeaderError, Exception) as e:
            # Erreur lecture métadonnées, utiliser le nom de fichier
            return self._guess_metadata_from_filename(file_path)
        
        return None
    
    def _get_tag_value(self, audio, tag_name: str) -> Optional[str]:
        """Récupère la valeur d'un tag ID3"""
        try:
            if tag_name in audio:
                value = str(audio[tag_name].text[0])
                return value.strip() if value else None
        except (IndexError, AttributeError):
            pass
        return None
    
    def _extract_year(self, audio) -> str:
        """Extrait l'année depuis différents tags possibles"""
        year_tags = ['TDRC', 'TYER', 'TDAT']
        for tag in year_tags:
            year = self._get_tag_value(audio, tag)
            if year:
                # Extrait les 4 premiers chiffres (année)
                year_match = re.search(r'\d{4}', str(year))
                if year_match:
                    return year_match.group()
        return '----'
    
    def _guess_metadata_from_folder(self, folder_name: str) -> Dict:
        """Devine les métadonnées à partir du nom du dossier"""
        # Patterns courants: "Artiste - Album (Année)", "Année - Album", etc.
        patterns = [
            r'^(.+?)\s*-\s*(.+?)\s*\((\d{4})\)$',  # Artiste - Album (Année)
            r'^(\d{4})\s*-\s*(.+)$',               # Année - Album
            r'^(.+?)\s*-\s*(.+)$',                 # Artiste - Album
        ]
        
        for pattern in patterns:
            match = re.match(pattern, folder_name)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # Artiste - Album (Année)
                    return {
                        'artist': groups[0].strip(),
                        'album': groups[1].strip(),
                        'year': groups[2],
                        'genre': 'Genre Inconnu'
                    }
                elif len(groups) == 2:
                    if groups[0].isdigit():  # Année - Album
                        return {
                            'artist': 'Artiste Inconnu',
                            'album': groups[1].strip(),
                            'year': groups[0],
                            'genre': 'Genre Inconnu'
                        }
                    else:  # Artiste - Album
                        return {
                            'artist': groups[0].strip(),
                            'album': groups[1].strip(),
                            'year': '----',
                            'genre': 'Genre Inconnu'
                        }
        
        # Fallback: utilise le nom du dossier comme album
        return {
            'artist': 'Artiste Inconnu',
            'album': folder_name,
            'year': '----',
            'genre': 'Genre Inconnu'
        }
    
    def _guess_metadata_from_filename(self, file_path: str) -> Dict:
        """Devine les métadonnées à partir du nom de fichier"""
        filename = os.path.splitext(os.path.basename(file_path))[0]
        folder_name = os.path.basename(os.path.dirname(file_path))
        
        # Le dossier parent comme album, le fichier comme titre
        return {
            'title': filename,
            'artist': 'Artiste Inconnu',
            'album': folder_name,
            'year': '----',
            'genre': 'Genre Inconnu'
        }
    
    def _guess_title_from_filename(self, file_path: str) -> str:
        """Devine le titre à partir du nom de fichier"""
        filename = os.path.splitext(os.path.basename(file_path))[0]
        # Supprime les numéros de piste en début: "01 - Titre" -> "Titre"
        title_match = re.sub(r'^\d+\s*[-.\s]*', '', filename)
        return title_match.strip() or filename
    
    def _is_coherent_album(self, tracks_info: List[Dict]) -> bool:
        """Vérifie si les pistes forment un album cohérent"""
        if len(tracks_info) < 2:
            return True  # Un seul fichier = album valide
        
        # Compte les artistes et albums différents
        artists = [track.get('artist', '') for track in tracks_info if track.get('artist')]
        albums = [track.get('album', '') for track in tracks_info if track.get('album')]
        
        # Un album est cohérent si >70% des pistes ont le même artiste OU le même album
        if artists:
            most_common_artist = max(set(artists), key=artists.count)
            artist_ratio = artists.count(most_common_artist) / len(artists)
            if artist_ratio >= 0.7:
                return True
        
        if albums:
            most_common_album = max(set(albums), key=albums.count)
            album_ratio = albums.count(most_common_album) / len(albums)
            if album_ratio >= 0.7:
                return True
        
        return False
    
    def _refine_album_metadata(self, base_metadata: Dict, tracks_info: List[Dict]) -> Dict:
        """Affine les métadonnées d'album en se basant sur les pistes"""
        if not tracks_info:
            return base_metadata
        
        # Trouve les valeurs les plus fréquentes
        artists = [track.get('artist', '') for track in tracks_info if track.get('artist')]
        albums = [track.get('album', '') for track in tracks_info if track.get('album')]
        genres = [track.get('genre', '') for track in tracks_info if track.get('genre')]
        years = [track.get('year', '') for track in tracks_info if track.get('year') and track.get('year') != '----']
        
        result = base_metadata.copy()
        
        if artists:
            result['artist'] = max(set(artists), key=artists.count)
        if albums:
            result['album'] = max(set(albums), key=albums.count)
        if genres:
            result['genre'] = max(set(genres), key=genres.count)
        if years:
            result['year'] = max(set(years), key=years.count)
        
        return result
    
    def _get_genre_emoji(self, genre: str) -> str:
        """Retourne un emoji correspondant au genre musical"""
        genre_lower = genre.lower()
        genre_map = {
            'rock': '🎸', 'pop': '🎤', 'jazz': '🎺', 'classical': '🎼',
            'electronic': '🎛️', 'hip hop': '🎵', 'rap': '🎤', 'country': '🤠',
            'blues': '🎸', 'folk': '🪕', 'metal': '🤘', 'punk': '🎸',
            'reggae': '🌴', 'funk': '🎷', 'soul': '❤️', 'disco': '🕺'
        }
        
        for key, emoji in genre_map.items():
            if key in genre_lower:
                return emoji
        
        return '🎵'  # Emoji par défaut
    
    def _get_genre_color(self, genre: str) -> str:
        """Retourne une couleur correspondant au genre musical"""
        genre_lower = genre.lower()
        color_map = {
            'rock': 'red', 'pop': 'pink', 'jazz': 'blue', 'classical': 'purple',
            'electronic': 'cyan', 'hip hop': 'orange', 'rap': 'orange', 'country': 'brown',
            'blues': 'indigo', 'folk': 'green', 'metal': 'gray', 'punk': 'red',
            'reggae': 'green', 'funk': 'yellow', 'soul': 'red', 'disco': 'purple'
        }
        
        for key, color in color_map.items():
            if key in genre_lower:
                return color
        
        return 'blue'  # Couleur par défaut
