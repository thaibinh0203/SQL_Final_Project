"""Employer-facing Streamlit pages."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time
from html import escape

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

from backend import crud
from backend.crud import BackendError
from frontend.components import (
    info_chip,
    log_panel,
    metric_row,
    page_header,
    panel_header,
    records_frame,
    resource_card,
    show_reference_activity_table,
    show_reference_data_table,
    show_records,
    sidebar_identity_card,
    sidebar_nav_heading,
    status_badge,
)
from frontend.session import current_account_id, current_employer_id


def _status_breakdown(records: list[dict[str, object]]) -> Counter[str]:
    """Build a compact application status summary for employer tables."""

    statuses = [str(row.get("ApplicationStatus") or row.get("Status") or "Unknown") for row in records]
    return Counter(statuses)


def _performance_frame(records: list[dict[str, object]]) -> pd.DataFrame:
    """Normalize job summary rows for chart-friendly employer reporting."""

    frame = records_frame(records)
    if frame.empty:
        return frame

    frame["PositionLabel"] = frame.apply(
        lambda row: f"#{int(row['PositionID'])} - {row['PositionTitle']}",
        axis=1,
    )
    frame["PostedDate"] = pd.to_datetime(frame["PostedDate"], errors="coerce")

    numeric_columns = [
        "TotalApplications",
        "PendingApplications",
        "ReviewedApplications",
        "InterviewingApplications",
        "RejectedApplications",
        "AcceptedApplications",
        "AverageInterviewScore",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

    return frame


def _int_metric(value: object) -> int:
    """Normalize dashboard metric values into safe integers for UI display."""

    if value in (None, ""):
        return 0
    return int(float(value))


def _float_metric(value: object) -> float:
    """Normalize dashboard metric values into safe floats for UI display."""

    if value in (None, ""):
        return 0.0
    return round(float(value), 2)


def _short_text(value: object, limit: int = 44) -> str:
    """Trim long table subtitles so activity rows stay compact."""

    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _job_activity_rows(records: list[dict[str, object]]) -> list[dict[str, str]]:
    """Map job-position rows into the deployment-style activity table shape."""

    return [
        {
            "title": str(row.get("Title") or "Untitled Position"),
            "subtitle": (
                f"#{row.get('PositionID')} | "
                f"{_short_text(row.get('Requirements') or row.get('JobDescription') or 'Recruitment position')}"
            ),
            "status": str(row.get("Status") or "Unknown"),
            "branch": f"Position {row.get('PositionID')}",
            "time": str(row.get("PostedDate") or "")[:16] or "-",
        }
        for row in records
    ]


def _application_activity_rows(records: list[dict[str, object]]) -> list[dict[str, str]]:
    """Map application rows into the deployment-style activity table shape."""

    return [
        {
            "title": str(row.get("CandidateName") or "Unknown Candidate"),
            "subtitle": f"App #{row.get('ApplicationID')} | {row.get('PositionTitle')}",
            "status": str(row.get("ApplicationStatus") or "Unknown"),
            "branch": str(row.get("CompanyName") or "Company"),
            "time": str(row.get("ApplicationDate") or "")[:16] or "-",
        }
        for row in records
    ]


def _shortlisted_activity_rows(records: list[dict[str, object]]) -> list[dict[str, str]]:
    """Map shortlisted candidate rows into the deployment-style activity table shape."""

    return [
        {
            "title": str(row.get("CandidateName") or "Unknown Candidate"),
            "subtitle": (
                f"{row.get('PositionTitle')} | "
                f"{_short_text(row.get('PhoneNumber') or row.get('ResumeURL') or 'Candidate shortlisted')}"
            ),
            "status": str(row.get("ApplicationStatus") or row.get("InterviewResult") or "Unknown"),
            "branch": str(row.get("CompanyName") or "Company"),
            "time": str(row.get("InterviewDate") or "No interview")[:16] or "-",
        }
        for row in records
    ]


def _interview_activity_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Map interview history rows into the deployment-style activity table shape."""

    rows: list[dict[str, str]] = []
    for row in records:
        score = row.get("Score")
        score_text = f"{float(score):.1f}" if score not in (None, "") else "-"
        application_status = str(row.get("ApplicationStatus") or "Unknown")
        notes = _short_text(row.get("Notes") or "No notes", limit=78)
        rows.append(
            {
                "title": str(row.get("CandidateName") or "Unknown Candidate"),
                "subtitle": f"Interview #{row.get('InterviewID')} | {row.get('PositionTitle') or 'Interview'}",
                "details": [
                    f"Application #{row.get('ApplicationID')} | {row.get('CompanyName') or 'Company'}",
                    f"Score: {score_text} | Application Status: {application_status}",
                    f"Notes: {notes}",
                ],
                "status": str(row.get("Result") or "Pending"),
                "branch": str(row.get("LocationOrLink") or "Interview slot"),
                "time": str(row.get("InterviewDate") or "No date")[:16] or "-",
            }
        )
    return rows


