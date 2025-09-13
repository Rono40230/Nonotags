#!/usr/bin/env python3
"""
Script de démonstration pour le Module 6 - Tag Synchronizer
Finalisation et synchronisation des métadonnées MP3
"""

import sys
import os
import time
from pathlib import Path

# Ajout du chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tag_synchronizer import TagSynchronizer, SynchronizationAction, CoverAssociationResult
from support.logger import AppLogger
from support.config_manager import ConfigManager

def create_demo_environment():
    """Crée un environnement de démonstration avec fichiers MP3 et pochettes."""
    demo_dir = Path("demo_tag_sync")
    demo_dir.mkdir(exist_ok=True)
    
    # Création d'un album de démonstration
    album_dir = demo_dir / "Album_Demo"
    album_dir.mkdir(exist_ok=True)
    
    print(f"📁 Création de l'environnement de démonstration dans : {album_dir}")
    
    # Création de fichiers MP3 de test (headers MP3 valides minimaux)
    mp3_files = [
        "01 - Première Chanson.mp3",
        "02 - Deuxième Titre.mp3", 
        "03 - Troisième Morceau.mp3"
    ]
    
    for mp3_file in mp3_files:
        mp3_path = album_dir / mp3_file
        with open(mp3_path, 'wb') as f:
            # Header MP3 minimal valide
            f.write(b'\xff\xfb\x90\x00')  # Sync word + layer info
            f.write(b'0' * 2000)  # Données audio factices
        print(f"   ✅ Fichier MP3 créé : {mp3_file}")
    
    # Création d'une pochette de test
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Création d'une image de pochette 500x500
        img = Image.new('RGB', (500, 500), color='#2E4057')
        draw = ImageDraw.Draw(img)
        
        # Ajout de texte sur la pochette
        try:
            # Essayer d'utiliser une police système
            font = ImageFont.truetype("DejaVuSans.ttf", 40)
        except:
            # Fallback vers la police par défaut
            font = ImageFont.load_default()
        
        # Dessiner le titre de l'album
        draw.text((50, 200), "ALBUM DEMO", fill='white', font=font)
        draw.text((50, 250), "Nonotags Test", fill='#FFD700', font=font)
        
        # Dessiner un cadre décoratif
        for i in range(5):
            draw.rectangle([i, i, 499-i, 499-i], outline='#FFD700')
        
        # Sauvegarder la pochette
        cover_path = album_dir / "cover.jpg"
        img.save(cover_path, 'JPEG', quality=95)
        print(f"   🎨 Pochette créée : cover.jpg (500x500)")
        
    except ImportError:
        # Fallback sans PIL
        cover_path = album_dir / "cover.jpg"
        # Créer un fichier JPEG minimal valide
        jpeg_header = bytes.fromhex('FFD8FFE000104A464946000101010060006000FFDB004300080606070605080707070909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C231C1C2837292C30313434341F27393D38323C2E333432FFDB0043010909090C0B0C180D0D1832211C213232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232FFC00011080064006403012200021101031101FFC4001F0000010501010101010100000000000000000102030405060708090A0BFFC400B5100002010303020403050504040000017D01020300041105122131410613516107227114328191A1082342B1C11552D1F02433627282090A161718191A25262728292A3435363738393A434445464748494A535455565758595A636465666768696A737475767778797A838485868788898A92939495969798999AA2A3A4A5A6A7A8A9AAB2B3B4B5B6B7B8B9BAC2C3C4C5C6C7C8C9CAD2D3D4D5D6D7D8D9DAE1E2E3E4E5E6E7E8E9EAF1F2F3F4F5F6F7F8F9FAFFC4001F0100030101010101010101010000000000000102030405060708090A0BFFC400B51100020102040403040705040400010277000102031104052131061241510761711322328108144291A1B1C109233352F0156272D10A162434E125F11718191A262728292A35363738393A434445464748494A535455565758595A636465666768696A737475767778797A82838485868788898A92939495969798999AA2A3A4A5A6A7A8A9AAB2B3B4B5B6B7B8B9BAC2C3C4C5C6C7C8C9CAD2D3D4D5D6D7D8D9DAE2E3E4E5E6E7E8E9EAF2F3F4F5F6F7F8F9FAFFDA000C03010002110311003F00')
        
        with open(cover_path, 'wb') as f:
            f.write(jpeg_header)
            f.write(b'\xFF' * 1000)  # Données d'image factices
            f.write(b'\xFF\xD9')  # Marqueur de fin JPEG
        
        print(f"   🎨 Pochette basique créée : cover.jpg")
    
    return album_dir

