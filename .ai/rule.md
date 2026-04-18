# AI Coding Standards & Guardrails


## 0. Mandatory AI Workflow: Planning, Orchestration, Execution (POE)
You are acting as an autonomous coding team. You MUST strictly follow this three-stage process for every feature request to ensure architectural integrity. Do not skip stages.
* **STAGE 1 - Planning (The Architect):** Analyze the user's request and all context files. Output a detailed, step-by-step Execution Plan. **STOP.** You must explicitly ask the user for approval. Do not write any functional code yet.
* **STAGE 2 - Orchestration (The Tech Lead):** Once the user approves the plan, break it down into a checklist of small, logical sub-tasks (e.g., `[ ] Task 1`). Announce which specific task you are beginning.
* **STAGE 3 - Execution (The Developer):** Write the code for ONLY the current sub-task. Follow all coding constraints below. Once finished, check off the task (e.g., `[x] Task 1`) and proceed to the next one.

## 1. General AI Behaviors & Python Rules
* **No Hallucinations:** Not suggested to import third-party libraries not explicitly listed in the project scope. However if necessary for some features, you can use third-party libraries. Stick to standard libraries, `sqlalchemy`, `mysql-connector-python`, `streamlit`, `faker`, and `pandas`.
* **Type Hinting:** ALWAYS use strict Python 3.10+ type hints for function arguments and return types (e.g., `def get_applications(candidate_id: int) -> List[Application]:`).
* **Documentation:** Provide concise Google-style docstrings for all functions and classes. Explain *why* the code does something, not *what* it does.

## 2. Architecture & Separation of Concerns (3-Tier)
* **Strict Layering:** The Streamlit frontend (`frontend/`) MUST NOT contain any direct database queries, SQL strings, or SQLAlchemy Session logic.
* **CRUD Isolation:** All database interactions MUST occur within `backend/crud.py`. The frontend will import and call these functions.
* **No Global Sessions:** Database sessions must be handled safely (e.g., using context managers `with Session(engine) as session:` or dependency injection) to prevent connection leaks.

## 3. Database & SQLAlchemy 2.0 Constraints
* **Modern Syntax Only:** ALWAYS use strict SQLAlchemy 2.0 syntax. 
  - Use `Mapped` and `mapped_column` for defining models. 
  - Use `Session.execute(select(...))` instead of the legacy `session.query(...)`.
* **Relationships:** Ensure all foreign key relationships are properly defined in the models using `relationship()` with appropriate `back_populates`.
* **Error Handling:** Catch `SQLAlchemyError` and `IntegrityError` in the CRUD layer. Return clean, user-friendly responses or standard Python exceptions to the UI layer; NEVER expose raw database errors to the frontend.

## 4. Security & Data Isolation (CRITICAL)
* **Always Filter by Owner:** When writing CRUD functions for Employers or Candidates, you MUST include the owner's ID in the query to prevent data leakage. 
  - *Example:* To fetch interviews for an employer, the query MUST join Applications and JobPositions and filter by `JobPositions.EmployerID == current_employer_id`.
* **Never Trust UI Input:** Validate all data inputs in the backend before committing to the database.

## 5. Streamlit UI Best Practices
* **Authentication State:** Use `st.session_state` to store the `AccountID`, `Role`, and the respective `EmployerID` or `CandidateID` of the logged-in user.
* **Layout:** Use `st.columns`, `st.tabs`, and `st.expander` to keep the UI clean and professional. Avoid long, endless scrolling pages.
* **Feedback:** ALWAYS use `st.success`, `st.error`, or `st.warning` to provide instant feedback after a user submits a form or performs an action.