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

    scope_options = ["All"] + ACCOUNT_TYPES_DB
    scope_db = st.radio(
        "Account scope", scope_options,
        format_func=lambda v: account_label(v) if v != "All" else "All",
        horizontal=True, label_visibility="collapsed", key="holdings_scope",
    )
    filtered = holdings if scope_db == "All" else [h for h in holdings if h.account_type == scope_db]

    port = calcs.summarize(filtered, fx.rate)

    rows = []
    holdings_data = []
    for h in filtered:
        mv_cad = h.mkt_value_cad(fx.rate)
        cost_cad = h.cost_cad(fx.rate)
        pl = None if mv_cad is None else mv_cad - cost_cad
        pl_pct = None if (h.price_native is None or h.acb_per_share == 0) else (h.price_native / h.acb_per_share) - 1
        holdings_data.append((h, mv_cad, pl, pl_pct))

    holdings_data.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)

    for h, mv_cad, pl, pl_pct in holdings_data:
        rows.append({
            "Ticker":     h.ticker,
            "Ticker Link": f"https://finance.yahoo.com/quote/{h.yahoo_ticker}",
            "Curr":       h.currency,
            "Qty":        h.quantity,
            "ACB/sh":     h.acb_per_share,
            "Price":      h.price_native if h.price_native is not None else None,
            "Mkt Value":  fmt_cad(mv_cad) if mv_cad is not None else "—",
            "P/L":        fmt_cad(pl) if pl is not None else "—",
            "P/L %":      fmt_pct(pl_pct) if pl_pct is not None else "—",
            "Class":      h.asset_class,
            "Category":   h.category,
            "_id":        h.id,
        })

    cols = st.columns(4)
    cols[0].markdown(f"**Total:** {fmt_cad(port.portfolio_cad)}")
    cols[1].markdown(f"**P/L:** {fmt_cad(port.unrealized_pl_cad)}")
    cols[2].markdown(f"**Positions:** {port.position_count}")
    cols[3].markdown(f"**Accounts:** {port.account_count}")

    st.divider()

    df = pd.DataFrame(rows)

    # Initialize session state for holdings edits
    if "holdings_original" not in st.session_state:
        st.session_state["holdings_original"] = {r["_id"]: r for r in rows}

    edited_df = st.data_editor(
        df,
        hide_index=True,
        width="stretch",
        use_container_width=True,
        column_order=["Ticker", "Ticker Link", "Curr", "Qty", "ACB/sh", "Price", "Mkt Value", "P/L", "P/L %", "Class", "Category"],
        column_config={
            "Ticker":      st.column_config.TextColumn(disabled=True),
            "Ticker Link": st.column_config.LinkColumn(
                help="Open on Yahoo Finance",
                display_text="↗", width="small",
            ),
            "Qty":         st.column_config.NumberColumn(format="%.2f", disabled=True),
            "ACB/sh":      st.column_config.NumberColumn(format="%.2f", disabled=True),
            "Price":       st.column_config.NumberColumn(format="%.2f", disabled=True),
            "Mkt Value":   st.column_config.TextColumn(disabled=True),
            "P/L":         st.column_config.TextColumn(disabled=True),
            "P/L %":       st.column_config.TextColumn(disabled=True),
            "Class":       st.column_config.SelectboxColumn(
                options=["Cash", "Stock", "ETF", "LeveragedETF", "Crypto"],
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
            for edited_row in edited_df.to_dict(orient="records"):
                holding_id = int(edited_row["_id"])
                orig = st.session_state["holdings_original"].get(holding_id, {})

                if orig.get("Category") != edited_row["Category"]:
                    conn.execute(
                        "UPDATE holdings SET category = ? WHERE id = ?",
                        (edited_row["Category"], holding_id),
                    )
                    changes_count += 1

                if orig.get("Class") != edited_row["Class"]:
                    conn.execute(
                        "UPDATE holdings SET asset_class = ? WHERE id = ?",
                        (edited_row["Class"], holding_id),
                    )
                    changes_count += 1

        if changes_count > 0:
            st.success(f"✓ Saved {changes_count} change(s)")
            st.session_state["holdings_original"] = {r["_id"]: r for r in edited_df.to_dict(orient="records")}
            st.rerun()
        else:
            st.info("No changes to save")

    st.caption(f"1 USD = {fx.rate:.4f} CAD · {fx.as_of}"
               + (" · stale" if fx.stale else ""))
