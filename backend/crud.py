"""Backend CRUD and workflow functions for the recruitment system."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import lru_cache
import hashlib
import hmac
import secrets
from typing import Any, Callable, Mapping, TypeVar

from sqlalchemy import Select, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.db import session_scope
from backend.models import (
    Account,
    Application,
    ApplicationStatusEnum,
    Candidate,
    Employer,
    Interview,
    InterviewResultEnum,
    JobPosition,
    JobStatusEnum,
    RoleEnum,
)


T = TypeVar("T")


class BackendError(Exception):
    """Base exception for backend failures that the UI can display safely."""


class AuthenticationError(BackendError):
    """Raised when login credentials are invalid for a requested account."""


class AuthorizationError(BackendError):
    """Raised when a user attempts to access another owner's data."""


class NotFoundError(BackendError):
    """Raised when a requested entity does not exist."""


class ValidationError(BackendError):
    """Raised when user input violates business rules before or during persistence."""


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents the resolved identity stored in session state after login."""

    account_id: int
    email: str
    role: str
    employer_id: int | None
    candidate_id: int | None
    display_name: str


def _serialize_value(value: Any) -> Any:
    """Convert database-native values into UI-friendly plain Python values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _serialize_mapping(row: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize row mappings returned from SQLAlchemy result sets."""

    return {key: _serialize_value(value) for key, value in row.items()}


def _run_db(operation: Callable[[Session], T]) -> T:
    """Wrap database work so CRUD code has one consistent error boundary."""

    try:
        with session_scope() as session:
            return operation(session)
    except BackendError:
        raise
    except IntegrityError as exc:
        raise ValidationError("The database rejected the operation due to invalid data.") from exc
    except SQLAlchemyError as exc:
        raise BackendError("A database error occurred while processing the request.") from exc


def _fetch_all(session: Session, sql: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Run a read-only SQL statement and normalize the result rows."""

    result = session.execute(text(sql), params or {})
    return [_serialize_mapping(row) for row in result.mappings().all()]


def _fetch_one(session: Session, sql: str, params: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Run a SQL statement and return one normalized row if present."""

    result = session.execute(text(sql), params or {})
    row = result.mappings().first()
    return None if row is None else _serialize_mapping(row)


def _consume_remaining_result_sets(result: Any) -> None:
    """Drain extra stored-procedure result sets so mysql-connector can commit safely."""

    cursor = getattr(result, "cursor", None)
    if cursor is None:
        return

    try:
        while cursor.nextset():
            # Drain rows from any trailing result sets produced by CALL statements.
            cursor.fetchall()
    except Exception:
        # Some drivers raise once there are no further sets; the main operation already succeeded.
        return


def _call_procedure(
    session: Session,
    sql: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a stored procedure and normalize its first result row."""

    result = session.execute(text(sql), params or {})
    try:
        rows = result.mappings().all()
        payload = {} if not rows else _serialize_mapping(rows[0])
        _consume_remaining_result_sets(result)
        return payload
    finally:
        result.close()


def _require_employer(session: Session, employer_id: int) -> Employer:
    """Load an employer or fail early so later ownership checks stay explicit."""

    employer = session.get(Employer, employer_id)
    if employer is None:
        raise NotFoundError("Employer not found.")
    return employer


def _require_candidate(session: Session, candidate_id: int) -> Candidate:
    """Load a candidate or fail early so later ownership checks stay explicit."""

    candidate = session.get(Candidate, candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    return candidate


def _require_position_for_employer(session: Session, employer_id: int, position_id: int) -> JobPosition:
    """Ensure a job position exists and belongs to the requesting employer."""

    statement: Select[tuple[JobPosition]] = select(JobPosition).where(
        JobPosition.position_id == position_id,
        JobPosition.employer_id == employer_id,
    )
    position = session.execute(statement).scalar_one_or_none()
    if position is None:
        raise AuthorizationError("The requested job position is not available for this employer.")
    return position


def _require_application_for_employer(session: Session, employer_id: int, application_id: int) -> Application:
    """Ensure an application exists and is tied to one of the employer's positions."""

    statement: Select[tuple[Application]] = (
        select(Application)
        .join(JobPosition, JobPosition.position_id == Application.position_id)
        .where(
            Application.application_id == application_id,
            JobPosition.employer_id == employer_id,
        )
    )
    application = session.execute(statement).scalar_one_or_none()
    if application is None:
        raise AuthorizationError("The requested application is not available for this employer.")
    return application


def _account_email(email: str) -> str:
    """Normalize user email input before account lookup."""

    normalized = email.strip().lower()
    if not normalized:
        raise ValidationError("Email is required.")
    return normalized


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 240_000
LEGACY_SCHEME = "sha256"
DEFAULT_DEMO_PASSWORD = "1"
LEGACY_GENERATOR_PASSWORD = "ChangeMe123!"


def _hash_password(password: str, *, salt: str | None = None) -> str:
    """Return a PBKDF2-based password hash string for persistent account auth."""

    password_value = password.strip()
    if not password_value:
        raise ValidationError("Password cannot be empty.")
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_value.encode("utf-8"),
        salt_value.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt_value}${digest}"


def _legacy_hash(email: str, password: str) -> str:
    """Recreate the deterministic legacy demo hash used by old seed data."""

    digest = hashlib.sha256(f"{email}:{password}".encode("utf-8")).hexdigest()
    return f"{LEGACY_SCHEME}${digest}"


def _verify_password(password: str, stored_hash: str, email: str) -> bool:
    """Verify a submitted password against supported hash formats."""

    if not stored_hash:
        return False

    if stored_hash.startswith(f"{PASSWORD_SCHEME}$"):
        try:
            _, iterations_text, salt, expected = stored_hash.split("$", 3)
            iterations = int(iterations_text)
        except ValueError:
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return hmac.compare_digest(candidate, expected)

    if stored_hash.startswith(f"{LEGACY_SCHEME}$"):
        # Compatibility path:
        # old seed data used ChangeMe123!, while the app later switched to demo password "1".
        return password in {DEFAULT_DEMO_PASSWORD, LEGACY_GENERATOR_PASSWORD}

    return False


def _validate_new_password(new_password: str, confirm_password: str) -> str:
    """Validate password update input and return a normalized new password."""

    password_value = new_password.strip()
    if len(password_value) < 6:
        raise ValidationError("New password must contain at least 6 characters.")
    if password_value != confirm_password:
        raise ValidationError("Password confirmation does not match.")
    return password_value


def authenticate_user(email: str, password: str) -> AuthenticatedUser:
    """Authenticate a demo user and resolve the linked employer or candidate profile."""

    normalized_email = _account_email(email)
    submitted_password = password.strip()
    if not submitted_password:
        raise AuthenticationError("Invalid email or password.")

    def operation(session: Session) -> AuthenticatedUser:
        statement: Select[tuple[Account]] = select(Account).where(Account.email == normalized_email)
        account = session.execute(statement).scalar_one_or_none()
        if account is None:
            raise AuthenticationError("Invalid email or password.")
        if not _verify_password(submitted_password, account.password_hash, account.email):
            raise AuthenticationError("Invalid email or password.")

        # Upgrade legacy demo hashes the first time they are used successfully.
        if account.password_hash.startswith(f"{LEGACY_SCHEME}$"):
            account.password_hash = _hash_password(submitted_password)
            session.add(account)

        if account.role == RoleEnum.EMPLOYER:
            employer = session.execute(
                select(Employer).where(Employer.account_id == account.account_id)
            ).scalar_one_or_none()
            if employer is None:
                raise NotFoundError("Employer profile is missing for this account.")
            return AuthenticatedUser(
                account_id=account.account_id,
                email=account.email,
                role=account.role.value,
                employer_id=employer.employer_id,
                candidate_id=None,
                display_name=employer.company_name,
            )

        candidate = session.execute(
            select(Candidate).where(Candidate.account_id == account.account_id)
        ).scalar_one_or_none()
        if candidate is None:
            raise NotFoundError("Candidate profile is missing for this account.")
        return AuthenticatedUser(
            account_id=account.account_id,
            email=account.email,
            role=account.role.value,
            employer_id=None,
            candidate_id=candidate.candidate_id,
            display_name=candidate.full_name,
        )

    return _run_db(operation)


def change_account_password(
    account_id: int,
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> dict[str, Any]:
    """Change the password for the authenticated account after verifying the current one."""

    current_password_value = current_password.strip()
    if not current_password_value:
        raise ValidationError("Current password is required.")
    next_password = _validate_new_password(new_password, confirm_password)

    def operation(session: Session) -> dict[str, Any]:
        account = session.get(Account, account_id)
        if account is None:
            raise NotFoundError("Account not found.")
        if not _verify_password(current_password_value, account.password_hash, account.email):
            raise AuthenticationError("Current password is incorrect.")
        if _verify_password(next_password, account.password_hash, account.email):
            raise ValidationError("New password must be different from the current password.")

        account.password_hash = _hash_password(next_password)
        session.add(account)
        return {
            "AccountID": account.account_id,
            "Message": "Password updated successfully.",
        }

    result = _run_db(operation)
    clear_read_caches()
    return result


def register_candidate_account(
    email: str,
    password: str,
    confirm_password: str,
    full_name: str,
    date_of_birth: date | None,
    phone_number: str | None,
    resume_url: str | None,
) -> AuthenticatedUser:
    """Create a new candidate account plus candidate profile, then return the authenticated session payload."""

    normalized_email = _account_email(email)
    next_password = _validate_new_password(password, confirm_password)
    normalized_name = full_name.strip()
    if not normalized_name:
        raise ValidationError("Full name is required.")

    def operation(session: Session) -> AuthenticatedUser:
        existing_account = session.execute(
            select(Account).where(Account.email == normalized_email)
        ).scalar_one_or_none()
        if existing_account is not None:
            raise ValidationError("Email is already registered.")

        account = Account(
            email=normalized_email,
            password_hash=_hash_password(next_password),
            role=RoleEnum.CANDIDATE,
            created_at=datetime.now(),
        )
        session.add(account)
        session.flush()

        candidate = Candidate(
            account_id=account.account_id,
            full_name=normalized_name,
            date_of_birth=date_of_birth,
            phone_number=(phone_number or "").strip() or None,
            resume_url=(resume_url or "").strip() or None,
        )
        session.add(candidate)
        session.flush()

        return AuthenticatedUser(
            account_id=account.account_id,
            email=account.email,
            role=account.role.value,
            employer_id=None,
            candidate_id=candidate.candidate_id,
            display_name=candidate.full_name,
        )

    result = _run_db(operation)
    clear_read_caches()
    return result


def register_employer_account(
    email: str,
    password: str,
    confirm_password: str,
    company_name: str,
    contact_number: str | None,
    address: str | None,
    description: str | None,
) -> AuthenticatedUser:
    """Create a new employer account plus employer profile, then return the authenticated session payload."""

    normalized_email = _account_email(email)
    next_password = _validate_new_password(password, confirm_password)
    normalized_company_name = company_name.strip()
    if not normalized_company_name:
        raise ValidationError("Company name is required.")

    def operation(session: Session) -> AuthenticatedUser:
        existing_account = session.execute(
            select(Account).where(Account.email == normalized_email)
        ).scalar_one_or_none()
        if existing_account is not None:
            raise ValidationError("Email is already registered.")

        account = Account(
            email=normalized_email,
            password_hash=_hash_password(next_password),
            role=RoleEnum.EMPLOYER,
            created_at=datetime.now(),
        )
        session.add(account)
        session.flush()

        employer = Employer(
            account_id=account.account_id,
            company_name=normalized_company_name,
            contact_number=(contact_number or "").strip() or None,
            address=(address or "").strip() or None,
            description=(description or "").strip() or None,
        )
        session.add(employer)
        session.flush()

        return AuthenticatedUser(
            account_id=account.account_id,
            email=account.email,
            role=account.role.value,
            employer_id=employer.employer_id,
            candidate_id=None,
            display_name=employer.company_name,
        )

    result = _run_db(operation)
    clear_read_caches()
    return result


@lru_cache(maxsize=128)
def _get_employer_profile_cached(employer_id: int) -> dict[str, Any]:
    """Cached employer profile lookup for employer-owned screens."""

    def operation(session: Session) -> dict[str, Any]:
        employer = _require_employer(session, employer_id)
        return {
            "EmployerID": employer.employer_id,
            "AccountID": employer.account_id,
            "CompanyName": employer.company_name,
            "ContactNumber": employer.contact_number,
            "Address": employer.address,
            "Description": employer.description,
        }

    return _run_db(operation)


def get_employer_profile(employer_id: int) -> dict[str, Any]:
    """Return an employer profile for rendering employer-owned screens."""

    return deepcopy(_get_employer_profile_cached(employer_id))


@lru_cache(maxsize=128)
def _get_candidate_profile_cached(candidate_id: int) -> dict[str, Any]:
    """Cached candidate profile lookup for candidate-owned screens."""

    def operation(session: Session) -> dict[str, Any]:
        candidate = _require_candidate(session, candidate_id)
        return {
            "CandidateID": candidate.candidate_id,
            "AccountID": candidate.account_id,
            "FullName": candidate.full_name,
            "DateOfBirth": _serialize_value(candidate.date_of_birth),
            "PhoneNumber": candidate.phone_number,
            "ResumeURL": candidate.resume_url,
        }

    return _run_db(operation)


def get_candidate_profile(candidate_id: int) -> dict[str, Any]:
    """Return a candidate profile for rendering candidate-owned screens."""

    return deepcopy(_get_candidate_profile_cached(candidate_id))


def list_candidate_profiles(candidate_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Return candidate profiles keyed by CandidateID for employer-side profile previews."""

    unique_ids = tuple(sorted({int(candidate_id) for candidate_id in candidate_ids if candidate_id}))
    if not unique_ids:
        return {}

    return deepcopy(_list_candidate_profiles_cached(unique_ids))


@lru_cache(maxsize=128)
def _list_candidate_profiles_cached(candidate_ids: tuple[int, ...]) -> dict[int, dict[str, Any]]:
    """Cached candidate profile preview lookup keyed by CandidateID tuple."""

    def operation(session: Session) -> dict[int, dict[str, Any]]:
        statement = (
            select(Candidate)
            .where(Candidate.candidate_id.in_(candidate_ids))
            .order_by(Candidate.full_name.asc())
        )
        candidates = session.execute(statement).scalars().all()
        return {
            candidate.candidate_id: {
                "CandidateID": candidate.candidate_id,
                "AccountID": candidate.account_id,
                "FullName": candidate.full_name,
                "DateOfBirth": _serialize_value(candidate.date_of_birth),
                "PhoneNumber": candidate.phone_number,
                "ResumeURL": candidate.resume_url,
            }
            for candidate in candidates
        }

    return _run_db(operation)


@lru_cache(maxsize=128)
def _get_employer_dashboard_metrics_cached(employer_id: int) -> dict[str, Any]:
    """Cached employer dashboard metrics lookup."""

    def operation(session: Session) -> dict[str, Any]:
        _require_employer(session, employer_id)
        metrics = _fetch_one(
            session,
            """
            SELECT *
            FROM vw_employer_dashboard_metrics
            WHERE EmployerID = :employer_id
            """,
            {"employer_id": employer_id},
        )
        if metrics is None:
            raise NotFoundError("Dashboard metrics are not available for this employer.")
        return metrics

    return _run_db(operation)


def get_employer_dashboard_metrics(employer_id: int) -> dict[str, Any]:
    """Return one row of dashboard metrics for the requesting employer only."""

    return deepcopy(_get_employer_dashboard_metrics_cached(employer_id))


@lru_cache(maxsize=128)
def _list_employer_job_application_summary_cached(employer_id: int) -> list[dict[str, Any]]:
    """Cached per-position application performance rows for one employer."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_employer(session, employer_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_job_application_summary
            WHERE EmployerID = :employer_id
            ORDER BY TotalApplications DESC, PostedDate DESC, PositionID DESC
            """,
            {"employer_id": employer_id},
        )

    return _run_db(operation)


def list_employer_job_application_summary(employer_id: int) -> list[dict[str, Any]]:
    """Return per-position application performance rows for one employer only."""

    return deepcopy(_list_employer_job_application_summary_cached(employer_id))


@lru_cache(maxsize=128)
def _list_employer_job_positions_cached(employer_id: int) -> list[dict[str, Any]]:
    """Cached job positions owned by the requesting employer."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_employer(session, employer_id)
        statement = (
            select(JobPosition)
            .where(JobPosition.employer_id == employer_id)
            .order_by(JobPosition.posted_date.desc())
        )
        positions = session.execute(statement).scalars().all()
        return [
            {
                "PositionID": position.position_id,
                "EmployerID": position.employer_id,
                "Title": position.title,
                "JobDescription": position.job_description,
                "Requirements": position.requirements,
                "Status": _serialize_value(position.status),
                "PostedDate": _serialize_value(position.posted_date),
            }
            for position in positions
        ]

    return _run_db(operation)


def list_employer_job_positions(employer_id: int) -> list[dict[str, Any]]:
    """Return only the job positions owned by the requesting employer."""

    return deepcopy(_list_employer_job_positions_cached(employer_id))


@lru_cache(maxsize=128)
def _list_employer_applications_cached(employer_id: int) -> list[dict[str, Any]]:
    """Cached applications attached to positions owned by the employer."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_employer(session, employer_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_candidate_application_tracker
            WHERE EmployerID = :employer_id
            ORDER BY ApplicationDate DESC
            """,
            {"employer_id": employer_id},
        )

    return _run_db(operation)


def list_employer_applications(employer_id: int) -> list[dict[str, Any]]:
    """Return all applications attached to positions owned by the employer."""

    return deepcopy(_list_employer_applications_cached(employer_id))


@lru_cache(maxsize=128)
def _list_employer_pending_interview_candidates_cached(employer_id: int) -> list[dict[str, Any]]:
    """Cached employer-owned applications that are ready for interview scheduling."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_employer(session, employer_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_candidate_application_tracker
            WHERE EmployerID = :employer_id
              AND InterviewDate IS NULL
              AND ApplicationStatus IN ('Pending', 'Reviewed')
            ORDER BY ApplicationDate DESC, PositionID DESC
            """,
            {"employer_id": employer_id},
        )

    return _run_db(operation)


def list_employer_pending_interview_candidates(employer_id: int) -> list[dict[str, Any]]:
    """Return employer-owned applications that are ready for interview scheduling."""

    return deepcopy(_list_employer_pending_interview_candidates_cached(employer_id))


@lru_cache(maxsize=128)
def _list_shortlisted_candidates_cached(employer_id: int) -> list[dict[str, Any]]:
    """Cached shortlisted candidates for the requesting employer."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_employer(session, employer_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_shortlisted_candidates
            WHERE EmployerID = :employer_id
            ORDER BY CandidateName ASC
            """,
            {"employer_id": employer_id},
        )

    return _run_db(operation)


def list_shortlisted_candidates(employer_id: int) -> list[dict[str, Any]]:
    """Return shortlisted candidates only for the requesting employer."""

    return deepcopy(_list_shortlisted_candidates_cached(employer_id))


@lru_cache(maxsize=128)
def _list_employer_interview_results_cached(employer_id: int) -> list[dict[str, Any]]:
    """Cached interview results for applications owned by the employer."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_employer(session, employer_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_interview_results
            WHERE EmployerID = :employer_id
            ORDER BY InterviewDate DESC
            """,
            {"employer_id": employer_id},
        )

    return _run_db(operation)