def _pending_interview_activity_rows(records: list[dict[str, object]]) -> list[dict[str, str]]:
    """Map interview-ready applications into the activity table shape."""

    return [
        {
            "title": str(row.get("CandidateName") or "Unknown Candidate"),
            "subtitle": f"App #{row.get('ApplicationID')} | {row.get('PositionTitle') or 'Job Position'}",
            "status": str(row.get("ApplicationStatus") or "Pending"),
            "branch": str(row.get("CompanyName") or "Company"),
            "time": str(row.get("ApplicationDate") or "No date")[:16] or "-",
        }
        for row in records
    ]


def _candidate_profile_map(records: list[dict[str, object]]) -> dict[int, dict[str, object]]:
    """Fetch candidate profiles for a record list keyed by CandidateID."""

    candidate_ids = sorted(
        {
            int(row["CandidateID"])
            for row in records
            if row.get("CandidateID") not in (None, "")
        }
    )
    if not candidate_ids:
        return {}
    return crud.list_candidate_profiles(candidate_ids)


def _render_candidate_profile_expanders(
    records: list[dict[str, object]],
    profile_map: dict[int, dict[str, object]],
    *,
    section_title: str,
    section_copy: str,
) -> None:
    """Render expandable applicant profile panels under application tables."""

    if not records:
        return

    st.divider()
    panel_header(section_title, section_copy, eyebrow="Profiles", badge=f"{len(records)} applicants")

    for row in records:
        candidate_id = int(row.get("CandidateID") or 0)
        profile = profile_map.get(candidate_id, {})
        candidate_name = str(profile.get("FullName") or row.get("CandidateName") or "Unknown Candidate")
        position_title = str(row.get("PositionTitle") or "Job Position")
        application_id = row.get("ApplicationID") or "-"
        application_status = str(row.get("ApplicationStatus") or "Unknown")
        company_name = str(row.get("CompanyName") or "Company")
        application_date = str(row.get("ApplicationDate") or "No application date")[:19]
        interview_date = str(row.get("InterviewDate") or "")[:19]
        interview_result = row.get("InterviewResult") or "-"
        interview_score = row.get("InterviewScore")
        score_text = f"{float(interview_score):.1f}" if interview_score not in (None, "") else "-"
        location_or_link = row.get("LocationOrLink") or "-"
        phone_number = profile.get("PhoneNumber") or row.get("PhoneNumber") or "-"
        resume_url = profile.get("ResumeURL") or row.get("ResumeURL") or ""
        date_of_birth = profile.get("DateOfBirth") or "-"
        resume_html = (
            f'<p class="profile-expander-line"><strong>Resume:</strong> <a href="{escape(str(resume_url))}" target="_blank">Open Resume</a></p>'
            if resume_url
            else '<p class="profile-expander-line"><strong>Resume:</strong> -</p>'
        )
        interview_html = ""
        if interview_date:
            location_html = (
                f'<p class="profile-expander-line"><strong>Location / Link:</strong> {escape(str(location_or_link))}</p>'
                if location_or_link != "-"
                else ""
            )
            interview_html = (
                f'<p class="profile-expander-line"><strong>Interview Date:</strong> {escape(interview_date)}</p>'
                f'<p class="profile-expander-line"><strong>Interview Result:</strong> {escape(str(interview_result))}</p>'
                f'<p class="profile-expander-line"><strong>Interview Score:</strong> {escape(score_text)}</p>'
                f"{location_html}"
            )

        st.markdown(
            f"""
            <details class="profile-expander">
                <summary>{escape(candidate_name)} | {escape(position_title)} | App #{escape(str(application_id))}</summary>
                <div class="profile-expander-body">
                    <div class="profile-expander-grid">
                        <div class="profile-expander-section">
                            <h4>Candidate Profile</h4>
                            <p class="profile-expander-line"><strong>Full Name:</strong> {escape(candidate_name)}</p>
                            <p class="profile-expander-line"><strong>Candidate ID:</strong> {escape(str(candidate_id or '-'))}</p>
                            <p class="profile-expander-line"><strong>Date of Birth:</strong> {escape(str(date_of_birth))}</p>
                            <p class="profile-expander-line"><strong>Phone Number:</strong> {escape(str(phone_number))}</p>
                            {resume_html}
                        </div>
                        <div class="profile-expander-section">
                            <h4>Application Details</h4>
                            <p class="profile-expander-line"><strong>Company:</strong> {escape(company_name)}</p>
                            <p class="profile-expander-line"><strong>Position:</strong> {escape(position_title)}</p>
                            <p class="profile-expander-line"><strong>Application ID:</strong> {escape(str(application_id))}</p>
                            <p class="profile-expander-line"><strong>Application Status:</strong> {escape(application_status)}</p>
                            <p class="profile-expander-line"><strong>Applied At:</strong> {escape(application_date)}</p>
                            {interview_html}
                        </div>
                    </div>
                </div>
            </details>
            """,
            unsafe_allow_html=True,
        )


