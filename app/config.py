"""
Configuration de l'application de migration
Charge les variables d'environnement et définit les paramètres
"""

import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

class Config:
    """Configuration centralisée de l'application"""
    
    # ========================================
    # CONFIGURATION MONGODB
    # ========================================
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'healthcare_db')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'data_engineer')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'DataEngineer2025!')
    
    # Construction de l'URI de connexion MongoDB
    MONGODB_URI = (
        f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@"
        f"{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"
        f"?authSource={MONGODB_DATABASE}"
    )
    
    # ========================================
    # CONFIGURATION APPLICATION
    # ========================================
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 1000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # ========================================
    # CHEMINS DE FICHIERS
    # ========================================
    DATA_DIR = '/app/data'
    LOGS_DIR = '/app/logs'
    CSV_FILENAME = 'healthcare_dataset.csv'
    CSV_PATH = os.path.join(DATA_DIR, CSV_FILENAME)
    LOG_FILE = os.path.join(LOGS_DIR, 'migration.log')
    REPORT_FILE = os.path.join(LOGS_DIR, 'rapport_migration.json')
    
    # ========================================
    # CONFIGURATION DATASET
    # ========================================
    KAGGLE_DATASET = 'prasad22/healthcare-dataset'
    
    # ========================================
    # TIMEOUTS ET RETRIES
    # ========================================
    MONGODB_TIMEOUT = 10000  # millisecondes
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # secondes
    
    @classmethod
    def display_config(cls):
        """Affiche la configuration (sans les mots de passe)"""
        config_info = f"""
        ========================================
        CONFIGURATION DE L'APPLICATION
        ========================================
        MongoDB:
          • Host: {cls.MONGODB_HOST}
          • Port: {cls.MONGODB_PORT}
          • Database: {cls.MONGODB_DATABASE}
          • Username: {cls.MONGODB_USERNAME}
          • Password: {'*' * len(cls.MONGODB_PASSWORD)}
        
        Application:
          • Batch Size: {cls.BATCH_SIZE}
          • Log Level: {cls.LOG_LEVEL}
          • Max Retries: {cls.MAX_RETRIES}
        
        Chemins:
          • Data Directory: {cls.DATA_DIR}
          • Logs Directory: {cls.LOGS_DIR}
          • CSV Path: {cls.CSV_PATH}
        
        Dataset:
          • Source: Kaggle - {cls.KAGGLE_DATASET}
        ========================================
        """
        return config_info
    
    @classmethod
    def validate_config(cls):
        """Valide que toutes les variables nécessaires sont définies"""
        required_vars = [
            'MONGODB_HOST',
            'MONGODB_PORT',
            'MONGODB_DATABASE',
            'MONGODB_USERNAME',
            'MONGODB_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(
                f"Variables d'environnement manquantes : {', '.join(missing_vars)}"
            )
        
        return True


# Instance de configuration
config = Config()