def demonstrate_file_synchronization():
    """Démontre la synchronisation d'un fichier individuel."""
    print("\n" + "="*60)
    print("🔄 DÉMONSTRATION - SYNCHRONISATION DE FICHIER INDIVIDUEL")
    print("="*60)
    
    try:
        # Création de l'environnement
        album_dir = create_demo_environment()
        
        # Initialisation du synchronizer
        print("\n📚 Initialisation du TagSynchronizer...")
        synchronizer = TagSynchronizer()
        
        # Sélection d'un fichier MP3
        mp3_files = list(album_dir.glob("*.mp3"))
        if not mp3_files:
            print("❌ Aucun fichier MP3 trouvé")
            return
        
        test_file = mp3_files[0]
        print(f"🎵 Fichier sélectionné : {test_file.name}")
        
        # Métadonnées de test
        metadata = {
            'TIT2': 'Chanson de Démonstration',
            'TPE1': 'Artiste Test',
            'TALB': 'Album Demo Nonotags',
            'TYER': '2024',
            'TCON': 'Démonstration',
            'TRCK': '1/3'
        }
        
        print(f"\n📝 Métadonnées à appliquer :")
        for key, value in metadata.items():
            print(f"   • {key}: {value}")
        
        # Synchronisation
        print(f"\n🔄 Synchronisation en cours...")
        start_time = time.time()
        
        result = synchronizer.synchronize_file(str(test_file), metadata)
        
        processing_time = time.time() - start_time
        
        # Affichage des résultats
        print(f"\n📊 RÉSULTATS DE LA SYNCHRONISATION :")
        print(f"   • Fichier : {result.file_path}")
        print(f"   • Pochette associée : {'✅' if result.cover_associated else '❌'}")
        print(f"   • Tags mis à jour : {'✅' if result.tags_updated else '❌'}")
        print(f"   • Temps de traitement : {result.processing_time:.3f}s")
        
        if result.cover_result:
            print(f"   • Résultat pochette : {result.cover_result.value}")
        
        if result.actions_performed:
            print(f"   • Actions effectuées :")
            for action in result.actions_performed:
                print(f"     - {action.value}")
        
        if result.warnings:
            print(f"   • ⚠️  Avertissements :")
            for warning in result.warnings:
                print(f"     - {warning}")
        
        if result.error:
            print(f"   • ❌ Erreur : {result.error}")
        
        print(f"\n✅ Synchronisation terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration : {e}")

