"""Employer-facing Streamlit pages."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time

import streamlit as st

from backend import crud
from backend.crud import BackendError
from frontend.components import metric_row, page_header, show_records
from frontend.session import current_employer_id


def _status_breakdown(records: list[dict[str, object]]) -> Counter[str]:
    """Build a compact application status summary for employer tables."""

    statuses = [str(row.get("ApplicationStatus") or row.get("Status") or "Unknown") for row in records]
    return Counter(statuses)


def render_dashboard() -> None:
    """Render the employer dashboard overview."""

    employer_id = current_employer_id()
    profile = crud.get_employer_profile(employer_id)
    metrics = crud.get_employer_dashboard_metrics(employer_id)
    recent_positions = crud.list_employer_job_positions(employer_id)[:8]
    recent_interviews = crud.list_employer_interview_results(employer_id)[:8]

    page_header(
        profile["CompanyName"],
        "Track hiring volume, open positions, interview outcomes, and recent activity for your company.",
        eyebrow="Employer Dashboard",
    )

    metric_row(
        [
            ("Total Positions", metrics["TotalPositions"]),
            ("Open Positions", metrics["OpenPositions"]),
            ("Applications", metrics["TotalApplications"]),
            ("Interviews", metrics["TotalInterviews"]),
        ]
    )
    metric_row(
        [
            ("Interviewing", metrics["InterviewingApplications"]),
            ("Accepted", metrics["AcceptedApplications"]),
            ("Rejected", metrics["RejectedApplications"]),
            ("Avg Interview Score", metrics["AverageInterviewScore"]),
        ]
    )

    with st.expander("Company Profile", expanded=False):
        st.write(f"Contact Number: {profile['ContactNumber'] or 'Not set'}")
        st.write(f"Address: {profile['Address'] or 'Not set'}")
        st.write(f"Description: {profile['Description'] or 'Not set'}")

    positions_tab, interviews_tab = st.tabs(["Recent Job Positions", "Recent Interview Results"])
    with positions_tab:
        show_records(recent_positions, "No job positions found for this employer.", height=320)
    with interviews_tab:
        show_records(recent_interviews, "No interview results recorded yet.", height=320)


def render_jobs() -> None:
    """Render employer job creation and status management pages."""

    employer_id = current_employer_id()
    positions = crud.list_employer_job_positions(employer_id)

    page_header(
        "Job Management",
        "Create job postings, track their status, and keep your visible openings current.",
        eyebrow="Employer Workspace",
    )

    create_col, update_col = st.columns([1.25, 1])
    with create_col:
        with st.container(border=True):
            st.markdown("### Create Job Position")
            with st.form("create_job_form", clear_on_submit=True):
                title = st.text_input("Title")
                job_description = st.text_area("Job Description", height=140)
                requirements = st.text_area("Requirements", height=110)
                status = st.selectbox("Initial Status", ["Open", "Closed"], index=0)
                submitted = st.form_submit_button("Create Job Position", use_container_width=True)

            if submitted:
                try:
                    crud.create_job_position(
                        employer_id=employer_id,
                        title=title,
                        job_description=job_description,
                        requirements=requirements,
                        status=status,
                    )
                except BackendError as exc:
                    st.error(str(exc))
                else:
                    st.success("Job position created successfully.")
                    st.rerun()

    with update_col:
        with st.container(border=True):
            st.markdown("### Update Job Status")
            if not positions:
                st.info("Create a position first to manage job status.")
            else:
                options = {
                    row["PositionID"]: f"#{row['PositionID']} - {row['Title']} ({row['Status']})"
                    for row in positions
                }
                with st.form("update_job_status_form"):
                    selected_position_id = st.selectbox(
                        "Select Position",
                        options=list(options.keys()),
                        format_func=lambda position_id: options[position_id],
                    )
                    new_status = st.selectbox("New Status", ["Open", "Closed"], index=0)
                    status_submitted = st.form_submit_button("Update Status", use_container_width=True)

                if status_submitted:
                    try:
                        crud.update_job_status(
                            employer_id=employer_id,
                            position_id=int(selected_position_id),
                            status=new_status,
                        )
                    except BackendError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Job status updated successfully.")
                        st.rerun()

    status_filter = st.selectbox("Filter Positions", ["All", "Open", "Closed"], index=0)
    filtered_positions = [
        row for row in positions if status_filter == "All" or row["Status"] == status_filter
    ]
    show_records(filtered_positions, "This employer does not have any matching job positions yet.")


def render_applications() -> None:
    """Render employer application pipeline and shortlisted candidates."""

    employer_id = current_employer_id()
    applications = crud.list_employer_applications(employer_id)
    shortlisted = crud.list_shortlisted_candidates(employer_id)
    breakdown = _status_breakdown(applications)

    page_header(
        "Applications Pipeline",
        "Review every incoming application, filter by status, and focus on candidates already moving forward.",
        eyebrow="Employer Workspace",
    )

    metric_row(
        [
            ("Total", len(applications)),
            ("Pending", breakdown.get("Pending", 0)),
            ("Interviewing", breakdown.get("Interviewing", 0)),
            ("Accepted", breakdown.get("Accepted", 0)),
        ]
    )

    status_options = ["All"] + sorted({str(row["ApplicationStatus"]) for row in applications})
    search_text = st.text_input("Search Applications", placeholder="Search candidate, company, or position")
    selected_status = st.selectbox("Status Filter", status_options, index=0)

    normalized_search = search_text.strip().lower()
    filtered_applications = []
    for row in applications:
        matches_status = selected_status == "All" or row["ApplicationStatus"] == selected_status
        haystack = " ".join(
            [
                str(row.get("CandidateName", "")),
                str(row.get("PositionTitle", "")),
                str(row.get("CompanyName", "")),
            ]
        ).lower()
        matches_search = not normalized_search or normalized_search in haystack
        if matches_status and matches_search:
            filtered_applications.append(row)

    all_tab, shortlisted_tab = st.tabs(["Filtered Applications", "Shortlisted Candidates"])
    with all_tab:
        show_records(filtered_applications, "No applications matched the current filters.")
    with shortlisted_tab:
        show_records(shortlisted, "There are no shortlisted candidates yet.")


def render_interviews() -> None:
    """Render interview scheduling, scoring, and history for one employer."""

    employer_id = current_employer_id()
    applications = crud.list_employer_applications(employer_id)
    interviews = crud.list_employer_interview_results(employer_id)
    schedulable = [row for row in applications if not row.get("InterviewDate")]
    scorable = [row for row in applications if row.get("InterviewDate")]

    page_header(
        "Interview Management",
        "Schedule interviews, record outcomes, and keep the hiring pipeline synchronized through database procedures.",
        eyebrow="Employer Workspace",
    )

    schedule_tab, result_tab, history_tab = st.tabs(["Schedule", "Record Result", "History"])

    with schedule_tab:
        if not schedulable:
            st.info("All current applications already have an interview scheduled.")
        else:
            options = {
                row["ApplicationID"]: (
                    f"App #{row['ApplicationID']} - {row['CandidateName']} for {row['PositionTitle']}"
                )
                for row in schedulable
            }
            with st.form("schedule_interview_form", clear_on_submit=True):
                application_id = st.selectbox(
                    "Application",
                    options=list(options.keys()),
                    format_func=lambda selected_id: options[selected_id],
                )
                interview_day = st.date_input("Interview Date", value=date.today())
                interview_time = st.time_input("Interview Time", value=time(9, 0))
                location_or_link = st.text_input("Location or Meeting Link")
                notes = st.text_area("Notes", height=100)
                submitted = st.form_submit_button("Schedule Interview", use_container_width=True)

            if submitted:
                try:
                    crud.schedule_interview(
                        employer_id=employer_id,
                        application_id=int(application_id),
                        interview_date=datetime.combine(interview_day, interview_time),
                        location_or_link=location_or_link,
                        notes=notes,
                    )
                except BackendError as exc:
                    st.error(str(exc))
                else:
                    st.success("Interview scheduled successfully.")
                    st.rerun()

    with result_tab:
        if not scorable:
            st.info("No scheduled interviews are available to score.")
        else:
            options = {
                row["ApplicationID"]: (
                    f"App #{row['ApplicationID']} - {row['CandidateName']} for {row['PositionTitle']}"
                )
                for row in scorable
            }
            with st.form("record_interview_result_form", clear_on_submit=True):
                application_id = st.selectbox(
                    "Application to Score",
                    options=list(options.keys()),
                    format_func=lambda selected_id: options[selected_id],
                )
                result = st.selectbox("Result", ["Pending", "Pass", "Fail"], index=1)
                score = st.number_input("Score", min_value=0.0, max_value=10.0, value=8.0, step=0.5)
                notes = st.text_area("Notes", height=100)
                submitted = st.form_submit_button("Record Result", use_container_width=True)

            if submitted:
                try:
                    crud.record_interview_result(
                        employer_id=employer_id,
                        application_id=int(application_id),
                        result=result,
                        score=None if result == "Pending" else float(score),
                        notes=notes,
                    )
                except BackendError as exc:
                    st.error(str(exc))
                else:
                    st.success("Interview result recorded successfully.")
                    st.rerun()

    with history_tab:
        show_records(interviews, "There are no interviews recorded yet.")


def render_workspace() -> None:
    """Route the employer session to one of the employer-facing pages."""

    page = st.sidebar.radio("Employer Menu", ["Dashboard", "Jobs", "Applications", "Interviews"])
    if page == "Dashboard":
        render_dashboard()
    elif page == "Jobs":
        render_jobs()
    elif page == "Applications":
        render_applications()
    else:
        render_interviews()
