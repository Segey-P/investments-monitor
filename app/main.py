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

st.markdown(
    """
    <style>
    .brand {
        font-family: DM Mono, monospace;
        font-size: 18px;
        letter-spacing: 0.04em;
    }
    [data-testid="stToolbar"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="brand">INVESTMENTS MONITOR</div>', unsafe_allow_html=True)

conn = init_db()

if not auth.tick(conn):
    st.stop()

tabs = st.tabs(["Dashboard", "Holdings", "Watchlist", "Leverage", "Net Worth", "Settings"])

with tabs[0]:
    dashboard_view.render(conn)
with tabs[1]:
    holdings_view.render(conn)
with tabs[2]:
    watchlist_view.render(conn)
with tabs[3]:
    leverage_view.render(conn)
with tabs[4]:
    net_worth_view.render(conn)
with tabs[5]:
    settings_view.render(conn)
