"""
Script principal de migration Healthcare vers MongoDB
Exécuté dans un conteneur Docker
"""

import sys
import json
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

# Import des modules locaux
from config import config
from utils import (
    setup_logging,
    download_dataset,
    load_and_clean_data,
    convert_row_to_document,
    retry_operation,
    format_duration,
    validate_dataframe
)

# Configuration du logger
logger = logging.getLogger(__name__)


class HealthcareMigration:
    """Classe principale de migration"""
    
    def __init__(self):
        """Initialisation"""
        self.client = None
        self.db = None
        self.collection = None
        self.stats = {
            'debut': datetime.now(),
            'total_lignes': 0,
            'succes': 0,
            'echecs': 0,
            'erreurs': []
        }
    
    def connect_mongodb(self):
        """Connexion à MongoDB avec retry"""
        logger.info("Connexion à MongoDB...")
        logger.info(f"URI: mongodb://{config.MONGODB_USERNAME}:***@{config.MONGODB_HOST}:{config.MONGODB_PORT}/{config.MONGODB_DATABASE}")
        
        def _connect():
            self.client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=config.MONGODB_TIMEOUT
            )
            # Test de connexion
            self.client.admin.command('ping')
            self.db = self.client[config.MONGODB_DATABASE]
            self.collection = self.db['patients']
            logger.info("✓ Connexion MongoDB établie")
        
        retry_operation(_connect, max_retries=config.MAX_RETRIES, delay=config.RETRY_DELAY)
    
    def clean_collection(self):
        """Nettoie la collection avant migration"""
        logger.info("Nettoyage de la collection...")
        result = self.collection.delete_many({})
        logger.info(f"✓ {result.deleted_count} documents supprimés")
    
    def migrate_data(self, df):
        """Migre les données vers MongoDB"""
        logger.info(f"Début de la migration de {len(df)} documents...")
        
        self.stats['total_lignes'] = len(df)
        documents_batch = []
        
        for index, row in df.iterrows():
            try:
                document = convert_row_to_document(row)
                documents_batch.append(document)
                
                # Insertion par lot
                if len(documents_batch) >= config.BATCH_SIZE:
                    self.collection.insert_many(documents_batch)
                    self.stats['succes'] += len(documents_batch)
                    
                    # Affichage de la progression
                    if self.stats['succes'] % 5000 == 0:
                        pct = (self.stats['succes'] / len(df)) * 100
                        logger.info(f"Progression : {self.stats['succes']}/{len(df)} ({pct:.1f}%)")
                    
                    documents_batch = []
                    
            except Exception as e:
                self.stats['echecs'] += 1
                self.stats['erreurs'].append({
                    'ligne': index,
                    'erreur': str(e)
                })
                logger.error(f"Erreur ligne {index} : {e}")
        
        # Insertion du dernier lot
        if documents_batch:
            self.collection.insert_many(documents_batch)
            self.stats['succes'] += len(documents_batch)
        
        self.stats['fin'] = datetime.now()
        self.stats['duree'] = (self.stats['fin'] - self.stats['debut']).total_seconds()
        
        logger.info(f"✓ Migration terminée")
        logger.info(f"  • Succès : {self.stats['succes']}")
        logger.info(f"  • Échecs : {self.stats['echecs']}")
        logger.info(f"  • Durée : {format_duration(self.stats['duree'])}")
    
    def verify_migration(self, df):
        """Vérifie l'intégrité de la migration"""
        logger.info("Vérification de l'intégrité...")
        
        verification = {
            'nb_documents_mongodb': self.collection.count_documents({}),
            'nb_lignes_csv': len(df),
            'coherence': False,
            'tests_passes': []
        }
        
        # Test 1 : Nombre de documents
        if verification['nb_documents_mongodb'] == verification['nb_lignes_csv']:
            verification['coherence'] = True
            verification['tests_passes'].append("Nombre de documents")
            logger.info(f"✓ Test 1 : Nombre cohérent ({verification['nb_documents_mongodb']})")
        else:
            logger.error(
                f"✗ Test 1 : Incohérence - "
                f"{verification['nb_documents_mongodb']} docs vs "
                f"{verification['nb_lignes_csv']} lignes"
            )
        
        # Test 2 : Échantillonnage
        echantillon = df.sample(min(100, len(df)))
        echantillons_verifies = 0
        
        for _, row in echantillon.iterrows():
            doc = self.collection.find_one({"personal_info.name": str(row['Name'])})
            if doc:
                echantillons_verifies += 1
        
        pct = (echantillons_verifies / len(echantillon)) * 100
        logger.info(f"✓ Test 2 : Échantillons - {echantillons_verifies}/{len(echantillon)} ({pct:.1f}%)")
        
        if pct >= 95:
            verification['tests_passes'].append("Échantillonnage")
        
        return verification
    
    def generate_report(self, verification):
        """Génère le rapport de migration"""
        logger.info("Génération du rapport...")
        
        rapport = {
            'migration': {
                'date': self.stats['debut'].strftime('%Y-%m-%d %H:%M:%S'),
                'duree_secondes': self.stats['duree'],
                'total_lignes': self.stats['total_lignes'],
                'succes': self.stats['succes'],
                'echecs': self.stats['echecs'],
                'taux_reussite': (self.stats['succes'] / self.stats['total_lignes'] * 100) 
                                 if self.stats['total_lignes'] > 0 else 0,
                'vitesse_docs_par_sec': self.stats['succes'] / self.stats['duree'] 
                                       if self.stats['duree'] > 0 else 0
            },
            'verification': verification,
            'base_donnees': {
                'nom': self.db.name,
                'collection': self.collection.name,
                'nb_documents': self.collection.count_documents({}),
                'nb_index': len(list(self.collection.list_indexes()))
            }
        }
        
        # Sauvegarde du rapport
        with open(config.REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=4, ensure_ascii=False, default=str)
        
        logger.info(f"✓ Rapport sauvegardé : {config.REPORT_FILE}")
        return rapport
    
    def close(self):
        """Ferme la connexion MongoDB"""
        if self.client:
            self.client.close()
            logger.info("✓ Connexion MongoDB fermée")


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("MIGRATION HEALTHCARE VERS MONGODB - VERSION DOCKER")
    print("=" * 80)
    
    try:
        # 1. Configuration du logging
        setup_logging(config.LOG_FILE, config.LOG_LEVEL)
        logger.info("Démarrage de la migration...")
        
        # 2. Affichage de la configuration
        logger.info(config.display_config())
        
        # 3. Validation de la configuration
        config.validate_config()
        
        # 4. Téléchargement du dataset (si nécessaire)
        
        if not os.path.exists(config.CSV_PATH):
            logger.error(f"✗ Dataset introuvable : {config.CSV_PATH}")
            logger.error("Veuillez télécharger le dataset manuellement depuis Kaggle")
            logger.error("https://www.kaggle.com/datasets/prasad22/healthcare-dataset")
            sys.exit(1)
        else:
            file_size = os.path.getsize(config.CSV_PATH) / (1024 * 1024)
            logger.info(f"✓ Dataset trouvé : {config.CSV_PATH} ({file_size:.2f} MB)")

        #if not os.path.exists(config.CSV_PATH):
            #logger.info("Dataset non trouvé, téléchargement en cours...")
            #download_dataset(config.KAGGLE_DATASET, config.DATA_DIR)
        #else:
            #logger.info(f"✓ Dataset trouvé : {config.CSV_PATH}")
        
        # 5. Chargement et nettoyage des données
        df = load_and_clean_data(config.CSV_PATH)
        
        # 6. Validation du DataFrame
        validation = validate_dataframe(df)
        if not validation['valid']:
            logger.error(f"Validation échouée : {validation['errors']}")
            sys.exit(1)
        
        logger.info(f"✓ Validation réussie : {validation['stats']}")
        
        # 7. Migration vers MongoDB
        migrateur = HealthcareMigration()
        
        # Connexion
        migrateur.connect_mongodb()
        
        # Nettoyage de la collection
        migrateur.clean_collection()
        
        # Migration des données
        migrateur.migrate_data(df)
        
        # Vérification de l'intégrité
        verification = migrateur.verify_migration(df)
        
        # Génération du rapport
        rapport = migrateur.generate_report(verification)
        
        # Affichage du résumé
        print("\n" + "=" * 80)
        print("RÉSUMÉ DE LA MIGRATION")
        print("=" * 80)
        print(json.dumps(rapport, indent=2, default=str))
        
        # Fermeture
        migrateur.close()
        
        print("\n✓ MIGRATION TERMINÉE AVEC SUCCÈS")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"✗ ERREUR FATALE : {e}", exc_info=True)
        print(f"\n✗ MIGRATION ÉCHOUÉE : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
