from __future__ import annotations

import pandas as pd
import streamlit as st

from app import prices


def _load_rows(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT w.ticker, w.target_price, w.notes, w.is_favorite,
               p.price AS current_price, p.currency AS price_currency
        FROM watchlist w
        LEFT JOIN prices p ON p.ticker = w.ticker
        ORDER BY w.is_favorite DESC, w.notes, w.ticker
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
            "Yahoo": f"https://finance.yahoo.com/quote/{r['ticker']}",
            "Category": r["notes"] or "",
            "Current": current,
            "Target": target or 0.0,
            "Gap %": gap,
            "Cur": r["price_currency"] or "",
            "★ Fav": bool(r["is_favorite"]),
            "_ticker": r["ticker"],
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

    # Initialize session state for watchlist edits
    if "watchlist_original" not in st.session_state:
        st.session_state["watchlist_original"] = {r["_ticker"]: r for r in rows}

    edited_df = st.data_editor(
        df,
        hide_index=True,
        width="stretch",
        use_container_width=True,
        column_order=["Ticker", "Yahoo", "Category", "Current", "Target", "Gap %", "Cur", "★ Fav"],
        column_config={
            "Ticker":   st.column_config.TextColumn(disabled=True),
            "Yahoo":    st.column_config.LinkColumn(
                            "↗", help="Open on Yahoo Finance",
                            display_text="↗", width="small",
                        ),
            "Category": st.column_config.TextColumn(),
            "Current":  st.column_config.NumberColumn(format="%.2f", disabled=True),
            "Target":   st.column_config.NumberColumn(format="%.2f"),
            "Gap %":    st.column_config.NumberColumn(format="%.2f%%", disabled=True),
            "Cur":      st.column_config.TextColumn(disabled=True, width="small"),
            "★ Fav":    st.column_config.CheckboxColumn(help="Pin up to 5 favorites for Dashboard"),
        },
        key="watchlist_editor",
    )
    st.caption(
        "Gap % = (current − target) / target. Positive = price **above** target; "
        "negative = **below**. Edit Target, Category, or ★ Fav, then click Save."
    )

    # Save button and logic
    if st.button("💾 Save Changes", key="watchlist_save"):
        fav_count = conn.execute(
            "SELECT COUNT(*) AS c FROM watchlist WHERE is_favorite = 1"
        ).fetchone()["c"]
        changes_count = 0

        with conn:
            for edited_row in edited_df.to_dict(orient="records"):
                ticker = edited_row["_ticker"]
                orig = st.session_state["watchlist_original"].get(ticker, {})

                # Check if adding a new favorite would exceed limit
                is_now_fav = edited_row["★ Fav"]
                was_fav = orig.get("★ Fav", False)
                if is_now_fav and not was_fav and fav_count >= 5:
                    st.error(f"{ticker}: Already 5 favorites pinned. Unpin one first.")
                    st.session_state["watchlist_original"] = {r["_ticker"]: r for r in rows}
                    st.rerun()
                    return

                if orig.get("Category") != edited_row["Category"]:
                    conn.execute(
                        "UPDATE watchlist SET notes = ? WHERE ticker = ?",
                        (edited_row["Category"] or None, ticker),
                    )
                    changes_count += 1

                if orig.get("Target") != edited_row["Target"]:
                    target_val = edited_row["Target"] if edited_row["Target"] > 0 else None
                    conn.execute(
                        "UPDATE watchlist SET target_price = ? WHERE ticker = ?",
                        (target_val, ticker),
                    )
                    changes_count += 1

                if orig.get("★ Fav") != is_now_fav:
                    conn.execute(
                        "UPDATE watchlist SET is_favorite = ? WHERE ticker = ?",
                        (int(is_now_fav), ticker),
                    )
                    if is_now_fav:
                        fav_count += 1
                    changes_count += 1

        if changes_count > 0:
            st.success(f"✓ Saved {changes_count} change(s)")
            st.session_state["watchlist_original"] = {r["_ticker"]: r for r in edited_df.to_dict(orient="records")}
            st.rerun()
        else:
            st.info("No changes to save")

    with st.expander("Edit / remove entries", expanded=False):
        all_tickers = [r["Ticker"] for r in rows]
        pick = st.selectbox("Ticker", all_tickers, key="wl_edit_pick")
        current = conn.execute(
            "SELECT target_price, notes, is_favorite FROM watchlist WHERE ticker = ?",
            (pick,),
        ).fetchone()
        c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
        edit_target = c1.number_input(
            "Target", min_value=0.0,
            value=float(current["target_price"] or 0),
            step=0.01, format="%.2f", key=f"wl_edit_target_{pick}",
        )
        edit_notes = c2.text_input(
            "Notes", value=current["notes"] or "", key=f"wl_edit_notes_{pick}",
        )
        edit_fav = c3.checkbox(
            "★ Favorite", value=bool(current["is_favorite"]),
            key=f"wl_edit_fav_{pick}",
            help="Top 5 favorites show on the Dashboard.",
        )
        if c4.button("Save", key=f"wl_edit_save_{pick}"):
            fav_count = conn.execute(
                "SELECT COUNT(*) AS c FROM watchlist WHERE is_favorite = 1 AND ticker != ?",
                (pick,),
            ).fetchone()["c"]
            if edit_fav and fav_count >= 5:
                st.error("Already 5 favorites pinned. Unpin one first.")
            else:
                with conn:
                    conn.execute(
                        "UPDATE watchlist SET target_price = ?, notes = ?, is_favorite = ? "
                        "WHERE ticker = ?",
                        (
                            edit_target if edit_target > 0 else None,
                            edit_notes.strip() or None,
                            int(edit_fav),
                            pick,
                        ),
                    )
                st.success(f"Updated {pick}.")
                st.rerun()
        if c5.button("Remove", key=f"wl_edit_remove_{pick}"):
            with conn:
                conn.execute("DELETE FROM watchlist WHERE ticker = ?", (pick,))
            st.warning(f"Removed {pick}.")
            st.rerun()
