# Recruitment Management System

This project contains a MySQL schema, SQL advanced objects, a SQLAlchemy backend, and a Streamlit frontend for employer and candidate workflows.

## Setup

1. Create and load the database scripts in this order:
   - `database/init.sql`
   - `database/seed_510.sql`
   - `database/02_views.sql`
   - `database/03_routines.sql`
   - `database/04_triggers.sql`
   - `database/05_security.sql`
2. Create a local `.env` file from `.env.example`.
3. Install Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Example `.env`:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=recruitment_management_system
DB_ECHO=false
```

## Run Backend Smoke Test

```powershell
python -m backend.smoke_test
```

This verifies:
- database connection
- employer login
- candidate login
- dashboard query access
- open job listing access
- candidate application/interview access

## Run Streamlit App

```powershell
streamlit run frontend/app.py
```

## Demo Login

- Employer email example: `employer0001@example.com`
- Candidate email example: `candidate0001@example.com`
- Password for all demo logins: `1`

## Current Structure

- `backend/config.py`: environment-backed runtime settings
- `backend/db.py`: engine and session management
- `backend/models.py`: SQLAlchemy 2.0 ORM models
- `backend/crud.py`: all database access and workflow functions
- `backend/smoke_test.py`: minimal backend verification
- `frontend/app.py`: Streamlit entrypoint and top-level routing
- `frontend/session.py`: auth/session-state helpers
- `frontend/components.py`: shared layout, table, and metric helpers
- `frontend/pages/auth.py`: login page
- `frontend/pages/employer.py`: employer screens
- `frontend/pages/candidate.py`: candidate screens
- `database/`: schema, seed, views, routines, triggers, and security scripts
