"""Authentication page rendering."""

from __future__ import annotations

from datetime import date

import streamlit as st

from backend import crud
from backend.crud import BackendError
from frontend.components import APP_TITLE, APP_SUBTITLE, info_chip, page_header, panel_header
from frontend.session import set_user_session


def render_login_page() -> None:
    """Render the shared login experience for employers and candidates."""

    page_header(
        APP_TITLE,
        f"{APP_SUBTITLE} Monitor hiring pipelines, interview outcomes, and job performance from one cloud-style workspace.",
        eyebrow="Secure Demo Access",
    )

    intro_col, form_col = st.columns([1.15, 0.95], gap="large")
    with intro_col:
        info_chip(
            "Dashboard Theme",
            [
                "Dark cloud-platform workspace with modular analytics surfaces.",
                "Employer views focus on hiring operations, applications, and interview reporting.",
                "Candidate views focus on job discovery, interview tracking, and profile management.",
            ],
        )
        hint_left, hint_right = st.columns(2)
        with hint_left:
            info_chip(
                "Employer Login",
                [
                    "Sample email: employer0001@example.com",
                    "Owns jobs, applications, dashboards, and interviews.",
                ],
            )
        with hint_right:
            info_chip(
                "Candidate Login",
                [
                    "Sample email: candidate0001@example.com",
                    "Can browse jobs, apply, and track interview status.",
                ],
            )

    with form_col:
        with st.container(border=True):
            tab_login, tab_candidate, tab_employer = st.tabs(
                ["Sign In", "Register Candidate", "Register Employer"]
            )

            with tab_login:
                panel_header(
                    "Sign In",
                    "Use a seeded account or any newly registered account to enter the workspace.",
                    eyebrow="Authentication",
                    badge="Login",
                )
                st.caption("Default seeded password is `1` unless it has been changed in Account Security.")
                with st.form("login_form", clear_on_submit=False):
                    email = st.text_input("Email", placeholder="employer0001@example.com", key="login_email")
                    password = st.text_input("Password", type="password", placeholder="1", key="login_password")
                    submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    try:
                        user = crud.authenticate_user(email=email, password=password)
                    except BackendError as exc:
                        st.error(str(exc))
                    else:
                        set_user_session(user)
                        st.success(f"Logged in as {user.display_name}.")
                        st.rerun()

            with tab_candidate:
                panel_header(
                    "Register Candidate",
                    "Create a new candidate account and profile in one step.",
                    eyebrow="Registration",
                    badge="Candidate",
                )
                with st.form("register_candidate_form", clear_on_submit=True):
                    email = st.text_input("Email", placeholder="newcandidate@example.com", key="candidate_register_email")
                    full_name = st.text_input("Full Name", placeholder="Nguyen Van A", key="candidate_register_full_name")
                    use_birth_date = st.checkbox("Store Date of Birth", value=False, key="candidate_register_use_birth")
                    date_of_birth = st.date_input(
                        "Date of Birth",
                        value=date.today(),
                        disabled=not use_birth_date,
                        key="candidate_register_birth_date",
                    )
                    phone_number = st.text_input("Phone Number", placeholder="0901234567", key="candidate_register_phone")
                    resume_url = st.text_input(
                        "Resume URL",
                        placeholder="https://example.com/resume.pdf",
                        key="candidate_register_resume",
                    )
                    password = st.text_input("Password", type="password", key="candidate_register_password")
                    confirm_password = st.text_input(
                        "Confirm Password",
                        type="password",
                        key="candidate_register_confirm_password",
                    )
                    submitted = st.form_submit_button("Create Candidate Account", use_container_width=True)

                if submitted:
                    try:
                        user = crud.register_candidate_account(
                            email=email,
                            password=password,
                            confirm_password=confirm_password,
                            full_name=full_name,
                            date_of_birth=date_of_birth if use_birth_date else None,
                            phone_number=phone_number,
                            resume_url=resume_url,
                        )
                    except BackendError as exc:
                        st.error(str(exc))
                    else:
                        set_user_session(user)
                        st.success(f"Candidate account created for {user.display_name}.")
                        st.rerun()

            with tab_employer:
                panel_header(
                    "Register Employer",
                    "Create a new employer account and company profile in one step.",
                    eyebrow="Registration",
                    badge="Employer",
                )
                with st.form("register_employer_form", clear_on_submit=True):
                    email = st.text_input("Email", placeholder="newemployer@example.com", key="employer_register_email")
                    company_name = st.text_input(
                        "Company Name",
                        placeholder="ABC Recruitment",
                        key="employer_register_company_name",
                    )
                    contact_number = st.text_input(
                        "Contact Number",
                        placeholder="02812345678",
                        key="employer_register_contact_number",
                    )
                    address = st.text_area("Address", height=90, key="employer_register_address")
                    description = st.text_area("Description", height=110, key="employer_register_description")
                    password = st.text_input("Password", type="password", key="employer_register_password")
                    confirm_password = st.text_input(
                        "Confirm Password",
                        type="password",
                        key="employer_register_confirm_password",
                    )
                    submitted = st.form_submit_button("Create Employer Account", use_container_width=True)

                if submitted:
                    try:
                        user = crud.register_employer_account(
                            email=email,
                            password=password,
                            confirm_password=confirm_password,
                            company_name=company_name,
                            contact_number=contact_number,
                            address=address,
                            description=description,
                        )
                    except BackendError as exc:
                        st.error(str(exc))
                    else:
                        set_user_session(user)
                        st.success(f"Employer account created for {user.display_name}.")
                        st.rerun()
