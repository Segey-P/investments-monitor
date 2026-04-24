"""Password gate + inactivity timeout for the local Streamlit app.

Session state keys:
  auth.ok            (bool)    — unlocked?
  auth.last_activity (float)   — epoch seconds of last verified tick
  auth.timeout_min   (int)     — minutes of inactivity before lockout
"""
from __future__ import annotations

import time

import bcrypt
import streamlit as st


def _get_password_hash(conn) -> str | None:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'password_hash'"
    ).fetchone()
    return row["value"] if row else None


def _get_timeout_min(conn) -> int:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'session_timeout_min'"
    ).fetchone()
    try:
        return int(row["value"]) if row else 15
    except (TypeError, ValueError):
        return 15


def _pre_auth_summary(conn) -> None:
    """Show leakage-safe summary on the login screen (proportions only)."""
    from app import calcs
    from app.fx import get_usdcad
    from app.theme import fmt_pct, fmt_ratio

    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)
    if port.portfolio_cad == 0:
        return
    unreg = calcs.summarize([h for h in hs if h.account_type == "Unreg"], fx.rate).portfolio_cad
    lev = calcs.leverage(conn, port.portfolio_cad, unreg)
    alloc = calcs.allocations(hs, fx.rate)

    st.caption("Public summary (no dollar totals) — visible pre-auth")
    cols = st.columns(4)
    cols[0].metric("Leverage Ratio", fmt_ratio(lev.leverage_ratio))
    cols[1].metric("HELOC Util", fmt_pct(lev.heloc_util_pct))
    cols[2].metric("Positions", f"{port.position_count}")
    cols[3].metric("Accounts", f"{port.account_count}")

    with st.expander("Allocation by account"):
        for k, v in sorted(alloc["by_account"].items(), key=lambda kv: -kv[1]):
            st.write(f"- **{k}** — {v * 100:.1f}%")


def tick(conn) -> bool:
    """Gate entry-point. Returns True if user is authenticated and not expired.

    If False, renders the login form (or lockout) in-place and stops further
    script execution upstream is the caller's responsibility.
    """
    ss = st.session_state
    ss.setdefault("auth", {"ok": False, "last_activity": 0.0})
    st_auth = ss["auth"]
    now = time.time()
    timeout_min = _get_timeout_min(conn)
    st_auth["timeout_min"] = timeout_min

    if st_auth["ok"]:
        elapsed_min = (now - st_auth["last_activity"]) / 60.0
        remaining_min = timeout_min - elapsed_min
        if remaining_min <= 0:
            st_auth["ok"] = False
            st.warning("Session expired. Please sign in again.")
        else:
            st_auth["last_activity"] = now
            if remaining_min <= 1.0:  # under 60s
                cols = st.columns([4, 1])
                cols[0].warning(
                    f"Session expires in ~{int(remaining_min * 60)}s of inactivity."
                )
                if cols[1].button("Stay signed in", key="auth_stay"):
                    st_auth["last_activity"] = now
                    st.rerun()
            return True

    # --- Login form ---
    stored = _get_password_hash(conn)
    if stored is None:
        st.error(
            "No password set. Run `python -m scripts.set_password` in the repo root."
        )
        st.stop()

    st.markdown("### Sign in")
    with st.form("login_form", clear_on_submit=False):
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Unlock")
    if submitted:
        if bcrypt.checkpw(pw.encode("utf-8"), stored.encode("utf-8")):
            st_auth["ok"] = True
            st_auth["last_activity"] = now
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.markdown("---")
    _pre_auth_summary(conn)
    return False
