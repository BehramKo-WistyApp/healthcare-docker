"""
Fonctions utilitaires pour la migration
"""

import logging
import time
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import kagglehub

# Configuration du logger
logger = logging.getLogger(__name__)


def setup_logging(log_file: str, log_level: str = 'INFO') -> None:
    """
    Configure le système de logging
    
    Args:
        log_file: Chemin du fichier de log
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
    """
    # Créer le répertoire de logs s'il n'existe pas
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configuration du format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configuration du logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Logging configuré : {log_file}")


def download_dataset(kaggle_dataset: str, destination_dir: str) -> str:
    """
    Télécharge le dataset depuis Kaggle
    
    Args:
        kaggle_dataset: Identifiant du dataset Kaggle
        destination_dir: Répertoire de destination
        
    Returns:
        Chemin du fichier CSV téléchargé
    """
    logger.info(f"Téléchargement du dataset : {kaggle_dataset}")
    
    try:
        # Téléchargement via kagglehub
        path = kagglehub.dataset_download(kaggle_dataset)
        logger.info(f"Dataset téléchargé dans : {path}")
        
        # Recherche du fichier CSV
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        
        if not csv_files:
            raise FileNotFoundError("Aucun fichier CSV trouvé dans le dataset")
        
        source_csv = os.path.join(path, csv_files[0])
        
        # Copie vers le répertoire de destination
        os.makedirs(destination_dir, exist_ok=True)
        destination_csv = os.path.join(destination_dir, csv_files[0])
        
        # Si le fichier existe déjà, le supprimer
        if os.path.exists(destination_csv):
            os.remove(destination_csv)
        
        # Copie du fichier
        import shutil
        shutil.copy2(source_csv, destination_csv)
        
        logger.info(f"✓ Dataset copié vers : {destination_csv}")
        return destination_csv
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement : {e}")
        raise


def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Charge et nettoie le dataset
    
    Args:
        csv_path: Chemin du fichier CSV
        
    Returns:
        DataFrame nettoyé
    """
    logger.info(f"Chargement du CSV : {csv_path}")
    
    # Vérification de l'existence du fichier
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Fichier CSV introuvable : {csv_path}")
    
    # Chargement du CSV
    df = pd.read_csv(csv_path)
    logger.info(f"✓ CSV chargé : {len(df)} lignes, {len(df.columns)} colonnes")
    
    # Nettoyage
    logger.info("Nettoyage des données...")
    
    # 1. Suppression des doublons
    nb_doublons = df.duplicated().sum()
    if nb_doublons > 0:
        logger.warning(f"Suppression de {nb_doublons} doublons")
        df = df.drop_duplicates()
    
    # 2. Conversion des dates
    logger.info("Conversion des dates...")
    df['Date of Admission'] = pd.to_datetime(df['Date of Admission'])
    df['Discharge Date'] = pd.to_datetime(df['Discharge Date'])
    
    # 3. Calcul de la durée de séjour
    df['Duree_Sejour'] = (df['Discharge Date'] - df['Date of Admission']).dt.days
    
    # 4. Correction des montants négatifs
    nb_negatifs = (df['Billing Amount'] < 0).sum()
    if nb_negatifs > 0:
        logger.warning(f"Correction de {nb_negatifs} montants négatifs")
        df['Billing Amount'] = df['Billing Amount'].abs()
    
    # 5. Normalisation des noms
    df['Name'] = df['Name'].str.title()
    df['Doctor'] = df['Doctor'].str.title()
    
    logger.info(f"✓ Nettoyage terminé : {len(df)} lignes conservées")
    
    return df


def convert_row_to_document(row: pd.Series) -> Dict:
    """
    Convertit une ligne du DataFrame en document MongoDB
    
    Args:
        row: Ligne du DataFrame
        
    Returns:
        Document MongoDB
    """
    document = {
        "personal_info": {
            "name": str(row['Name']),
            "age": int(row['Age']),
            "gender": str(row['Gender']),
            "blood_type": str(row['Blood Type'])
        },
        
        "medical_info": {
            "condition": str(row['Medical Condition']),
            "medication": str(row['Medication']),
            "test_results": str(row['Test Results'])
        },
        
        "admission_info": {
            "date_admission": row['Date of Admission'],
            "date_discharge": row['Discharge Date'],
            "duration_days": int(row['Duree_Sejour']),
            "admission_type": str(row['Admission Type']),
            "room_number": int(row['Room Number'])
        },
        
        "administrative_info": {
            "doctor": str(row['Doctor']),
            "hospital": str(row['Hospital']),
            "insurance_provider": str(row['Insurance Provider']),
            "billing_amount": float(row['Billing Amount'])
        },
        
        "metadata": {
            "created_at": datetime.now(),
            "source": "kaggle_healthcare_dataset",
            "migration_version": "1.0",
            "migration_date": datetime.now().strftime('%Y-%m-%d')
        }
    }
    
    return document


def retry_operation(func, max_retries: int = 3, delay: int = 5):
    """
    Réessaie une opération en cas d'échec
    
    Args:
        func: Fonction à exécuter
        max_retries: Nombre maximum de tentatives
        delay: Délai entre les tentatives (secondes)
        
    Returns:
        Résultat de la fonction
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Tentative {attempt + 1}/{max_retries} échouée : {e}. "
                    f"Nouvelle tentative dans {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Échec après {max_retries} tentatives")
                raise


def format_duration(seconds: float) -> str:
    """
    Formate une durée en secondes en format lisible
    
    Args:
        seconds: Durée en secondes
        
    Returns:
        Durée formatée (ex: "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_size(bytes_size: int) -> str:
    """
    Formate une taille en octets en format lisible
    
    Args:
        bytes_size: Taille en octets
        
    Returns:
        Taille formatée (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def print_progress_bar(iteration: int, total: int, prefix: str = '', 
                       suffix: str = '', length: int = 50):
    """
    Affiche une barre de progression
    
    Args:
        iteration: Itération actuelle
        total: Total d'itérations
        prefix: Préfixe à afficher
        suffix: Suffixe à afficher
        length: Longueur de la barre
    """
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    
    if iteration == total:
        print()


def validate_dataframe(df: pd.DataFrame) -> Dict:
    """
    Valide le DataFrame avant migration
    
    Args:
        df: DataFrame à valider
        
    Returns:
        Dictionnaire de validation
    """
    validation = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    # Vérification des colonnes requises
    required_columns = [
        'Name', 'Age', 'Gender', 'Blood Type', 'Medical Condition',
        'Date of Admission', 'Discharge Date', 'Doctor', 'Hospital',
        'Insurance Provider', 'Billing Amount', 'Room Number',
        'Admission Type', 'Medication', 'Test Results'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation['valid'] = False
        validation['errors'].append(f"Colonnes manquantes : {missing_columns}")
    
    # Vérification des valeurs manquantes
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        validation['warnings'].append(
            f"Valeurs manquantes détectées : {null_counts[null_counts > 0].to_dict()}"
        )
    
    # Statistiques
    validation['stats'] = {
        'nb_lignes': len(df),
        'nb_colonnes': len(df.columns),
        'doublons': df.duplicated().sum(),
        'valeurs_manquantes': int(null_counts.sum())
    }
    
    return validation
