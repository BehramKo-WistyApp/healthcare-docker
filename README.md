# Medical Data Migration to MongoDB

## Project Context

This project was carried out as part of a mission at **Health Data SoluTech Engineering**, a company specializing in data management and analytics solutions. The objective was to migrate a dataset of sensitive medical data from a relational system to a scalable Big Data solution based on MongoDB, with a secure cloud architecture on AWS.

The client, a healthcare facility, was facing scalability issues with their current system (limited to ~50,000 patients) and required a solution capable of handling over one million patients without major refactoring.

## Project Objectives

- Automated migration of **54,966 medical records** to MongoDB
- Complete containerization with Docker to ensure portability and scalability
- Secure and highly available AWS cloud architecture
- Strict compliance with **GDPR** and **HIPAA** regulations
- Performance optimization (99%+ reduction in query times)
- Implementation of granular authentication and role-based access control system

## Database Architecture

### MongoDB Structure (Document Model)

**Database:** `healthcare_db`  
**Main Collection:** `hospitalizations` (54,966 documents)

```json
{
  "_id": "ObjectId",
  "personal_info": {
    "name": "String",
    "age": "Number",
    "gender": "String",
    "blood_type": "String"
  },
  "medical_info": {
    "condition": "String",
    "medication": "String",
    "test_results": ["Array"]
  },
  "admission_info": {
    "date_admission": "Date",
    "date_discharge": "Date",
    "duration_days": "Number",
    "admission_type": "String",
    "room_number": "String"
  },
  "administrative_info": {
    "doctor": "String",
    "hospital": "String",
    "insurance_provider": "String",
    "billing_amount": "Number"
  },
  "metadata": {
    "created_at": "Date",
    "source": "String",
    "migration_version": "String"
  }
}
```

## Optimized Indexes

To ensure optimal performance, the following indexes were created:

    personal_info.name - Fast patient name lookup
    personal_info.age - Age-based filtering
    medical_info.condition - Pathology filtering
    admission_info.date_admission - Temporal queries
    administrative_info.hospital - Hospital-based search
    administrative_info.billing_amount - Financial analysis
    Compound index (gender, age) - Demographic statistics

## Anonymized View
A patients_anonymized_view was created for analysts, masking personally identifiable information while enabling statistical analysis.

## Authentication System and Roles
### Role Hierarchy (Principle of Least Privilege)
```env
Role 	              Read 	   Write 	     Index 	      Admin 	       Description
ADMIN_MASTER      	✅ 	      ✅ 	        ✅ 	         ✅ 	         Full access, user management
DATA_ENGINEER 	    ✅ 	      ✅ 	        ✅ 	         ❌ 	         Read/write on healthcare_db
BACKEND_API 	      ✅ 	      ✅ 	        ❌ 	         ❌ 	         Targeted application operations
ANALYST_ 	          ✅ 	      ❌ 	        ❌ 	         ❌ 	         Read-only on anonymized view
DOCTOR_APP 	        ✅* 	    ✅* 	      ❌ 	         ❌ 	         Hospital-filtered access only

✅ = Full access | ❌ = No access | ✅ = Limited/filtered access*
```


### Role Configuration Example
```javascript
// Creating ANALYST_READONLY role
db.createRole({
  role: "ANALYST_READONLY",
  privileges: [
    {
      resource: { db: "healthcare_db", collection: "patients_anonymized_view" },
      actions: ["find"]
    }
  ],
  roles: []
})
```

## Installation and Usage
### Prerequisites

    Docker and Docker Compose (version 20.10+)
    Python 3.9 or higher
    MongoDB Atlas account (or local MongoDB instance)
    Git for version control

### Configuration

1. Clone the repository
```bash 
git clone https://github.com/....../healthcare-docker.git
cd healthcare-docker

```
2. Create the .env file

Create a .env file at the project root with your credentials:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=healthcare_db
MONGODB_COLLECTION=hospitalizations

# Authentication
ADMIN_USERNAME=admin_master
ADMIN_PASSWORD=your_secure_password

