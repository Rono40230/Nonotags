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
        self.itunes_base = "https://itunes.apple.com/search"
        
        # Headers pour les requêtes
        self.headers = {
            'User-Agent': 'Nonotags/1.0 ( https://github.com/Rono40230/Nonotags )',
            'Accept': 'application/json'
        }
        
        # Configuration des timeouts et limites
        self.timeout = 10
        self.max_results = 20
        self.min_cover_size = 200  # Taille minimum 200x200 (plus souple)
        self.required_formats = ['jpg', 'jpeg']  # JPG uniquement comme demandé
        
        # Délais entre requêtes (politesse envers les APIs)
        self.request_delay = 0.5  # Plus rapide
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
    
    def _make_request(self, url, headers=None, raise_on_error=False):
        """Effectue une requête HTTP avec gestion d'erreurs"""
        self._wait_for_rate_limit()
        
        try:
            req_headers = self.headers.copy()
            if headers:
                req_headers.update(headers)
            
            self.logger.debug(f"Requête: {url}")
            response = requests.get(url, headers=req_headers, timeout=self.timeout)
            
            if response.status_code == 404:
                self.logger.debug(f"Ressource non trouvée: {url}")
                return None
            
            response.raise_for_status()
            
            self.logger.debug(f"Requête réussie: {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur requête {url}: {e}"
            self.logger.warning(error_msg)
            if raise_on_error:
                raise CoverSearchError(error_msg)
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
        print(f"🔍 Recherche pochettes: {artist} - {album}")
        
        results = []
        errors = []
        
        # 1. Recherche via MusicBrainz + Cover Art Archive
        try:
            print("📡 Recherche MusicBrainz...")
            mb_results = self._search_musicbrainz(artist, album, year)
            results.extend(mb_results)
            print(f"✅ MusicBrainz: {len(mb_results)} résultats")
            self.logger.info(f"MusicBrainz: {len(mb_results)} résultats")
        except Exception as e:
            error_msg = f"Erreur MusicBrainz: {e}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg)
            errors.append(error_msg)
        
        # 2. Recherche via iTunes (prioritaire, haute qualité)
        if len(results) < 10:
            try:
                print("🎵 Recherche iTunes...")
                itunes_results = self._search_itunes(artist, album, year)
                results.extend(itunes_results)
                print(f"✅ iTunes: {len(itunes_results)} résultats")
                self.logger.info(f"iTunes: {len(itunes_results)} résultats")
            except Exception as e:
                error_msg = f"Erreur iTunes: {e}"
                print(f"❌ {error_msg}")
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # 3. Recherche via Discogs (toujours disponible)
        if len(results) < 15:
            try:
                print("📀 Recherche Discogs...")
                discogs_results = self._search_discogs(artist, album, year)
                results.extend(discogs_results)
                print(f"✅ Discogs: {len(discogs_results)} résultats")
                self.logger.info(f"Discogs: {len(discogs_results)} résultats")
            except Exception as e:
                error_msg = f"Erreur Discogs: {e}"
                print(f"❌ {error_msg}")
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # Si aucun résultat et des erreurs, lever une exception informative
        if not results and errors:
            raise CoverSearchError(f"Aucun résultat trouvé. Erreurs: {'; '.join(errors)}")
        
        # Filtrer et trier les résultats
        filtered_results = self._filter_and_sort_results(results)
        
        print(f"🎯 Résultats finaux: {len(filtered_results)} pochettes (sur {len(results)} trouvées)")
        self.logger.info(f"Trouvé {len(filtered_results)} pochettes")
        return filtered_results
    
    def _search_musicbrainz(self, artist, album, year=None):
        """Recherche via MusicBrainz + Cover Art Archive"""
        results = []
        
        try:
            # Essayer plusieurs variantes de recherche
            search_queries = []
            
            # 1. Recherche exacte
            query_parts = [f'artist:"{artist}"', f'release:"{album}"']
            if year:
                query_parts.append(f'date:{year}')
            search_queries.append(' AND '.join(query_parts))
            
            # 2. Recherche plus souple (sans guillemets)
            query_parts_loose = [f'artist:{artist}', f'release:{album}']
            if year:
                query_parts_loose.append(f'date:{year}')
            search_queries.append(' AND '.join(query_parts_loose))
            
            # 3. Recherche par mots-clés de l'album
            album_words = album.replace('-', ' ').split()
            if len(album_words) > 1:
                album_keywords = ' '.join([f'release:{word}' for word in album_words if len(word) > 3])
                if album_keywords:
                    search_queries.append(f'artist:{artist} AND ({album_keywords})')
            
            # 4. Recherche par artiste seulement (pour trouver des albums proches)
            search_queries.append(f'artist:{artist}')
            
            for i, query in enumerate(search_queries):
                self.logger.info(f"Tentative {i+1}/4: {query}")
                
                encoded_query = urllib.parse.quote(query)
                search_url = f"{self.musicbrainz_base}/release/?query={encoded_query}&fmt=json&limit=10"
                self.logger.info(f"URL MusicBrainz: {search_url}")
                
                response = self._make_request(search_url, raise_on_error=True)
                if not response:
                    self.logger.warning("Aucune réponse de MusicBrainz")
                    continue
                
                data = response.json()
                releases = data.get('releases', [])
                
                self.logger.info(f"MusicBrainz: {len(releases)} releases trouvées pour query: {query}")
                
                # Log des résultats pour debug
                for j, release in enumerate(releases[:5]):
                    release_title = release.get('title', 'Unknown')
                    release_date = release.get('date', 'Unknown')
                    self.logger.info(f"  {j+1}. \"{release_title}\" ({release_date})")
                
                if releases:
                    # Pour chaque release, chercher les pochettes
                    for release in releases[:5]:  # Limiter à 5 releases
                        release_id = release.get('id')
                        release_title = release.get('title', 'Unknown')
                        if not release_id:
                            continue
                        
                        self.logger.debug(f"Recherche covers pour release: {release_title} (ID: {release_id})")
                        cover_results = self._get_coverart_for_release(release_id, release)
                        results.extend(cover_results)
                        self.logger.debug(f"Trouvé {len(cover_results)} covers pour {release_title}")
                    
                    # Si on a trouvé des résultats, arrêter seulement si c'est une recherche précise
                    if results and i < 2:  # Arrêter seulement pour les 2 premières tentatives précises
                        break
            
        except Exception as e:
            self.logger.error(f"Erreur recherche MusicBrainz: {e}")
            raise
        
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
                # Filtres de qualité stricts
                
                # 1. Privilégier les images "front" uniquement
                if not image.get('front', False):
                    self.logger.debug("Image ignorée: pas une couverture avant")
                    continue
                
                # Vérifier l'extension dans l'URL (JPG uniquement)
                image_url = image.get('image')
                if not image_url:
                    continue
                    
                # Vérifier que c'est bien du JPG
                is_jpg = any(fmt in image_url.lower() for fmt in ['.jpg', '.jpeg'])
                if not is_jpg:
                    self.logger.debug(f"Image ignorée: format non-JPG - {image_url}")
                    continue
                
                # 3. Vérifier les dimensions si disponibles
                thumbnails = image.get('thumbnails', {})
                
                # Essayer de déduire la taille depuis les thumbnails
                has_large_thumbnail = False
                for thumb_size, thumb_url in thumbnails.items():
                    if thumb_size in ['large', '500', '1200']:
                        has_large_thumbnail = True
                        break
                
                # Si pas de grande miniature, l'image est probablement petite
                if thumbnails and not has_large_thumbnail:
                    self.logger.debug("Image ignorée: probablement trop petite (pas de grande miniature)")
                    continue
                
                # 4. Validation finale de l'image via requête HEAD pour obtenir les métadonnées
                if self._validate_image_quality(image_url):
                    result = CoverResult(
                        url=image_url,
                        thumbnail_url=thumbnails.get('small', image_url),
                        source='Cover Art Archive',
                        format='jpeg'
                    )
                    results.append(result)
                    self.logger.debug(f"Image acceptée: {image_url}")
                else:
                    self.logger.debug(f"Image rejetée après validation: {image_url}")
            
            self.logger.debug(f"Cover Art Archive: {len(results)} images pour {release_id}")
            
        except Exception as e:
            self.logger.debug(f"Pas de pochettes Cover Art Archive pour {release_id}: {e}")
        
        return results
    
    def _search_itunes(self, artist, album, year=None):
        """Recherche via l'API iTunes"""
        results = []
        
        try:
            # Construire la requête iTunes
            query_parts = [artist, album]
            query = ' '.join(query_parts)
            
            # Paramètres de recherche iTunes
            params = {
                'term': query,
                'media': 'music',
                'entity': 'album',
                'limit': 20
            }
            
            # URL de recherche
            search_url = f"{self.itunes_base}"
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            albums = data.get('results', [])
            
            self.logger.info(f"iTunes: {len(albums)} albums trouvés")
            
            for album_data in albums:
                # Récupérer l'URL de l'artwork
                artwork_url = album_data.get('artworkUrl100')
                if not artwork_url:
                    continue
                
                # iTunes fournit des URLs en 100x100 par défaut, on peut les agrandir
                # Remplacer 100x100 par une taille plus grande
                high_res_url = artwork_url.replace('100x100', '600x600')
                
                # Vérifier que c'est du JPG
                is_jpg = any(fmt in high_res_url.lower() for fmt in ['.jpg', '.jpeg'])
                if not is_jpg:
                    self.logger.debug(f"Image iTunes ignorée: format non-JPG - {high_res_url}")
                    continue
                
                # Valider la qualité de l'image
                if self._validate_image_quality(high_res_url):
                    result = CoverResult(
                        url=high_res_url,
                        thumbnail_url=artwork_url,  # 100x100 comme miniature
                        source='iTunes',
                        format='jpeg'
                    )
                    results.append(result)
                    self.logger.debug(f"Image iTunes acceptée: {high_res_url}")
                else:
                    self.logger.debug(f"Image iTunes rejetée après validation: {high_res_url}")
            
        except Exception as e:
            self.logger.error(f"Erreur recherche iTunes: {e}")
            raise
        
        return results
    
    def _validate_image_quality(self, image_url):
        """Valide la qualité d'une image (version simplifiée)"""
        try:
            # Validation simple: essayer juste de télécharger les headers
            response = requests.head(image_url, headers=self.headers, timeout=3)
            
            # Si HEAD ne fonctionne pas, essayer GET avec limite
            if response.status_code != 200:
                response = requests.get(image_url, stream=True, timeout=3, headers=self.headers)
                response.raise_for_status()
            
            # Vérifier le type de contenu
            content_type = response.headers.get('content-type', '').lower()
            if 'image' not in content_type:
                self.logger.debug(f"Image rejetée: type non-image - {content_type}")
                return False
            
            # Accepter toutes les images pour l'instant (validation plus souple)
            self.logger.debug(f"Image acceptée: {image_url}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Erreur validation image {image_url}: {e}")
            # En cas d'erreur, accepter l'image quand même
            return True
    
    def _search_discogs(self, artist, album, year=None):
        """Recherche via l'API Discogs (mode public)"""
        results = []
        
        try:
            # Construire la requête
            query_parts = [artist, album]
            if year:
                query_parts.append(year)
            
            query = ' '.join(query_parts)
            
            search_url = f"{self.discogs_base}/database/search"
            
            # Paramètres de recherche
            params = {
                'q': query,
                'type': 'release',
                'per_page': 10,
                'page': 1
            }
            
            # Headers spéciaux pour Discogs (User-Agent obligatoire)
            headers = {
                'User-Agent': 'Nonotags/1.0 +https://github.com/Rono40230/Nonotags',
                'Accept': 'application/vnd.discogs.v2.discogs+json'
            }
            
            # Vérifier si on a un token configuré (optionnel)
            discogs_token = self.config.get('discogs_token', None)
            if discogs_token:
                headers['Authorization'] = f'Discogs token={discogs_token}'
                print("🔑 Utilisation token Discogs configuré")
            else:
                print("🌐 Utilisation API Discogs publique")
            
            response = requests.get(search_url, params=params, headers=headers, timeout=self.timeout)
            
            # Gérer les erreurs spécifiques
            if response.status_code == 401:
                # Essayer sans token si l'autorisation échoue
                if 'Authorization' in headers:
                    print("❌ Token invalide, tentative sans token...")
                    del headers['Authorization']
                    response = requests.get(search_url, params=params, headers=headers, timeout=self.timeout)
                
                if response.status_code == 401:
                    self.logger.warning("Accès Discogs non autorisé - API peut-être restreinte")
                    return results
            elif response.status_code == 403:
                self.logger.warning("Accès Discogs refusé - quota ou restrictions")
                return results
            elif response.status_code == 429:
                self.logger.warning("Limite de taux Discogs atteinte")
                time.sleep(2)
                return results
            
            response.raise_for_status()
            
            data = response.json()
            releases = data.get('results', [])
            
            print(f"📀 Discogs: {len(releases)} releases trouvées")
            self.logger.info(f"Discogs: {len(releases)} releases trouvées")
            
            for release in releases[:5]:  # Limiter à 5 releases
                # Récupérer l'image de couverture
                cover_image = release.get('cover_image')
                thumb = release.get('thumb')
                
                if not cover_image or cover_image == 'null':
                    continue
                
                # Vérifier que c'est du JPG
                is_jpg = any(fmt in cover_image.lower() for fmt in ['.jpg', '.jpeg'])
                if not is_jpg:
                    self.logger.debug(f"Image Discogs ignorée: format non-JPG - {cover_image}")
                    continue
                
                # Valider la qualité de l'image
                if self._validate_image_quality(cover_image):
                    result = CoverResult(
                        url=cover_image,
                        thumbnail_url=thumb or cover_image,
                        source='Discogs',
                        format='jpeg'
                    )
                    results.append(result)
                    self.logger.debug(f"Image Discogs acceptée: {cover_image}")
                else:
                    self.logger.debug(f"Image Discogs rejetée après validation: {cover_image}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur réseau Discogs: {e}")
            print(f"❌ Erreur réseau Discogs: {e}")
        except Exception as e:
            self.logger.error(f"Erreur inattendue Discogs: {e}")
            print(f"❌ Erreur Discogs: {e}")
        
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
        
        # Trier par source (ordre de priorité)
        def sort_key(result):
            source_priority = {
                'Cover Art Archive': 0,  # Meilleure qualité, source officielle
                'iTunes': 1,            # Haute qualité, source officielle
                'Discogs': 2            # Qualité variable, parfois petites images
            }
            return source_priority.get(result.source, 3)
        
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