def list_employer_interview_results(employer_id: int) -> list[dict[str, Any]]:
    """Return interview results only for applications owned by the employer."""

    return deepcopy(_list_employer_interview_results_cached(employer_id))


@lru_cache(maxsize=128)
def _list_open_job_positions_cached(search_term: str | None = None) -> list[dict[str, Any]]:
    """Cached global open job positions for candidate browsing."""

    def operation(session: Session) -> list[dict[str, Any]]:
        if search_term and search_term.strip():
            wildcard = f"%{search_term.strip()}%"
            return _fetch_all(
                session,
                """
                SELECT *
                FROM vw_open_job_positions
                WHERE Title LIKE :search
                   OR CompanyName LIKE :search
                   OR JobDescription LIKE :search
                   OR Requirements LIKE :search
                ORDER BY PostedDate DESC
                """,
                {"search": wildcard},
            )

        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_open_job_positions
            ORDER BY PostedDate DESC
            """,
        )

    return _run_db(operation)


def list_open_job_positions(search_term: str | None = None) -> list[dict[str, Any]]:
    """Return globally visible open job positions for candidate browsing."""

    normalized_search = None if search_term is None else search_term.strip()
    return deepcopy(_list_open_job_positions_cached(normalized_search or None))


@lru_cache(maxsize=128)
def _list_candidate_applications_cached(candidate_id: int) -> list[dict[str, Any]]:
    """Cached applications owned by the requesting candidate."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_candidate(session, candidate_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_candidate_application_tracker
            WHERE CandidateID = :candidate_id
            ORDER BY ApplicationDate DESC
            """,
            {"candidate_id": candidate_id},
        )

    return _run_db(operation)


def list_candidate_applications(candidate_id: int) -> list[dict[str, Any]]:
    """Return only the applications owned by the requesting candidate."""

    return deepcopy(_list_candidate_applications_cached(candidate_id))


@lru_cache(maxsize=128)
def _list_candidate_interviews_cached(candidate_id: int) -> list[dict[str, Any]]:
    """Cached scheduled interviews owned by the requesting candidate."""

    def operation(session: Session) -> list[dict[str, Any]]:
        _require_candidate(session, candidate_id)
        return _fetch_all(
            session,
            """
            SELECT *
            FROM vw_candidate_application_tracker
            WHERE CandidateID = :candidate_id
              AND InterviewDate IS NOT NULL
            ORDER BY InterviewDate DESC
            """,
            {"candidate_id": candidate_id},
        )

    return _run_db(operation)


def list_candidate_interviews(candidate_id: int) -> list[dict[str, Any]]:
    """Return only scheduled interviews owned by the requesting candidate."""

    return deepcopy(_list_candidate_interviews_cached(candidate_id))


def create_job_position(
    employer_id: int,
    title: str,
    job_description: str,
    requirements: str | None,
    status: str = "Open",
) -> dict[str, Any]:
    """Create a job position directly so app writes avoid driver-specific CALL issues."""

    title_value = title.strip()
    description_value = job_description.strip()
    if not title_value:
        raise ValidationError("Job title is required.")
    if not description_value:
        raise ValidationError("Job description is required.")
    if status not in {"Open", "Closed"}:
        raise ValidationError("Job status must be Open or Closed.")

    def operation(session: Session) -> dict[str, Any]:
        _require_employer(session, employer_id)
        position = JobPosition(
            employer_id=employer_id,
            title=title_value,
            job_description=description_value,
            requirements=(requirements or "").strip() or None,
            status=JobStatusEnum(status),
            posted_date=datetime.now(),
        )
        session.add(position)
        session.flush()
        return {
            "PositionID": position.position_id,
            "Message": "Job position created successfully.",
        }

    result = _run_db(operation)
    clear_read_caches()
    return result


def update_job_status(employer_id: int, position_id: int, status: str) -> dict[str, Any]:
    """Update a job status only when the position belongs to the employer."""

    if status not in {"Open", "Closed"}:
        raise ValidationError("Job status must be Open or Closed.")

    def operation(session: Session) -> dict[str, Any]:
        position = _require_position_for_employer(session, employer_id, position_id)
        position.status = JobStatusEnum(status)
        session.add(position)
        return {
            "PositionID": position.position_id,
            "UpdatedStatus": position.status.value,
            "Message": "Job status updated successfully.",
        }

    result = _run_db(operation)
    clear_read_caches()
    return result


def submit_application(candidate_id: int, position_id: int) -> dict[str, Any]:
    """Submit an application directly so the frontend can write reliably with MySQL."""

    def operation(session: Session) -> dict[str, Any]:
        _require_candidate(session, candidate_id)
        position = session.get(JobPosition, position_id)
        if position is None:
            raise NotFoundError("Job position does not exist.")
        if position.status != JobStatusEnum.OPEN:
            raise ValidationError("Applications can only be submitted to open positions.")

        existing_application = session.execute(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.position_id == position_id,
            )
        ).scalar_one_or_none()
        if existing_application is not None:
            raise ValidationError("Candidate has already applied for this job position.")

        application = Application(
            candidate_id=candidate_id,
            position_id=position_id,
            application_date=datetime.now(),
            status=ApplicationStatusEnum.PENDING,
        )
        session.add(application)
        session.flush()
        return {
            "ApplicationID": application.application_id,
            "Message": "Application submitted successfully.",
        }

    result = _run_db(operation)
    clear_read_caches()
    return result


def clear_read_caches() -> None:
    """Clear cached read models so navigation stays fast but writes remain fresh."""

    _get_employer_profile_cached.cache_clear()
    _get_candidate_profile_cached.cache_clear()
    _list_candidate_profiles_cached.cache_clear()
    _get_employer_dashboard_metrics_cached.cache_clear()
    _list_employer_job_application_summary_cached.cache_clear()
    _list_employer_job_positions_cached.cache_clear()
    _list_employer_applications_cached.cache_clear()
    _list_employer_pending_interview_candidates_cached.cache_clear()
    _list_shortlisted_candidates_cached.cache_clear()
    _list_employer_interview_results_cached.cache_clear()
    _list_open_job_positions_cached.cache_clear()
    _list_candidate_applications_cached.cache_clear()
    _list_candidate_interviews_cached.cache_clear()


def update_candidate_profile(
    candidate_id: int,
    full_name: str,
    date_of_birth: date | None,
    phone_number: str | None,
    resume_url: str | None,
) -> dict[str, Any]:
    """Update the requesting candidate's own profile with basic validation."""

    normalized_name = full_name.strip()
    if not normalized_name:
        raise ValidationError("Full name is required.")

    def operation(session: Session) -> dict[str, Any]:
        candidate = _require_candidate(session, candidate_id)
        candidate.full_name = normalized_name
        candidate.date_of_birth = date_of_birth
        candidate.phone_number = (phone_number or "").strip() or None
        candidate.resume_url = (resume_url or "").strip() or None
        session.add(candidate)
        return {
            "CandidateID": candidate.candidate_id,
            "AccountID": candidate.account_id,
            "FullName": candidate.full_name,
            "DateOfBirth": _serialize_value(candidate.date_of_birth),
            "PhoneNumber": candidate.phone_number,
            "ResumeURL": candidate.resume_url,
        }

    result = _run_db(operation)
    clear_read_caches()
    return result