def render_account() -> None:
    """Render account security controls for the authenticated employer account."""

    account_id = current_account_id()
    page_header(
        "Account Security",
        "Create your own password or change the current one used to sign in to the employer workspace.",
        eyebrow="Employer Workspace",
    )
    with st.container(border=True):
        panel_header(
            "Change Password",
            "Use your current password to set a new login password for this employer account.",
            eyebrow="Security",
            badge="Password",
        )
        st.caption("For older seeded accounts, the initial demo password may still be `1`.")
        with st.form("employer_change_password_form", clear_on_submit=True):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password", use_container_width=True)

        if submitted:
            try:
                crud.change_account_password(
                    account_id=account_id,
                    current_password=current_password,
                    new_password=new_password,
                    confirm_password=confirm_password,
                )
            except BackendError as exc:
                st.error(str(exc))
            else:
                st.success("Password updated successfully.")


def _applications_by_position_chart(records: list[dict[str, object]]) -> pd.DataFrame:
    """Build a chart frame for total applications per job position."""

    frame = records_frame(records)
    if frame.empty:
        return frame

    frame["PositionTitle"] = frame["PositionTitle"].fillna("Unknown Position")
    frame["PositionID"] = pd.to_numeric(frame["PositionID"], errors="coerce").fillna(0).astype(int)
    frame["TotalApplications"] = pd.to_numeric(frame["TotalApplications"], errors="coerce").fillna(0).astype(int)
    frame = frame.sort_values(by=["TotalApplications", "PositionID"], ascending=[False, False]).copy()
    frame["Job"] = frame.apply(
        lambda row: f"#{int(row['PositionID'])} - {_short_text(row['PositionTitle'], limit=22)}",
        axis=1,
    )
    chart = frame.set_index("Job")[["TotalApplications"]]
    chart.columns = ["Applications"]
    return chart


def _scheduled_interviews_by_month_chart(records: list[dict[str, object]]) -> pd.DataFrame:
    """Build a monthly chart frame for scheduled interviews."""

    frame = records_frame(records)
    if frame.empty:
        return frame

    frame["InterviewDate"] = pd.to_datetime(frame["InterviewDate"], errors="coerce")
    frame = frame.dropna(subset=["InterviewDate"]).copy()
    if frame.empty:
        return pd.DataFrame()

    monthly = (
        frame.groupby(frame["InterviewDate"].dt.to_period("M"))
        .size()
        .rename("ScheduledInterviews")
        .to_frame()
        .sort_index()
    )
    monthly.index = monthly.index.astype(str)
    monthly.columns = ["Scheduled Interviews"]
    return monthly


def _pass_rate_trend_chart(pass_rate: float) -> pd.DataFrame:
    """Build a compact pass-rate trend line for the dashboard."""

    baseline = max(pass_rate, 1.0)
    values = [round(baseline * factor / 6, 2) for factor in [0.2, 0.35, 0.55, 0.8, 1.0, 0.75]]
    return pd.DataFrame({"Pass Rate": values})


def _outcome_ratio_frame(pass_count: int, fail_count: int, pending_count: int) -> pd.DataFrame:
    """Build a small ratio table for pass/fail/pending visualization."""

    frame = pd.DataFrame(
        {
            "Outcome": ["Pass", "Fail", "Pending"],
            "Count": [pass_count, fail_count, pending_count],
        }
    )
    total = int(frame["Count"].sum())
    if total <= 0:
        frame["Percentage"] = 0.0
    else:
        frame["Percentage"] = (frame["Count"] / total * 100).round(1)
    frame["RatioValue"] = frame["Percentage"] / 100.0
    return frame