# Application Settings
BATCH_SIZE=1000
LOG_LEVEL=INFO
```
!!!!!!!!!!!!!!!!!!    ⚠️ IMPORTANT: NEVER commit this file to GitHub!!!!!!!!!!!!!!!!!!!!!!!

3. Install Python dependencies (optional for local execution)!

```bash
cd app
pip install -r requirements.txt
```


## Launch with Docker

Start the complete stack (MongoDB + Migration)
```bash
docker-compose up -d
```

Check migration logs
```bash
docker-compose logs -f migration_app
```

Stop containers
```bash
docker-compose down
```

Manual Execution (without Docker)
```bash
cd app
python migration.py
```


## Project Structure

```env

healthcare-docker/
├── app/
│   ├── config.py              # Configuration and environment variables
│   ├── Dockerfile             # Docker image for Python scripts
│   ├── migration.py           # Main migration script
│   ├── requirements.txt       # Python dependencies
│   └── utils.py               # Utility functions (cleaning, validation)
├── data/
│   └── healthcare_dataset.csv # Medical dataset (54,966 records)
├── logs/                      # Migration logs (auto-generated)
├── mongodb/
│   └── init-mongo.js          # MongoDB initialization script (users, roles)
├── .dockerignore              # Files excluded from Docker build
├── .env                       # Environment variables (NOT COMMITTED)
├── docker-compose.yml         # Container orchestration
├── EXPLORATION_AWS_CLOUD.md   # AWS options documentation
├── EXPLORATION_AWS_CLOUD.pdf  # PDF version of AWS exploration
└── README.md                  # This file

```


## Migration Results
### Key Metrics
Metric 	                  Value
Documents migrated 	      54,966 / 54,966 (100%)
Success rate 	            100% ✅
Total duration 	          2 min 23 sec
Average speed 	          384 documents/sec
Duplicates removed 	      534
Amounts corrected 	      106 (negative values)
Validation                Tests Performed

✅ Test 1: Document count (100% validated)
✅ Test 2: Document structure (100% compliant)
✅ Test 3: Data types (100% correct)
✅ Test 4: Indexes created (7/7 operational)
✅ Test 5: Query performance (< 50ms)
✅ Test 6: Samples verified (100/100)
✅ Test 7: Valid values (100%)

### Performance Gains
Query          Type 	       Before (CSV) 	After (MongoDB) 	Gain
Patient        search 	       2.5s 	        15ms 	            99.4% ↓
Stats          aggregation 	   8.2s 	        120ms 	            98.5% ↓
Report         export 	       15s 	            450ms 	            97.0% ↓


### Security and Compliance
Implemented Security Measures

Multi-Level Encryption

    In transit: TLS 1.3 for all connections (User → ALB → ECS → MongoDB)
    At rest: Automatic AES-256 on MongoDB Atlas
    Field-level: Encryption of ultra-sensitive data (SSN, etc.)

Audit and Traceability

    Detailed logs of all operations (CloudWatch + MongoDB Atlas Audit)
    Complete access traceability (who, when, what)
    Automatic alerts for suspicious access


### Data Anonymization

Creation of an anonymized view for analysts:
```json
// ORIGINAL Document
{
  "personal_info": {
    "name": "Bobby Jackson",  // ← Identifier
    "age": 30                 // ← Precise
  },
  "administrative_info": {
    "billing_amount": 18856.28  // ← Exact amount
  }
}

// ANONYMIZED Document
{
  "patient_id": "a3f7b2c9...",    // ← Anonymous hash
  "age_range": "30-49",            // ← Range
  "billing_range": "10K-25K"       // ← Range
  // No name, doctor, hospital, exact amount
}
``` 


## Regulatory Compliance

**GDPR (General Data Protection Regulation)**

    ✓ Right to erasure: Deletion API implemented
    ✓ Right to portability: JSON export available
    ✓ Data minimization: Anonymized view for analysts
    ✓ Complete traceability: CloudTrail + MongoDB audit logs
    ✓ Encryption: End-to-end (transit + rest)
    ✓ Location: Data hosted in EU (Paris region)

**HIPAA (Health Insurance Portability and Accountability Act)**

    ✓ Strict access control (granular roles)
    ✓ Complete audit trail
    ✓ Healthcare data encryption
    ✓ Tested backup and recovery procedures


## AWS Cloud Architecture
### AWS Services Used
Service 	                   Usage 	                              Justification
ECS Fargate 	               Container orchestration 	            Serverless, automatic scaling
ECR 	                       Private Docker registry 	            Secure image storage
S3 	                         Backups and exports 	                99.999999999% durability
CloudWatch 	                 Monitoring and logs 	                Centralized surveillance
Secrets Manager 	           Credentials management 	            Automatic secret rotation
IAM 	                       Access management 	                  Principle of least privilege
EventBridge 	               Scheduled tasks 	                    Migration automation
SNS 	                       Notifications 	                      Real-time alerts

### Architecture Diagram

```env
┌─────────────┐
│    Users    │
└───────┬─────┘
        │ HTTPS (TLS 1.3)
        ▼
