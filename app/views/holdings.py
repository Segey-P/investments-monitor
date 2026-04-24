from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import fmt_cad


def render(conn) -> None:
    fx = get_usdcad(conn)
    holdings = calcs.load_holdings(conn)

    st.markdown("### Holdings")

    scope = st.radio(
        "Account scope", ["All", "RRSP", "TFSA", "Unreg", "Crypto"],
        horizontal=True, label_visibility="collapsed", key="holdings_scope",
    )
    filtered = holdings if scope == "All" else [h for h in holdings if h.account_type == scope]

    port = calcs.summarize(filtered, fx.rate)

    rows = []
    for h in filtered:
        mv_cad = h.mkt_value_cad(fx.rate)
        cost_cad = h.cost_cad(fx.rate)
        gl = None if mv_cad is None else mv_cad - cost_cad
        gl_pct = None if (gl is None or cost_cad == 0) else (gl / cost_cad)
        pct_port = None if (mv_cad is None or port.portfolio_cad == 0) else (mv_cad / port.portfolio_cad)
        rows.append({
            "Ticker":     h.ticker,
            "Acct":       h.account_type,
            "Cur":        h.currency,
            "Qty":        h.quantity,
            "ACB/sh":     h.acb_per_share,
            "Price":      h.price_native if h.price_native is not None else None,
            "Mkt Value":  mv_cad,
            "G/L":        gl,
            "G/L %":      gl_pct,
            "% Portfolio": pct_port,
            "Class":      h.asset_class,
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "Qty":         st.column_config.NumberColumn(format="%.2f"),
            "ACB/sh":      st.column_config.NumberColumn(format="%.2f"),
            "Price":       st.column_config.NumberColumn(format="%.2f"),
            "Mkt Value":   st.column_config.NumberColumn(format="$%.0f"),
            "G/L":         st.column_config.NumberColumn(format="$%.0f"),
            "G/L %":       st.column_config.NumberColumn(format="%.2f%%"),
            "% Portfolio": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    cols = st.columns(4)
    cols[0].markdown(f"**Total:** {fmt_cad(port.portfolio_cad)}")
    cols[1].markdown(f"**G/L:** {fmt_cad(port.unrealized_gl_cad)}")
    cols[2].markdown(f"**Positions:** {port.position_count}")
    cols[3].markdown(f"**Accounts:** {port.account_count}")

    st.caption(f"1 USD = {fx.rate:.4f} CAD · BOC · {fx.as_of}"
               + (" · stale" if fx.stale else ""))