def _render_outcome_pie_chart(
    title: str,
    pass_count: int,
    fail_count: int,
    pending_count: int,
    *,
    empty_message: str,
    inner_radius: int = 45,
) -> None:
    """Render a pass/fail/pending pie chart without requiring extra chart libraries."""

    st.markdown(f"### {title}")
    ratio_frame = _outcome_ratio_frame(pass_count, fail_count, pending_count)
    if int(ratio_frame["Count"].sum()) <= 0:
        st.info(empty_message)
        return

    chart_frame = ratio_frame[ratio_frame["Count"] > 0].copy()
    if chart_frame.empty:
        st.info(empty_message)
        return

    st.vega_lite_chart(
        chart_frame,
        {
            "mark": {"type": "arc", "innerRadius": inner_radius},
            "encoding": {
                "theta": {"field": "RatioValue", "type": "quantitative"},
                "color": {
                    "field": "Outcome",
                    "type": "nominal",
                    "scale": {"range": ["#557c3e", "#b65a4d", "#d4a94d"]},
                    "legend": {"title": None},
                },
                "tooltip": [
                    {"field": "Outcome", "type": "nominal"},
                    {"field": "Count", "type": "quantitative"},
                    {"field": "Percentage", "type": "quantitative", "format": ".1f"},
                ],
            },
        },
        use_container_width=True,
    )

    display = ratio_frame.copy()
    display["Percentage"] = display["Percentage"].map(lambda value: f"{value:.1f}%")
    show_reference_data_table(
        display[["Outcome", "Count", "Percentage"]].to_dict(orient="records"),
        "No interview outcomes are available.",
        headers=["Outcome", "Count", "Percentage"],
        widths=[1.6, 1.0, 1.2],
    )


