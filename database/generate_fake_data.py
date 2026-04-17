"""Generate deterministic seed SQL for the recruitment management system."""

from __future__ import annotations

import argparse
import hashlib
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence

from faker import Faker


DATABASE_NAME = "recruitment_management_system"
DEFAULT_BUSINESS_COUNT = 510
DEFAULT_SEED = 20260410
DEFAULT_OUTPUT = Path("database/seed_510.sql")
DEFAULT_ACCOUNT_PASSWORD = "1"
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 240_000
EMPLOYER_ROLE = "Employer"
CANDIDATE_ROLE = "Candidate"
JOB_STATUS_OPEN = "Open"
JOB_STATUS_CLOSED = "Closed"
APPLICATION_STATUS_INTERVIEWING = "Interviewing"
APPLICATION_STATUS_REJECTED = "Rejected"
APPLICATION_STATUS_ACCEPTED = "Accepted"
INTERVIEW_RESULT_PENDING = "Pending"
INTERVIEW_RESULT_PASS = "Pass"
INTERVIEW_RESULT_FAIL = "Fail"


@dataclass(frozen=True)
class AccountRow:
    """Represents one account insert row for deterministic authentication data."""

    account_id: int
    email: str
    password_hash: str
    role: str
    created_at: datetime


@dataclass(frozen=True)
class EmployerRow:
    """Represents one employer profile tied to an employer account."""

    employer_id: int
    account_id: int
    company_name: str
    contact_number: str | None
    address: str | None
    description: str | None


@dataclass(frozen=True)
class CandidateRow:
    """Represents one candidate profile tied to a candidate account."""

    candidate_id: int
    account_id: int
    full_name: str
    date_of_birth: date | None
    phone_number: str | None
    resume_url: str | None


@dataclass(frozen=True)
class JobPositionRow:
    """Represents one job posting published by an employer."""

    position_id: int
    employer_id: int
    title: str
    job_description: str
    requirements: str | None
    status: str
    posted_date: datetime


@dataclass(frozen=True)
class ApplicationRow:
    """Represents one candidate application to a specific job position."""

    application_id: int
    candidate_id: int
    position_id: int
    application_date: datetime
    status: str


@dataclass(frozen=True)
class InterviewRow:
    """Represents one interview outcome linked one-to-one with an application."""

    interview_id: int
    application_id: int
    interview_date: datetime
    location_or_link: str | None
    result: str
    score: float | None
    notes: str | None


def parse_args() -> argparse.Namespace:
    """Parse CLI options so generation stays reproducible but configurable."""

    parser = argparse.ArgumentParser(
        description="Generate deterministic SQL seed data for the recruitment system."
    )
    parser.add_argument(
        "--business-count",
        type=int,
        default=DEFAULT_BUSINESS_COUNT,
        help="Number of Employers, Candidates, JobPositions, Applications, and Interviews.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed used for Faker and Python's random module.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output SQL file path.",
    )
    return parser.parse_args()


def build_password_hash(email: str, password: str = DEFAULT_ACCOUNT_PASSWORD) -> str:
    """Return a stable seeded password hash so generated accounts can log in consistently."""

    salt = hashlib.sha256(f"seed-salt:{email}".encode("utf-8")).hexdigest()[:32]
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def sql_quote(value: object | None) -> str:
    """Escape scalar values for MySQL insert statements."""

    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(value, date):
        return f"'{value.strftime('%Y-%m-%d')}'"
    if isinstance(value, (int, float)):
        return str(value)

    escaped = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def build_insert_statement(
    table_name: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[object | None]],
) -> str:
    """Render one multi-row INSERT statement for a table."""

    value_lines = []
    for row in rows:
        rendered_values = ", ".join(sql_quote(value) for value in row)
        value_lines.append(f"    ({rendered_values})")

    joined_values = ",\n".join(value_lines)
    rendered_columns = ", ".join(columns)
    return f"INSERT INTO {table_name} ({rendered_columns})\nVALUES\n{joined_values};"


def generate_accounts(business_count: int) -> tuple[list[AccountRow], list[AccountRow]]:
    """Create employer and candidate accounts in separate ranges for clean 1:1 mapping."""

    employer_accounts: list[AccountRow] = []
    candidate_accounts: list[AccountRow] = []
    base_created_at = datetime(2025, 1, 1, 9, 0, 0)

    for index in range(1, business_count + 1):
        employer_email = f"employer{index:04d}@example.com"
        employer_accounts.append(
            AccountRow(
                account_id=index,
                email=employer_email,
                password_hash=build_password_hash(employer_email),
                role=EMPLOYER_ROLE,
                created_at=base_created_at + timedelta(minutes=index),
            )
        )

    candidate_offset = business_count
    for index in range(1, business_count + 1):
        account_id = candidate_offset + index
        candidate_email = f"candidate{index:04d}@example.com"
        candidate_accounts.append(
            AccountRow(
                account_id=account_id,
                email=candidate_email,
                password_hash=build_password_hash(candidate_email),
                role=CANDIDATE_ROLE,
                created_at=base_created_at + timedelta(minutes=account_id),
            )
        )

    return employer_accounts, candidate_accounts


