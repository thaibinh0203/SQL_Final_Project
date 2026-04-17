"""Authentication page rendering."""

from __future__ import annotations

import streamlit as st

from backend import crud
from backend.crud import BackendError
from frontend.components import APP_TITLE, APP_SUBTITLE, info_chip, page_header
from frontend.session import set_user_session


def render_login_page() -> None:
    """Render the shared login experience for employers and candidates."""

    page_header(
        APP_TITLE,
        f"{APP_SUBTITLE} Use any seeded account to log in. Demo password for every account is `1`.",
        eyebrow="Secure Demo Access",
    )

    hints_left, hints_right = st.columns(2)
    with hints_left:
        info_chip(
            "Employer Login",
            [
                "Sample email: employer0001@example.com",
                "Can manage owned jobs, applications, and interviews.",
            ],
        )
    with hints_right:
        info_chip(
            "Candidate Login",
            [
                "Sample email: candidate0001@example.com",
                "Can browse jobs, apply, and track interviews.",
            ],
        )

    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.container(border=True):
            st.markdown("### Sign In")
            st.caption("Use a seeded email from `database/seed_510.sql` and password `1`.")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="employer0001@example.com")
                password = st.text_input("Password", type="password", placeholder="1")
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