def render_dashboard() -> None:
    """Render the employer dashboard in the light reference layout."""

    employer_id = current_employer_id()
    profile = crud.get_employer_profile(employer_id)
    metrics = crud.get_employer_dashboard_metrics(employer_id)
    recent_positions = crud.list_employer_job_positions(employer_id)[:4]
    all_interviews = crud.list_employer_interview_results(employer_id)
    recent_interviews = all_interviews[:6]
    recent_applications = crud.list_employer_applications(employer_id)[:6]
    summary_records = crud.list_employer_job_application_summary(employer_id)
    summary_by_position = {int(row["PositionID"]): row for row in summary_records}
    total_positions = _int_metric(metrics.get("TotalPositions"))
    open_positions = _int_metric(metrics.get("OpenPositions"))
    total_applications = _int_metric(metrics.get("TotalApplications"))
    total_interviews = _int_metric(metrics.get("TotalInterviews"))
    passed_interviews = _int_metric(metrics.get("PassedInterviews"))
    failed_interviews = _int_metric(metrics.get("FailedInterviews"))
    interviewing_applications = _int_metric(metrics.get("InterviewingApplications"))
    accepted_applications = _int_metric(metrics.get("AcceptedApplications"))
    rejected_applications = _int_metric(metrics.get("RejectedApplications"))
    average_interview_score = _float_metric(metrics.get("AverageInterviewScore"))
    closed_positions = max(total_positions - open_positions, 0)
    pass_rate = round((passed_interviews / total_interviews) * 100, 1) if total_interviews else 0.0

    header_col, action_col = st.columns([3.6, 1.55], gap="small")
    with header_col:
        page_header(
            "Project Overview",
            "Manage your applications, interviews, job positions, and analytics from one structured workspace.",
            eyebrow=profile["CompanyName"],
        )
    with action_col:
        st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
        if st.button("View Jobs", use_container_width=True):
            st.session_state["employer_nav_target"] = "Jobs"
            st.rerun()

    metric_row(
        [
            ("Total Jobs", total_positions),
            ("Open Jobs", open_positions),
            ("Total Applications", total_applications),
            ("Scheduled Interviews", total_interviews),
        ]
    )
    metric_row(
        [
            ("Passed Interviews", passed_interviews),
            ("Failed Interviews", failed_interviews),
            ("Avg Interview Score", average_interview_score),
            ("Interview Pass Rate", f"{pass_rate}%"),
        ]
    )

    st.markdown("<div class='hero-eyebrow' style='margin-bottom:0.75rem;'>POSITIONS</div>", unsafe_allow_html=True)
    card_columns = st.columns(4, gap="small")
    for index, column in enumerate(card_columns):
        with column:
            if index < len(recent_positions):
                position = recent_positions[index]
                summary = summary_by_position.get(int(position["PositionID"]), {})
                latest_application = pd.to_datetime(summary.get("LatestApplicationDate"), errors="coerce")
                time_label = (
                    latest_application.strftime("%d %b") if pd.notna(latest_application) else str(position["PostedDate"])[:10]
                )
                subtitle = f"{position['Status']} | {summary.get('TotalApplications', 0)} applications"
                meta = str(position.get("Requirements") or position.get("JobDescription") or "Recruitment position")[:42]
                resource_card(
                    position["Title"],
                    subtitle,
                    meta,
                    str(position["Status"]),
                    time_label,
                )
            else:
                with st.container(border=True):
                    panel_header("Empty Slot", "Add another job position to populate this dashboard row.", eyebrow="Positions")
                    st.info("No additional job position is available yet.")

    main_left, main_right = st.columns([2.05, 0.95], gap="large")
    with main_left:
        with st.container(border=True):
            panel_header(
                "Recent Applications",
                "Incoming applications across your most recent positions.",
                eyebrow="Pipeline",
                badge="View All",
            )
            application_rows = [
                {
                    "title": row.get("CandidateName"),
                    "subtitle": f"{row.get('ApplicationID')} | {row.get('PositionTitle')}",
                    "status": row.get("ApplicationStatus"),
                    "branch": row.get("CompanyName"),
                    "time": str(row.get("ApplicationDate"))[:16],
                }
                for row in recent_applications
            ]
            show_reference_activity_table(application_rows, "No recent applications are available.")

    with main_right:
        with st.container(border=True):
            panel_header(
                "Hiring Trends",
                "Track application volume by job and scheduled interviews by month.",
                eyebrow="Metrics",
                badge="By Job / Month",
            )

            applications_chart = _applications_by_position_chart(summary_records)
            st.markdown("**Applications by Job Position**")
            if applications_chart.empty:
                st.info("No application totals are available for the current job positions yet.")
            else:
                st.line_chart(applications_chart, use_container_width=True, height=180)

            monthly_interviews_chart = _scheduled_interviews_by_month_chart(all_interviews)
            st.markdown("**Scheduled Interviews by Month**")
            if monthly_interviews_chart.empty:
                st.info("No scheduled interviews are available yet.")
            else:
                st.line_chart(monthly_interviews_chart, use_container_width=True, height=180)

            st.markdown("**Pass Rate**")
            st.caption(f"{pass_rate}%")
            st.line_chart(_pass_rate_trend_chart(pass_rate), use_container_width=True, height=150)

    bottom_left, bottom_right = st.columns([1.35, 1.2], gap="large")
    with bottom_left:
        activity_lines: list[str] = []
        for row in recent_applications[:4]:
            activity_lines.append(
                f"{str(row.get('ApplicationDate'))[:19]} | {row.get('CandidateName')} applied for {row.get('PositionTitle')}"
            )
        for row in recent_interviews[:4]:
            activity_lines.append(
                f"{str(row.get('InterviewDate'))[:19]} | interview result {row.get('Result')} for {row.get('CandidateName')}"
            )
        log_panel("Live Logs", activity_lines, eyebrow="Activity", badge="Live")

    with bottom_right:
        with st.container(border=True):
            panel_header(
                "Position Summary",
                "A compact summary of application and interview outcomes by position.",
                eyebrow="Summary",
                badge=f"{len(summary_records)} jobs",
            )
            summary_rows = [
                {
                    "Position": row.get("PositionTitle"),
                    "Applications": _int_metric(row.get("TotalApplications")),
                    "Accepted": _int_metric(row.get("AcceptedApplications")),
                    "Rejected": _int_metric(row.get("RejectedApplications")),
                    "Avg Score": f"{_float_metric(row.get('AverageInterviewScore')):.2f}",
                }
                for row in summary_records[:6]
            ]
            show_reference_data_table(
                summary_rows,
                "No job summary data is available.",
                headers=["Position", "Applications", "Accepted", "Rejected", "Avg Score"],
                widths=[2.2, 1.1, 1.0, 1.0, 1.0],
                right_align=[False, True, True, True, True],
            )


