import pytest
import pandas as pd
from mongomock import MongoClient
from app.migration import HealthcareMigration  # ajuste le chemin si besoin

@pytest.fixture
def sample_df():
    return pd.read_csv("tests/fixtures/sample_data.csv")

@pytest.fixture
def mock_migrator():
    client = MongoClient()
    return HealthcareMigration(
        mongo_uri="mongomock://localhost",
        database_name="test_db",
        collection_name="test_collection"
    )

def test_nettoyer_dataframe_supprime_doublons(sample_df, mock_migrator):
    df_clean = mock_migrator.nettoyer_dataframe(sample_df)
    assert len(df_clean) == 3  # 4 lignes - 1 doublon

def test_convertir_ligne_en_document_structure(sample_df, mock_migrator):
    row = sample_df.iloc[0]
    doc = mock_migrator.convertir_ligne_en_document(row)
    assert "personal_info" in doc
    assert doc["personal_info"]["name"] == "Bobby Jackson"

def test_migrer_donnees_insere_tous_les_documents(sample_df, mock_migrator):
    stats = mock_migrator.migrer_donnees(sample_df)
    assert stats["succes"] == 3
    assert stats["echecs"] == 0