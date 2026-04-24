from __future__ import annotations

import streamlit as st

from app.db import init_db
from app.theme import apply_theme
from app.views import cockpit, holdings as holdings_view

st.set_page_config(
    page_title="Investments Monitor",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

conn = init_db()

st.markdown(
    '<div style="display:flex;justify-content:space-between;align-items:center;'
    'margin-bottom:12px;">'
    '<div style="font-family:DM Mono,monospace;font-size:18px;letter-spacing:0.04em;">'
    'INVESTMENTS MONITOR</div>'
    '<div style="color:#9ca3af;font-size:12px;">Individual · 🔒 Local</div>'
    '</div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(["Cockpit", "Holdings", "Leverage", "Net Worth", "Watchlist", "Settings"])

with tabs[0]:
    cockpit.render(conn)

with tabs[1]:
    holdings_view.render(conn)

with tabs[2]:
    st.info("Leverage screen — not yet implemented. "
            "HELOC + Margin panels planned for Phase 2.")

with tabs[3]:
    st.info("Net Worth ledger — not yet implemented. Planned for Phase 2.")

with tabs[4]:
    st.info("Watchlist — not yet implemented. Planned for Phase 3.")

with tabs[5]:
    st.info("Settings — not yet implemented. Planned for Phase 2.")
