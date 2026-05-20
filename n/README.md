# GenAI Clinician-Style Reports from Cognitive-Decline Speech Models

A comprehensive end-to-end system for cognitive decline risk screening using speech analysis, machine learning, and clinician-style report generation.

**Status**: Core Pipeline Complete | Ready for Testing & Integration

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Installation & Setup](#installation--setup)
7. [Configuration](#configuration)
8. [Running the Application](#running-the-application)
9. [API Endpoints](#api-endpoints)
10. [Agent Workflow](#agent-workflow)
11. [Models & Decision Logic](#models--decision-logic)
12. [Database Schema](#database-schema)
13. [Deployment](#deployment)
14. [Testing](#testing)
15. [Known Issues & Workarounds](#known-issues--workarounds)
16. [Contributing](#contributing)

---

## Project Overview

This project takes speech audio and produces a structured clinician-style report for cognitive decline risk screening. It combines machine learning models, automatic speech recognition (ASR), feature extraction, and retrieval-augmented generation (RAG) in one integrated pipeline.

The system is designed as a **three-tier architecture**:
- **Frontend**: Flutter mobile app for iOS/Android
- **Backend**: PHP API gateway for user management and report storage
- **AI Service**: Python FastAPI service for audio processing and model inference

---

## Key Features

- ✅ **Audio-based cognitive risk screening** - Upload or record speech samples
- ✅ **Automatic speech recognition** - Uses faster-whisper (local, no API keys)
- ✅ **Dual-model ensemble** - SMOTE+Voting vs XGBoost/LightGBM/CatBoost fusion
- ✅ **Rule-based decision logic** - Explainable, not black-box predictions
- ✅ **Agent-based pipeline** - Data processing, prediction, explanation, retrieval, reporting, safety checks
- ✅ **Clinician-style reports** - Professional structured narratives with confidence metrics
- ✅ **Safety compliance** - Non-diagnostic disclaimers and caution flags
- ✅ **RAG integration** - Evidence-backed explanations from knowledge base
- ✅ **Production-ready schema** - MySQL database with audit logs and user management
- ✅ **End-to-end testing** - From audio upload to report generation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUTTER MOBILE APP                       │
│        (iOS/Android UI, recording, file upload)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│              PHP BACKEND (XAMPP/Hostinger)                  │
│  - User authentication & registration                       │
│  - Request routing to Python AI service                     │
│  - Database persistence (MySQL)                            │
│  - Report storage & retrieval                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────────┐
│        PYTHON AI SERVICE (FastAPI on Azure/Local)          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             ORCHESTRATOR AGENT                       │   │
│  │  (Manages sequential agent execution & handoff)      │   │
│  └─────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  DATA AGENT: Audio → Features                        │   │
│  │  • Audio preprocessing                               │   │
│  │  • Voice detection                                   │   │
│  │  • Automatic ASR (faster-whisper)                    │   │
│  │  • Feature extraction (60 features)                  │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │ PREDICTION AGENT: Features → Probabilities           │   │
│  │  • Model 1: SMOTE + Voting Classifier               │   │
│  │  • Model 2: XGB/LGBM/CAT Voting                     │   │
│  │  • Weighted probability fusion                       │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  DECISION AGENT: Rules-based Risk Assessment         │   │
│  │  • Risk level: LOW/MODERATE/HIGH                     │   │
│  │  • Confidence scores                                 │   │
│  │  • Caution flags                                     │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │ EXPLANATION AGENT: Predictions → Interpretations     │   │
│  │  • Map features to clinical indicators               │   │
│  │  • Generate supporting observations                  │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  RETRIEVAL AGENT: Evidence from RAG Knowledge Base   │   │
│  │  • Query knowledge base                              │   │
│  │  • Retrieve supporting evidence                      │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  REPORT AGENT: Generate Clinician-Style Report       │   │
│  │  • Format structured narrative                       │   │
│  │  • Include observations & recommendations            │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  SAFETY AGENT: Compliance & Disclaimers              │   │
│  │  • Rewrite medical claims safely                     │   │
│  │  • Append non-diagnostic disclaimer                  │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│               ▼ Final Report Response                       │
└──────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  MYSQL DATABASE                             │
│  • users, reports, predictions, reading_sessions           │
│  • audit_logs, feature_vectors                             │
│  • Views: user_statistics, recent_reports                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend Services
- **Python 3.11+** - Core inference engine
- **FastAPI** - REST API framework with automatic OpenAPI docs
- **PHP 8.0+** - Web gateway and user management
- **MySQL 8.0+** - Relational database

### Machine Learning
- **scikit-learn** - Preprocessing, feature selection, ensemble models
- **XGBoost** - Gradient boosting classifier
- **LightGBM** - Light gradient boosting machine
- **CatBoost** - Categorical boosting
- **librosa** - Audio feature extraction
- **faster-whisper** - Local automatic speech recognition

### Frontend
- **Flutter 3.0+** - Cross-platform mobile development
- **Dart** - Flutter programming language
- **Provider** - State management

### Deployment
- **Azure App Service** - Python service hosting
- **Hostinger/XAMPP** - PHP backend hosting
- **Docker** - Optional containerization

### Development Tools
- **Virtual Environment** - Python dependency isolation
- **Composer** - PHP package management
- **pytest** - Python testing framework
- **Postman** - API testing

---

## Project Structure

```
project/
├── ai_service_python/              # Python FastAPI service
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── asr.py                # Automatic speech recognition
│   │   ├── config.py             # Configuration management
│   │   ├── model_assets.py       # Model loading utilities
│   │   ├── orchestrator.py       # Agent orchestration
│   │   ├── report_files.py       # Report file handling
│   │   ├── agents/               # Agent implementations
│   │   │   ├── data_agent.py
│   │   │   ├── prediction_agent.py
│   │   │   ├── explanation_agent.py
│   │   │   ├── retrieval_agent.py
│   │   │   ├── report_agent.py
│   │   │   └── safety_agent.py
│   │   ├── rag/                  # RAG knowledge base
│   │   └── models/               # Trained model artifacts
│   │       ├── final_model_1.pkl
│   │       ├── final_model_2.pkl
│   │       ├── scaler.pkl
│   │       ├── selected_features.json
│   │       └── label_encoder.pkl
│   ├── scripts/
│   │   ├── validate_artifacts.py # Verify model files
│   │   └── validate_sample.py    # Test with sample audio
│   └── tests/
│       └── test_probability_fix.py
│
├── backend_php/                    # PHP API gateway
│   ├── index.php                 # Main entry point
│   ├── composer.json             # PHP dependencies
│   ├── api/
│   │   ├── chat.php             # Chat endpoint
│   │   ├── predict.php          # Prediction endpoint
│   │   ├── history.php          # Report history
│   │   ├── login.php            # Authentication
│   │   ├── register.php         # User registration
│   │   ├── upload-report.php    # Report upload
│   │   └── download-report.php  # Report download
│   ├── config/
│   │   ├── ai_service.php       # Python service config
│   │   ├── bootstrap.php        # App initialization
│   │   ├── database.php         # DB connection
│   │   └── report_files.php     # Report file paths
│   ├── storage/
│   │   └── uploads/             # User uploaded files
│   └── public/
│       └── poll_reports.js      # AJAX polling script
│
├── frontend_flutter/              # Flutter mobile app
│   ├── pubspec.yaml             # Flutter dependencies
│   ├── lib/
│   │   ├── main.dart            # App entry point
│   │   ├── screens/             # UI screens
│   │   ├── widgets/             # Reusable widgets
│   │   ├── models/              # Data models
│   │   ├── services/            # API services
│   │   └── providers/           # State management
│   ├── android/                 # Android native code
│   ├── ios/                     # iOS native code
│   └── assets/
│       └── reading_passages.json # Test passages
│
├── mysql_schema/                  # Database schema
│   └── schema.sql               # SQL DDL for all tables
│
├── deployment_docs/              # Deployment guides
│   ├── setup.md                 # Quick start guide
│   ├── deploy_python_azure.md   # Azure deployment
│   ├── deploy_php_hostinger.md  # Hostinger deployment
│   ├── deploy_flutter_android.md# Android app build
│   └── api_contract.md          # API specifications
│
├── prompts/                       # LLM prompt templates
│   ├── master_prompt.txt
│   ├── report_prompt.txt
│   └── safety_prompt.txt
│
├── reports/                       # Generated reports
│   ├── *.txt                    # Report artifacts
│   ├── uploaded/                # User uploaded files
│   └── reports_index.json       # Report index
│
├── test_audio_files/            # Test audio samples
│   ├── Stacy Keach-Nondemenitia/
│   ├── Steve Reich-nondemenetia/
│   ├── Trevor Peacock-demenitia/
│   └── ... (various speakers)
│
├── resource/                      # ML resources
│   ├── features_preprocessed.csv
│   ├── features.csv
│   ├── label.csv
│   └── ADITYA.ipynb            # Training notebook
│
├── README.md                      # This file
├── setup.md                       # Setup instructions
└── IMPLEMENTATION_SUMMARY.md     # Detailed implementation log
```

---

## Installation & Setup

### Prerequisites

- **Python 3.11+** with pip
- **PHP 8.0+**
- **MySQL 8.0+**
- **Node.js** (for Flutter web)
- **Flutter SDK** 3.0+ (for mobile)
- **Git**

### Python AI Service Setup

```bash
# 1. Clone and navigate to project
cd c:\xampp\htdocs\project\ai_service_python

# 2. Create virtual environment
python -m venv .venv

# 3. Activate environment
.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate   # macOS/Linux

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify model artifacts
python scripts/validate_artifacts.py
```

### PHP Backend Setup

```bash
# 1. Navigate to PHP directory
cd ..\backend_php

# 2. Install PHP dependencies
composer install

# 3. Create uploads directory
mkdir storage/uploads

# 4. Update configuration
# Edit config/ai_service.php with Python service URL
# Edit config/database.php with MySQL credentials
```

### MySQL Database Setup

```bash
# 1. Start MySQL (XAMPP)
# Start MySQL from XAMPP Control Panel
# or: mysql -u root -p

# 2. Create database
mysql -u root -p < ..\mysql_schema\schema.sql

# 3. Verify tables
mysql -u root -p -e "USE cognitive_decline_db; SHOW TABLES;"
```

---

## Configuration

### Python Service Configuration

**File**: [ai_service_python/app/config.py](ai_service_python/app/config.py)

```python
# ASR Model Size
ASR_MODEL_SIZE = "tiny"  # Options: tiny, base, small, medium, large
ASR_LANGUAGE = "en"

# Model Paths (relative to project root)
MODEL_1_PATH = "ai_service_python/app/models/final_model_1.pkl"
MODEL_2_PATH = "ai_service_python/app/models/final_model_2.pkl"
SCALER_PATH = "ai_service_python/app/models/scaler.pkl"
SELECTED_FEATURES_PATH = "ai_service_python/app/models/selected_features.json"

# Feature Extraction
FEATURE_COUNT = 60
MFCC_N_MELS = 13
MFCC_N_MFCC = 13
SAMPLING_RATE = 16000

# Audio Processing
SILENCE_THRESHOLD_DB = 20
MIN_DURATION_SECONDS = 0.5
```

### PHP Database Configuration

**File**: [backend_php/config/database.php](backend_php/config/database.php)

```php
return [
    'driver' => 'mysql',
    'host' => '127.0.0.1',
    'database' => 'cognitive_decline_db',
    'username' => 'root',
    'password' => '',  // Set your MySQL password
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
];
```

---

## Running the Application

### Start Python AI Service

```bash
cd ai_service_python

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Access API docs
# Interactive docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Start PHP Backend (XAMPP)

```bash
# 1. Start XAMPP (Apache + MySQL)
# Via XAMPP Control Panel or:
# C:\xampp\apache_start.bat
# C:\xampp\mysql_start.bat

# 2. Access PHP backend
# http://localhost/project/backend_php/

# 3. Test health endpoint
# http://localhost/project/backend_php/?route=health
```

### Run Flutter Mobile App

```bash
cd frontend_flutter

# Activate dependencies
flutter pub get

# Run on emulator/device
flutter run

# Build APK for Android
flutter build apk --release

# Build for iOS
flutter build ios
```

---

## API Endpoints

### Python AI Service

#### Health Check
```
GET /health

Response:
{
  "status": "ok"
}
```

#### Audio Prediction (Main Entry Point)
```
POST /predict/audio
Content-Type: multipart/form-data

File: audio (WAV, MP3, OGG)

Response (Success):
{
  "status": "success",
  "transcript": "the quick brown fox...",
  "probability": 0.72,
  "risk_level": "MODERATE",
  "confidence": 0.85,
  "model_1_probability": 0.70,
  "model_2_probability": 0.74,
  "explanation": "Speech shows moderate decline indicators...",
  "recommendations": "Consider further assessment...",
  "report": "Clinician-style narrative..."
}

Response (No Voice):
{
  "status": "needs_restart",
  "message": "No voice detected. Please restart reading."
}
```

#### CSV Feature Prediction (Testing)
```
POST /predict/csv
Content-Type: multipart/form-data

File: csv (comma-separated features)

Response:
{
  "status": "success",
  "probability": 0.68,
  "risk_level": "MODERATE",
  "confidence": 0.82
}
```

### PHP API Gateway

#### Health Check
```
GET /api/index.php?route=health

Response:
{
  "status": "ok"
}
```

#### Audio Prediction
```
POST /api/index.php?route=predict_audio

Fields:
- audio (file upload)
- user_id (integer)
- paragraph_text (string, optional)

Response:
{
  "status": "success",
  "report_id": 123,
  "prediction": {...}
}
```

#### Get User Reports
```
GET /api/index.php?route=reports&user_id=1

Response:
{
  "status": "success",
  "reports": [
    {
      "id": 123,
      "created_at": "2024-01-15",
      "risk_level": "MODERATE",
      "probability": 0.72
    }
  ]
}
```

#### Get Report Detail
```
GET /api/index.php?route=report_detail&id=123

Response:
{
  "status": "success",
  "report": {
    "user_id": 1,
    "transcript": "...",
    "risk_level": "MODERATE",
    "probability": 0.72,
    "clinician_report": "...",
    "created_at": "2024-01-15"
  }
}
```

---

## Agent Workflow

### Execution Sequence

```
Input: Audio File
   ↓
[1. DATA AGENT]
    ├─ Load and preprocess audio
    ├─ Detect voice presence
    ├─ Run ASR (faster-whisper) → Transcript
    ├─ Extract audio features (MFCC, pitch, energy, etc.)
    ├─ Extract linguistic features from transcript
    ├─ Extract text features (word counts, complexity)
    ├─ Apply feature selection (60 features)
    ├─ Scale features
    └─ Output: Preprocessed feature vector
   ↓
[2. PREDICTION AGENT]
    ├─ Load Model 1 (SMOTE + Voting)
    ├─ Load Model 2 (XGB/LGBM/CAT Voting)
    ├─ Generate probability from Model 1
    ├─ Generate probability from Model 2
    ├─ Apply weighted fusion (0.5 × prob1 + 0.5 × prob2)
    └─ Output: prob1, prob2, final_probability
   ↓
[3. DECISION AGENT]
    ├─ Apply risk thresholds
    │  ├─ HIGH RISK: probability ≥ 0.65
    │  ├─ MODERATE: 0.45 ≤ probability < 0.65
    │  └─ LOW RISK: probability < 0.45
    ├─ Check for model agreement
    ├─ Generate caution flags if models disagree
    └─ Output: risk_level, confidence, rationale
   ↓
[4. EXPLANATION AGENT]
    ├─ Analyze feature contributions
    ├─ Map to clinical indicators:
    │  ├─ Speech rate and rhythm changes
    │  ├─ Pause behavior and hesitations
    │  ├─ MFCC patterns (voice quality)
    │  ├─ Linguistic complexity
    │  ├─ Word finding difficulties
    │  └─ Repetition and perseveration
    └─ Output: Supporting observations
   ↓
[5. RETRIEVAL AGENT]
    ├─ Query RAG knowledge base
    ├─ Retrieve evidence snippets
    ├─ Match to clinical indicators
    └─ Output: Evidence-backed text
   ↓
[6. REPORT AGENT]
    ├─ Format structured narrative:
    │  ├─ Risk level summary
    │  ├─ Confidence metrics
    │  ├─ Key observations
    │  ├─ Clinical indicators
    │  ├─ Behavioral patterns
    │  └─ Recommendations
    └─ Output: Clinician-style report
   ↓
[7. SAFETY AGENT]
    ├─ Scan for diagnostic claims
    ├─ Rewrite as non-diagnostic
    ├─ Append non-diagnostic disclaimer
    └─ Output: Safety-compliant final report
   ↓
[8. ORCHESTRATOR]
    ├─ Aggregate all outputs
    ├─ Handle failures gracefully
    ├─ Format API response
    └─ Output: Complete prediction response
   ↓
Response: JSON with report, probabilities, confidence
```

### Agent Responsibilities

| Agent | Input | Process | Output |
|-------|-------|---------|--------|
| **Data** | Raw audio | Preprocess, ASR, feature extract | 60-feature vector + transcript |
| **Prediction** | Features | Run both models, fuse probabilities | prob1, prob2, final probability |
| **Decision** | Probabilities | Apply rules, check agreement | risk_level, confidence, rationale |
| **Explanation** | Predictions + Features | Map to clinical indicators | Supporting observations |
| **Retrieval** | Observations | Query RAG knowledge base | Evidence snippets |
| **Report** | All above outputs | Format narrative | Clinician-style report |
| **Safety** | Draft report | Rewrite claims, add disclaimer | Final safe report |
| **Orchestrator** | Request payload | Coordinate all agents | Complete API response |

---

## Models & Decision Logic

### Model 1: SMOTE + Voting Classifier

**Pipeline**:
1. SMOTE - Synthetic minority oversampling
2. VotingClassifier with soft voting:
   - XGBoost (weight: 2)
   - LightGBM (weight: 2)
   - RandomForest (weight: 1)

**Performance**:
- Test Accuracy: ~67.57%
- ROC-AUC: ~0.66
- Handles class imbalance

### Model 2: Voting Classifier

**Ensemble**:
- XGBoost (weight: 2)
- LightGBM (weight: 2)
- CatBoost (weight: 1)

**Performance**:
- Test Accuracy: ~66.22%
- ROC-AUC: ~0.63
- Diverse base learners

### Final Probability Fusion

```
final_probability = 0.5 × model_1_probability + 0.5 × model_2_probability
```

### Risk Decision Rules

```
Both models HIGH (prob ≥ 0.65)
    → HIGH RISK (confidence: 95%)

One HIGH + One MODERATE (0.45-0.65)
    → MODERATE-HIGH (confidence: 85%, flag: Models differ)

One HIGH + One LOW (prob < 0.45)
    → MODERATE (confidence: 70%, flag: Substantial disagreement)

Both MODERATE (0.45-0.65)
    → MODERATE RISK (confidence: 80%)

One MODERATE + One LOW
    → MODERATE (confidence: 75%)

Both LOW (prob < 0.45)
    → LOW RISK (confidence: 90%)
```

### Risk Thresholds

| Risk Level | Probability Range | Interpretation |
|-----------|------------------|-----------------|
| **HIGH** | ≥ 0.65 | Strong indicators of cognitive decline |
| **MODERATE** | 0.45 - 0.65 | Noticeable indicators, further assessment recommended |
| **LOW** | < 0.45 | Limited indicators, within normal range |

### Feature Selection

- **Total Features**: 60 (selected from 200+)
- **Audio Features** (~20): MFCC, pitch, energy, spectral centroid, RMS, zero crossing rate, deltas
- **Text Features** (~25): Word counts, complexity metrics (type-token ratio, flesch-kincaid), lexical diversity, filler rates
- **TF-IDF Features** (~15): Top unigrams and bigrams from training corpus

---

## Database Schema

### Tables

#### users
```sql
- id (PK)
- full_name
- email (UNIQUE, indexed)
- password_hash
- phone
- age
- gender
- created_at (indexed)
- updated_at
```

#### reports
```sql
- id (PK)
- user_id (FK)
- transcript (TEXT)
- audio_file_path
- model_1_score (probability from Model 1)
- model_2_score (probability from Model 2)
- combined_probability (final fused probability)
- risk_level (LOW, MODERATE, HIGH)
- confidence (0-1)
- rationale (decision explanation)
- clinician_report (full formatted report)
- recommendations (clinical recommendations)
- safety_note (non-diagnostic disclaimer)
- created_at (indexed)
- updated_at
```

#### predictions
```sql
- id (PK)
- report_id (FK)
- model_name (Model 1 or Model 2)
- probability_score
- prediction_label (dementia or non_dementia)
- confidence_score
- created_at
```

#### reading_sessions
```sql
- id (PK)
- user_id (FK)
- paragraph_text
- audio_path
- transcript
- status (in_progress, completed, failed)
- created_at
- updated_at
```

#### audit_logs
```sql
- id (PK)
- user_id (FK, nullable)
- action_type (login, prediction, report_download, etc.)
- action_details (JSON)
- ip_address
- user_agent
- created_at (indexed)
```

#### feature_vectors (optional, for ML analysis)
```sql
- id (PK)
- report_id (FK)
- feature_name
- feature_value
- created_at
```

### Views

#### user_statistics
- user_id, total_reports, avg_risk_probability, last_report_date

#### recent_reports
- Reports from last 30 days with summary info

---

## Deployment

### Azure Deployment (Python Service)

See: [deployment_docs/deploy_python_azure.md](deployment_docs/deploy_python_azure.md)

```bash
# Key Steps:
1. Create Azure App Service (Linux, Python 3.11)
2. Configure environment variables for model paths
3. Deploy via Git or ZIP upload
4. Configure MySQL connection strings
5. Set up health check endpoint
```

### Hostinger Deployment (PHP Backend)

See: [deployment_docs/deploy_php_hostinger.md](deployment_docs/deploy_php_hostinger.md)

```bash
# Key Steps:
1. SSH into Hostinger server
2. Upload PHP files to public_html
3. Configure database credentials
4. Point Python service URL to Azure endpoint
5. Set up SSL/TLS certificates
```

### Flutter Mobile App Deployment

See: [deployment_docs/deploy_flutter_android.md](deployment_docs/deploy_flutter_android.md)

```bash
# Android:
flutter build apk --release
# Upload to Google Play Store

# iOS:
flutter build ios --release
# Upload to Apple App Store
```

---

## Testing

### Unit Tests

Run individual component tests:

```bash
# Python unit tests
cd ai_service_python
pytest tests/test_probability_fix.py -v

# Test audio preprocessing
pytest -v -k "test_preprocessing"

# Test model loading
pytest -v -k "test_models"
```

### Integration Tests

```bash
# Test full pipeline with sample audio
python scripts/validate_sample.py

# Test with test audio files
python -m pytest tests/ --audio-samples
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test audio prediction
curl -X POST http://localhost:8000/predict/audio \
  -F "file=@test_audio_files/sample.wav"

# Test CSV prediction
curl -X POST http://localhost:8000/predict/csv \
  -F "file=@sample_input.csv"
```

### Test Coverage

- ✅ Audio preprocessing
- ✅ Feature extraction
- ✅ ASR transcription
- ✅ Decision rules
- ✅ Model inference
- ⏳ End-to-end pipeline
- ⏳ Database integration
- ⏳ API endpoints
- ⏳ Flutter UI

---

## Known Issues & Workarounds

### Issue 1: TF-IDF Vectorizer Corruption
**Problem**: `tfidf_vectorizer.pkl` has empty vocabulary  
**Impact**: TF-IDF features not extracted during inference  
**Workaround**: Vectorizer re-created on-demand with training parameters  
**Solution**: Regenerate from training corpus (requires original training notebook)

### Issue 2: Feature Name Mismatch
**Problem**: Model 2 expects 'of_the' but selected_features.json has 'of the'  
**Impact**: MEDIUM - May cause shape mismatch if not handled  
**Workaround**: Feature alignment in data_agent before scaling  
**Solution**: Retrain models or normalize feature names consistently

### Issue 3: Feature Selector Format
**Problem**: `feature_selector.pkl` is plain list, not SelectKBest object  
**Impact**: LOW - Not used in inference pipeline  
**Solution**: Remove or replace with proper selector object

---

## Contributing

### Code Style
- Python: Follow PEP 8 (use `black` for formatting)
- PHP: PSR-12 standard
- Dart/Flutter: Follow Flutter style guide

### Git Workflow
1. Create feature branch: `git checkout -b feature/description`
2. Make changes and test thoroughly
3. Commit with descriptive messages
4. Submit pull request
5. Code review before merge

### Testing Requirements
- All unit tests must pass
- New features require test coverage
- Integration tests recommended for critical paths

### Documentation
- Update README for user-facing changes
- Add docstrings to all functions
- Document API changes in api_contract.md
- Update IMPLEMENTATION_SUMMARY.md for major changes

---

## Support & Resources

- **API Documentation**: http://localhost:8000/docs (when running locally)
- **Implementation Details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Deployment Guides**: See [deployment_docs/](deployment_docs/)
- **Database Schema**: See [mysql_schema/schema.sql](mysql_schema/schema.sql)

---

## License

[Add your license information here]

## Contact

For questions or issues, please contact the development team or file an issue in the project repository.

- ai_service_python: ML service, agents, inference pipeline, and Colab artifacts
- backend_php: PHP API gateway between Flutter, Python, and MySQL
- frontend_flutter: Android application UI and API integration

## 9. Setup Instructions

1. Install Python dependencies:

```bash
cd ai_service_python
pip install -r requirements.txt
```

2. Start Python API service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. Configure PHP backend with AI service URL (`AI_SERVICE_URL`) and database credentials.
4. Apply MySQL schema from `mysql_schema/schema.sql`.
5. Run Flutter app from `frontend_flutter`.

## 10. How It Works

Audio input is preprocessed, transcribed, and converted into audio plus text features. TF-IDF is transformed (not fit), merged with engineered features, reordered by `feature_names.json`, filtered by `selected_features.json`, then passed through imputer and scaler. Both models produce probabilities, a weighted final score is computed, and the agent stack generates a safe clinician-style report.

## 11. Output Example

The output report includes:

- Risk Level (High Risk or Low Risk)
- Model Confidence
- Individual model probabilities (`prob1`, `prob2`)
- Supporting observations (speech and language markers)
- Behavioral indicators
- Retrieved evidence snippets
- Final clinician-style narrative report

## 12. Safety Disclaimer

This system is a screening support tool, not a diagnostic system.

This is not a medical diagnosis. Please consult a qualified professional.

## 13. Future Improvements

- Add automated artifact-version checks at startup
- Improve end-to-end monitoring and error observability
- Expand multilingual ASR and domain-specific retrieval coverage