def generate_employers(fake: Faker, business_count: int) -> list[EmployerRow]:
    """Create one employer profile for each employer account."""

    employers: list[EmployerRow] = []
    for employer_id in range(1, business_count + 1):
        company_name = f"{fake.company()} Recruitment"
        employers.append(
            EmployerRow(
                employer_id=employer_id,
                account_id=employer_id,
                company_name=company_name[:120],
                contact_number=fake.phone_number()[:20],
                address=fake.address().replace("\n", ", "),
                description=fake.text(max_nb_chars=180),
            )
        )
    return employers


def generate_candidates(fake: Faker, business_count: int) -> list[CandidateRow]:
    """Create one candidate profile for each candidate account."""

    candidates: list[CandidateRow] = []
    account_offset = business_count
    for candidate_id in range(1, business_count + 1):
        full_name = fake.name()
        birth_date = fake.date_of_birth(minimum_age=21, maximum_age=45)
        candidates.append(
            CandidateRow(
                candidate_id=candidate_id,
                account_id=account_offset + candidate_id,
                full_name=full_name[:120],
                date_of_birth=birth_date,
                phone_number=fake.phone_number()[:20],
                resume_url=f"https://example.com/resumes/candidate_{candidate_id:04d}.pdf",
            )
        )
    return candidates


def generate_job_positions(fake: Faker, business_count: int) -> list[JobPositionRow]:
    """Create one job posting per employer so ownership remains easy to validate."""

    titles = [
        "Software Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Data Analyst",
        "QA Engineer",
        "DevOps Engineer",
        "Business Analyst",
        "Product Manager",
        "UI UX Designer",
        "Database Administrator",
    ]
    positions: list[JobPositionRow] = []
    base_date = datetime(2025, 2, 1, 8, 0, 0)

    for position_id in range(1, business_count + 1):
        posted_date = base_date + timedelta(days=random.randint(0, 90), hours=position_id % 8)
        status = JOB_STATUS_CLOSED if position_id % 7 == 0 else JOB_STATUS_OPEN
        title = f"{random.choice(titles)} {position_id}"
        positions.append(
            JobPositionRow(
                position_id=position_id,
                employer_id=position_id,
                title=title[:120],
                job_description=fake.paragraph(nb_sentences=5),
                requirements=fake.paragraph(nb_sentences=3),
                status=status,
                posted_date=posted_date,
            )
        )
    return positions


def application_status_for_result(result: str) -> str:
    """Map interview results to a valid application state progression."""

    if result == INTERVIEW_RESULT_PASS:
        return APPLICATION_STATUS_ACCEPTED
    if result == INTERVIEW_RESULT_FAIL:
        return APPLICATION_STATUS_REJECTED
    return APPLICATION_STATUS_INTERVIEWING


def interview_score_for_result(result: str) -> float | None:
    """Return realistic interview scores only when a final result exists."""

    if result == INTERVIEW_RESULT_PASS:
        return round(random.uniform(7.0, 10.0), 2)
    if result == INTERVIEW_RESULT_FAIL:
        return round(random.uniform(3.0, 6.8), 2)
    return None


def generate_applications_and_interviews(
    fake: Faker,
    candidates: Sequence[CandidateRow],
    positions: Sequence[JobPositionRow],
) -> tuple[list[ApplicationRow], list[InterviewRow]]:
    """Create one application and one interview per candidate with valid time ordering."""

    positions_by_id = {position.position_id: position for position in positions}
    position_ids = list(positions_by_id)

    applications: list[ApplicationRow] = []
    interviews: list[InterviewRow] = []
    result_choices = [
        INTERVIEW_RESULT_PENDING,
        INTERVIEW_RESULT_PASS,
        INTERVIEW_RESULT_FAIL,
    ]
    result_weights = [0.34, 0.33, 0.33]

    for application_id, candidate in enumerate(candidates, start=1):
        position_id = random.choice(position_ids)
        position = positions_by_id[position_id]
        application_date = position.posted_date + timedelta(days=random.randint(1, 20), hours=2)
        result = random.choices(result_choices, weights=result_weights, k=1)[0]
        score = interview_score_for_result(result)
        interview_date = application_date + timedelta(days=random.randint(1, 14), hours=3)
        location_or_link = (
            f"https://meet.example.com/interview/{application_id:04d}"
            if application_id % 2 == 0
            else f"{fake.street_address()}, {fake.city()}"[:255]
        )
        notes = fake.sentence(nb_words=12)

        applications.append(
            ApplicationRow(
                application_id=application_id,
                candidate_id=candidate.candidate_id,
                position_id=position_id,
                application_date=application_date,
                status=application_status_for_result(result),
            )
        )
        interviews.append(
            InterviewRow(
                interview_id=application_id,
                application_id=application_id,
                interview_date=interview_date,
                location_or_link=location_or_link,
                result=result,
                score=score,
                notes=notes,
            )
        )

    return applications, interviews


