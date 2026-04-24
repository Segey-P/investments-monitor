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
    margin_avail = max(lev.margin_limit_cad - lev.margin_balance_cad, 0)
    margin_util = (lev.margin_balance_cad / lev.margin_limit_cad) if lev.margin_limit_cad > 0 else 0.0
    total_util = ((lev.heloc_drawn_cad + lev.margin_balance_cad) / (lev.heloc_limit_cad + lev.margin_limit_cad)) if (lev.heloc_limit_cad + lev.margin_limit_cad) > 0 else 0.0

    cols = st.columns([2, 2, 2])
    with cols[0]:
        st.markdown(kpi_tile("HELOC Drawn", fmt_cad(lev.heloc_drawn_cad),
                            f"{fmt_pct(lev.heloc_util_pct)} util"), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(kpi_tile("Margin Drawn", fmt_cad(lev.margin_balance_cad),
                            f"{fmt_pct(margin_util)} util"), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(kpi_tile("Total Util", fmt_pct(total_util),
                            f"ratio {fmt_ratio(lev.leverage_ratio)}"), unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    cols = st.columns([2, 2, 2])
    with cols[0]:
        st.markdown(kpi_tile("HELOC Available", fmt_cad(heloc_avail),
                            f"of {fmt_cad(lev.heloc_limit_cad)}"), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(kpi_tile("Margin Available", fmt_cad(margin_avail),
                            f"of {fmt_cad(lev.margin_limit_cad)}"), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(kpi_tile("Zone", _zone_label(lev.leverage_ratio),
                            ""), unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    tab_whatif, tab_heloc, tab_margin = st.tabs(["What-if", "HELOC", "Margin"])

    # ========================= What-if tab =========================
    with tab_whatif:
        h = conn.execute("SELECT * FROM heloc_account WHERE id = 1").fetchone()
        m = conn.execute("SELECT * FROM margin_account WHERE id = 1").fetchone()
        h_rate = float(h["rate_pct"] or 0)
        m_rate = float(m["rate_pct"] or 0)

        st.markdown("#### HELOC Scenario")
        extra_h = st.slider(
            "Additional HELOC draw ($CAD)", min_value=0, max_value=int(max(heloc_avail, 1)),
            value=0, step=500, key="lev_whatif_h",
        )
        new_h_drawn = lev.heloc_drawn_cad + extra_h
        new_h_util = (new_h_drawn / lev.heloc_limit_cad) if lev.heloc_limit_cad else 0.0
        new_h_mo = new_h_drawn * (h_rate / 100.0) / 12.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("New drawn", fmt_cad(new_h_drawn))
        c2.metric("New util", fmt_pct(new_h_util))
        denom = port.portfolio_cad - new_h_drawn - lev.margin_balance_cad
        new_ratio = (port.portfolio_cad / denom) if denom > 0 else 0.0
        c3.metric("New ratio", fmt_ratio(new_ratio), _zone_label(new_ratio))
        c4.metric("New monthly interest", fmt_cad(new_h_mo))

        st.markdown("#### Margin Scenario")
        extra_m = st.slider(
            "Additional Margin draw ($CAD)", min_value=0, max_value=int(max(margin_avail, 1)),
            value=0, step=500, key="lev_whatif_m",
        )
        new_m_bal = lev.margin_balance_cad + extra_m
        new_m_util = (new_m_bal / lev.margin_limit_cad) if lev.margin_limit_cad else 0.0
        new_m_mo = new_m_bal * (m_rate / 100.0) / 12.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("New balance", fmt_cad(new_m_bal))
        c2.metric("New util", fmt_pct(new_m_util))
        denom = port.portfolio_cad - new_h_drawn - new_m_bal
        new_ratio = (port.portfolio_cad / denom) if denom > 0 else 0.0
        c3.metric("New ratio", fmt_ratio(new_ratio), _zone_label(new_ratio))
        c4.metric("New monthly interest", fmt_cad(new_m_mo))

    # ========================= HELOC tab =========================
    with tab_heloc:
        st.markdown("#### Settings")
        c1, c2, c3 = st.columns(3)
        h_drawn = c1.number_input(
            "Drawn ($CAD)", min_value=0.0,
            value=float(lev.heloc_drawn_cad), step=500.0, format="%.2f",
            key="lev_h_drawn",
        )
        h_limit = c2.number_input(
            "Limit ($CAD)", min_value=0.0,
            value=float(lev.heloc_limit_cad), step=1000.0, format="%.2f",
            key="lev_h_limit",
        )
        h_rate = c3.number_input(
            "Rate (% annual)", min_value=0.0, max_value=30.0,
            value=float(_heloc_rate(conn)), step=0.05, format="%.2f",
            key="lev_h_rate",
        )
        if st.button("Save", key="lev_h_save"):
            _set_heloc(conn, h_limit, h_rate)
            _reset_heloc_balance(conn, h_drawn)
            st.success("Saved.")
            st.rerun()

        st.markdown("#### Utilization")
        util = (h_drawn / h_limit) if h_limit > 0 else 0.0
        st.progress(min(util, 1.0),
                    text=f"{util * 100:.1f}% · {fmt_cad(h_drawn)} of {fmt_cad(h_limit)}")

        st.markdown("#### Entries")
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

    # ========================= Margin tab =========================
    with tab_margin:
        m = conn.execute("SELECT * FROM margin_account WHERE id = 1").fetchone()

        st.markdown("#### Settings")
        c1, c2, c3 = st.columns(3)
        m_bal = c1.number_input(
            "Drawn ($CAD)", min_value=0.0,
            value=float(m["balance_cad"] or 0), step=500.0, format="%.2f",
            key="lev_m_bal",
        )
        m_limit = c2.number_input(
            "Limit ($CAD)", min_value=0.0,
            value=float(m["limit_cad"] or 0), step=1000.0, format="%.2f",
            key="lev_m_limit",
        )
        m_rate = c3.number_input(
            "Rate (% annual)", min_value=0.0, max_value=30.0,
            value=float(m["rate_pct"] or 0), step=0.05, format="%.2f",
            key="lev_m_rate",
        )
        if st.button("Save", key="lev_m_save"):
            with conn:
                conn.execute(
                    "UPDATE margin_account SET balance_cad = ?, limit_cad = ?, rate_pct = ? WHERE id = 1",
                    (m_bal, m_limit, m_rate),
                )
            st.success("Saved.")
            st.rerun()

        st.markdown("#### Utilization")
        m_util = (m_bal / m_limit) if m_limit > 0 else 0.0
        st.progress(min(m_util, 1.0),
                    text=f"{m_util * 100:.1f}% · {fmt_cad(m_bal)} of {fmt_cad(m_limit)}")

        warn_thresh = float(m["warn_buffer_pct"] or 50) / 100.0
        if lev.margin_buffer_pct is not None and lev.margin_buffer_pct < warn_thresh and m_bal > 0:
            st.error(
                f"⚠ Buffer {lev.margin_buffer_pct*100:.1f}% below "
                f"warning threshold {warn_thresh*100:.0f}%"
            )


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
