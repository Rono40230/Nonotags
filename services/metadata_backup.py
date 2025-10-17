"""
Module de sauvegarde et restauration des métadonnées originales
Permet d'annuler les corrections automatiques appliquées lors de l'import
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3NoHeaderError

class MetadataBackup:
    """Gestionnaire de sauvegarde et restauration des métadonnées originales"""
    
    def __init__(self, db_path="database/metadata_backup.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données de sauvegarde"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS original_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                original_metadata TEXT NOT NULL,
                backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                album_path TEXT,
                UNIQUE(file_path, file_hash)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_file_hash(self, file_path):
        """Calcule un hash du fichier pour détecter les changements"""
        try:
            with open(file_path, 'rb') as f:
                # Lire seulement les premiers 64KB pour la performance
                content = f.read(65536)
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            print(f"❌ Erreur calcul hash {file_path}: {e}")
            return None
    
    def _extract_metadata(self, file_path):
        """Extrait les métadonnées originales d'un fichier audio"""
        try:
            metadata = {
                'file_path': file_path,
                'title': '',
                'artist': '',
                'album': '',
                'year': '',
                'genre': '',
                'track_number': '',
                'albumartist': ''
            }
            
            if file_path.lower().endswith('.mp3'):
                try:
                    audio = MP3(file_path)
                    if audio.tags:
                        metadata['title'] = str(audio.tags.get('TIT2', [''])[0])
                        metadata['artist'] = str(audio.tags.get('TPE1', [''])[0])
                        metadata['album'] = str(audio.tags.get('TALB', [''])[0])
                        metadata['year'] = str(audio.tags.get('TDRC', [''])[0])
                        metadata['genre'] = str(audio.tags.get('TCON', [''])[0])
                        metadata['track_number'] = str(audio.tags.get('TRCK', [''])[0])
                        metadata['albumartist'] = str(audio.tags.get('TPE2', [''])[0])
                except ID3NoHeaderError:
                    pass
                    
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                metadata['title'] = audio.get('TITLE', [''])[0]
                metadata['artist'] = audio.get('ARTIST', [''])[0]
                metadata['album'] = audio.get('ALBUM', [''])[0]
                metadata['year'] = audio.get('DATE', [''])[0]
                metadata['genre'] = audio.get('GENRE', [''])[0]
                metadata['track_number'] = audio.get('TRACKNUMBER', [''])[0]
                metadata['albumartist'] = audio.get('ALBUMARTIST', [''])[0]
                
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                audio = MP4(file_path)
                metadata['title'] = audio.get('\xa9nam', [''])[0] if audio.get('\xa9nam') else ''
                metadata['artist'] = audio.get('\xa9ART', [''])[0] if audio.get('\xa9ART') else ''
                metadata['album'] = audio.get('\xa9alb', [''])[0] if audio.get('\xa9alb') else ''
                metadata['year'] = audio.get('\xa9day', [''])[0] if audio.get('\xa9day') else ''
                metadata['genre'] = audio.get('\xa9gen', [''])[0] if audio.get('\xa9gen') else ''
                metadata['albumartist'] = audio.get('aART', [''])[0] if audio.get('aART') else ''
                
                # Numéro de piste (format spécial MP4)
                track_info = audio.get('trkn', [(0, 0)])[0]
                metadata['track_number'] = str(track_info[0]) if track_info[0] > 0 else ''
            
            return metadata
            
        except Exception as e:
            print(f"❌ Erreur extraction métadonnées {file_path}: {e}")
            return None
    
    def backup_file_metadata(self, file_path, album_path=None):
        """Sauvegarde les métadonnées originales d'un fichier"""
        try:
            if not os.path.exists(file_path):
                print(f"Fichier introuvable pour sauvegarde: {file_path}")
                return False
            
            # Calculer le hash du fichier
            file_hash = self._get_file_hash(file_path)
            if not file_hash:
                return False
            
            # Extraire les métadonnées
            metadata = self._extract_metadata(file_path)
            if not metadata:
                return False
            
            # Sauvegarder en base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO original_metadata 
                (file_path, file_hash, original_metadata, album_path)
                VALUES (?, ?, ?, ?)
            ''', (file_path, file_hash, json.dumps(metadata), album_path))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Métadonnées sauvegardées: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"Erreur sauvegarde métadonnées {file_path}: {e}")
            return False
    
    def backup_album_metadata(self, album_path):
        """Sauvegarde les métadonnées de tous les fichiers d'un album"""
        try:
            if not os.path.exists(album_path):
                print(f"Dossier album introuvable: {album_path}")
                return False
            
            backup_count = 0
            audio_extensions = ('.mp3', '.flac', '.m4a', '.mp4')
            
            for filename in os.listdir(album_path):
                if filename.lower().endswith(audio_extensions):
                    file_path = os.path.join(album_path, filename)
                    if self.backup_file_metadata(file_path, album_path):
                        backup_count += 1
            
            print(f"✅ {backup_count} fichiers sauvegardés pour l'album {os.path.basename(album_path)}")
            return backup_count > 0
            
        except Exception as e:
            print(f"Erreur sauvegarde album {album_path}: {e}")
            return False
    
    def has_backup(self, file_path):
        """Vérifie si une sauvegarde existe pour ce fichier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM original_metadata WHERE file_path = ?
            ''', (file_path,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            print(f"Erreur vérification sauvegarde {file_path}: {e}")
            return False
    
    def restore_file_metadata(self, file_path):
        """Restaure les métadonnées originales d'un fichier"""
        try:
            if not os.path.exists(file_path):
                print(f"Fichier introuvable pour restauration: {file_path}")
                return False
            
            # Récupérer la sauvegarde
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT original_metadata FROM original_metadata 
                WHERE file_path = ? ORDER BY backup_date DESC LIMIT 1
            ''', (file_path,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print(f"Aucune sauvegarde trouvée pour: {file_path}")
                return False
            
            # Restaurer les métadonnées
            original_metadata = json.loads(result[0])
            success = self._write_metadata_to_file(file_path, original_metadata)
            
            if success:
                print(f"✅ Métadonnées restaurées: {os.path.basename(file_path)}")
            
            return success
            
        except Exception as e:
            print(f"Erreur restauration métadonnées {file_path}: {e}")
            return False
    
    def _write_metadata_to_file(self, file_path, metadata):
        """Écrit les métadonnées dans un fichier audio"""
        try:
            if file_path.lower().endswith('.mp3'):
                from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, TDRC, TCON, TRCK, ID3NoHeaderError
                try:
                    audio = ID3(file_path)
                except ID3NoHeaderError:
                    audio = ID3()
                
                if metadata['title']:
                    audio['TIT2'] = TIT2(encoding=3, text=metadata['title'])
                if metadata['artist']:
                    audio['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
                if metadata['albumartist']:
                    audio['TPE2'] = TPE2(encoding=3, text=metadata['albumartist'])
                if metadata['album']:
                    audio['TALB'] = TALB(encoding=3, text=metadata['album'])
                if metadata['year']:
                    audio['TDRC'] = TDRC(encoding=3, text=metadata['year'])
                if metadata['genre']:
                    audio['TCON'] = TCON(encoding=3, text=metadata['genre'])
                if metadata['track_number']:
                    audio['TRCK'] = TRCK(encoding=3, text=metadata['track_number'])
                
                audio.save(file_path)
                
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                
                if metadata['title']:
                    audio['TITLE'] = metadata['title']
                if metadata['artist']:
                    audio['ARTIST'] = metadata['artist']
                if metadata['albumartist']:
                    audio['ALBUMARTIST'] = metadata['albumartist']
                if metadata['album']:
                    audio['ALBUM'] = metadata['album']
                if metadata['year']:
                    audio['DATE'] = metadata['year']
                if metadata['genre']:
                    audio['GENRE'] = metadata['genre']
                if metadata['track_number']:
                    audio['TRACKNUMBER'] = metadata['track_number']
                
                audio.save()
                
            elif file_path.lower().endswith(('.m4a', '.mp4')):
                audio = MP4(file_path)
                
                if metadata['title']:
                    audio['\xa9nam'] = metadata['title']
                if metadata['artist']:
                    audio['\xa9ART'] = metadata['artist']
                if metadata['albumartist']:
                    audio['aART'] = metadata['albumartist']
                if metadata['album']:
                    audio['\xa9alb'] = metadata['album']
                if metadata['year']:
                    audio['\xa9day'] = metadata['year']
                if metadata['genre']:
                    audio['\xa9gen'] = metadata['genre']
                if metadata['track_number']:
                    track_num = int(metadata['track_number']) if metadata['track_number'].isdigit() else 0
                    if track_num > 0:
                        audio['trkn'] = [(track_num, 0)]
                
                audio.save()
            
            return True
            
        except Exception as e:
            print(f"Erreur écriture métadonnées {file_path}: {e}")
            return False
    
    def restore_album_metadata(self, album_path):
        """Restaure les métadonnées de tous les fichiers d'un album"""
        try:
            if not os.path.exists(album_path):
                print(f"Dossier album introuvable: {album_path}")
                return False
            
            restored_count = 0
            audio_extensions = ('.mp3', '.flac', '.m4a', '.mp4')
            
            for filename in os.listdir(album_path):
                if filename.lower().endswith(audio_extensions):
                    file_path = os.path.join(album_path, filename)
                    if self.restore_file_metadata(file_path):
                        restored_count += 1
            
            print(f"✅ {restored_count} fichiers restaurés pour l'album {os.path.basename(album_path)}")
            return restored_count > 0
            
        except Exception as e:
            print(f"Erreur restauration album {album_path}: {e}")
            return False
    
    def get_backup_info(self, file_path):
        """Récupère les informations de sauvegarde d'un fichier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT backup_date, original_metadata FROM original_metadata 
                WHERE file_path = ? ORDER BY backup_date DESC LIMIT 1
            ''', (file_path,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'backup_date': result[0],
                    'original_metadata': json.loads(result[1])
                }
            
            return None
            
        except Exception as e:
            print(f"Erreur récupération info sauvegarde {file_path}: {e}")
            return None
    
    def cleanup_old_backups(self, days_old=30):
        """Nettoie les anciennes sauvegardes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM original_metadata 
                WHERE backup_date < datetime('now', '-{} days')
            '''.format(days_old))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"🧹 {deleted_count} anciennes sauvegardes supprimées")
            return deleted_count
            
        except Exception as e:
            print(f"Erreur nettoyage sauvegardes: {e}")
            return 0

# Instance globale
metadata_backup = MetadataBackup()