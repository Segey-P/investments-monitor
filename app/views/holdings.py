from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import account_label, fmt_cad

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
    for h in filtered:
        mv_cad = h.mkt_value_cad(fx.rate)
        cost_cad = h.cost_cad(fx.rate)
        pl = None if mv_cad is None else mv_cad - cost_cad
        pl_pct = None if (h.price_native is None or h.acb_per_share == 0) else (h.price_native / h.acb_per_share) - 1
        rows.append({
            "Ticker":     h.ticker,
            "Yahoo":      f"https://finance.yahoo.com/quote/{h.yahoo_ticker}",
            "Curr":       h.currency,
            "Qty":        h.quantity,
            "ACB/sh":     h.acb_per_share,
            "Price":      h.price_native if h.price_native is not None else None,
            "Mkt Value":  mv_cad,
            "P/L":        pl,
            "P/L %":      pl_pct,
            "Class":      h.asset_class,
        })

    rows.sort(key=lambda r: r["Mkt Value"] if r["Mkt Value"] is not None else 0, reverse=True)

    cols = st.columns(4)
    cols[0].markdown(f"**Total:** {fmt_cad(port.portfolio_cad)}")
    cols[1].markdown(f"**P/L:** {fmt_cad(port.unrealized_pl_cad)}")
    cols[2].markdown(f"**Positions:** {port.position_count}")
    cols[3].markdown(f"**Accounts:** {port.account_count}")

    st.divider()

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_order=["Ticker", "Yahoo", "Curr", "Qty", "ACB/sh", "Price",
                      "Mkt Value", "P/L", "P/L %", "Class"],
        column_config={
            "Yahoo":       st.column_config.LinkColumn(
                "↗", help="Open on Yahoo Finance",
                display_text="↗", width="small",
            ),
            "Qty":         st.column_config.NumberColumn(format="%.2f"),
            "ACB/sh":      st.column_config.NumberColumn(format="%.2f"),
            "Price":       st.column_config.NumberColumn(format="%.2f"),
            "Mkt Value":   st.column_config.NumberColumn(format="$%.0f"),
            "P/L":         st.column_config.NumberColumn(format="$%.0f"),
            "P/L %":       st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    st.caption(f"1 USD = {fx.rate:.4f} CAD · {fx.as_of}"
               + (" · stale" if fx.stale else ""))