def demonstrate_album_synchronization():
    """Démontre la synchronisation complète d'un album."""
    print("\n" + "="*60)
    print("🎼 DÉMONSTRATION - SYNCHRONISATION COMPLÈTE D'ALBUM")
    print("="*60)
    
    try:
        # Création de l'environnement
        album_dir = create_demo_environment()
        
        # Initialisation du synchronizer
        print("\n📚 Initialisation du TagSynchronizer...")
        synchronizer = TagSynchronizer()
        
        print(f"📁 Album à synchroniser : {album_dir}")
        
        # Compter les fichiers MP3
        mp3_files = list(album_dir.glob("*.mp3"))
        print(f"🎵 Fichiers MP3 trouvés : {len(mp3_files)}")
        
        # Vérifier la présence de pochette
        covers = list(album_dir.glob("cover.*"))
        print(f"🎨 Pochettes trouvées : {len(covers)}")
        
        # Synchronisation complète
        print(f"\n🔄 Synchronisation complète en cours...")
        start_time = time.time()
        
        result = synchronizer.synchronize_album(str(album_dir), apply_metadata=True)
        
        processing_time = time.time() - start_time
        
        # Affichage des résultats globaux
        print(f"\n📊 RÉSULTATS DE LA SYNCHRONISATION D'ALBUM :")
        print(f"   • Album : {result.album_path}")
        print(f"   • Fichiers traités : {result.files_processed}/{result.total_files}")
        print(f"   • Pochettes associées : {result.covers_associated}")
        print(f"   • Tags mis à jour : {result.tags_updated}")
        print(f"   • Temps total : {result.processing_time:.3f}s")
        
        # Détails par fichier
        if result.file_results:
            print(f"\n📋 DÉTAILS PAR FICHIER :")
            for i, file_result in enumerate(result.file_results, 1):
                filename = Path(file_result.file_path).name
                cover_status = "✅" if file_result.cover_associated else "❌"
                tags_status = "✅" if file_result.tags_updated else "❌"
                
                print(f"   {i}. {filename}")
                print(f"      • Pochette : {cover_status}")
                print(f"      • Tags : {tags_status}")
                print(f"      • Temps : {file_result.processing_time:.3f}s")
                
                if file_result.warnings:
                    for warning in file_result.warnings:
                        print(f"      • ⚠️  {warning}")
        
        # Avertissements globaux
        if result.warnings:
            print(f"\n⚠️  AVERTISSEMENTS GLOBAUX :")
            for warning in result.warnings:
                print(f"   • {warning}")
        
        # Erreurs
        if result.errors:
            print(f"\n❌ ERREURS :")
            for error in result.errors:
                print(f"   • {error}")
        
        print(f"\n✅ Synchronisation d'album terminée !")
        
        # Statistiques finales
        success_rate = (result.files_processed / max(result.total_files, 1)) * 100
        print(f"\n📈 STATISTIQUES :")
        print(f"   • Taux de réussite : {success_rate:.1f}%")
        print(f"   • Pochettes par fichier : {result.covers_associated}/{result.files_processed}")
        print(f"   • Performance : {result.files_processed/max(result.processing_time, 0.001):.1f} fichiers/seconde")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration : {e}")

def demonstrate_cover_management():
    """Démontre la gestion des pochettes."""
    print("\n" + "="*60)
    print("🎨 DÉMONSTRATION - GESTION DES POCHETTES")
    print("="*60)
    
    try:
        # Création de l'environnement
        album_dir = create_demo_environment()
        
        # Initialisation du synchronizer
        print("\n📚 Initialisation du TagSynchronizer...")
        synchronizer = TagSynchronizer()
        
        # Test de recherche de pochette
        print(f"\n🔍 Recherche de pochette dans : {album_dir}")
        cover_path = synchronizer.find_cover_image(str(album_dir))
        
        if cover_path:
            print(f"✅ Pochette trouvée : {Path(cover_path).name}")
            
            # Validation de la pochette
            print(f"\n🔍 Validation de la pochette...")
            is_valid, warnings = synchronizer.validate_cover_image(cover_path)
            
            print(f"📊 VALIDATION DE LA POCHETTE :")
            print(f"   • Validité : {'✅ Valide' if is_valid else '❌ Invalide'}")
            
            if warnings:
                print(f"   • ⚠️  Avertissements :")
                for warning in warnings:
                    print(f"     - {warning}")
            else:
                print(f"   • ✅ Aucun avertissement")
            
            # Test d'association à un MP3
            mp3_files = list(album_dir.glob("*.mp3"))
            if mp3_files:
                test_file = mp3_files[0]
                print(f"\n🔗 Test d'association avec : {test_file.name}")
                
                result = synchronizer.associate_cover_to_mp3(str(test_file), cover_path)
                
                print(f"📊 RÉSULTAT DE L'ASSOCIATION :")
                print(f"   • Statut : {result.value}")
                
                status_messages = {
                    CoverAssociationResult.SUCCESS: "✅ Association réussie",
                    CoverAssociationResult.ALREADY_EXISTS: "ℹ️  Pochette déjà présente",
                    CoverAssociationResult.COVER_NOT_FOUND: "❌ Pochette introuvable",
                    CoverAssociationResult.INVALID_FORMAT: "❌ Format invalide",
                    CoverAssociationResult.SIZE_TOO_SMALL: "❌ Taille trop petite",
                    CoverAssociationResult.ERROR: "❌ Erreur d'association"
                }
                
                print(f"   • Message : {status_messages.get(result, 'Statut inconnu')}")
        else:
            print(f"❌ Aucune pochette trouvée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration : {e}")

