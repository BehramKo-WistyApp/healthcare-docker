// Script d'initialisation MongoDB
// Exécuté automatiquement au premier démarrage du conteneur

print('========================================');
print('Initialisation de la base MongoDB');
print('========================================');

// Connexion à la base healthcare_db
db = db.getSiblingDB('healthcare_db');

// Création de l'utilisateur data_engineer avec permissions limitées
db.createUser({
  user: 'data_engineer',
  pwd: 'DataEngineer2025!',
  roles: [
    {
      role: 'readWrite',
      db: 'healthcare_db'
    }
  ]
});

print('✓ Utilisateur data_engineer créé avec succès');

// Création de la collection patients
db.createCollection('patients', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["personal_info", "medical_info", "admission_info", "administrative_info"],
      properties: {
        personal_info: {
          bsonType: "object",
          required: ["name", "age", "gender", "blood_type"]
        },
        medical_info: {
          bsonType: "object",
          required: ["condition", "medication", "test_results"]
        }
      }
    }
  }
});

print('✓ Collection patients créée avec validation de schéma');

// Création des index pour optimiser les performances
db.patients.createIndex({ "personal_info.name": 1 });
db.patients.createIndex({ "personal_info.age": 1 });
db.patients.createIndex({ "medical_info.condition": 1 });
db.patients.createIndex({ "admission_info.date_admission": 1 });
db.patients.createIndex({ "administrative_info.hospital": 1 });

// Index composé
db.patients.createIndex({ 
  "personal_info.gender": 1, 
  "personal_info.age": 1 
});

print('✓ Index créés avec succès');

// Création de la vue anonymisée pour les analystes
db.createView(
  'patients_anonymized_view',
  'patients',
  [
    {
      $project: {
        patient_id: { $toString: "$_id" },
        age_range: {
          $switch: {
            branches: [
              { case: { $lt: ["$personal_info.age", 18] }, then: "0-17" },
              { case: { $lt: ["$personal_info.age", 30] }, then: "18-29" },
              { case: { $lt: ["$personal_info.age", 50] }, then: "30-49" },
              { case: { $lt: ["$personal_info.age", 65] }, then: "50-64" }
            ],
            default: "65+"
          }
        },
        gender: "$personal_info.gender",
        blood_type: "$personal_info.blood_type",
        medical_condition: "$medical_info.condition",
        medication: "$medical_info.medication",
        admission_type: "$admission_info.admission_type",
        duration_days: "$admission_info.duration_days",
        insurance_provider: "$administrative_info.insurance_provider"
      }
    }
  ]
);

print('✓ Vue anonymisée créée pour les analystes');

print('========================================');
print('Initialisation terminée avec succès');
print('Base de données healthcare_db prête');
print('========================================');
