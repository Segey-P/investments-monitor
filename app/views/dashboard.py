from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs, prices
from app.fx import get_usdcad
from app.theme import (
    PALETTE, account_badge, account_label, fmt_cad, fmt_change_pct,
    fmt_pct, fmt_ratio, kpi_tile, leverage_disclaimer, yahoo_link,
)

ACCOUNT_TYPES_DB = ["RRSP", "TFSA", "Unreg", "Crypto"]


def _scope_filter(holdings, scope_db: str):
    if scope_db == "All":
        return holdings
    return [h for h in holdings if h.account_type == scope_db]


def _auto_refresh(conn, holdings) -> None:
    """Hit yfinance on every page render; 60s in-process cache absorbs duplicates."""
    fav_tickers = [r["ticker"] for r in conn.execute(
        "SELECT ticker FROM watchlist WHERE is_favorite = 1 ORDER BY ticker LIMIT 5"
    ).fetchall()]
    tickers = sorted({h.yahoo_ticker for h in holdings} | set(fav_tickers))
    if not tickers:
        return
    try:
        quotes = prices.get_quotes(tickers)
        prices.persist_quotes(conn, quotes)
    except Exception as e:
        st.warning(f"Live price fetch failed: {e}. Showing cached values.")


def render(conn) -> None:
    holdings_all = calcs.load_holdings(conn)
    _auto_refresh(conn, holdings_all)
    holdings_all = calcs.load_holdings(conn)

    fx = get_usdcad(conn)

    st.markdown("### Dashboard")

    scope_options = ["All"] + ACCOUNT_TYPES_DB
    scope_db = st.radio(
        "Account scope", scope_options,
        format_func=lambda v: account_label(v) if v != "All" else "All",
        horizontal=True, label_visibility="collapsed", key="dash_scope",
    )
    holdings = _scope_filter(holdings_all, scope_db)

    port = calcs.summarize(holdings, fx.rate)
    unreg_value = calcs.summarize(
        [h for h in holdings_all if h.account_type == "Unreg"], fx.rate
    ).portfolio_cad
    lev = calcs.leverage(conn, port.portfolio_cad, unreg_value)
    nw = calcs.net_worth(conn, port.portfolio_cad)

    fx_sub = (
        f'FX <a href="https://ca.finance.yahoo.com/quote/CAD=X/" '
        f'target="_blank" rel="noopener noreferrer">{fx.rate:.4f}</a> · {fx.as_of}'
        + (" · stale" if fx.stale else "")
    )

    pl_pct_text = (
        f"{(port.unrealized_pl_cad / port.portfolio_cad * 100):+.2f}%"
        if port.portfolio_cad else "—"
    )

    tiles = [
        kpi_tile("Net Worth", fmt_cad(nw.net_worth_cad), fx_sub),
        kpi_tile("Portfolio", fmt_cad(port.portfolio_cad),
                 f"{port.position_count} positions · {port.account_count} accts"),
        kpi_tile("Unrealized P/L", fmt_cad(port.unrealized_pl_cad),
                 sub=pl_pct_text,
                 tone=("gain" if port.unrealized_pl_cad >= 0 else "loss")),
        kpi_tile("Leverage Ratio", fmt_ratio(lev.leverage_ratio),
                 leverage_disclaimer(lev.leverage_ratio)),
        kpi_tile("HELOC Drawn", fmt_cad(lev.heloc_drawn_cad),
                 f"util {fmt_pct(lev.heloc_util_pct)} · limit {fmt_cad(lev.heloc_limit_cad)}"),
    ]
    cols = st.columns(5)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    left, right = st.columns([1, 2])

    with left:
        _allocation_widget(holdings, fx.rate)
        st.markdown("&nbsp;", unsafe_allow_html=True)
        _watchlist_mini(conn)

    with right:
        _top_holdings_table(holdings, port.portfolio_cad, fx.rate)


def _allocation_widget(holdings, usdcad: float) -> None:
    st.markdown("#### Allocation")
    dim = st.radio(
        "Allocation dimension",
        ["Asset class", "Country", "Currency"],
        horizontal=True, label_visibility="collapsed", key="alloc_dim",
    )
    dim_key = {"Asset class": "by_asset_class",
               "Country": "by_country",
               "Currency": "by_currency"}[dim]
    alloc = calcs.allocations(holdings, usdcad)[dim_key]
    if not alloc:
        st.info("No priced positions yet.")
        return
    df = pd.DataFrame(
        sorted(alloc.items(), key=lambda kv: -kv[1]),
        columns=["Bucket", "Share"],
    )
    st.bar_chart(df.set_index("Bucket")["Share"], height=240)