def demonstrate_backup_restore():
    """Démontre la sauvegarde et restauration."""
    print("\n" + "="*60)
    print("💾 DÉMONSTRATION - SAUVEGARDE ET RESTAURATION")
    print("="*60)
    
    try:
        # Création de l'environnement
        album_dir = create_demo_environment()
        
        # Initialisation du synchronizer
        print("\n📚 Initialisation du TagSynchronizer...")
        synchronizer = TagSynchronizer()
        
        # Sélection d'un fichier MP3
        mp3_files = list(album_dir.glob("*.mp3"))
        if not mp3_files:
            print("❌ Aucun fichier MP3 trouvé")
            return
        
        test_file = mp3_files[0]
        print(f"🎵 Fichier de test : {test_file.name}")
        
        # Création d'une sauvegarde
        print(f"\n💾 Création de la sauvegarde...")
        backup_path = synchronizer.create_backup(str(test_file))
        
        if backup_path:
            print(f"✅ Sauvegarde créée : {Path(backup_path).name}")
            
            # Modification simulée du fichier original
            print(f"\n✏️  Simulation de modification du fichier...")
            with open(test_file, 'ab') as f:
                f.write(b'\x00' * 100)  # Ajout de données
            
            print(f"✅ Fichier modifié (taille augmentée)")
            
            # Vérification des tailles
            original_size = Path(test_file).stat().st_size
            backup_size = Path(backup_path).stat().st_size
            
            print(f"\n📊 COMPARAISON DES TAILLES :")
            print(f"   • Fichier original : {original_size} bytes")
            print(f"   • Sauvegarde : {backup_size} bytes")
            print(f"   • Différence : {original_size - backup_size} bytes")
            
            # Restauration depuis la sauvegarde
            print(f"\n🔄 Restauration depuis la sauvegarde...")
            restore_success = synchronizer.restore_from_backup(backup_path, str(test_file))
            
            if restore_success:
                print(f"✅ Restauration réussie")
                
                # Vérification de la restauration
                restored_size = Path(test_file).stat().st_size
                print(f"📊 VÉRIFICATION DE LA RESTAURATION :")
                print(f"   • Taille après restauration : {restored_size} bytes")
                print(f"   • Restauration correcte : {'✅' if restored_size == backup_size else '❌'}")
            else:
                print(f"❌ Échec de la restauration")
            
            # Nettoyage de la sauvegarde
            try:
                Path(backup_path).unlink()
                print(f"🗑️  Sauvegarde nettoyée")
            except:
                pass
        else:
            print(f"❌ Échec de la création de sauvegarde")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration : {e}")

def main():
    """Fonction principale de démonstration."""
    print("🎵" + "="*58 + "🎵")
    print("           MODULE 6 - TAG SYNCHRONIZER DEMO")
    print("                Finalisation MP3 Nonotags")
    print("🎵" + "="*58 + "🎵")
    
    try:
        # Affichage du menu
        print("\n📋 Démonstrations disponibles :")
        print("   1. 🔄 Synchronisation de fichier individuel")
        print("   2. 🎼 Synchronisation complète d'album")
        print("   3. 🎨 Gestion des pochettes")
        print("   4. 💾 Sauvegarde et restauration")
        print("   5. 🎯 Toutes les démonstrations")
        
        # Choix interactif ou automatique
        if len(sys.argv) > 1:
            choice = sys.argv[1]
        else:
            try:
                choice = input("\n👉 Choisissez une démonstration (1-5) : ").strip()
            except (EOFError, KeyboardInterrupt):
                choice = "5"  # Par défaut, toutes les démos
        
        # Exécution des démonstrations
        if choice == "1":
            demonstrate_file_synchronization()
        elif choice == "2":
            demonstrate_album_synchronization()
        elif choice == "3":
            demonstrate_cover_management()
        elif choice == "4":
            demonstrate_backup_restore()
        elif choice == "5":
            print("\n🎯 Exécution de toutes les démonstrations...")
            demonstrate_file_synchronization()
            demonstrate_album_synchronization()
            demonstrate_cover_management()
            demonstrate_backup_restore()
        else:
            print(f"❌ Choix invalide : {choice}")
            return
        
        print(f"\n🎉 DÉMONSTRATION TERMINÉE !")
        print(f"💡 Le Module 6 - TagSynchronizer est maintenant opérationnel")
        print(f"🔗 Il peut être intégré avec les autres modules Nonotags")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration : {e}")
        raise

if __name__ == "__main__":
    main()
