# Project Brief: Digital Recruitment Management System

## 1. Project Objective
Develop a digital recruitment management system to streamline the job application process, track interviews, manage candidate profiles, and enhance employer-candidate communication. The system is designed with strict role-based access control to ensure data privacy and a tailored experience for both employers and candidates.

## 2. Technology Stack
* **Database:** MySQL
* **Backend & ORM:** Python 3.10+, SQLAlchemy 2.0
* **Frontend/UI:** Streamlit
* **Mock Data:** Python `Faker` library

## 3. Core Domain Entities
The system revolves around these core relationships (strictly normalized to 3NF/BCNF):
* **Accounts:** Manages secure authentication and system roles (Employer vs. Candidate).
* **Employers:** Company profile data, exclusively linked to an Account.
* **JobPositions:** Roles available, strictly linked to specific Employers.
* **Candidates:** Individual applicant profiles, exclusively linked to an Account.
* **Applications:** The intersection of Candidates applying to JobPositions, tracking submission status.
* **Interviews:** Scheduled events linked to Applications, tracking outcomes and results.

## 4. Key Workflows & Authorization (Strict Data Isolation)
The system enforces strict data isolation based on two primary user roles. Users can ONLY access data authorized for their specific `AccountID`.

### A. Employer Workflows
Employers can ONLY view, edit, and manage `JobPositions`, `Applications`, and `Interviews` tied to their own `EmployerID`.
* **HR Dashboard:** View high-level metrics for their own postings (application statistics, interview outcomes, hiring trends).
* **Job Management:** Post new jobs, update statuses (Open/Closed), and view applicant lists exclusively for their active positions.
* **Candidate Management & Search:** Search and filter candidate profiles *only* for individuals who have applied to their company.
* **Pipeline Tracking (Kanban):** Manage the hiring flow by updating application statuses (e.g., Pending -> Interviewing) and logging interview results.
* **System Automation:** Automatically trigger status updates and notifications when an interview result is recorded.

### B. Candidate Workflows
Candidates can view public job postings but can ONLY manage `Applications` and `Interviews` tied to their own `CandidateID`.
* **Global Job Board:** View, search, and filter ALL open `JobPositions` from all employers across the platform.
* **1-Click Apply:** Submit applications to open jobs seamlessly using their saved profile and `ResumeURL`.
* **My Applications Tracker:** View a timeline to track the status of their submitted applications (e.g., Applied -> Reviewed -> Interview Scheduled).
* **Interview Calendar:** View scheduled dates, times, and locations/meeting links for their upcoming interviews.