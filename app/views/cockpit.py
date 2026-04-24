from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import account_badge, fmt_cad, fmt_pct, fmt_ratio, kpi_tile


def _scope_filter(holdings, scope: str):
    if scope == "All":
        return holdings
    return [h for h in holdings if h.account_type == scope]


def render(conn) -> None:
    fx = get_usdcad(conn)
    holdings_all = calcs.load_holdings(conn)

    st.markdown("### Cockpit")

    scope = st.radio(
        "Account scope", ["All", "RRSP", "TFSA", "Unreg", "Crypto"],
        horizontal=True, label_visibility="collapsed", key="scope",
    )
    holdings = _scope_filter(holdings_all, scope)

    port = calcs.summarize(holdings, fx.rate)
    unreg_value = calcs.summarize(
        [h for h in holdings_all if h.account_type == "Unreg"], fx.rate
    ).portfolio_cad
    lev = calcs.leverage(conn, port.portfolio_cad, unreg_value)
    nw = calcs.net_worth(conn, port.portfolio_cad)

    missing_note = (
        f"{port.missing_prices} position(s) missing price — refresh prices"
        if port.missing_prices else f"FX {fx.rate:.4f} · BOC {fx.as_of}"
    )

    tiles = [
        kpi_tile("Net Worth", fmt_cad(nw.net_worth_cad), missing_note),
        kpi_tile("Portfolio", fmt_cad(port.portfolio_cad),
                 f"{port.position_count} positions · {port.account_count} accts"),
        kpi_tile("Leverage Ratio", fmt_ratio(lev.leverage_ratio),
                 "Safe <1.5× · Caution 1.5–2× · High 2×+"),
        kpi_tile("HELOC Drawn", fmt_cad(lev.heloc_drawn_cad),
                 f"util {fmt_pct(lev.heloc_util_pct)} · limit {fmt_cad(lev.heloc_limit_cad)}"),
        kpi_tile(
            "Unrealized G/L", fmt_cad(port.unrealized_gl_cad),
            tone=("gain" if port.unrealized_gl_cad >= 0 else "loss"),
            sub=f"{(port.unrealized_gl_cad / port.portfolio_cad * 100):+.2f}%"
                if port.portfolio_cad else "—",
        ),
        kpi_tile("Monthly HELOC Interest", fmt_cad(lev.heloc_monthly_interest_cad),
                 f"margin: {fmt_cad(lev.margin_monthly_interest_cad)}"),
    ]
    cols = st.columns(6)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    left, right = st.columns([2, 1])

    with left:
        st.markdown("#### Allocation")
        dim = st.selectbox(
            "Dimension",
            ["By Account", "By Asset Class", "By Country", "By Currency"],
            label_visibility="collapsed", key="alloc_dim",
        )
        dim_key = {"By Account": "by_account", "By Asset Class": "by_asset_class",
                   "By Country": "by_country", "By Currency": "by_currency"}[dim]
        alloc = calcs.allocations(holdings, fx.rate)[dim_key]
        if alloc:
            df = pd.DataFrame(
                sorted(alloc.items(), key=lambda kv: -kv[1]),
                columns=["Bucket", "Share"],
            )
            df["Pct"] = df["Share"].map(lambda v: f"{v*100:.1f}%")
            st.bar_chart(df.set_index("Bucket")["Share"], height=220)
            st.dataframe(df[["Bucket", "Pct"]], hide_index=True,
                         width="stretch")
        else:
            st.info("No priced positions yet. Click 'Refresh prices' below.")

    with right:
        st.markdown("#### Top Holdings")
        ranked = [
            (h, h.mkt_value_cad(fx.rate))
            for h in holdings if h.mkt_value_cad(fx.rate) is not None
        ]
        ranked.sort(key=lambda x: -x[1])
        for h, mv in ranked[:5]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:6px 0;border-bottom:1px solid #2a2a2a;">'
                f'<span class="mono">{h.ticker}</span>'
                f'<span>{account_badge(h.account_type)}</span>'
                f'<span class="mono">{fmt_cad(mv)}</span></div>',
                unsafe_allow_html=True,
            )
        if not ranked:
            st.caption("No priced positions yet.")

    st.markdown("&nbsp;", unsafe_allow_html=True)
    if st.button("↻ Refresh prices"):
        _do_price_refresh(conn, holdings_all)
        st.rerun()


def _do_price_refresh(conn, holdings) -> None:
    from app import prices
    tickers = sorted({h.yahoo_ticker for h in holdings})
    with st.spinner(f"Fetching {len(tickers)} prices…"):
        quotes = prices.get_quotes(tickers)
        prices.persist_quotes(conn, quotes)
    missing = [t for t, q in quotes.items() if q.price is None]
    if missing:
        st.warning(f"Missing price for: {', '.join(missing[:10])}"
                   + ("…" if len(missing) > 10 else ""))
    else:
        st.success(f"Refreshed {len(quotes)} tickers.")
