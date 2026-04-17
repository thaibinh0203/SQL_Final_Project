"""Session-state helpers for Streamlit authentication and routing."""

from __future__ import annotations

from typing import Any

import streamlit as st

from backend.crud import AuthenticatedUser


SESSION_DEFAULTS: dict[str, Any] = {
    "authenticated": False,
    "account_id": None,
    "role": None,
    "employer_id": None,
    "candidate_id": None,
    "display_name": None,
    "email": None,
}


def ensure_session_state() -> None:
    """Initialize auth-related session state keys once per browser session."""

    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_user_session(user: AuthenticatedUser) -> None:
    """Persist the authenticated user so role-aware pages can render safely."""

    st.session_state["authenticated"] = True
    st.session_state["account_id"] = user.account_id
    st.session_state["role"] = user.role
    st.session_state["employer_id"] = user.employer_id
    st.session_state["candidate_id"] = user.candidate_id
    st.session_state["display_name"] = user.display_name
    st.session_state["email"] = user.email


def logout() -> None:
    """Clear the active session so a different user can log in cleanly."""

    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value


def is_authenticated() -> bool:
    """Return whether a valid login session is currently active."""

    return bool(st.session_state.get("authenticated"))


def current_role() -> str | None:
    """Return the current user role stored in session state."""

    return st.session_state.get("role")


def current_account_id() -> int:
    """Return the current account ID or fail if the session is incomplete."""

    account_id = st.session_state.get("account_id")
    if account_id is None:
        raise RuntimeError("Account session is not available.")
    return int(account_id)


def current_employer_id() -> int:
    """Return the current employer ID or fail if the session is incomplete."""

    employer_id = st.session_state.get("employer_id")
    if employer_id is None:
        raise RuntimeError("Employer session is not available.")
    return int(employer_id)


def current_candidate_id() -> int:
    """Return the current candidate ID or fail if the session is incomplete."""

    candidate_id = st.session_state.get("candidate_id")
    if candidate_id is None:
        raise RuntimeError("Candidate session is not available.")
    return int(candidate_id)
