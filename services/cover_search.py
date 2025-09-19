"""
Service de recherche de pochettes d'albums sur Internet
Utilise les APIs MusicBrainz et Discogs pour trouver des pochettes
"""

import requests
import json
import os
import urllib.parse
from PIL import Image
import io
import time
from support.logger import AppLogger
from support.config_manager import ConfigManager


class CoverSearchError(Exception):
    """Exception pour les erreurs de recherche de pochettes"""
    pass


class CoverResult:
    """Résultat de recherche de pochette"""
    
    def __init__(self, url, thumbnail_url, source, size=None, format=None):
        self.url = url
        self.thumbnail_url = thumbnail_url
        self.source = source
        self.size = size  # (width, height)
        self.format = format
    
    def __str__(self):
        return f"CoverResult({self.source}, {self.size}, {self.format})"


class CoverSearchService:
    """Service de recherche de pochettes d'albums"""
    
    def __init__(self):
        """Initialise le service de recherche"""
        self.logger = AppLogger()
        self.config = ConfigManager()
        
        # Configuration des APIs
        self.musicbrainz_base = "https://musicbrainz.org/ws/2"
        self.coverart_base = "https://coverartarchive.org"
        self.discogs_base = "https://api.discogs.com"
        
        # Headers pour les requêtes
        self.headers = {
            'User-Agent': 'Nonotags/1.0 ( https://github.com/user/nonotags )',
            'Accept': 'application/json'
        }
        
        # Configuration des timeouts et limites
        self.timeout = 10
        self.max_results = 20
        self.min_cover_size = 200  # Taille minimum 200x200
        
        # Délais entre requêtes (politesse envers les APIs)
        self.request_delay = 1.0
        self.last_request_time = 0
        
        self.logger.info("CoverSearchService initialisé")
    
    def _wait_for_rate_limit(self):
        """Respecte les limites de taux des APIs"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            wait_time = self.request_delay - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url, headers=None):
        """Effectue une requête HTTP avec gestion d'erreurs"""
        self._wait_for_rate_limit()
        
        try:
            req_headers = self.headers.copy()
            if headers:
                req_headers.update(headers)
            
            response = requests.get(url, headers=req_headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.debug(f"Requête réussie: {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Erreur requête {url}: {e}")
            return None
    
    def search_covers(self, artist, album, year=None):
        """
        Recherche des pochettes pour un album donné
        
        Args:
            artist (str): Nom de l'artiste
            album (str): Nom de l'album
            year (str, optional): Année de l'album
        
        Returns:
            list[CoverResult]: Liste des pochettes trouvées
        """
        if not artist or not album:
            raise CoverSearchError("Artiste et album requis")
        
        self.logger.info(f"Recherche pochettes: {artist} - {album}")
        
        results = []
        
        # 1. Recherche via MusicBrainz + Cover Art Archive
        mb_results = self._search_musicbrainz(artist, album, year)
        results.extend(mb_results)
        
        # 2. Recherche via Discogs (si pas assez de résultats)
        if len(results) < 5:
            discogs_results = self._search_discogs(artist, album, year)
            results.extend(discogs_results)
        
        # Filtrer et trier les résultats
        filtered_results = self._filter_and_sort_results(results)
        
        self.logger.info(f"Trouvé {len(filtered_results)} pochettes")
        return filtered_results
    
    def _search_musicbrainz(self, artist, album, year=None):
        """Recherche via MusicBrainz + Cover Art Archive"""
        results = []
        
        try:
            # Construire la requête de recherche
            query_parts = [
                f'artist:"{artist}"',
                f'release:"{album}"'
            ]
            
            if year:
                query_parts.append(f'date:{year}')
            
            query = ' AND '.join(query_parts)
            encoded_query = urllib.parse.quote(query)
            
            # Rechercher les releases
            search_url = f"{self.musicbrainz_base}/release/?query={encoded_query}&fmt=json&limit=10"
            
            response = self._make_request(search_url)
            if not response:
                return results
            
            data = response.json()
            releases = data.get('releases', [])
            
            self.logger.debug(f"MusicBrainz: {len(releases)} releases trouvées")
            
            # Pour chaque release, chercher les pochettes
            for release in releases[:5]:  # Limiter à 5 releases
                release_id = release.get('id')
                if not release_id:
                    continue
                
                cover_results = self._get_coverart_for_release(release_id, release)
                results.extend(cover_results)
            
        except Exception as e:
            self.logger.error(f"Erreur recherche MusicBrainz: {e}")
        
        return results
    
    def _get_coverart_for_release(self, release_id, release_info):
        """Récupère les pochettes pour une release MusicBrainz"""
        results = []
        
        try:
            cover_url = f"{self.coverart_base}/release/{release_id}"
            
            response = self._make_request(cover_url)
            if not response:
                return results
            
            data = response.json()
            images = data.get('images', [])
            
            for image in images:
                # Privilégier les images "front"
                if not image.get('front', False):
                    continue
                
                thumbnails = image.get('thumbnails', {})
                image_url = image.get('image')
                
                if image_url:
                    result = CoverResult(
                        url=image_url,
                        thumbnail_url=thumbnails.get('small', image_url),
                        source='Cover Art Archive',
                        format='jpeg'
                    )
                    results.append(result)
            
            self.logger.debug(f"Cover Art Archive: {len(results)} images pour {release_id}")
            
        except Exception as e:
            self.logger.debug(f"Pas de pochettes Cover Art Archive pour {release_id}: {e}")
        
        return results
    
    def _search_discogs(self, artist, album, year=None):
        """Recherche via l'API Discogs"""
        results = []
        
        try:
            # Construire la requête
            query_parts = [artist, album]
            if year:
                query_parts.append(year)
            
            query = ' '.join(query_parts)
            encoded_query = urllib.parse.quote(query)
            
            search_url = f"{self.discogs_base}/database/search?q={encoded_query}&type=release&per_page=10"
            
            response = self._make_request(search_url)
            if not response:
                return results
            
            data = response.json()
            releases = data.get('results', [])
            
            self.logger.debug(f"Discogs: {len(releases)} releases trouvées")
            
            for release in releases[:5]:  # Limiter à 5 releases
                cover_image = release.get('cover_image')
                thumb = release.get('thumb')
                
                if cover_image and cover_image != 'null':
                    result = CoverResult(
                        url=cover_image,
                        thumbnail_url=thumb or cover_image,
                        source='Discogs',
                        format='jpeg'
                    )
                    results.append(result)
            
        except Exception as e:
            self.logger.error(f"Erreur recherche Discogs: {e}")
        
        return results
    
    def _filter_and_sort_results(self, results):
        """Filtre et trie les résultats par qualité"""
        filtered = []
        
        for result in results:
            # Éviter les doublons
            if any(r.url == result.url for r in filtered):
                continue
            
            # Vérifier la taille si disponible
            if result.size:
                width, height = result.size
                if width < self.min_cover_size or height < self.min_cover_size:
                    continue
            
            filtered.append(result)
        
        # Trier par source (Cover Art Archive en premier)
        def sort_key(result):
            source_priority = {
                'Cover Art Archive': 0,
                'Discogs': 1
            }
            return source_priority.get(result.source, 2)
        
        filtered.sort(key=sort_key)
        
        return filtered[:self.max_results]
    
    def download_cover(self, cover_result, output_path):
        """
        Télécharge une pochette et la sauvegarde
        
        Args:
            cover_result (CoverResult): Résultat de recherche
            output_path (str): Chemin de sauvegarde
        
        Returns:
            bool: True si le téléchargement a réussi
        """
        try:
            self.logger.info(f"Téléchargement pochette: {cover_result.url}")
            
            response = self._make_request(cover_result.url)
            if not response:
                return False
            
            # Vérifier le type de contenu
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                self.logger.warning(f"Type de contenu invalide: {content_type}")
                return False
            
            # Traiter l'image avec PIL
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            # Vérifier la taille minimum
            width, height = image.size
            if width < self.min_cover_size or height < self.min_cover_size:
                self.logger.warning(f"Image trop petite: {width}x{height}")
                return False
            
            # Redimensionner si nécessaire (carré)
            if width != height:
                size = min(width, height)
                image = image.crop(((width - size) // 2, (height - size) // 2, 
                                 (width + size) // 2, (height + size) // 2))
            
            # Redimensionner à 500x500 maximum
            if image.size[0] > 500:
                image = image.resize((500, 500), Image.Resampling.LANCZOS)
            
            # Sauvegarder
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path, 'JPEG', quality=90)
            
            self.logger.info(f"Pochette sauvegardée: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur téléchargement pochette: {e}")
            return False
    
    def get_image_info(self, cover_result):
        """
        Obtient les informations d'une image sans la télécharger
        
        Args:
            cover_result (CoverResult): Résultat de recherche
        
        Returns:
            dict: Informations sur l'image (taille, format, etc.)
        """
        try:
            # Télécharger seulement les headers
            response = requests.head(cover_result.url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            content_length = response.headers.get('content-length')
            content_type = response.headers.get('content-type', '')
            
            info = {
                'content_type': content_type,
                'size_bytes': int(content_length) if content_length else None,
                'format': content_type.split('/')[-1] if '/' in content_type else None
            }
            
            # Essayer d'obtenir la taille de l'image
            try:
                response = self._make_request(cover_result.url)
                if response:
                    image = Image.open(io.BytesIO(response.content))
                    info['dimensions'] = image.size
                    cover_result.size = image.size
                    cover_result.format = image.format.lower()
            except:
                pass
            
            return info
            
        except Exception as e:
            self.logger.debug(f"Erreur info image: {e}")
            return {}
    
    def validate_cover_file(self, file_path):
        """
        Valide un fichier de pochette existant
        
        Args:
            file_path (str): Chemin vers le fichier
        
        Returns:
            dict: Informations de validation
        """
        result = {
            'valid': False,
            'width': 0,
            'height': 0,
            'format': None,
            'size_bytes': 0,
            'issues': []
        }
        
        try:
            if not os.path.exists(file_path):
                result['issues'].append("Fichier introuvable")
                return result
            
            # Taille du fichier
            result['size_bytes'] = os.path.getsize(file_path)
            
            # Ouvrir avec PIL
            with Image.open(file_path) as image:
                result['width'], result['height'] = image.size
                result['format'] = image.format.lower()
            
            # Validations
            if result['width'] < self.min_cover_size:
                result['issues'].append(f"Largeur trop petite: {result['width']} < {self.min_cover_size}")
            
            if result['height'] < self.min_cover_size:
                result['issues'].append(f"Hauteur trop petite: {result['height']} < {self.min_cover_size}")
            
            if result['format'] not in ['jpeg', 'jpg', 'png']:
                result['issues'].append(f"Format non supporté: {result['format']}")
            
            if result['size_bytes'] > 5 * 1024 * 1024:  # 5MB max
                result['issues'].append(f"Fichier trop volumineux: {result['size_bytes']} bytes")
            
            result['valid'] = len(result['issues']) == 0
            
        except Exception as e:
            result['issues'].append(f"Erreur validation: {e}")
        
        return result