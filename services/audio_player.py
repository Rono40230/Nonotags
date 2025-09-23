"""
Service de lecture audio pour l'application Nonotags
Utilise GStreamer pour la lecture audio avec support multi-formats
"""

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gst, GLib
import os
from enum import Enum
from support.logger import AppLogger


class PlayerState(Enum):
    """États du lecteur audio"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    ERROR = "error"


class AudioPlayer:
    """Service de lecture audio avec GStreamer"""
    
    def __init__(self):
        """Initialise le lecteur audio"""
        self.logger = AppLogger()
        
        # Initialiser GStreamer
        Gst.init(None)
        
        # Créer le pipeline
        self.pipeline = Gst.Pipeline.new("audio-player")
        
        # Éléments du pipeline
        self.source = Gst.ElementFactory.make("filesrc", "source")
        self.decoder = Gst.ElementFactory.make("decodebin", "decoder")
        self.converter = Gst.ElementFactory.make("audioconvert", "converter")
        self.resampler = Gst.ElementFactory.make("audioresample", "resampler")
        self.sink = Gst.ElementFactory.make("autoaudiosink", "sink")
        
        if not all([self.source, self.decoder, self.converter, self.resampler, self.sink]):
            self.logger.error("Impossible de créer les éléments GStreamer")
            raise RuntimeError("Éléments GStreamer manquants")
        
        # Ajouter les éléments au pipeline
        self.pipeline.add(self.source)
        self.pipeline.add(self.decoder)
        self.pipeline.add(self.converter)
        self.pipeline.add(self.resampler)
        self.pipeline.add(self.sink)
        
        # Lier les éléments
        self.source.link(self.decoder)
        self.converter.link(self.resampler)
        self.resampler.link(self.sink)
        
        # Connecter le signal du décodeur
        self.decoder.connect("pad-added", self.on_decoder_pad_added)
        
        # Bus pour les messages
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_bus_message)
        
        # État du lecteur
        self.state = PlayerState.STOPPED
        self.current_file = None
        self.duration = 0
        self.position = 0
        
        # Callbacks externes
        self.on_state_changed = None
        self.on_position_changed = None
        self.on_duration_changed = None
        self.on_error_occurred = None
        
        self.logger.info("AudioPlayer initialisé avec succès")
    
    def on_decoder_pad_added(self, decoder, pad):
        """Callback pour connecter le décodeur au convertisseur"""
        sink_pad = self.converter.get_static_pad("sink")
        if not sink_pad.is_linked():
            pad.link(sink_pad)
    
    def on_bus_message(self, bus, message):
        """Traite les messages du bus GStreamer"""
        msg_type = message.type
        
        if msg_type == Gst.MessageType.EOS:
            # Fin du fichier
            self.stop()
            self.logger.debug("Fin de lecture atteinte")
            
        elif msg_type == Gst.MessageType.ERROR:
            # Erreur de lecture
            err, debug = message.parse_error()
            self.logger.error(f"Erreur audio: {err}, Debug: {debug}")
            self.state = PlayerState.ERROR
            if self.on_error_occurred:
                self.on_error_occurred(str(err))
                
        elif msg_type == Gst.MessageType.STATE_CHANGED:
            # Changement d'état
            if message.src == self.pipeline:
                old_state, new_state, pending_state = message.parse_state_changed()
                self._update_state_from_gst(new_state)
        
        return True
    
    def _update_state_from_gst(self, gst_state):
        """Met à jour l'état interne basé sur l'état GStreamer"""
        if gst_state == Gst.State.PLAYING:
            self.state = PlayerState.PLAYING
        elif gst_state == Gst.State.PAUSED:
            self.state = PlayerState.PAUSED
        elif gst_state == Gst.State.NULL or gst_state == Gst.State.READY:
            self.state = PlayerState.STOPPED
        
        if self.on_state_changed:
            self.on_state_changed(self.state)
    
    def load_file(self, file_path):
        """Charge un fichier audio"""
        if not os.path.exists(file_path):
            self.logger.error(f"Fichier audio introuvable: {file_path}")
            return False
        
        # Formats supportés
        supported_formats = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext not in supported_formats:
            self.logger.warning(f"Format non supporté: {ext}")
            return False
        
        try:
            # Arrêter la lecture en cours
            self.stop()
            
            # Configurer la source
            file_uri = f"file://{os.path.abspath(file_path)}"
            self.source.set_property("location", file_path)
            
            self.current_file = file_path
            self.logger.info(f"Fichier chargé: {os.path.basename(file_path)}")
            
            # Ne pas interroger la durée immédiatement, attendre la lecture
            # self._query_duration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement: {e}")
            return False
    
    def play(self):
        """Lance la lecture"""
        if not self.current_file:
            self.logger.warning("Aucun fichier chargé")
            return False
        
        try:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.logger.debug("Lecture lancée")
            
            # Obtenir la durée après démarrage (avec délai)
            from gi.repository import GLib
            GLib.timeout_add(1000, self._delayed_query_duration)  # 1 seconde après démarrage
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture: {e}")
            return False
    
    def pause(self):
        """Met en pause la lecture"""
        try:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.logger.debug("Lecture en pause")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la pause: {e}")
            return False
    
    def stop(self):
        """Arrête la lecture"""
        try:
            self.pipeline.set_state(Gst.State.NULL)
            self.position = 0
            self.logger.debug("Lecture arrêtée")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt: {e}")
            return False
    
    def seek(self, position_seconds):
        """Se déplace à une position donnée (en secondes)"""
        if not self.current_file:
            return False
        
        try:
            position_ns = position_seconds * Gst.SECOND
            self.pipeline.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                position_ns
            )
            self.position = position_seconds
            self.logger.debug(f"Seek à {position_seconds}s")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du seek: {e}")
            return False
    
    def set_volume(self, volume):
        """Définit le volume (0.0 - 1.0)"""
        try:
            # Ajouter un élément volume si nécessaire
            volume_element = self.pipeline.get_by_name("volume")
            if not volume_element:
                volume_element = Gst.ElementFactory.make("volume", "volume")
                # Insérer dans le pipeline
                self.pipeline.add(volume_element)
                self.converter.unlink(self.resampler)
                self.converter.link(volume_element)
                volume_element.link(self.resampler)
            
            volume_element.set_property("volume", max(0.0, min(1.0, volume)))
            self.logger.debug(f"Volume défini à {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du réglage du volume: {e}")
            return False
    
    def get_position(self):
        """Obtient la position actuelle en secondes"""
        # Retourner 0 si pas de fichier chargé ou pipeline non prêt
        if not self.current_file or self.state == PlayerState.STOPPED:
            return 0
            
        try:
            success, position = self.pipeline.query_position(Gst.Format.TIME)
            if success and position != Gst.CLOCK_TIME_NONE:
                self.position = position / Gst.SECOND
                return self.position
            else:
                # Si la requête échoue, retourner la dernière position connue
                return self.position
        except Exception as e:
            self.logger.debug(f"Position query failed: {e}")
            # Retourner la dernière position connue au lieu de 0
            return self.position
    
    def get_duration(self):
        """Obtient la durée totale en secondes"""
        return self.duration
    
    def _query_duration(self):
        """Requête la durée du fichier"""
        try:
            # Sauvegarder l'état actuel
            current_state = self.pipeline.get_state(0)[1]
            
            # Mettre en pause pour obtenir la durée
            self.pipeline.set_state(Gst.State.PAUSED)
            
            # Attendre que l'état soit stable avec timeout
            ret, state, pending = self.pipeline.get_state(5 * Gst.SECOND)  # 5 sec timeout
            
            if ret == Gst.StateChangeReturn.SUCCESS:
                success, duration = self.pipeline.query_duration(Gst.Format.TIME)
                if success and duration != Gst.CLOCK_TIME_NONE:
                    self.duration = duration / Gst.SECOND
                    if self.on_duration_changed:
                        self.on_duration_changed(self.duration)
                    self.logger.debug(f"Durée: {self.duration}s")
            
            # Restaurer l'état précédent au lieu de forcer NULL
            if current_state != Gst.State.NULL:
                self.pipeline.set_state(current_state)
            else:
                self.pipeline.set_state(Gst.State.NULL)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la requête de durée: {e}")
            self.duration = 0
    
    def _delayed_query_duration(self):
        """Interroge la durée avec délai après démarrage de la lecture"""
        if self.current_file and self.state == PlayerState.PLAYING:
            try:
                success, duration = self.pipeline.query_duration(Gst.Format.TIME)
                if success and duration != Gst.CLOCK_TIME_NONE:
                    self.duration = duration / Gst.SECOND
                    if self.on_duration_changed:
                        self.on_duration_changed(self.duration)
                    self.logger.info(f"Durée obtenue: {self.duration}s")
                else:
                    self.logger.warning("Impossible d'obtenir la durée")
            except Exception as e:
                self.logger.error(f"Erreur requête durée delayed: {e}")
        return False  # Ne pas répéter le timeout
    
    def get_state(self):
        """Retourne l'état actuel du lecteur"""
        return self.state
    
    def is_playing(self):
        """Vérifie si le lecteur est en train de jouer"""
        return self.state == PlayerState.PLAYING
    
    def is_paused(self):
        """Vérifie si le lecteur est en pause"""
        return self.state == PlayerState.PAUSED
    
    def is_stopped(self):
        """Vérifie si le lecteur est arrêté"""
        return self.state == PlayerState.STOPPED
    
    def get_current_file(self):
        """Retourne le fichier actuellement chargé"""
        return self.current_file
    
    def get_supported_formats(self):
        """Retourne la liste des formats supportés"""
        return ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.stop()
            self.bus.remove_signal_watch()
            self.pipeline = None
            self.logger.info("AudioPlayer nettoyé")
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage: {e}")