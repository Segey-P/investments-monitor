from __future__ import annotations

import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path

import bcrypt
import streamlit as st

from app.db import init_db
from app.fx import get_usdcad
from scripts.importers.questrade import QuestradeImporter
from scripts.importers.ibkr import IBKRImporter
from scripts.importers.persist import FileAlreadyImported, persist_result, clear_holdings


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


def _render_import_flow(conn) -> None:
    """3-stage import flow: upload → preview/review → done."""
    ss = st.session_state
    ss.setdefault("import_flow", {"stage": 0, "path": None, "result": None, "overrides": {}, "broker": "Questrade"})
    flow = ss["import_flow"]

    repo_root = Path(__file__).resolve().parent.parent.parent
    import_dir = repo_root / "data" / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)

    # Stage 0: Upload
    if flow["stage"] == 0:
        st.markdown("#### Import Holdings")
        
        broker = st.radio(
            "Select Broker",
            ["Questrade", "Interactive Brokers"],
            index=0 if flow.get("broker", "Questrade") == "Questrade" else 1,
            horizontal=True,
            key="import_broker_select"
        )
        flow["broker"] = broker

        if broker == "Questrade":
            st.info(
                "**Instructions:**\n"
                "1. Log in to Questrade.\n"
                "2. Go to **Reports** > **Investment Summary**.\n"
                "3. Select accounts and click **Export to Excel**.\n"
                "4. Upload the **.xlsx** file below."
            )
            file_types = ["xlsx"]
            importer_cls = QuestradeImporter
        else:
            st.info(
                "**Instructions:**\n"
                "1. Log in to IBKR Portal.\n"
                "2. Go to **Performance & Reports** > **Statements**.\n"
                "3. Select **Investment Summary** (preferred) or **Activity Statement**.\n"
                "4. Select **Format: CSV** and **Period: From Inception**.\n"
                "5. Upload the **.csv** file below."
            )
            file_types = ["csv"]
            importer_cls = IBKRImporter

        uploaded = st.file_uploader(f"Drop {broker} file here", type=file_types)

        if uploaded:
            file_path = import_dir / uploaded.name
            file_path.write_bytes(uploaded.getvalue())
            st.success(f"✓ Saved {uploaded.name}")

            importer = importer_cls()
            if importer.detect_format(file_path):
                try:
                    parsed = importer.parse(file_path)
                    flow["path"] = file_path
                    flow["result"] = parsed
                    flow["overrides"] = {}
                    flow["stage"] = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse file: {e}")
            else:
                st.warning(f"File doesn't look like {broker} format; attempting anyway...")
                try:
                    parsed = importer.parse(file_path)
                    flow["path"] = file_path
                    flow["result"] = parsed
                    flow["overrides"] = {}
                    flow["stage"] = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Parse failed: {e}")

        st.markdown("---")
        st.markdown("#### Import History")
        import_records = conn.execute("""
            SELECT filename, rows, imported_at FROM imports
            ORDER BY imported_at DESC
        """).fetchall()

        if import_records:
            for r in import_records:
                st.caption(f"**{r['filename']}** — {r['rows']} holdings on {r['imported_at']}")
        else:
            st.caption("No imports yet.")

        st.markdown("---")
        st.markdown("#### Clear Holdings")
        st.warning(
            "**⚠️ Danger Zone:** Delete all holdings and import history. Use before re-uploading a full portfolio snapshot."
        )
        if st.button("Clear all holdings", key="clear_holdings_btn", type="secondary"):
            clear_holdings(conn)
            st.success("✓ Holdings and import history cleared.")
            st.rerun()

    # Stage 1: Preview & Ticker Review
    elif flow["stage"] == 1:
        parsed = flow["result"]
        path = flow["path"]

        st.markdown(f"#### Preview: {path.name}")

        # Accounts summary
        st.markdown("**Accounts**")
        acct_data = []
        for num, acct in parsed.accounts.items():
            acct_data.append({
                "Account": num,
                "Type": acct.account_type,
                "Cash (CAD)": f"${acct.cash_cad:,.2f}",
            })
        if acct_data:
            st.dataframe(acct_data, use_container_width=True, hide_index=True)

        st.markdown(f"**Holdings:** {len(parsed.holdings)} positions")

        # Ticker mismatches only
        mismatches = [
            h for h in parsed.holdings
            if h.yahoo_ticker != h.ticker
        ]

        if mismatches:
            st.markdown("**Ticker Mappings (mismatches only)**")
            st.caption(
                "Review auto-mapped Yahoo symbols and categories. Edit columns as needed."
            )

            editor_data = []
            for h in mismatches:
                editor_data.append({
                    "Questrade": h.ticker,
                    "Description": h.description[:50] if h.description else "—",
                    "Auto-mapped": h.yahoo_ticker,
                    "Yahoo Override": flow["overrides"].get(("yahoo", h.ticker), ""),
                    "Category": flow["overrides"].get(("category", h.ticker), h.category),
                    "Currency": h.currency,
                })

            edited = st.data_editor(
                editor_data,
                use_container_width=True,
                hide_index=True,
                key="import_ticker_overrides",
                column_config={
                    "Category": st.column_config.SelectboxColumn(
                        options=["Cash", "Dividend", "Growth", "Other"],
                    ),
                },
            )

            # Store any overrides
            for row in edited:
                ticker = row["Questrade"]
                yahoo_override = row["Yahoo Override"]
                category_override = row["Category"]

                if yahoo_override:
                    flow["overrides"][("yahoo", ticker)] = yahoo_override
                elif ("yahoo", ticker) in flow["overrides"]:
                    del flow["overrides"][("yahoo", ticker)]

                # Store category if different from default
                default_cat = next((h.category for h in mismatches if h.ticker == ticker), "Other")
                if category_override != default_cat:
                    flow["overrides"][("category", ticker)] = category_override
                elif ("category", ticker) in flow["overrides"]:
                    del flow["overrides"][("category", ticker)]
        else:
            st.info("All ticker mappings look good (no mismatches).")

        col1, col2 = st.columns(2)
        if col1.button("← Back", key="import_back"):
            flow["stage"] = 0
            flow["path"] = None
            flow["result"] = None
            flow["overrides"] = {}
            st.rerun()

        if col2.button("Confirm Import →", key="import_confirm"):
            flow["stage"] = 2
            st.rerun()

    # Stage 2: Done
    elif flow["stage"] == 2:
        parsed = flow["result"]
        path = flow["path"]

        st.markdown(f"#### Importing {path.name}...")

        # Apply any user overrides to the ParseResult holdings
        for h in parsed.holdings:
            if ("yahoo", h.ticker) in flow["overrides"]:
                h.yahoo_ticker = flow["overrides"][("yahoo", h.ticker)]
            if ("category", h.ticker) in flow["overrides"]:
                h.category = flow["overrides"][("category", h.ticker)]

        try:
            result = persist_result(conn, path, parsed)
            st.success(
                f"✓ Imported {result['holdings']} holdings into {result['accounts']} account(s). "
                f"Cash total: ${result['cash_total']:,.2f} CAD"
            )

            if st.button("Import another file", key="import_again"):
                flow["stage"] = 0
                flow["path"] = None
                flow["result"] = None
                flow["overrides"] = {}
                st.rerun()

        except FileAlreadyImported as e:
            st.warning(f"File already imported on {e.imported_at}")
            if st.button("Re-import (replace)", key="import_reimport"):
                try:
                    conn.execute("DELETE FROM imports WHERE filename = ?", (path.name,))
                    conn.commit()
                    result = persist_result(conn, path, parsed)
                    st.success(
                        f"✓ Re-imported {result['holdings']} holdings into {result['accounts']} account(s)."
                    )
                    if st.button("Import another file", key="import_again_2"):
                        flow["stage"] = 0
                        flow["path"] = None
                        flow["result"] = None
                        flow["overrides"] = {}
                        st.rerun()
                except Exception as e2:
                    st.error(f"Re-import failed: {e2}")

        except Exception as e:
            st.error(f"Import failed: {e}")
            if st.button("Try again", key="import_retry"):
                flow["stage"] = 1
                st.rerun()


def render(conn) -> None:
    st.markdown("### Settings")

    # -------------------- Imports --------------------
    with st.expander("Imports", expanded=True):
        _render_import_flow(conn)

    # -------------------- Security --------------------
    with st.expander("Security", expanded=False):
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
