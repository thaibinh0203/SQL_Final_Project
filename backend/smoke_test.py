"""Minimal smoke test for backend connectivity and core workflows."""

from __future__ import annotations

from pprint import pprint

from backend import crud
from backend.crud import BackendError


def main() -> None:
    """Exercise a few backend entrypoints so setup issues show up quickly."""

    try:
        employer_user = crud.authenticate_user("employer0001@example.com", "1")
        candidate_user = crud.authenticate_user("candidate0001@example.com", "1")

        employer_metrics = crud.get_employer_dashboard_metrics(employer_user.employer_id or 0)
        open_jobs = crud.list_open_job_positions()
        candidate_apps = crud.list_candidate_applications(candidate_user.candidate_id or 0)
        candidate_interviews = crud.list_candidate_interviews(candidate_user.candidate_id or 0)

        print("Employer login:")
        pprint(employer_user)
        print("\nCandidate login:")
        pprint(candidate_user)
        print("\nEmployer dashboard metrics:")
        pprint(employer_metrics)
        print(f"\nOpen jobs available: {len(open_jobs)}")
        print(f"Candidate applications visible: {len(candidate_apps)}")
        print(f"Candidate interviews visible: {len(candidate_interviews)}")
        print("\nBackend smoke test passed.")
    except BackendError as exc:
        print(f"Backend smoke test failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