def schedule_interview(
    employer_id: int,
    application_id: int,
    interview_date: datetime,
    location_or_link: str | None,
    notes: str | None,
) -> dict[str, Any]:
    """Schedule an interview directly while preserving employer ownership checks."""

    def operation(session: Session) -> dict[str, Any]:
        application = _require_application_for_employer(session, employer_id, application_id)
        if interview_date is None:
            raise ValidationError("Interview date is required.")
        if interview_date <= application.application_date:
            raise ValidationError("Interview date must be after the application date.")

        existing_interview = session.execute(
            select(Interview).where(Interview.application_id == application_id)
        ).scalar_one_or_none()
        if existing_interview is not None:
            raise ValidationError("Interview already exists for this application.")

        interview = Interview(
            application_id=application_id,
            interview_date=interview_date,
            location_or_link=(location_or_link or "").strip() or None,
            result=InterviewResultEnum.PENDING,
            score=None,
            notes=(notes or "").strip() or None,
        )
        application.status = ApplicationStatusEnum.INTERVIEWING
        session.add(interview)
        session.add(application)
        session.flush()
        return {
            "InterviewID": interview.interview_id,
            "Message": "Interview scheduled successfully.",
        }

    result = _run_db(operation)
    clear_read_caches()
    return result


def record_interview_result(
    employer_id: int,
    application_id: int,
    result: str,
    score: float | None,
    notes: str | None,
) -> dict[str, Any]:
    """Record an interview outcome directly while leaving trigger-based status sync intact."""

    if result not in {"Pending", "Pass", "Fail"}:
        raise ValidationError("Interview result must be Pending, Pass, or Fail.")
    if result == "Pending" and score is not None:
        raise ValidationError("Pending interview results must not have a score.")
    if result in {"Pass", "Fail"} and (score is None or score < 0 or score > 10):
        raise ValidationError("Final interview results require a score between 0 and 10.")

    def operation(session: Session) -> dict[str, Any]:
        application = _require_application_for_employer(session, employer_id, application_id)
        interview = session.execute(
            select(Interview).where(Interview.application_id == application_id)
        ).scalar_one_or_none()
        if interview is None:
            raise NotFoundError("Interview does not exist for this application.")

        interview.result = InterviewResultEnum(result)
        interview.score = None if result == "Pending" else score
        cleaned_notes = (notes or "").strip()
        if cleaned_notes:
            interview.notes = cleaned_notes
        if result == "Pass":
            application.status = ApplicationStatusEnum.ACCEPTED
        elif result == "Fail":
            application.status = ApplicationStatusEnum.REJECTED
        else:
            application.status = ApplicationStatusEnum.INTERVIEWING
        session.add(interview)
        session.add(application)
        return {
            "ApplicationID": application_id,
            "InterviewResult": interview.result.value,
            "Message": "Interview result recorded successfully.",
        }

    result = _run_db(operation)
    clear_read_caches()
    return result
