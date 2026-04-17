"""Candidate-facing Streamlit pages."""

from __future__ import annotations

from collections import Counter
from datetime import date

import streamlit as st

from backend import crud
from backend.crud import BackendError
from frontend.components import metric_row, page_header, parse_optional_date, show_records
from frontend.session import current_candidate_id


def _status_breakdown(records: list[dict[str, object]]) -> Counter[str]:
    """Summarize application statuses for candidate progress tracking."""

    statuses = [str(row.get("ApplicationStatus") or row.get("Status") or "Unknown") for row in records]
    return Counter(statuses)


def render_job_board() -> None:
    """Render the global job board and one-click apply flow for one candidate."""

    candidate_id = current_candidate_id()
    current_applications = crud.list_candidate_applications(candidate_id)
    open_jobs = crud.list_open_job_positions()

    page_header(
        "Job Board",
        "Browse all currently open positions across employers and apply directly from your saved profile.",
        eyebrow="Candidate Workspace",
    )

    metric_row(
        [
            ("Open Jobs", len(open_jobs)),
            ("My Applications", len(current_applications)),
            ("Scheduled Interviews", len([row for row in current_applications if row.get("InterviewDate")])),
        ]
    )

    search_term = st.text_input("Search Jobs", placeholder="Search by title, company, or keyword")
    positions = crud.list_open_job_positions(search_term=search_term)
    show_records(positions, "No open jobs matched the current search.")

    if positions:
        options = {
            row["PositionID"]: f"#{row['PositionID']} - {row['Title']} at {row['CompanyName']}"
            for row in positions
        }
        with st.form("submit_application_form", clear_on_submit=True):
            position_id = st.selectbox(
                "Select Job Position",
                options=list(options.keys()),
                format_func=lambda selected_id: options[selected_id],
            )
            submitted = st.form_submit_button("Apply Now", use_container_width=True)

        if submitted:
            try:
                crud.submit_application(candidate_id=candidate_id, position_id=int(position_id))
            except BackendError as exc:
                st.error(str(exc))
            else:
                st.success("Application submitted successfully.")
                st.rerun()


def render_applications() -> None:
    """Render the current candidate's application tracker."""

    candidate_id = current_candidate_id()
    applications = crud.list_candidate_applications(candidate_id)
    breakdown = _status_breakdown(applications)

    page_header(
        "My Applications",
        "Track every application you have submitted and monitor how each one is progressing.",
        eyebrow="Candidate Workspace",
    )

    metric_row(
        [
            ("Total", len(applications)),
            ("Pending", breakdown.get("Pending", 0)),
            ("Interviewing", breakdown.get("Interviewing", 0)),
            ("Accepted", breakdown.get("Accepted", 0)),
        ]
    )
    show_records(applications, "This candidate has not applied for any jobs yet.")


def render_interviews() -> None:
    """Render interview history split into upcoming and full history views."""

    candidate_id = current_candidate_id()
    interviews = crud.list_candidate_interviews(candidate_id)

    page_header(
        "My Interviews",
        "Review your interview schedule, outcomes, and meeting details from one place.",
        eyebrow="Candidate Workspace",
    )

    today = date.today().isoformat()
    upcoming = [row for row in interviews if str(row.get("InterviewDate", ""))[:10] >= today]
    history_tab, upcoming_tab = st.tabs(["All Interviews", "Upcoming"])
    with history_tab:
        show_records(interviews, "There are no scheduled interviews for this candidate.")
    with upcoming_tab:
        show_records(upcoming, "There are no upcoming interviews right now.")


def render_profile() -> None:
    """Render and update the current candidate's own profile."""

    candidate_id = current_candidate_id()
    profile = crud.get_candidate_profile(candidate_id)
    stored_birth_date = parse_optional_date(profile["DateOfBirth"])

    page_header(
        "My Profile",
        "Keep your candidate profile current so applications and interview workflows stay consistent.",
        eyebrow="Candidate Workspace",
    )

    summary_col, form_col = st.columns([0.9, 1.3])
    with summary_col:
        with st.container(border=True):
            st.markdown("### Current Details")
            st.write(f"**Full Name:** {profile['FullName']}")
            st.write(f"**Phone Number:** {profile['PhoneNumber'] or 'Not set'}")
            st.write(f"**Resume URL:** {profile['ResumeURL'] or 'Not set'}")
            st.write(f"**Date of Birth:** {profile['DateOfBirth'] or 'Not set'}")

    with form_col:
        with st.container(border=True):
            st.markdown("### Update Profile")
            with st.form("update_candidate_profile_form"):
                full_name = st.text_input("Full Name", value=profile["FullName"])
                use_birth_date = st.checkbox("Store Date of Birth", value=stored_birth_date is not None)
                date_of_birth = st.date_input(
                    "Date of Birth",
                    value=stored_birth_date or date.today(),
                    disabled=not use_birth_date,
                )
                phone_number = st.text_input("Phone Number", value=profile["PhoneNumber"] or "")
                resume_url = st.text_input("Resume URL", value=profile["ResumeURL"] or "")
                submitted = st.form_submit_button("Update Profile", use_container_width=True)

            if submitted:
                try:
                    crud.update_candidate_profile(
                        candidate_id=candidate_id,
                        full_name=full_name,
                        date_of_birth=date_of_birth if use_birth_date else None,
                        phone_number=phone_number,
                        resume_url=resume_url,
                    )
                except BackendError as exc:
                    st.error(str(exc))
                else:
                    st.success("Profile updated successfully.")
                    st.rerun()


def render_workspace() -> None:
    """Route the candidate session to one of the candidate-facing pages."""

    page = st.sidebar.radio("Candidate Menu", ["Job Board", "My Applications", "My Interviews", "My Profile"])
    if page == "Job Board":
        render_job_board()
    elif page == "My Applications":
        render_applications()
    elif page == "My Interviews":
        render_interviews()
    else:
        render_profile()
