from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import fmt_cad, fmt_pct, kpi_tile


def _get_setting_float(conn, key: str, default: float = 0.0) -> float:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row or row["value"] is None:
        return default
    try:
        return float(row["value"])
    except (TypeError, ValueError):
        return default


def _put_setting(conn, key: str, value: str) -> None:
    with conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def render(conn) -> None:
    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)
    nw = calcs.net_worth(conn, port.portfolio_cad)

    other_assets = _get_setting_float(conn, "other_assets_cad", 0.0)
    other_debt   = _get_setting_float(conn, "other_debt_cad", 0.0)

    total_assets = nw.total_assets_cad + other_assets
    total_liabs  = nw.total_liabilities_cad + other_debt
    net_w = total_assets - total_liabs
    dte = (total_liabs / net_w) if net_w > 0 else 0.0

    st.markdown("### Net Worth Ledger")

    tiles = [
        kpi_tile("Net Worth",      fmt_cad(net_w)),
        kpi_tile("Total Assets",   fmt_cad(total_assets)),
        kpi_tile("Total Liabs",    fmt_cad(total_liabs)),
        kpi_tile("Debt-to-Equity", f"{dte:.2f}",
                 "Low <0.5 · Caution 0.5–1 · High 1+"),
        kpi_tile("Mortgage LTV",   fmt_pct(nw.mortgage_ltv)),
    ]
    cols = st.columns(5)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### Ledger")
        rows = [
            ("Asset",     "Portfolio (auto)",    nw.portfolio_cad, "auto"),
            ("Asset",     "Cash",                nw.cash_cad,      "cash"),
            ("Asset",     "Other assets",        other_assets,     "other_assets"),
            ("Asset",     "Property",            nw.property_cad,  "property"),
            ("Liability", "Mortgage",            nw.mortgage_cad,  "mortgage"),
            ("Liability", "HELOC",               nw.heloc_drawn_cad, "heloc"),
            ("Liability", "Margin",              nw.margin_balance_cad, "margin"),
            ("Liability", "Other debt",          other_debt,       "other_debt"),
        ]
        df = pd.DataFrame([
            {"Type": t, "Item": item, "CAD": val} for t, item, val, _ in rows
        ])
        st.dataframe(
            df,
            hide_index=True,
            width="stretch",
            column_config={"CAD": st.column_config.NumberColumn(format="$%.0f")},
        )

        with st.expander("Edit manual entries"):
            new_cash = st.number_input(
                "Cash balance (aggregate, $CAD)", min_value=0.0,
                value=float(nw.cash_cad), step=100.0, format="%.2f", key="nw_cash",
            )
            new_other_a = st.number_input(
                "Other assets ($CAD)", min_value=0.0,
                value=float(other_assets), step=100.0, format="%.2f", key="nw_other_a",
            )
            new_other_d = st.number_input(
                "Other debt ($CAD)", min_value=0.0,
                value=float(other_debt), step=100.0, format="%.2f", key="nw_other_d",
            )
            c1, c2 = st.columns([1, 4])
            if c1.button("Save", key="nw_save"):
                with conn:
                    conn.execute(
                        "UPDATE cash_aggregate SET balance_cad = ? WHERE id = 1",
                        (new_cash,),
                    )
                _put_setting(conn, "other_assets_cad", str(new_other_a))
                _put_setting(conn, "other_debt_cad", str(new_other_d))
                st.success("Saved.")
                st.rerun()

    with right:
        st.markdown("#### Assets vs Liabilities")
        chart_df = pd.DataFrame(
            {"Side": ["Assets", "Liabilities"], "CAD": [total_assets, total_liabs]}
        ).set_index("Side")
        st.bar_chart(chart_df, height=200)

        st.markdown("#### Mortgage & Property")
        mort = conn.execute("SELECT * FROM mortgage WHERE id = 1").fetchone()
        prop_equity = nw.property_cad - nw.mortgage_cad
        renewal = mort["renewal_date"]
        if hasattr(renewal, "isoformat"):
            renewal = renewal.isoformat()
        rows = [
            ("Property value", fmt_cad(nw.property_cad)),
            ("Mortgage balance", fmt_cad(nw.mortgage_cad)),
            ("Equity", fmt_cad(prop_equity)),
            ("LTV", fmt_pct(nw.mortgage_ltv)),
            ("Rate", f"{(mort['rate_pct'] or 0):.2f}%"),
            ("Renewal", str(renewal or "—")),
            ("Lender", mort["lender"] or "—"),
        ]
        for label, value in rows:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:4px 0;border-bottom:1px solid #2a2a2a;">'
                f'<span style="color:#9ca3af;">{label}</span>'
                f'<span class="mono">{value}</span></div>',
                unsafe_allow_html=True,
            )
