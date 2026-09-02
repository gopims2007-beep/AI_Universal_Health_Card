# AI Universal Health Card — Real Project Implementation

A real, empty-database implementation of the 9 modules specified in the project document.

## Modules
1. Home Page
2. User Registration
3. User Login
4. Patient Dashboard
5. Patient Profile Management
6. Medical History Management
7. Medical Report Upload
8. AI Medical Report Analysis
9. QR Code Generation

The implementation also includes role-aware Doctor/Hospital/Admin API foundations, emergency QR access, digital health-card PDF download, secure password hashing, JWT authentication, refresh tokens, consent-token support, and audit logging.

## Important: no demo data
- No sample users
- No sample patients
- No fake medical reports
- No seed script
- The database starts empty.
- AI analysis never invents patient data. It analyzes only uploaded report text or supplied patient symptoms/data.

## Stack
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Backend: Python 3.13+, FastAPI
- Database: MySQL 8+ (SQLAlchemy)
- Auth: JWT + bcrypt/passlib
- AI/ML: scikit-learn, pandas, numpy
- PDF: pypdf + ReportLab
- QR: qrcode
- File upload: PDF/JPG/PNG
- API docs: Swagger UI

## Quick start

### 1. Create database
Create an empty MySQL database:

```sql
CREATE DATABASE ai_health_card CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend
```bash
cd backend
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Linux/macOS:
```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set the MySQL connection, JWT secret, upload directory and optional SMTP settings.

Run:
```bash
uvicorn app.main:app --reload --port 8000
```

API:
- http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

### 3. Frontend
The frontend is served by FastAPI at:
- http://127.0.0.1:8000/

No separate Node/npm setup is required.

## AI model
The application does not ship a fake trained model or fake dataset.

For real ML training, put a real, legally usable CSV dataset in `backend/ml/datasets/` and run:

```bash
python -m app.ml.train_model --csv ml/datasets/your_dataset.csv --target disease
```

The command validates the target column, trains a scikit-learn pipeline, reports metrics, and writes `ml/models/disease_risk.joblib`.

If no trained model exists, the report-analysis API still performs transparent clinical-text extraction and returns "model not trained" rather than fabricating a prediction.

## Security notes
For production deployment:
- Use HTTPS.
- Set a long random JWT secret.
- Use a managed MySQL/PostgreSQL service with backups.
- Configure SMTP for real email verification/password reset.
- Store uploads outside the web root/object storage.
- Add antivirus scanning before accepting untrusted files.
- Use a reverse proxy and secure cookies where appropriate.
- Obtain proper medical/legal/privacy review before clinical use.

This is software engineering code, not medical advice or a medical diagnostic device.
