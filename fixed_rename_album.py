    def rename_album_fixed(self, album_path: str) -> AlbumRenamingResult:
        """
        Version corrigée de rename_album sans les validators défaillants.
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Début du renommage de l'album : {album_path}")
            
            # Mise à jour du statut
            self.state_manager.update_album_processing_status(album_path, "renaming_files")
            
            # Validation basique du dossier
            validation_result = self.file_validator.validate_directory(album_path)
            if not validation_result.is_valid:
                return AlbumRenamingResult(
                    album_path=album_path,
                    files_renamed=0,
                    folder_renamed=False,
                    total_files=0,
                    file_results=[],
                    folder_result=None,
                    processing_time=time.time() - start_time,
                    errors=[f"Dossier invalide : {', '.join(validation_result.errors)}"],
                    warnings=validation_result.warnings
                )
            
            # Recherche des fichiers MP3
            album_dir = Path(album_path)
            mp3_files = []
            for pattern in ['*.mp3', '*.MP3', '*.Mp3', '*.mP3']:
                mp3_files.extend(album_dir.glob(pattern))
            mp3_files = list(set(mp3_files))
            
            # Collecte des métadonnées pour l'album (du premier fichier)
            album_metadata = {}
            if mp3_files and MUTAGEN_AVAILABLE:
                try:
                    audio_file = MP3(str(mp3_files[0]))
                    if audio_file and audio_file.tags:
                        tags = audio_file.tags
                        if 'TALB' in tags:
                            album_metadata['album'] = str(tags['TALB'])
                        if 'TYER' in tags:
                            album_metadata['year'] = str(tags['TYER'])
                        elif 'TDRC' in tags:
                            album_metadata['year'] = str(tags['TDRC'])
                except Exception as e:
                    self.honest_logger.warning(f"Erreur extraction métadonnées album: {e}")
            
            # Renommage des fichiers
            file_results = []
            files_renamed = 0
            current_album_path = album_path
            
            for mp3_file in mp3_files:
                # Validation basique
                file_validation = self.file_validator.validate_mp3_file(str(mp3_file))
                if file_validation.is_valid:
                    # Extraction métadonnées directe
                    metadata = {}
                    try:
                        if MUTAGEN_AVAILABLE:
                            audio_file = MP3(str(mp3_file))
                            if audio_file and audio_file.tags:
                                tags = audio_file.tags
                                # Numéro de piste
                                if 'TRCK' in tags:
                                    track = str(tags['TRCK'])
                                    if '/' in track:
                                        track = track.split('/')[0]
                                    metadata['track_number'] = track
                                # Titre
                                if 'TIT2' in tags:
                                    metadata['title'] = str(tags['TIT2'])
                    except Exception as e:
                        self.honest_logger.warning(f"Erreur extraction métadonnées {mp3_file}: {e}")
                    
                    # Utilisation des métadonnées ou valeurs par défaut
                    if not metadata:
                        metadata = {
                            'track_number': '01',
                            'title': Path(mp3_file).stem
                        }
                    
                    result = self.rename_file(str(mp3_file), metadata)
                    file_results.append(result)
                    if result.renamed:
                        files_renamed += 1
                else:
                    # Fichier invalide
                    result = RenamingResult(
                        original_path=str(mp3_file),
                        new_path=str(mp3_file),
                        renamed=False,
                        rules_applied=[],
                        warnings=[],
                        error="Fichier MP3 invalide"
                    )
                    file_results.append(result)
            
            # Renommage du dossier (optionnel)
            folder_result = None
            folder_renamed = False
            if album_metadata and self.config.get('rename_folders', True):
                try:
                    folder_result = self.rename_folder(current_album_path, album_metadata)
                    if folder_result.renamed:
                        folder_renamed = True
                        current_album_path = folder_result.new_path
                except Exception as e:
                    self.honest_logger.warning(f"Erreur renommage dossier: {e}")
            
            processing_time = time.time() - start_time
            
            # Log des résultats
            self.logger.info(
                f"Renommage terminé en {processing_time:.2f}s: "
                f"{files_renamed}/{len(mp3_files)} fichiers, "
                f"dossier: {'Oui' if folder_renamed else 'Non'}"
            )
            
            # Mise à jour du statut
            self.state_manager.update_album_processing_status(current_album_path, "file_renaming_completed")
            
            # Enregistrement en base
            try:
                self.db_manager.add_import_history(
                    folder_path=current_album_path,
                    import_type="file_renaming",
                    status="completed" if files_renamed > 0 else "no_changes",
                    files_processed=len(mp3_files),
                    processing_time=processing_time
                )
            except Exception as e:
                self.honest_logger.warning(f"Erreur enregistrement base: {e}")
            
            return AlbumRenamingResult(
                album_path=current_album_path,
                files_renamed=files_renamed,
                folder_renamed=folder_renamed,
                total_files=len(mp3_files),
                file_results=file_results,
                folder_result=folder_result,
                processing_time=processing_time,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            error_msg = f"Erreur lors du renommage de l'album {album_path} : {str(e)}"
            self.logger.error(error_msg)
            self.honest_logger.error(error_msg)
            
            return AlbumRenamingResult(
                album_path=album_path,
                files_renamed=0,
                folder_renamed=False,
                total_files=0,
                file_results=[],
                folder_result=None,
                processing_time=time.time() - start_time,
                errors=[error_msg],
                warnings=[]
            )