def render_seed_sql(
    employer_accounts: Sequence[AccountRow],
    candidate_accounts: Sequence[AccountRow],
    employers: Sequence[EmployerRow],
    candidates: Sequence[CandidateRow],
    positions: Sequence[JobPositionRow],
    applications: Sequence[ApplicationRow],
    interviews: Sequence[InterviewRow],
) -> str:
    """Assemble the final SQL file in dependency order."""

    sections = [
        "-- Seed data for recruitment_management_system",
        f"USE {DATABASE_NAME};",
        "",
        "START TRANSACTION;",
        "",
        build_insert_statement(
            "Accounts",
            ["AccountID", "Email", "PasswordHash", "Role", "CreatedAt"],
            [
                (
                    row.account_id,
                    row.email,
                    row.password_hash,
                    row.role,
                    row.created_at,
                )
                for row in [*employer_accounts, *candidate_accounts]
            ],
        ),
        "",
        build_insert_statement(
            "Employers",
            ["EmployerID", "AccountID", "CompanyName", "ContactNumber", "Address", "Description"],
            [
                (
                    row.employer_id,
                    row.account_id,
                    row.company_name,
                    row.contact_number,
                    row.address,
                    row.description,
                )
                for row in employers
            ],
        ),
        "",
        build_insert_statement(
            "Candidates",
            ["CandidateID", "AccountID", "FullName", "DateOfBirth", "PhoneNumber", "ResumeURL"],
            [
                (
                    row.candidate_id,
                    row.account_id,
                    row.full_name,
                    row.date_of_birth,
                    row.phone_number,
                    row.resume_url,
                )
                for row in candidates
            ],
        ),
        "",
        build_insert_statement(
            "JobPositions",
            ["PositionID", "EmployerID", "Title", "JobDescription", "Requirements", "Status", "PostedDate"],
            [
                (
                    row.position_id,
                    row.employer_id,
                    row.title,
                    row.job_description,
                    row.requirements,
                    row.status,
                    row.posted_date,
                )
                for row in positions
            ],
        ),
        "",
        build_insert_statement(
            "Applications",
            ["ApplicationID", "CandidateID", "PositionID", "ApplicationDate", "Status"],
            [
                (
                    row.application_id,
                    row.candidate_id,
                    row.position_id,
                    row.application_date,
                    row.status,
                )
                for row in applications
            ],
        ),
        "",
        build_insert_statement(
            "Interviews",
            [
                "InterviewID",
                "ApplicationID",
                "InterviewDate",
                "LocationOrLink",
                "Result",
                "Score",
                "Notes",
            ],
            [
                (
                    row.interview_id,
                    row.application_id,
                    row.interview_date,
                    row.location_or_link,
                    row.result,
                    row.score,
                    row.notes,
                )
                for row in interviews
            ],
        ),
        "",
        "COMMIT;",
        "",
    ]
    return "\n".join(sections)


def main() -> None:
    """Generate and write seed SQL that matches the approved row-count strategy."""

    args = parse_args()
    if args.business_count <= 0:
        raise ValueError("--business-count must be greater than 0.")

    Faker.seed(args.seed)
    random.seed(args.seed)
    fake = Faker()

    employer_accounts, candidate_accounts = generate_accounts(args.business_count)
    employers = generate_employers(fake, args.business_count)
    candidates = generate_candidates(fake, args.business_count)
    positions = generate_job_positions(fake, args.business_count)
    applications, interviews = generate_applications_and_interviews(fake, candidates, positions)

    sql_text = render_seed_sql(
        employer_accounts=employer_accounts,
        candidate_accounts=candidate_accounts,
        employers=employers,
        candidates=candidates,
        positions=positions,
        applications=applications,
        interviews=interviews,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sql_text, encoding="utf-8")

    print(
        "Generated seed data:"
        f" Accounts={len(employer_accounts) + len(candidate_accounts)},"
        f" Employers={len(employers)},"
        f" Candidates={len(candidates)},"
        f" JobPositions={len(positions)},"
        f" Applications={len(applications)},"
        f" Interviews={len(interviews)}"
    )
    print(f"Output written to {args.output}")


if __name__ == "__main__":
    main()
