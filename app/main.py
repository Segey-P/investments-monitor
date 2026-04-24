from __future__ import annotations

import sys
from pathlib import Path

# Streamlit's `streamlit run app/main.py` launcher puts app/ on sys.path instead
# of the repo root. Prepend the repo root so `from app.x import …` resolves.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from app import auth
from app.db import init_db
from app.theme import apply_theme
from app.views import (
    dashboard as dashboard_view,
    holdings as holdings_view,
    leverage as leverage_view,
    net_worth as net_worth_view,
    settings as settings_view,
    watchlist as watchlist_view,
)

st.set_page_config(
    page_title="Investments Monitor",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

conn = init_db()

st.markdown(
    """
    <style>
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .brand {
        font-family: DM Mono, monospace;
        font-size: 18px;
        letter-spacing: 0.04em;
    }
    .status {
        color: #9ca3af;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "public_view" not in st.session_state:
    st.session_state["public_view"] = False

c1, c2 = st.columns([1, 1])
with c1:
    st.markdown('<div class="brand">INVESTMENTS MONITOR</div>', unsafe_allow_html=True)
with c2:
    cols = st.columns([3, 2])
    with cols[1]:
        if st.toggle("☁ Public view", value=st.session_state["public_view"], key="public_view_toggle"):
            st.session_state["public_view"] = True
        else:
            st.session_state["public_view"] = False
    with cols[0]:
        st.markdown(
            f'<div class="status" style="justify-content: flex-end; height: 100%; align-items: center;">'
            f'Individual · 🔒 Local</div>',
            unsafe_allow_html=True
        )

if not auth.tick(conn):
    st.stop()

tabs = st.tabs(["Dashboard", "Holdings", "Leverage", "Net Worth", "Watchlist", "Settings"])

with tabs[0]:
    dashboard_view.render(conn)
with tabs[1]:
    holdings_view.render(conn)
with tabs[2]:
    leverage_view.render(conn)
with tabs[3]:
    net_worth_view.render(conn)
with tabs[4]:
    watchlist_view.render(conn)
with tabs[5]:
    settings_view.render(conn)