def render_performance() -> None:
    """Render employer-facing performance charts for each posted position."""

    employer_id = current_employer_id()
    summary_records = crud.list_employer_job_application_summary(employer_id)

    page_header(
        "Posting Performance",
        "Use job-level application summaries to compare which postings attract candidates and move them through the pipeline.",
        eyebrow="Employer Analytics",
    )

    if not summary_records:
        st.info("No job posting performance data is available yet.")
        return

    frame = _performance_frame(summary_records)
    position_status = st.selectbox("Position Status", ["All", "Open", "Closed"], index=0)
    rank_by = st.selectbox(
        "Rank Positions By",
        ["TotalApplications", "AcceptedApplications", "InterviewingApplications", "AverageInterviewScore"],
        index=0,
    )

    filtered = frame.copy()
    if position_status != "All":
        filtered = filtered[filtered["PositionStatus"] == position_status]

    if filtered.empty:
        st.info("No positions match the current performance filters.")
        return

    max_positions = min(12, len(filtered))
    if max_positions == 1:
        position_count = 1
        st.caption("Only 1 position matches the current filter.")
    else:
        position_count = st.slider(
            "Positions To Display",
            min_value=1,
            max_value=max_positions,
            value=min(8, max_positions),
        )

    metric_labels = {
        "TotalApplications": "Total Applications",
        "AcceptedApplications": "Accepted Applications",
        "InterviewingApplications": "Interviewing Applications",
        "AverageInterviewScore": "Average Interview Score",
    }

    ranked = (
        filtered.sort_values(by=[rank_by, "PostedDate", "PositionID"], ascending=[False, False, False])
        .head(position_count)
        .copy()
    )

    scored = filtered[filtered["AverageInterviewScore"] > 0]
    average_score = round(float(scored["AverageInterviewScore"].mean()), 2) if not scored.empty else 0.0
    metric_row(
        [
            ("Tracked Positions", int(filtered["PositionID"].nunique())),
            ("Applications", int(filtered["TotalApplications"].sum())),
            ("Accepted", int(filtered["AcceptedApplications"].sum())),
            ("Avg Interview Score", average_score),
        ]
    )

    applications_tab, pipeline_tab, table_tab = st.tabs(
        ["Applications", "Pipeline Breakdown", "Detailed Summary"]
    )

    with applications_tab:
        chart_col, score_col = st.columns(2)
        with chart_col:
            st.markdown(f"### Top Positions By {metric_labels[rank_by]}")
            primary_chart = ranked.set_index("PositionLabel")[[rank_by]]
            primary_chart.columns = [metric_labels[rank_by]]
            st.bar_chart(primary_chart, use_container_width=True)
        with score_col:
            if rank_by == "TotalApplications":
                st.markdown("### Accepted Applications")
                secondary_chart = ranked.set_index("PositionLabel")[["AcceptedApplications"]]
                secondary_chart.columns = ["Accepted Applications"]
                st.bar_chart(secondary_chart, use_container_width=True)
            else:
                st.markdown("### Total Applications")
                secondary_chart = ranked.set_index("PositionLabel")[["TotalApplications"]]
                secondary_chart.columns = ["Total Applications"]
                st.bar_chart(secondary_chart, use_container_width=True)

        if rank_by == "AverageInterviewScore" and ranked["AverageInterviewScore"].max() <= 0:
            st.info("The selected positions do not have interview scores yet, so the ranking is currently flat at 0.")

        if rank_by != "AverageInterviewScore" and ranked[rank_by].max() <= 0:
            st.info(f"The selected positions all have {metric_labels[rank_by].lower()} equal to 0 right now.")

    with pipeline_tab:
        st.markdown("### Application Status Mix By Position")
        st.bar_chart(
            ranked.set_index("PositionLabel")[
                [
                    "PendingApplications",
                    "ReviewedApplications",
                    "InterviewingApplications",
                    "AcceptedApplications",
                    "RejectedApplications",
                ]
            ],
            use_container_width=True,
        )

    with table_tab:
        display = ranked[
            [
                "PositionID",
                "PositionTitle",
                "PositionStatus",
                "PostedDate",
                "TotalApplications",
                "PendingApplications",
                "ReviewedApplications",
                "InterviewingApplications",
                "AcceptedApplications",
                "RejectedApplications",
                "AverageInterviewScore",
                "LatestApplicationDate",
            ]
        ].copy()
        display["PostedDate"] = display["PostedDate"].dt.strftime("%Y-%m-%d %H:%M:%S")
        display["LatestApplicationDate"] = pd.to_datetime(display["LatestApplicationDate"], errors="coerce").dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        st.dataframe(display, use_container_width=True, height=360)


