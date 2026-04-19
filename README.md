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

## Web Functionalities

- Authentication:
  - Sign in with employer or candidate accounts
  - Register a new candidate account
  - Register a new employer account
  - Change password from the account security section

- Employer dashboard:
  - View company-level metrics such as total jobs, open jobs, applications, interviews, pass/fail counts, and average interview score
  - View recent applications in a dashboard activity table
  - View hiring trend charts for applications by position, scheduled interviews by month, and pass rate
  - Navigate quickly to job management from the dashboard

- Employer job management:
  - Create new job positions
  - Update job status between `Open` and `Closed`
  - View all owned positions
  - Inspect a job snapshot showing applicant count, pass/fail/pending interview counts, average score, and current job status
  - View per-position interview outcome ratios

- Employer application management:
  - View all applications for the employer's own job positions
  - Filter applications by status
  - Search applications by candidate, company, or position
  - View applications ready for interview scheduling
  - View shortlisted candidates
  - Expand and inspect detailed applicant profiles, including personal details, resume link, application status, and interview information when available

- Employer interview management:
  - View new applicants who do not yet have an interview scheduled
  - Schedule interviews for valid applications
  - Record interview results with pass, fail, pending, score, and notes
  - View full interview history with candidate, application, score, result, location/link, and interview date

- Employer performance analytics:
  - View application summaries by job position
  - Rank positions by application volume, accepted count, interviewing count, or average interview score
  - Visualize interview outcome distributions with chart-based summaries
  - Review company-wide hiring outcome ratios

- Candidate job board:
  - Browse all open job positions
  - Search open jobs by title, company, description, or requirements
  - Apply directly to eligible open positions

- Candidate application tracking:
  - View all submitted applications
  - Track current application status for each submission
  - View company, position, and application date in a structured activity table

- Candidate interview tracking:
  - View all scheduled interviews
  - View upcoming interviews separately
  - Review interview date, company, result, and related application information

- Candidate profile management:
  - Update full name, phone number, resume URL, and optional date of birth
  - Manage account password from the profile section

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

## Web Deployment Architecture

For cloud deployment, the recommended architecture is:

- `Railway MySQL` as the managed relational database
- `Render` as the globally accessible backend API host
- `Streamlit Community Cloud` as the public dashboard host

This separation is appropriate for academic and demonstration purposes because it preserves the current project stack while assigning one clear responsibility to each platform:

- the database layer remains compatible with the MySQL-specific schema, views, routines, and triggers
- the backend layer exposes HTTP endpoints through FastAPI without requiring the Streamlit interface to be rewritten
- the dashboard layer remains lightweight and easy to publish from the same GitHub repository

The project already includes deployment-oriented files:

- `backend/api.py`: FastAPI entrypoint for Render deployment
- `render.yaml`: Render service definition
- `streamlit_app.py`: root Streamlit entrypoint for Community Cloud
- `.streamlit/secrets.toml.example`: secrets template for Streamlit Cloud
- `database/cloud_01_schema.sql`
- `database/cloud_seed_510.sql`
- `database/cloud_02_views.sql`
- `database/cloud_03_routines.sql`
- `database/cloud_04_triggers.sql`
- `database/CLOUD_IMPORT_ORDER.md`

## Railway MySQL Deployment

### Objective

The purpose of Railway in this architecture is to host the production database externally so that both Render and Streamlit Community Cloud can connect to the same shared dataset.

### Procedure

1. Create a new project on Railway.
2. Add a `MySQL` database service.
3. Open the service variables and record the following values:
   - `MYSQLHOST`
   - `MYSQLPORT`
   - `MYSQLUSER`
   - `MYSQLPASSWORD`
   - `MYSQLDATABASE`
4. Use the public TCP proxy values, not the private internal hostname, when connecting from your own computer:
   - `RAILWAY_TCP_PROXY_DOMAIN`
   - `RAILWAY_TCP_PROXY_PORT`
