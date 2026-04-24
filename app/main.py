from __future__ import annotations

import os
import sys
from pathlib import Path

# Streamlit's `streamlit run app/main.py` launcher puts app/ on sys.path instead
# of the repo root. Prepend the repo root so `from app.x import …` resolves.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from app import auth, cloud_mode
from app.db import init_db
from app.theme import apply_theme
from app.views import (
    dashboard as dashboard_view,
    holdings as holdings_view,
    leverage as leverage_view,
    net_worth as net_worth_view,
    settings as settings_view,
)

st.set_page_config(
    page_title="Investments Monitor",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

# Detect mode
MODE = os.getenv("IM_DATA_SOURCE", "local").lower()
IS_CLOUD = MODE == "cloud"

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
    .stale-banner {
        background: #fee2e2; color: #991b1b; padding: 12px; border-radius: 4px; margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="brand">INVESTMENTS MONITOR</div>', unsafe_allow_html=True)


def _render_cloud_mode() -> None:
    """Cloud deployment: reads public/summary.json only."""
    if "cloud_auth" not in st.session_state:
        st.session_state["cloud_auth"] = False

    if not st.session_state["cloud_auth"]:
        _render_cloud_login()
    else:
        _render_cloud_dashboard()


def _render_cloud_login() -> None:
    """Pre-auth page: show summary + watchlist."""
    summary = cloud_mode.load_summary(_REPO_ROOT)

    if summary is None:
        st.error("Summary not available. Please check back later.")
        return

    # Stale banner
    if summary.is_stale:
        st.markdown(
            '<div class="stale-banner">⚠ Data is stale (older than 6 hours). '
            'Check back later or contact support.</div>',
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Public Summary")
        if summary.ratios:
            st.markdown("**Leverage & Returns**")
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("Leverage", f"{summary.ratios.get('leverage_ratio', 0):.2f}×")
            with metric_cols[1]:
                st.metric("HELOC Util.", f"{summary.ratios.get('heloc_utilization_pct', 0)*100:.1f}%")
            with metric_cols[2]:
                st.metric("D/E Ratio", f"{summary.ratios.get('debt_to_equity', 0):.2f}")
            with metric_cols[3]:
                st.metric("YTD Return", f"{summary.ratios.get('portfolio_return_ytd_pct', 0):.2f}%")

        # Allocations
        if summary.allocations.get("by_asset_class"):
            st.markdown("**Allocation by Asset Class**")
            st.json(summary.allocations["by_asset_class"])

        if summary.allocations.get("by_account"):
            st.markdown("**Allocation by Account**")
            st.json(summary.allocations["by_account"])

    with col2:
        st.markdown("### Watchlist")
        if summary.watchlist:
            for item in summary.watchlist[:5]:
                ticker = item["ticker"]
                gap_pct = item["gap_pct"] * 100
                arrow = "▲" if gap_pct >= 0 else "▼"
                st.caption(f"**{ticker}** {arrow} {abs(gap_pct):.1f}%")
                st.caption(f"Current: ${item['current']:.2f}")
                st.caption(f"Target: ${item['target']:.2f}")
                st.divider()
        else:
            st.caption("No favorites pinned.")

    st.divider()
    st.markdown(f"**As of:** {summary.as_of}")

    # Login
    col1, col2 = st.columns(2)
    with col1:
        pwd = st.text_input("Password", type="password", key="cloud_pwd")
    with col2:
        if st.button("Sign in"):
            if auth.verify_password(pwd):
                st.session_state["cloud_auth"] = True
                st.rerun()
            else:
                st.error("Invalid password")


def _render_cloud_dashboard() -> None:
    """Post-auth cloud view: simplified (Dashboard + Holdings only)."""
    summary = cloud_mode.load_summary(_REPO_ROOT)

    if summary and summary.is_stale:
        st.markdown(
            '<div class="stale-banner">⚠ Data is stale (>6h old). '
            'Refresh now?</div>',
            unsafe_allow_html=True,
        )

    if st.button("🔄 Refresh Now"):
        st.info("Refresh triggered. Cloud will update within 1 minute.")
        st.stop()

    st.button("Sign out", on_click=lambda: st.session_state.update({"cloud_auth": False}))

    # Simplified tabs (no Settings or Leverage)
    tabs = st.tabs(["Dashboard", "Holdings"])
    with tabs[0]:
        conn = init_db()
        dashboard_view.render(conn)
    with tabs[1]:
        conn = init_db()
        holdings_view.render(conn)


def _render_local_mode() -> None:
    """Local deployment: full app with all tabs."""
    conn = init_db()

    if not auth.tick(conn):
        st.stop()

    tabs = st.tabs(["Dashboard", "Holdings", "Leverage", "Net Worth", "Settings"])

    with tabs[0]:
        dashboard_view.render(conn)
    with tabs[1]:
        holdings_view.render(conn)
    with tabs[2]:
        leverage_view.render(conn)
    with tabs[3]:
        net_worth_view.render(conn)
    with tabs[4]:
        settings_view.render(conn)


if IS_CLOUD:
    _render_cloud_mode()
else:
    _render_local_mode()
