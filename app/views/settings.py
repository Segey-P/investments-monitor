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
        import_dir = Path(__file__).resolve().parent.parent.parent / "data" / "imports"
        import_files = sorted([f.name for f in import_dir.glob("*.xlsx") if f.is_file()])

        if not import_files:
            st.caption("No files in `data/imports/` yet.")
        else:
            st.markdown("**Available imports:**")
            existing = {row["filename"] for row in conn.execute("SELECT DISTINCT filename FROM imports").fetchall()}
            for fname in import_files:
                status = "✓ Imported" if fname in existing else "○ New"
                st.markdown(f"- `{fname}` — {status}")

            st.markdown("**To import:**")
            st.code("python -m scripts.import_questrade <file.xlsx>", language="bash")
            st.caption("Duplicate files will be skipped automatically.")

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
