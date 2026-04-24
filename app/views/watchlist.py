from __future__ import annotations

import pandas as pd
import streamlit as st

from app import prices


def _load_rows(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT w.ticker, w.target_price, w.notes,
               p.price AS current_price, p.currency AS price_currency,
               p.stale
        FROM watchlist w
        LEFT JOIN prices p ON p.ticker = w.ticker
        ORDER BY w.notes, w.ticker
    """).fetchall()
    out = []
    for r in rows:
        current = r["current_price"]
        target = r["target_price"]
        gap = None
        if current is not None and target and target > 0:
            gap = (current - target) / target
        out.append({
            "Ticker": r["ticker"],
            "Category": r["notes"] or "",
            "Current": current,
            "Target": target,
            "Gap %": gap,
            "Cur": r["price_currency"] or "",
            "Stale": "⚠" if r["stale"] else "",
        })
    return out


def render(conn) -> None:
    st.markdown("### Watchlist")

    rows = _load_rows(conn)

    with st.expander("Add ticker", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        new_t = c1.text_input("Ticker (Yahoo symbol)", key="wl_new_t",
                              placeholder="e.g. LITE or POET.TO")
        new_target = c2.number_input("Target price", min_value=0.0, value=0.0,
                                     step=0.01, format="%.2f", key="wl_new_target")
        new_notes = c3.text_input("Category / notes", key="wl_new_notes",
                                  placeholder="long-term / dividend / …")
        if c4.button("Add", key="wl_add"):
            if new_t.strip():
                with conn:
                    conn.execute(
                        "INSERT INTO watchlist (ticker, target_price, notes) "
                        "VALUES (?, ?, ?) "
                        "ON CONFLICT(ticker) DO UPDATE SET "
                        "  target_price = excluded.target_price, "
                        "  notes = excluded.notes",
                        (
                            new_t.strip().upper(),
                            new_target if new_target > 0 else None,
                            new_notes.strip() or None,
                        ),
                    )
                st.success(f"Added {new_t.strip().upper()}.")
                st.rerun()

    c1, c2 = st.columns([1, 4])
    if c1.button("↻ Refresh prices", key="wl_refresh"):
        tickers = [r["Ticker"] for r in rows]
        if tickers:
            with st.spinner(f"Fetching {len(tickers)} prices…"):
                q = prices.get_quotes(tickers)
                prices.persist_quotes(conn, q)
            st.rerun()

    if not rows:
        st.info("No watchlist entries yet. Add one above.")
        return

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "Current": st.column_config.NumberColumn(format="%.2f"),
            "Target":  st.column_config.NumberColumn(format="%.2f"),
            "Gap %":   st.column_config.NumberColumn(format="%.2f%%"),
        },
    )
    st.caption(
        "Gap % = (current − target) / target. Positive means price is **above** target; "
        "negative means **below**. Set a target in the Add/Edit form."
    )

    with st.expander("Edit / remove entries", expanded=False):
        all_tickers = [r["Ticker"] for r in rows]
        pick = st.selectbox("Ticker", all_tickers, key="wl_edit_pick")
        current = conn.execute(
            "SELECT target_price, notes FROM watchlist WHERE ticker = ?", (pick,)
        ).fetchone()
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        edit_target = c1.number_input(
            "Target", min_value=0.0,
            value=float(current["target_price"] or 0),
            step=0.01, format="%.2f", key=f"wl_edit_target_{pick}",
        )
        edit_notes = c2.text_input(
            "Notes", value=current["notes"] or "", key=f"wl_edit_notes_{pick}",
        )
        if c3.button("Save", key=f"wl_edit_save_{pick}"):
            with conn:
                conn.execute(
                    "UPDATE watchlist SET target_price = ?, notes = ? WHERE ticker = ?",
                    (edit_target if edit_target > 0 else None, edit_notes.strip() or None, pick),
                )
            st.success(f"Updated {pick}.")
            st.rerun()
        if c4.button("Remove", key=f"wl_edit_remove_{pick}"):
            with conn:
                conn.execute("DELETE FROM watchlist WHERE ticker = ?", (pick,))
            st.warning(f"Removed {pick}.")
            st.rerun()