┌─────────────────┐
│  ALB (Load Balancer) │  ← Load distribution
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│   ECS Fargate         │  ← Serverless containers
│  (Migration Scripts)  │
└────────┬─────────┘
         │
         ▼
┌───────────────────┐
│  MongoDB Atlas        │  ← Managed NoSQL database
│  (Multi-AZ Paris)     │  ← 99.95% SLA
└────────┬──────────┘
         │
         ▼
┌──────────────────┐
│  S3 + Glacier         │  ← Daily backups
│  (Cross-region)       │
└───────────────────┘

```


### Estimated Cost
Solution 	                    Monthly Cost 	                    Advantages
MongoDB Atlas (Recommended) 	~$60 	                            Managed, zero ops, auto backups
Amazon DocumentDB 	          ~$215 	                          Native AWS integration
EC2 + Self-managed MongoDB 	  ~$860 	                          Full control but high hidden cost
On-premise infrastructure 	  ~$1,610 	                        Hardware, hosting, maintenance

Immediate ROI: Savings of ~$1,550/month vs on-premise infrastructure


### Data Processing Pipeline
Automated Cleaning Steps

1. Deduplication

    Detection and removal of 534 duplicates
    Method: df.drop_duplicates()

2. Amount Correction

    Conversion of 106 negative amounts to absolute values
    Method: abs(df['amount'])

3. Normalization

    Standardization of name casing (.str.title())
    Date format correction (pd.to_datetime())
    Automatic calculation of length of stay

4. Quality Control

    Integrity checks
    Generation of cleaning report (logs/rapport_nettoyage_final.txt)



## Migration Plan (8 Phases - 8 Weeks)
Phase 	     Duration 	Description
W1 	         1 week 	  AWS infrastructure preparation (IAM, VPC, Security Groups)
W2 	         1 week 	  MongoDB Atlas provisioning (cluster, users, backups)
W3 	         1 week 	  Dockerization and ECR push
W4 	         1 week 	  ECS deployment (Task Definition, Service, ALB)
W5 	         1 week 	  Orchestration and automation (EventBridge, auto-scaling)
W6 	         1 week 	  Backups and recovery (AWS Backup, Lambda → S3)
W7 	         1 week 	  Security and compliance (GuardDuty, WAF, GDPR audit)
W8 	         1 week 	  Go-Live and user training



## Recommendations and Perspectives
Short Term (0-3 months)

    ✅ Complete architecture deployment
    ✅ Active monitoring and configuration tuning

Medium Term (6-12 months)

    💰 Cost optimization (Reserved Instances, Savings Plans)
    🔌 Development of a secure REST API to expose data

Long Term (>12 months)

    🏗️ Transition to microservices architecture
    🤖 Machine Learning with AWS SageMaker for predictive analytics
    📊 Data Lake on S3 for advanced analytics



## Troubleshooting
###Issue: MongoDB connection error

**Check logs**
```bash
docker-compose logs mongodb
```

**Test connection**
```bash
docker exec -it mongodb mongosh --eval "db.adminCommand('ping')"
```

### Issue: Migration fails

**Check migration logs**
```bash
cat logs/migration.log
```

**Restart with verbose mode**
```bash
python app/migration.py --verbose
```

### Issue: Permission denied

**Check user roles**
```bash
docker exec -it mongodb mongosh healthcare_db --eval "db.getUsers()"
```


# Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Development workflow:

    Fork the repository
    Create your feature branch (git checkout -b feature/AmazingFeature)
    Commit your changes (git commit -m 'Add some AmazingFeature')
    Push to the branch (git push origin feature/AmazingFeature)
    Open a Pull Request





# License

This project is licensed under the MIT License. See the LICENSE file for details.

Author
Behram Korrkut
Data Engineer @ Health Data SoluTech Engineering  , Paris / France 



⭐⭐⭐⭐⭐  If you found this project useful, please consider giving it a star on GitHub!

Last updated: November 2025

