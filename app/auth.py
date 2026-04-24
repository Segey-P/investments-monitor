"""Password gate + inactivity timeout for the local Streamlit app.

Session state keys:
  auth.ok            (bool)    — unlocked?
  auth.last_activity (float)   — epoch seconds of last verified tick
  auth.timeout_min   (int)     — minutes of inactivity before lockout
"""
from __future__ import annotations

import time

import bcrypt
import streamlit as st


def _get_password_hash(conn) -> str | None:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'password_hash'"
    ).fetchone()
    return row["value"] if row else None


def _get_timeout_min(conn) -> int:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'session_timeout_min'"
    ).fetchone()
    try:
        return int(row["value"]) if row else 15
    except (TypeError, ValueError):
        return 15


def _pre_auth_summary(conn) -> None:
    """Show leakage-safe summary on the login screen: top holdings, watchlist favorites, allocations."""
    from app import calcs
    from app.fx import get_usdcad
    from app.theme import (
        PALETTE, account_badge, fmt_cad, fmt_change_pct, yahoo_link,
    )

    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)
    if port.portfolio_cad == 0:
        return

    st.caption("Public summary — visible pre-auth")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top Holdings")
        ranked = []
        for h in hs:
            mv = h.mkt_value_cad(fx.rate)
            if mv is None:
                continue
            ranked.append((h, mv))
        ranked.sort(key=lambda x: -x[1])
        top = ranked[:10]

        if top:
            head_cells = []
            for label, align in [
                ("Ticker", "left"), ("Acct", "left"), ("% Portfolio", "right"),
                ("Today", "right"), ("P/L %", "right"),
            ]:
                head_cells.append(
                    f'<th style="text-align:{align};padding:6px 8px;font-size:9px;'
                    f'color:{PALETTE["textDim"]};letter-spacing:0.06em;font-weight:600;'
                    f'border-bottom:1px solid {PALETTE["border"]};text-transform:uppercase;">{label}</th>'
                )

            body_rows = []
            for i, (h, mv) in enumerate(top):
                cost = h.cost_cad(fx.rate)
                pl = h.unrealized_pl_cad(fx.rate) or 0.0
                portfolio_pct = (mv / port.portfolio_cad * 100) if port.portfolio_cad > 0 else 0.0
                pl_pct = ((pl / cost) * 100) if cost > 0 else 0.0
                pl_color = PALETTE["green"] if pl >= 0 else PALETTE["red"]
                usd_badge = (
                    f' <span style="font-size:8px;color:{PALETTE["amber"]};'
                    f'border:1px solid {PALETTE["amber"]};border-radius:2px;'
                    f'padding:0 3px;margin-left:3px;">USD</span>'
                    if h.currency == "USD" else ""
                )
                bg = PALETTE["bgRaised"] if i % 2 else "transparent"
                body_rows.append(
                    f'<tr style="background:{bg};">'
                    f'<td style="padding:6px 8px;font-size:11px;font-weight:700;'
                    f'border-bottom:1px solid {PALETTE["border"]};">'
                    f'{yahoo_link(h.ticker, h.yahoo_ticker)}{usd_badge}</td>'
                    f'<td style="padding:6px 8px;border-bottom:1px solid {PALETTE["border"]};">'
                    f'{account_badge(h.account_type)}</td>'
                    f'<td class="mono" style="padding:6px 8px;text-align:right;font-size:11px;'
                    f'border-bottom:1px solid {PALETTE["border"]};">{portfolio_pct:.1f}%</td>'
                    f'<td style="padding:6px 8px;text-align:right;'
                    f'border-bottom:1px solid {PALETTE["border"]};">'
                    f'{fmt_change_pct(h.price_native, h.prev_close_native)}</td>'
                    f'<td class="mono" style="padding:6px 8px;text-align:right;font-size:11px;'
                    f'color:{pl_color};border-bottom:1px solid {PALETTE["border"]};">{pl_pct:.1f}%</td>'
                    f'</tr>'
                )

            st.markdown(
                '<table style="width:100%;border-collapse:collapse;font-size:11px;">'
                f'<thead><tr style="background:{PALETTE["bgRaised"]};">'
                f'{"".join(head_cells)}</tr></thead>'
                f'<tbody>{"".join(body_rows)}</tbody></table>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No priced positions yet.")

    with col2:
        st.markdown("#### Watchlist Favorites")
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

        st.markdown("---")
        st.markdown("#### Allocation by Category")
        alloc = calcs.allocations(hs, fx.rate)["by_category"]
        if alloc:
            import plotly.graph_objects as go
            items = sorted(alloc.items(), key=lambda kv: -kv[1])
            labels = [item[0] for item in items]
            values = [item[1] for item in items]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=True,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No allocations yet.")


def tick(conn) -> bool:
    """Gate entry-point. Returns True if user is authenticated and not expired.

    If False, renders the login form (or lockout) in-place and stops further
    script execution upstream is the caller's responsibility.
    """
    ss = st.session_state
    ss.setdefault("auth", {"ok": False, "last_activity": 0.0})
    st_auth = ss["auth"]
    now = time.time()
    timeout_min = _get_timeout_min(conn)
    st_auth["timeout_min"] = timeout_min

    if st_auth["ok"]:
        elapsed_min = (now - st_auth["last_activity"]) / 60.0
        remaining_min = timeout_min - elapsed_min
        if remaining_min <= 0:
            st_auth["ok"] = False
            st.warning("Session expired. Please sign in again.")
        else:
            st_auth["last_activity"] = now
            if remaining_min <= 1.0:  # under 60s
                cols = st.columns([4, 1])
                cols[0].warning(
                    f"Session expires in ~{int(remaining_min * 60)}s of inactivity."
                )
                if cols[1].button("Stay signed in", key="auth_stay"):
                    st_auth["last_activity"] = now
                    st.rerun()
            return True

    # --- Login form ---
    stored = _get_password_hash(conn)
    if stored is None:
        st.error(
            "No password set. Run `python -m scripts.set_password` in the repo root."
        )
        st.stop()

    st.markdown("### Sign in")
    with st.form("login_form", clear_on_submit=False):
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Unlock")
    if submitted:
        if bcrypt.checkpw(pw.encode("utf-8"), stored.encode("utf-8")):
            st_auth["ok"] = True
            st_auth["last_activity"] = now
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.markdown("---")
    _pre_auth_summary(conn)
    return False
