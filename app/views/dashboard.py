from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from app import calcs, prices
from app.fx import get_usdcad
from app.theme import (
    PALETTE, account_badge, account_label, fmt_cad, fmt_change_pct,
    fmt_ratio, kpi_tile, leverage_disclaimer, yahoo_link,
)

ACCOUNT_TYPES_DB = ["RRSP", "TFSA", "Unreg", "Crypto"]


def _scope_filter(holdings, scope_db: str):
    if scope_db == "All":
        return holdings
    return [h for h in holdings if h.account_type == scope_db]


def _auto_refresh(conn, holdings) -> None:
    """Hit yfinance on every page render; 60s in-process cache absorbs duplicates."""
    tickers = sorted({h.yahoo_ticker for h in holdings})
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

    today_delta = calcs.today_delta(holdings, fx.rate)
    biggest = calcs.biggest_mover(holdings)
    biggest_pct = biggest.day_change_pct() if biggest else 0.0

    today_delta_pct = (today_delta / port.portfolio_cad * 100) if port.portfolio_cad else 0.0

    # --- KPI tiles ---
    tiles = [
        kpi_tile("Portfolio value", fmt_cad(port.portfolio_cad),
                 f"{port.position_count} positions"),
        kpi_tile("Today's Δ", fmt_cad(today_delta),
                 sub=f"{today_delta_pct:+.2f}% on portfolio",
                 tone=("gain" if today_delta >= 0 else "loss")),
        kpi_tile("Biggest mover", f"{biggest.ticker if biggest else '—'}",
                 sub=f"{'▲' if biggest_pct >= 0 else '▼'} {abs(biggest_pct):.2f}% today" if biggest else "—",
                 tone=("gain" if biggest_pct >= 0 else "loss") if biggest else None),
        kpi_tile("Leverage Ratio", fmt_ratio(lev.leverage_ratio),
                 leverage_disclaimer(lev.leverage_ratio)),
    ]
    cols = st.columns(4)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # --- Allocation chart, Watchlist, What-if (3-column layout) ---
    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("#### Allocation")
        alloc = calcs.allocations(holdings, fx.rate)["by_category"]
        if alloc:
            items = sorted(alloc.items(), key=lambda kv: -kv[1])
            labels = [item[0] for item in items]
            values = [item[1] for item in items]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(
                height=280,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=True,
                font=dict(size=11),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No allocations yet.")

    with col2:
        st.markdown(
            f'#### Watchlist Favorites'
            f'<span style="float:right;font-size:10px;color:{PALETTE["textDim"]};'
            f'font-weight:normal;padding-top:6px;">→ Watchlist tab</span>',
            unsafe_allow_html=True,
        )
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
            st.caption("No favorites pinned yet.")
        else:
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
                    f'<span style="font-weight:700;font-size:12px;">{yahoo_link(ticker)}</span>'
                    f'<span style="display:flex;gap:10px;align-items:baseline;font-size:11px;">'
                    f'{chg_html}<span class="mono">{price_html}</span></span></div>'
                    f'<div style="font-size:10px;color:{PALETTE["textDim"]};margin-top:2px;">{target_html}</div>'
                    f'</div>'
                )
            st.markdown("".join(parts), unsafe_allow_html=True)

    with col3:
        st.markdown("#### Leverage Stress Test")
        h = conn.execute("SELECT * FROM heloc_account WHERE id = 1").fetchone()
        m = conn.execute("SELECT * FROM margin_account WHERE id = 1").fetchone()
        h_rate = float(h["rate_pct"] or 0)
        m_rate = float(m["rate_pct"] or 0)

        heloc_avail = max(lev.heloc_limit_cad - lev.heloc_drawn_cad, 0)
        margin_avail = max(lev.margin_limit_cad - lev.margin_balance_cad, 0)

        extra_h = st.slider(
            "Draw HELOC ($CAD)", min_value=0, max_value=int(max(heloc_avail, 1)),
            value=0, step=500, key="dash_whatif_h",
        )
        drawdown_pct = st.slider(
            "Market fall (%)", min_value=0, max_value=50,
            value=0, step=1, key="dash_whatif_drawdown",
        )

        new_h_drawn = lev.heloc_drawn_cad + extra_h
        stressed_port_val = port.portfolio_cad * (1 - drawdown_pct / 100.0)
        denom = stressed_port_val - new_h_drawn - lev.margin_balance_cad
        new_ratio = (stressed_port_val / denom) if denom > 0 else 0.0
        ratio_delta = new_ratio - lev.leverage_ratio

        st.metric(
            "Stressed ratio",
            fmt_ratio(new_ratio),
            delta=f"{ratio_delta:+.2f}×" if (extra_h > 0 or drawdown_pct > 0) else None,
        )
        if new_ratio >= 2.0:
            st.warning("⚠ Exceeds 2.0×")

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # --- Top holdings (15) ---
    last_fetch = conn.execute(
        "SELECT MAX(fetched_at) AS ts FROM prices"
    ).fetchone()["ts"]
    _top_holdings_table(holdings, port.portfolio_cad, fx.rate, last_fetch)


def _top_holdings_table(holdings, portfolio_cad: float, usdcad: float, last_fetch: str | None = None) -> None:
    col_h, col_ts = st.columns([3, 1])
    col_h.markdown("#### Top 15 Holdings")
    if last_fetch:
        col_ts.markdown(
            f'<div style="text-align:right;padding-top:6px;font-size:10px;'
            f'color:#6b7280;">Market data: {last_fetch[:16].replace("T", " ")} UTC'
            f'<br><span style="font-size:9px;">→ Holdings tab for full list</span></div>',
            unsafe_allow_html=True,
        )
    ranked = []
    for h in holdings:
        mv = h.mkt_value_cad(usdcad)
        if mv is None:
            continue
        ranked.append((h, mv))
    ranked.sort(key=lambda x: -x[1])
    top = ranked[:15]
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
