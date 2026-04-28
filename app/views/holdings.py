from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import account_label, fmt_cad, fmt_change_pct, fmt_pct

ACCOUNT_TYPES_DB = ["RRSP", "TFSA", "Unreg", "Crypto"]


def render(conn) -> None:
    fx = get_usdcad(conn)
    holdings = calcs.load_holdings(conn)

    st.markdown("### Holdings")

    col_scope, col_search = st.columns([2, 1])

    scope_options = ["All"] + ACCOUNT_TYPES_DB
    scope_db = col_scope.radio(
        "Account scope", scope_options,
        format_func=lambda v: account_label(v) if v != "All" else "All",
        horizontal=True, label_visibility="collapsed", key="holdings_scope",
    )
    search_ticker = col_search.text_input(
        "Search ticker", placeholder="e.g. TSLA", label_visibility="collapsed", key="holdings_search"
    )

    filtered = holdings if scope_db == "All" else [h for h in holdings if h.account_type == scope_db]
    if search_ticker:
        filtered = [h for h in filtered if search_ticker.upper() in h.ticker]

    port = calcs.summarize(filtered, fx.rate)

    # Fetch prev_close from prices table for accurate Today % calculation
    prices_map = {}
    for row in conn.execute("SELECT ticker, price, prev_close FROM prices").fetchall():
        prices_map[row["ticker"]] = {"price": row["price"], "prev_close": row["prev_close"]}

    rows = []
    holdings_data = []
    for h in filtered:
        mv_cad = h.mkt_value_cad(fx.rate)
        cost_cad = h.cost_cad(fx.rate)
        pl = None if mv_cad is None else mv_cad - cost_cad
        pl_pct = None if (h.price_native is None or h.acb_per_share == 0) else (h.price_native / h.acb_per_share) - 1

        # Today's change from prices table
        price_data = prices_map.get(h.ticker)
        day_delta_native = None
        day_delta_cad = None
        day_delta_pct = None

        if price_data and price_data["prev_close"]:
            prev = price_data["prev_close"]
            curr = price_data["price"]
            if curr is not None:
                day_delta_native = h.quantity * (curr - prev)
                day_delta_cad = day_delta_native * (fx.rate if h.currency == "USD" else 1)
                day_delta_pct = ((curr - prev) / prev) * 100 if prev != 0 else None

        total_acb = h.quantity * h.acb_per_share
        holdings_data.append((h, mv_cad, pl, pl_pct, day_delta_cad, day_delta_pct, total_acb))

    holdings_data.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)

    for h, mv_cad, pl, pl_pct, day_delta_cad, day_delta_pct, total_acb in holdings_data:
        rows.append({
            "Ticker":     h.ticker,
            "Ticker Link": f"https://finance.yahoo.com/quote/{h.yahoo_ticker}",
            "Name":       h.description or "—",
            "Curr":       h.currency,
            "Qty":        int(h.quantity) if h.quantity == int(h.quantity) else h.quantity,
            "ACB":        total_acb,
            "Price":      h.price_native if h.price_native is not None else None,
            "Today":      day_delta_cad,
            "Today %":    day_delta_pct,
            "Mkt Value":  mv_cad,
            "P/L":        pl,
            "P/L %":      pl_pct,
            "Class":      h.asset_class,
            "Category":   h.category,
            "_id":        h.id,
        })

    cols = st.columns(3)
    cols[0].markdown(f"**Total:** {fmt_cad(port.portfolio_cad)}")
    cols[1].markdown(f"**P/L:** {fmt_cad(port.unrealized_pl_cad)}")
    cols[2].markdown(f"**Positions:** {port.position_count}")

    st.divider()

    df = pd.DataFrame(rows)

    # Initialize session state for holdings edits
    if "holdings_original" not in st.session_state:
        st.session_state["holdings_original"] = {r["_id"]: r for r in rows}

    st.caption(
        "Editable: **Qty**, **ACB**, **Class**, **Category** · "
        "Read-only: everything else (live feed)"
    )

    edited_df = st.data_editor(
        df,
        hide_index=True,
        width="stretch",
        use_container_width=True,
        column_order=["Ticker", "Ticker Link", "Name", "Curr", "Qty", "Price", "ACB", "Today", "Today %", "Mkt Value", "P/L", "P/L %", "Class", "Category"],
        column_config={
            "Ticker":      st.column_config.TextColumn(disabled=True),
            "Ticker Link": st.column_config.LinkColumn(
                help="Open on Yahoo Finance",
                display_text="↗", width="small",
            ),
            "Name":        st.column_config.TextColumn(disabled=True),
            "Qty":         st.column_config.NumberColumn(format="%d"),
            "Price":       st.column_config.NumberColumn(format="$%.2f", disabled=True),
            "ACB":         st.column_config.NumberColumn(format="$,.2f"),
            "Today":       st.column_config.NumberColumn(format="$%.2f", disabled=True),
            "Today %":     st.column_config.NumberColumn(format="%.2f%%", disabled=True),
            "Mkt Value":   st.column_config.NumberColumn(format="$,.2f", disabled=True),
            "P/L":         st.column_config.NumberColumn(format="$%.2f", disabled=True),
            "P/L %":       st.column_config.NumberColumn(format="%.2f%%", disabled=True),
            "Class":       st.column_config.SelectboxColumn(
                options=["Cash", "Stock", "ETF", "LeveragedETF", "Crypto", "Options"],
            ),
            "Curr":        st.column_config.TextColumn(disabled=True),
            "Category":    st.column_config.SelectboxColumn(
                options=["Cash", "Dividend", "Growth", "Other"],
            ),
        },
        key="holdings_editor",
    )

    # Save button and logic
    if st.button("💾 Save Changes", key="holdings_save"):
        changes_count = 0
        with conn:
            for orig_row in df.to_dict(orient="records"):
                holding_id = int(orig_row["_id"])
                orig = st.session_state["holdings_original"].get(holding_id, {})

                if orig.get("Category") != orig_row["Category"]:
                    conn.execute(
                        "UPDATE holdings SET category = ? WHERE id = ?",
                        (orig_row["Category"], holding_id),
                    )
                    changes_count += 1

                if orig.get("Class") != orig_row["Class"]:
                    conn.execute(
                        "UPDATE holdings SET asset_class = ? WHERE id = ?",
                        (orig_row["Class"], holding_id),
                    )
                    changes_count += 1

                qty_orig = round(float(orig.get("Qty") or 0), 6)
                qty_new = round(float(orig_row.get("Qty") or 0), 6)
                if qty_orig != qty_new and qty_new > 0:
                    conn.execute(
                        "UPDATE holdings SET quantity = ? WHERE id = ?",
                        (qty_new, holding_id),
                    )
                    changes_count += 1

                acb_total_orig = round(float(orig.get("ACB") or 0), 2)
                acb_total_new = round(float(orig_row.get("ACB") or 0), 2)
                if acb_total_orig != acb_total_new and acb_total_new >= 0:
                    acb_per_share_new = acb_total_new / qty_new if qty_new > 0 else 0
                    conn.execute(
                        "UPDATE holdings SET acb_per_share = ? WHERE id = ?",
                        (acb_per_share_new, holding_id),
                    )
                    changes_count += 1

        if changes_count > 0:
            st.success(f"✓ Saved {changes_count} change(s)")
            st.session_state.pop("holdings_original", None)
            st.rerun()
        else:
            st.info("No changes to save")

    last_fetch = conn.execute(
        "SELECT MAX(fetched_at) AS ts FROM prices"
    ).fetchone()["ts"]
    ts_str = last_fetch[:16].replace("T", " ") + " UTC" if last_fetch else "—"
    st.caption(
        f"1 USD = {fx.rate:.4f} CAD · {fx.as_of}"
        + (" · stale" if fx.stale else "")
        + f" · Market data: {ts_str}"
    )
