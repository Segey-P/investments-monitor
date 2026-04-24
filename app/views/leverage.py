from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import fmt_cad, fmt_pct, fmt_ratio, kpi_tile


def _zone_label(ratio: float) -> str:
    if ratio < 1.5:
        return "Safe"
    if ratio < 2.0:
        return "Caution"
    return "High"


def render(conn) -> None:
    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)
    unreg_value = calcs.summarize(
        [h for h in hs if h.account_type == "Unreg"], fx.rate
    ).portfolio_cad
    lev = calcs.leverage(conn, port.portfolio_cad, unreg_value)

    st.markdown("### Leverage")

    heloc_avail = max(lev.heloc_limit_cad - lev.heloc_drawn_cad, 0)
    tiles = [
        kpi_tile("HELOC Drawn",     fmt_cad(lev.heloc_drawn_cad),
                 f"util {fmt_pct(lev.heloc_util_pct)}"),
        kpi_tile("HELOC Available", fmt_cad(heloc_avail),
                 f"limit {fmt_cad(lev.heloc_limit_cad)}"),
        kpi_tile("Margin Balance",  fmt_cad(lev.margin_balance_cad)),
        kpi_tile("Total Borrowed",  fmt_cad(lev.total_borrowed_cad)),
        kpi_tile("Leverage Ratio",  fmt_ratio(lev.leverage_ratio),
                 _zone_label(lev.leverage_ratio)),
        kpi_tile("Margin Buffer",
                 fmt_pct(lev.margin_buffer_pct) if lev.margin_buffer_pct is not None else "—"),
    ]
    cols = st.columns(6)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    tab_heloc, tab_margin = st.tabs(["HELOC", "Margin"])

    # ========================= HELOC tab =========================
    with tab_heloc:
        st.markdown("#### Balances")
        c1, c2, c3 = st.columns(3)
        h_drawn = c1.number_input(
            "Total drawn ($CAD)", min_value=0.0,
            value=float(lev.heloc_drawn_cad), step=500.0, format="%.2f",
            key="lev_h_drawn",
        )
        h_limit = c2.number_input(
            "Credit limit ($CAD)", min_value=0.0,
            value=float(lev.heloc_limit_cad), step=1000.0, format="%.2f",
            key="lev_h_limit",
        )
        h_rate = c3.number_input(
            "Rate (% annual)", min_value=0.0, max_value=30.0,
            value=float(_heloc_rate(conn)), step=0.05, format="%.2f",
            key="lev_h_rate",
        )
        if st.button("Save HELOC balances", key="lev_h_save"):
            _set_heloc(conn, h_limit, h_rate)
            _reset_heloc_balance(conn, h_drawn)
            st.success("Saved.")
            st.rerun()

        st.markdown("#### Utilization")
        util = (h_drawn / h_limit) if h_limit > 0 else 0.0
        st.progress(min(util, 1.0),
                    text=f"{util * 100:.1f}% used · {fmt_cad(h_drawn)} of {fmt_cad(h_limit)}")

        st.markdown("#### Drawdown ledger")
        ledger_rows = conn.execute(
            "SELECT id, date, amount_cad, purpose FROM heloc_draws ORDER BY date DESC, id DESC"
        ).fetchall()
        if ledger_rows:
            df = pd.DataFrame([dict(r) for r in ledger_rows])
            st.dataframe(
                df, hide_index=True, width="stretch",
                column_config={"amount_cad": st.column_config.NumberColumn(format="$%.2f")},
            )
        else:
            st.caption("No entries yet.")

        with st.expander("Add entry"):
            c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
            new_date = c1.date_input("Date", value=date.today(), key="lev_add_date")
            new_amt = c2.number_input("Amount (CAD)", step=100.0, format="%.2f",
                                       key="lev_add_amt",
                                       help="Positive = draw, negative = repayment")
            new_purpose = c3.text_input("Purpose", key="lev_add_purpose")
            if c4.button("Add", key="lev_add_btn"):
                if new_amt != 0:
                    with conn:
                        conn.execute(
                            "INSERT INTO heloc_draws (date, amount_cad, purpose) VALUES (?, ?, ?)",
                            (new_date.isoformat(), new_amt, new_purpose or None),
                        )
                    st.success("Entry added.")
                    st.rerun()

        with st.expander("Remove entry"):
            if ledger_rows:
                pick = st.selectbox(
                    "Entry", options=[r["id"] for r in ledger_rows],
                    format_func=lambda i: next(
                        f"{r['date']} · ${r['amount_cad']:.2f} · {r['purpose'] or ''}"
                        for r in ledger_rows if r["id"] == i
                    ),
                    key="lev_rm_pick",
                )
                if st.button("Remove", key="lev_rm_btn"):
                    with conn:
                        conn.execute("DELETE FROM heloc_draws WHERE id = ?", (pick,))
                    st.warning("Removed.")
                    st.rerun()

        st.markdown("#### What-if")
        extra = st.slider(
            "Additional draw ($CAD)", min_value=0, max_value=int(max(heloc_avail, 1)),
            value=0, step=500, key="lev_whatif",
        )
        if extra > 0 or True:
            new_drawn = lev.heloc_drawn_cad + extra
            new_util = (new_drawn / lev.heloc_limit_cad) if lev.heloc_limit_cad else 0.0
            denom = port.portfolio_cad - new_drawn - lev.margin_balance_cad
            new_ratio = (port.portfolio_cad / denom) if denom > 0 else 0.0
            new_mo = new_drawn * (h_rate / 100.0) / 12.0
            cols = st.columns(4)
            cols[0].metric("New drawn", fmt_cad(new_drawn))
            cols[1].metric("New util", fmt_pct(new_util))
            cols[2].metric("New ratio", fmt_ratio(new_ratio), _zone_label(new_ratio))
            cols[3].metric("New mo. interest", fmt_cad(new_mo))

    # ========================= Margin tab =========================
    with tab_margin:
        m = conn.execute("SELECT * FROM margin_account WHERE id = 1").fetchone()

        st.markdown("#### Balances")
        c1, c2, c3 = st.columns(3)
        m_bal = c1.number_input(
            "Current balance ($CAD)", min_value=0.0,
            value=float(m["balance_cad"] or 0), step=500.0, format="%.2f",
            key="lev_m_bal",
        )
        m_limit = c2.number_input(
            "Borrowing limit ($CAD)", min_value=0.0,
            value=float(m["limit_cad"] or 0), step=1000.0, format="%.2f",
            key="lev_m_limit",
        )
        m_broker = c3.text_input(
            "Broker", value=m["broker"] or "Questrade", key="lev_m_broker",
        )
        if st.button("Save margin balances", key="lev_m_save"):
            with conn:
                conn.execute(
                    "UPDATE margin_account SET balance_cad = ?, limit_cad = ?, broker = ? WHERE id = 1",
                    (m_bal, m_limit, m_broker),
                )
            st.success("Saved.")
            st.rerun()

        st.markdown("#### Utilization")
        m_util = (m_bal / m_limit) if m_limit > 0 else 0.0
        st.progress(min(m_util, 1.0),
                    text=f"{m_util * 100:.1f}% used · {fmt_cad(m_bal)} of {fmt_cad(m_limit)}")

        # Margin-call warning
        warn_thresh = float(m["warn_buffer_pct"] or 50) / 100.0
        if lev.margin_buffer_pct is not None and lev.margin_buffer_pct < warn_thresh and m_bal > 0:
            st.error(
                f"⚠ Margin buffer {lev.margin_buffer_pct*100:.1f}% is below "
                f"warning threshold {warn_thresh*100:.0f}%."
            )

        st.markdown("#### Monthly interest")
        st.markdown(f"`{fmt_cad(lev.margin_monthly_interest_cad)}` "
                    f"at {float(m['rate_pct'] or 0):.2f}%")


def _heloc_rate(conn) -> float:
    row = conn.execute("SELECT rate_pct FROM heloc_account WHERE id = 1").fetchone()
    return float(row["rate_pct"] or 0)


def _set_heloc(conn, limit: float, rate: float) -> None:
    with conn:
        conn.execute(
            "UPDATE heloc_account SET limit_cad = ?, rate_pct = ? WHERE id = 1",
            (limit, rate),
        )


def _reset_heloc_balance(conn, drawn: float) -> None:
    """Replace the drawdown ledger with a single opening-balance row.

    Preserves the ledger structure (spec requires per-draw entries) while
    keeping the 'quick balance update' ergonomics specified in Module 2 §C.
    """
    with conn:
        conn.execute("DELETE FROM heloc_draws")
        conn.execute(
            "INSERT INTO heloc_draws (date, amount_cad, purpose) VALUES (?, ?, ?)",
            (date.today().isoformat(), drawn, "Opening balance (reset via Leverage screen)"),
        )
