"""Streamlit entrypoint for the modular recruitment frontend."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.crud import BackendError
from frontend.components import APP_TITLE, apply_base_styles, render_topbar
from frontend.views.auth import render_login_page
from frontend.views import candidate, employer
from frontend.session import current_role, ensure_session_state, is_authenticated, logout


def main() -> None:
    """Run the Streamlit app with login-aware role routing."""

    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_base_styles()
    ensure_session_state()

    if not is_authenticated():
        render_login_page()
        return

    if render_topbar(st.session_state["display_name"], st.session_state["role"]):
        logout()
        st.rerun()

    try:
        if current_role() == "Employer":
            employer.render_workspace()
        else:
            candidate.render_workspace()
    except BackendError as exc:
        st.error(str(exc))
    except RuntimeError as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