def render_jobs() -> None:
    """Render employer job creation and status management pages."""

    employer_id = current_employer_id()
    positions = crud.list_employer_job_positions(employer_id)
    summary_records = crud.list_employer_job_application_summary(employer_id)
    summary_by_position = {int(row["PositionID"]): row for row in summary_records}

    page_header(
        "Job Management",
        "Create job postings, track their status, and keep your visible openings current.",
        eyebrow="Employer Workspace",
    )

    create_col, update_col = st.columns([1.25, 1])
    with create_col:
        with st.container(border=True):
            panel_header(
                "Create Job Position",
                "Publish a new position with title, description, requirements, and initial status.",
                eyebrow="Creation",
            )
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
            panel_header(
                "Update Job Status",
                "Move any owned job between open and closed states.",
                eyebrow="Control",
            )
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

    if positions:
        with st.container(border=True):
            panel_header(
                "Job Position Snapshot",
                "Inspect application volume, interview outcomes, and current status for one selected job.",
                eyebrow="Inspection",
                badge=f"{len(positions)} jobs",
            )
            snapshot_options = {
                int(row["PositionID"]): f"#{row['PositionID']} - {row['Title']} ({row['Status']})"
                for row in positions
            }
            selected_snapshot_id = st.selectbox(
                "Select Job Position",
                options=list(snapshot_options.keys()),
                format_func=lambda position_id: snapshot_options[position_id],
                key="job_snapshot_position_id",
            )

            snapshot = summary_by_position.get(int(selected_snapshot_id))
            if snapshot is not None:
                total_applications = _int_metric(snapshot.get("TotalApplications"))
                passed_interviews = _int_metric(snapshot.get("AcceptedApplications"))
                failed_interviews = _int_metric(snapshot.get("RejectedApplications"))
                pending_interviews = _int_metric(snapshot.get("InterviewingApplications"))
                average_score = _float_metric(snapshot.get("AverageInterviewScore"))
                latest_application = pd.to_datetime(snapshot.get("LatestApplicationDate"), errors="coerce")
                latest_application_text = (
                    latest_application.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(latest_application) else "No applications yet"
                )

                metric_row(
                    [
                        ("Applicants", total_applications),
                        ("Passed Interviews", passed_interviews),
                        ("Failed Interviews", failed_interviews),
                        ("Pending Interviews", pending_interviews),
                    ]
                )
                metric_row(
                    [
                        ("Average Score", average_score),
                        ("Job Status", snapshot.get("PositionStatus", "Unknown")),
                    ]
                )

                detail_col, score_col = st.columns([1.05, 0.95])
                with detail_col:
                    info_chip(
                        "Selected Job",
                        [
                            f"Title: {snapshot.get('PositionTitle', 'Unknown')}",
                            f"Status: {snapshot.get('PositionStatus', 'Unknown')}",
                            f"Posted Date: {snapshot.get('PostedDate', 'Unknown')}",
                            f"Latest Application: {latest_application_text}",
                        ],
                    )
                with score_col:
                    _render_outcome_pie_chart(
                        "Interview Outcome Ratio",
                        passed_interviews,
                        failed_interviews,
                        pending_interviews,
                        empty_message="This job position does not have pass, fail, or pending interview outcomes yet.",
                    )

                    job_snapshot_frame = pd.DataFrame(
                        {
                            "Count": [
                                total_applications,
                                passed_interviews,
                                failed_interviews,
                                pending_interviews,
                            ]
                        },
                        index=["Applicants", "Pass", "Fail", "Pending"],
                    )
                    st.bar_chart(job_snapshot_frame, use_container_width=True)

    status_filter = st.selectbox("Filter Positions", ["All", "Open", "Closed"], index=0)
    filtered_positions = [
        row for row in positions if status_filter == "All" or row["Status"] == status_filter
    ]
    with st.container(border=True):
        panel_header(
            "All Owned Positions",
            "Browse the full portfolio of jobs owned by this employer.",
            eyebrow="Inventory",
            badge=f"{len(filtered_positions)} shown",
        )
        show_reference_activity_table(
            _job_activity_rows(filtered_positions),
            "This employer does not have any matching job positions yet.",
            headers=["Job Position", "Status", "Reference", "Posted"],
        )


def render_applications() -> None:
    """Render employer application pipeline and shortlisted candidates."""

    employer_id = current_employer_id()
    applications = crud.list_employer_applications(employer_id)
    ready_for_interview = crud.list_employer_pending_interview_candidates(employer_id)
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
            ("Ready to Schedule", len(ready_for_interview)),
            ("Interviewing", breakdown.get("Interviewing", 0)),
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

    filtered_profiles = _candidate_profile_map(filtered_applications)
    shortlisted_profiles = _candidate_profile_map(shortlisted)

    all_tab, ready_tab, shortlisted_tab = st.tabs(
        ["Filtered Applications", "Ready for Interview", "Shortlisted Candidates"]
    )
    with all_tab:
        with st.container(border=True):
            panel_header("Filtered Applications", "Applications matching your current filters.", eyebrow="Review")
            show_reference_activity_table(
                _application_activity_rows(filtered_applications),
                "No applications matched the current filters.",
                headers=["Applicant", "Status", "Company", "Applied"],
            )
            _render_candidate_profile_expanders(
                filtered_applications,
                filtered_profiles,
                section_title="Applicant Profiles",
                section_copy="Open any applicant below to review their detailed profile and application information.",
            )
    with ready_tab:
        with st.container(border=True):
            panel_header("Ready For Interview", "Applications that can be moved directly into interview scheduling.", eyebrow="Action")
            show_reference_activity_table(
                _application_activity_rows(ready_for_interview),
                "There are no new applications ready for interview scheduling right now.",
                headers=["Applicant", "Status", "Company", "Applied"],
            )
    with shortlisted_tab:
        with st.container(border=True):
            panel_header("Shortlisted Candidates", "Candidates already moving deeper into the hiring funnel.", eyebrow="Shortlist")
            show_reference_activity_table(
                _shortlisted_activity_rows(shortlisted),
                "There are no shortlisted candidates yet.",
                headers=["Candidate", "Status", "Company", "Interview"],
            )
            _render_candidate_profile_expanders(
                shortlisted,
                shortlisted_profiles,
                section_title="Shortlisted Candidate Profiles",
                section_copy="Open any shortlisted applicant below to review their profile and interview details.",
            )


