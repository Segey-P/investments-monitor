from __future__ import annotations

import subprocess
from datetime import date, datetime
from pathlib import Path

import bcrypt
import streamlit as st

from app.fx import get_usdcad


def _get_setting(conn, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if (row and row["value"] is not None) else default


def _put_setting(conn, key: str, value: str) -> None:
    with conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def _git_info(repo_root: Path) -> dict[str, str]:
    try:
        branch = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        short = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        subject = subprocess.check_output(
            ["git", "-C", str(repo_root), "log", "-1", "--pretty=%s"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return {"branch": branch, "commit": short, "subject": subject}
    except Exception:
        return {"branch": "—", "commit": "—", "subject": "—"}


def render(conn) -> None:
    st.markdown("### Settings")

    # -------------------- Security --------------------
    with st.expander("Security", expanded=True):
        timeout = int(_get_setting(conn, "session_timeout_min", "15") or "15")
        new_timeout = st.number_input(
            "Session timeout (minutes)", min_value=1, max_value=240, value=timeout, step=1,
            key="set_timeout",
        )
        st.markdown("**Change password**")
        pw1 = st.text_input("New password", type="password", key="set_pw1")
        pw2 = st.text_input("Confirm password", type="password", key="set_pw2")
        if st.button("Save security settings", key="set_sec_save"):
            _put_setting(conn, "session_timeout_min", str(new_timeout))
            if pw1 or pw2:
                if len(pw1) < 8:
                    st.error("Password must be at least 8 characters.")
                elif pw1 != pw2:
                    st.error("Passwords do not match.")
                else:
                    hashed = bcrypt.hashpw(pw1.encode("utf-8"), bcrypt.gensalt())
                    _put_setting(conn, "password_hash", hashed.decode("utf-8"))
                    st.success("Password updated.")
            else:
                st.success("Timeout saved.")

    # -------------------- Borrowing --------------------
    heloc = conn.execute("SELECT * FROM heloc_account WHERE id = 1").fetchone()
    margin = conn.execute("SELECT * FROM margin_account WHERE id = 1").fetchone()

    with st.expander("Borrowing — HELOC", expanded=True):
        cols = st.columns(3)
        h_limit = cols[0].number_input(
            "Limit ($CAD)", min_value=0.0, value=float(heloc["limit_cad"] or 0),
            step=1000.0, format="%.2f", key="set_h_limit",
        )
        h_rate = cols[1].number_input(
            "Rate (% annual)", min_value=0.0, max_value=30.0,
            value=float(heloc["rate_pct"] or 0), step=0.05, format="%.2f", key="set_h_rate",
        )
        h_warn = cols[2].number_input(
            "Util warn threshold (%)", min_value=0.0, max_value=100.0,
            value=float(heloc["util_warn_pct"] or 80), step=1.0, format="%.0f",
            key="set_h_warn",
        )
        if st.button("Save HELOC settings", key="set_h_save"):
            with conn:
                conn.execute(
                    "UPDATE heloc_account SET limit_cad = ?, rate_pct = ?, util_warn_pct = ? WHERE id = 1",
                    (h_limit, h_rate, h_warn),
                )
            st.success("HELOC saved.")
            st.rerun()

    with st.expander("Borrowing — Margin", expanded=False):
        cols = st.columns(2)
        m_broker = cols[0].text_input(
            "Broker", value=margin["broker"] or "Questrade", key="set_m_broker"
        )
        m_limit = cols[1].number_input(
            "Limit ($CAD)", min_value=0.0, value=float(margin["limit_cad"] or 0),
            step=1000.0, format="%.2f", key="set_m_limit",
        )
        cols = st.columns(3)
        m_rate = cols[0].number_input(
            "Rate (% annual)", min_value=0.0, max_value=30.0,
            value=float(margin["rate_pct"] or 0), step=0.05, format="%.2f", key="set_m_rate",
        )
        m_call = cols[1].number_input(
            "Call threshold (% equity)", min_value=0.0, max_value=100.0,
            value=float(margin["call_threshold_pct"] or 70), step=1.0, format="%.0f",
            key="set_m_call",
        )
        m_buf = cols[2].number_input(
            "Warn buffer threshold (% buffer)", min_value=0.0, max_value=100.0,
            value=float(margin["warn_buffer_pct"] or 50), step=1.0, format="%.0f",
            key="set_m_buf",
        )
        if st.button("Save Margin settings", key="set_m_save"):
            with conn:
                conn.execute(
                    """UPDATE margin_account
                       SET broker = ?, limit_cad = ?, rate_pct = ?,
                           call_threshold_pct = ?, warn_buffer_pct = ?
                       WHERE id = 1""",
                    (m_broker, m_limit, m_rate, m_call, m_buf),
                )
            st.success("Margin saved.")
            st.rerun()

    # -------------------- Refresh --------------------
    with st.expander("Refresh", expanded=False):
        interval = int(_get_setting(conn, "refresh_interval_hours", "4") or "4")
        new_interval = st.number_input(
            "Refresh interval (hours)", min_value=1, max_value=24, value=interval, step=1,
            key="set_refresh_int",
        )
        enabled = _get_setting(conn, "refresh_enabled", "true") == "true"
        new_enabled = st.toggle("Enable scheduled refresh", value=enabled, key="set_refresh_on")
        if st.button("Save refresh settings", key="set_refresh_save"):
            _put_setting(conn, "refresh_interval_hours", str(new_interval))
            _put_setting(conn, "refresh_enabled", "true" if new_enabled else "false")
            st.success("Saved.")

    # -------------------- FX --------------------
    with st.expander("FX (Bank of Canada, read-only)", expanded=False):
        fx = get_usdcad(conn)
        st.markdown(
            f"**Rate:** `1 USD = {fx.rate:.4f} CAD`  \n"
            f"**Source:** Bank of Canada Valet  \n"
            f"**Observation date:** {fx.as_of}  \n"
            f"**Fetched:** {fx.fetched_at}" + ("  — **stale**" if fx.stale else "")
        )
        st.markdown("[BOC chart ↗](https://www.bankofcanada.ca/rates/exchange/currency-converter/)")

    # -------------------- Imports --------------------
    with st.expander("Imports", expanded=False):
        rows = conn.execute(
            "SELECT filename, broker, rows, imported_at FROM imports "
            "ORDER BY imported_at DESC LIMIT 20"
        ).fetchall()
        if not rows:
            st.caption("No imports yet.")
        else:
            import pandas as pd
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df, hide_index=True, width="stretch")
        st.caption(
            "To import a new file, drop it in `data/imports/` and run "
            "`python -m scripts.import_questrade <file.xlsx>`."
        )

    # -------------------- Public summary --------------------
    with st.expander("Public summary (cloud payload)", expanded=False):
        repo_root = Path(__file__).resolve().parent.parent.parent
        summary_path = repo_root / "public" / "summary.json"
        last = _get_setting(conn, "summary_last_regenerated", "—")
        st.markdown(f"**Path:** `{summary_path.relative_to(repo_root)}`")
        st.markdown(f"**Last regenerated:** {last}")
        if st.button("Regenerate now", key="set_regen"):
            st.info("Regeneration hook not yet implemented — Phase 3.")

    # -------------------- About --------------------
    with st.expander("About", expanded=False):
        repo_root = Path(__file__).resolve().parent.parent.parent
        gi = _git_info(repo_root)
        st.markdown(
            f"**Version:** v0.1 (Phase 2)  \n"
            f"**Branch:** `{gi['branch']}`  \n"
            f"**Commit:** `{gi['commit']}` — {gi['subject']}  \n"
            f"**Today:** {date.today().isoformat()}"
        )