5. Connect to the Railway database using MySQL Workbench or another MySQL client.
6. Select the target schema, usually `railway`.
7. Import the SQL files in this order:
   - `database/cloud_01_schema.sql`
   - `database/cloud_seed_510.sql`
   - `database/cloud_02_views.sql`
   - `database/cloud_03_routines.sql`
   - `database/cloud_04_triggers.sql`

### Verification

After import, verify that the base tables contain data:

```sql
SELECT COUNT(*) FROM Accounts;
SELECT COUNT(*) FROM Employers;
SELECT COUNT(*) FROM Candidates;
SELECT COUNT(*) FROM JobPositions;
SELECT COUNT(*) FROM Applications;
SELECT COUNT(*) FROM Interviews;
```

### Important Note

`database/05_security.sql` is intentionally not part of the recommended Railway import workflow. Managed cloud MySQL environments often restrict role and privilege operations, and these statements are not required for the current application deployment.

## Render Backend Deployment

### Objective

The purpose of Render in this project is to publish the backend as a globally reachable HTTP service. This enables external validation of backend availability and provides a foundation for future frontend-to-API integration.

### Procedure

1. Push the repository to GitHub.
2. In Render, create a new `Web Service`.
3. Connect the GitHub repository.
4. Use the following runtime configuration:

- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
uvicorn backend.api:app --host 0.0.0.0 --port $PORT
```

- Health Check Path:

```text
/health
```

5. Add the following environment variables in Render:

```env
DB_HOST=YOUR_RAILWAY_TCP_PROXY_DOMAIN
DB_PORT=YOUR_RAILWAY_TCP_PROXY_PORT
DB_USER=YOUR_MYSQL_USER
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=YOUR_MYSQL_DATABASE
DB_ECHO=false
```

The included `render.yaml` file already expresses this deployment model and may be used directly.

### Verification

After deployment, the following endpoints should be reachable:

- `/`
- `/health`
- `/docs`
- `/smoke-test`

Example:

```text
https://your-render-service.onrender.com/health
```

## Streamlit Community Cloud Deployment

### Objective

The purpose of Streamlit Community Cloud in this architecture is to publish the interactive employer and candidate dashboard as a public web application without changing the Streamlit-based frontend design.

### Procedure

1. Open Streamlit Community Cloud.
2. Create a new app from the GitHub repository.
3. Set the main app file to:

```text
streamlit_app.py
```

4. In the app settings, add secrets using the format from `.streamlit/secrets.toml.example`:

```toml
DB_HOST = "YOUR_RAILWAY_TCP_PROXY_DOMAIN"
DB_PORT = "YOUR_RAILWAY_TCP_PROXY_PORT"
DB_USER = "YOUR_MYSQL_USER"
DB_PASSWORD = "YOUR_MYSQL_PASSWORD"
DB_NAME = "YOUR_MYSQL_DATABASE"
DB_ECHO = "false"
API_BASE_URL = "https://your-render-service.onrender.com"
```

### Verification

Once deployed, verify that:

- the login page loads successfully
- employer accounts can open the employer workspace
- candidate accounts can open the candidate workspace
- seeded demo accounts still authenticate correctly

## Local-to-Cloud Configuration Mapping

The same database configuration pattern is used across local and cloud environments. The only difference is the host and port values.

### Local Example

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_LOCAL_PASSWORD
DB_NAME=recruitment_management_system
DB_ECHO=false
```

### Railway/Cloud Example

```env
DB_HOST=YOUR_RAILWAY_TCP_PROXY_DOMAIN
DB_PORT=YOUR_RAILWAY_TCP_PROXY_PORT
DB_USER=YOUR_MYSQL_USER
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=YOUR_MYSQL_DATABASE
DB_ECHO=false
```

## Suggested Deployment Order

For stability, deploy in the following sequence:

1. Provision Railway MySQL.
2. Import schema, seed data, views, routines, and triggers.
3. Deploy the Render backend and verify `/health`.
4. Deploy the Streamlit dashboard and verify login plus dashboard access.

This order is recommended because both application layers depend on a valid, preloaded database before they can function correctly.