def _watchlist_mini(conn) -> None:
    st.markdown("#### Watchlist favorites")
    rows = conn.execute("""
        SELECT w.ticker, w.target_price,
               p.price AS price, p.prev_close AS prev
        FROM watchlist w
        LEFT JOIN prices p ON p.ticker = w.ticker
        WHERE w.is_favorite = 1
        ORDER BY w.ticker
        LIMIT 5
    """).fetchall()
    if not rows:
        st.caption(
            "No favorites pinned. Mark watchlist items as favorite ⭐ in the "
            "Watchlist tab and the top 5 will surface here."
        )
        return
    parts = []
    for r in rows:
        ticker = r["ticker"]
        price = r["price"]
        prev = r["prev"]
        target = r["target_price"]
        chg_html = fmt_change_pct(price, prev)
        price_html = f'${price:.2f}' if price is not None else '—'
        if price is not None and target:
            gap_pct = (price - target) / target * 100
            arrow = "▲" if gap_pct >= 0 else "▼"
            color = PALETTE["green"] if gap_pct >= 0 else PALETTE["amber"]
            target_html = (
                f'Target <span class="mono">${target:.2f}</span> · '
                f'<span style="color:{color};">{arrow} {abs(gap_pct):.1f}% '
                f'{"above" if gap_pct >= 0 else "away"}</span>'
            )
        else:
            target_html = '<span style="color:#6b7280;">No target set</span>'
        parts.append(
            f'<div style="padding:8px 0;border-bottom:1px solid {PALETTE["border"]};">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
            f'<span style="font-weight:700;">{yahoo_link(ticker)}</span>'
            f'<span style="display:flex;gap:12px;align-items:baseline;">'
            f'{chg_html}<span class="mono">{price_html}</span></span></div>'
            f'<div style="font-size:11px;color:{PALETTE["textDim"]};margin-top:2px;">{target_html}</div>'
            f'</div>'
        )
    st.markdown("".join(parts), unsafe_allow_html=True)


def _top_holdings_table(holdings, portfolio_cad: float, usdcad: float) -> None:
    st.markdown("#### Top holdings")
    ranked = []
    for h in holdings:
        mv = h.mkt_value_cad(usdcad)
        if mv is None:
            continue
        ranked.append((h, mv))
    ranked.sort(key=lambda x: -x[1])
    top = ranked[:10]
    if not top:
        st.caption("No priced positions yet.")
        return

    head_cells = []
    for label, align in [
        ("Ticker", "left"), ("Acct", "left"), ("Mkt Value", "right"),
        ("Today", "right"), ("P/L", "right"), ("% Port", "right"),
    ]:
        head_cells.append(
            f'<th style="text-align:{align};padding:6px 12px;font-size:10px;'
            f'color:{PALETTE["textDim"]};letter-spacing:0.06em;font-weight:600;'
            f'border-bottom:1px solid {PALETTE["border"]};text-transform:uppercase;">{label}</th>'
        )

    body_rows = []
    for i, (h, mv) in enumerate(top):
        pl = h.unrealized_pl_cad(usdcad) or 0.0
        pl_color = PALETTE["green"] if pl >= 0 else PALETTE["red"]
        port_pct = (mv / portfolio_cad * 100) if portfolio_cad else 0.0
        usd_badge = (
            f' <span style="font-size:9px;color:{PALETTE["amber"]};'
            f'border:1px solid {PALETTE["amber"]};border-radius:2px;'
            f'padding:0 3px;margin-left:4px;">USD</span>'
            if h.currency == "USD" else ""
        )
        bg = PALETTE["bgRaised"] if i % 2 else "transparent"
        body_rows.append(
            f'<tr style="background:{bg};">'
            f'<td style="padding:7px 12px;font-size:12px;font-weight:700;'
            f'border-bottom:1px solid {PALETTE["border"]};">'
            f'{yahoo_link(h.ticker, h.yahoo_ticker)}{usd_badge}</td>'
            f'<td style="padding:7px 12px;border-bottom:1px solid {PALETTE["border"]};">'
            f'{account_badge(h.account_type)}</td>'
            f'<td class="mono" style="padding:7px 12px;text-align:right;font-size:12px;'
            f'border-bottom:1px solid {PALETTE["border"]};">{fmt_cad(mv)}</td>'
            f'<td style="padding:7px 12px;text-align:right;'
            f'border-bottom:1px solid {PALETTE["border"]};">'
            f'{fmt_change_pct(h.price_native, h.prev_close_native)}</td>'
            f'<td class="mono" style="padding:7px 12px;text-align:right;font-size:12px;'
            f'color:{pl_color};border-bottom:1px solid {PALETTE["border"]};">{fmt_cad(pl)}</td>'
            f'<td class="mono" style="padding:7px 12px;text-align:right;font-size:11px;'
            f'color:{PALETTE["textDim"]};border-bottom:1px solid {PALETTE["border"]};">'
            f'{port_pct:.1f}%</td>'
            f'</tr>'
        )

    st.markdown(
        '<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:{PALETTE["bgRaised"]};">'
        f'{"".join(head_cells)}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table>',
        unsafe_allow_html=True,
    )