def render_interviews() -> None:
    """Render interview scheduling, scoring, and history for one employer."""

    employer_id = current_employer_id()
    pending_candidates = crud.list_employer_pending_interview_candidates(employer_id)
    interviews = crud.list_employer_interview_results(employer_id)
    scheduled_candidates = crud.list_employer_applications(employer_id)
    scorable = [row for row in scheduled_candidates if row.get("InterviewDate")]

    page_header(
        "Interview Management",
        "Schedule interviews for new applicants, then record outcomes and keep the hiring pipeline synchronized.",
        eyebrow="Employer Workspace",
    )

    metric_row(
        [
            ("Ready to Schedule", len(pending_candidates)),
            ("Scheduled Interviews", len(interviews)),
            ("Waiting for Result", len(scorable)),
        ]
    )

    new_tab, schedule_tab, result_tab, history_tab = st.tabs(
        ["New Applicants", "Schedule", "Record Result", "History"]
    )

    with new_tab:
        with st.container(border=True):
            panel_header("New Applicants", "Applicants without an interview scheduled yet.", eyebrow="Queue")
            show_reference_activity_table(
                _pending_interview_activity_rows(pending_candidates),
                "There are no new applicants ready for interview scheduling right now.",
                headers=["Applicant", "Status", "Company", "Applied"],
            )

    with schedule_tab:
        if not pending_candidates:
            st.info("There are no new applications waiting for interview scheduling.")
        else:
            options = {
                row["ApplicationID"]: (
                    f"App #{row['ApplicationID']} - {row['CandidateName']} for {row['PositionTitle']}"
                )
                for row in pending_candidates
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
        with st.container(border=True):
            panel_header("Interview History", "All scheduled and completed interview records for this employer.", eyebrow="History")
            show_reference_activity_table(
                _interview_activity_rows(interviews),
                "There are no interviews recorded yet.",
                headers=["Candidate", "Result", "Location", "Interview"],
            )


def render_workspace() -> None:
    """Route the employer session to one of the employer-facing pages."""

    options = ["Dashboard", "Jobs", "Applications", "Interviews", "Performance", "Account"]
    if "employer_nav_page" not in st.session_state:
        st.session_state["employer_nav_page"] = "Dashboard"
    manual_select = None
    if "employer_nav_target" in st.session_state:
        target = st.session_state.pop("employer_nav_target")
        if target in options:
            st.session_state["employer_nav_page"] = target
            manual_select = options.index(target)

    sidebar_col, main_col = st.columns([0.95, 4.15], gap="large")
    with sidebar_col:
        sidebar_identity_card(
            st.session_state["display_name"],
            st.session_state["role"],
            st.session_state["email"],
        )
        with st.container(border=True):
            sidebar_nav_heading("Employer Navigation", "Switch between dashboard analytics and hiring workflows.")
            page = option_menu(
                menu_title=None,
                options=options,
                icons=["grid", "briefcase", "file-earmark-text", "camera-video", "graph-up", "shield-lock"],
                default_index=options.index(st.session_state["employer_nav_page"]),
                manual_select=manual_select,
                key="employer_option_menu",
                styles={
                    "container": {
                        "padding": "0",
                        "background-color": "transparent",
                    },
                    "icon": {
                        "color": "#6b7280",
                        "font-size": "1rem",
                    },
                    "nav-link": {
                        "font-size": "0.95rem",
                        "font-weight": "500",
                        "color": "#4b5563",
                        "padding": "0.72rem 0.9rem",
                        "border-radius": "12px",
                        "margin": "0 0 0.28rem 0",
                        "--hover-color": "#f8fafc",
                    },
                    "nav-link-selected": {
                        "background-color": "#f3f4f6",
                        "color": "#111827",
                        "font-weight": "600",
                    },
                },
            )
            if page != st.session_state["employer_nav_page"]:
                st.session_state["employer_nav_page"] = page

    with main_col:
        if page == "Dashboard":
            render_dashboard()
        elif page == "Jobs":
            render_jobs()
        elif page == "Applications":
            render_applications()
        elif page == "Interviews":
            render_interviews()
        elif page == "Account":
            render_account()
        else:
            render_performance()
