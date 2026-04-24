from __future__ import annotations

import pandas as pd
import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import fmt_cad, kpi_tile


def render(conn) -> None:
    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)
    nw = calcs.net_worth(conn, port.portfolio_cad)

    cash_bal = float(nw.cash_cad)
    heloc_drawn = float(nw.heloc_drawn_cad)
    margin_drawn = float(nw.margin_balance_cad)

    manual_assets = conn.execute(
        "SELECT id, name, description, amount_cad FROM manual_assets ORDER BY name"
    ).fetchall()
    manual_liabs = conn.execute(
        "SELECT id, name, description, amount_cad FROM manual_liabilities ORDER BY name"
    ).fetchall()

    total_manual_assets = sum(float(a["amount_cad"]) for a in manual_assets)
    total_manual_liabs = sum(float(l["amount_cad"]) for l in manual_liabs)

    total_assets = nw.portfolio_cad + cash_bal + total_manual_assets
    total_liabs = heloc_drawn + margin_drawn + total_manual_liabs
    net_w = total_assets - total_liabs
    dte = (total_liabs / net_w) if net_w > 0 else 0.0

    st.markdown("### Net Worth Ledger")

    tiles = [
        kpi_tile("Net Worth",      fmt_cad(net_w)),
        kpi_tile("Total Assets",   fmt_cad(total_assets)),
        kpi_tile("Total Liabs",    fmt_cad(total_liabs)),
        kpi_tile("Debt-to-Equity", f"{dte:.2f}",
                 "Low <0.5 · Caution 0.5–1 · High 1+"),
    ]
    cols = st.columns(4)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### Ledger")
        rows = [
            ("Asset", "Portfolio (auto)", nw.portfolio_cad),
            ("Asset", "Cash", cash_bal),
        ] + [
            ("Asset", a["name"], float(a["amount_cad"])) for a in manual_assets
        ] + [
            ("Liability", "HELOC", heloc_drawn),
            ("Liability", "Margin", margin_drawn),
        ] + [
            ("Liability", l["name"], float(l["amount_cad"])) for l in manual_liabs
        ]
        df = pd.DataFrame([
            {"Type": t, "Item": item, "CAD": val} for t, item, val in rows
        ])
        st.dataframe(
            df,
            hide_index=True,
            width="stretch",
            column_config={"CAD": st.column_config.NumberColumn(format="$%.0f")},
        )

        with st.expander("Add / Edit / Remove"):
            st.markdown("**Manage manual assets and liabilities**")

            with st.container():
                st.subheader("Assets", divider=True)
                for asset in manual_assets:
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.text_input("Name", value=asset["name"], disabled=True, key=f"asset_name_{asset['id']}")
                    c2.number_input("Amount ($CAD)", value=float(asset["amount_cad"]), step=1.0, format="%.2f", key=f"asset_amt_{asset['id']}")
                    c3.text_input("Desc", value=asset["description"] or "", key=f"asset_desc_{asset['id']}")
                    if c4.button("Remove", key=f"asset_remove_{asset['id']}"):
                        with conn:
                            conn.execute("DELETE FROM manual_assets WHERE id = ?", (asset['id'],))
                        st.rerun()

                st.text("Add new asset:")
                a_name = st.text_input("Asset name", key="new_asset_name", placeholder="e.g., Cottage, Car")
                a_desc = st.text_input("Description", key="new_asset_desc", placeholder="e.g., Net value")
                a_amt = st.number_input("Amount ($CAD)", min_value=0.0, step=1.0, format="%.2f", key="new_asset_amt")
                if st.button("Add asset", key="add_asset_btn"):
                    if a_name.strip():
                        with conn:
                            conn.execute(
                                "INSERT INTO manual_assets (name, description, amount_cad) VALUES (?, ?, ?)",
                                (a_name.strip(), a_desc.strip() or None, a_amt),
                            )
                        st.success(f"Added {a_name}.")
                        st.rerun()

            with st.container():
                st.subheader("Liabilities", divider=True)
                for liab in manual_liabs:
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.text_input("Name", value=liab["name"], disabled=True, key=f"liab_name_{liab['id']}")
                    c2.number_input("Amount ($CAD)", value=float(liab["amount_cad"]), step=1.0, format="%.2f", key=f"liab_amt_{liab['id']}")
                    c3.text_input("Desc", value=liab["description"] or "", key=f"liab_desc_{liab['id']}")
                    if c4.button("Remove", key=f"liab_remove_{liab['id']}"):
                        with conn:
                            conn.execute("DELETE FROM manual_liabilities WHERE id = ?", (liab['id'],))
                        st.rerun()

                st.text("Add new liability:")
                l_name = st.text_input("Liability name", key="new_liab_name", placeholder="e.g., Car loan, Student loan")
                l_desc = st.text_input("Description", key="new_liab_desc", placeholder="e.g., Monthly payment info")
                l_amt = st.number_input("Amount ($CAD)", min_value=0.0, step=1.0, format="%.2f", key="new_liab_amt")
                if st.button("Add liability", key="add_liab_btn"):
                    if l_name.strip():
                        with conn:
                            conn.execute(
                                "INSERT INTO manual_liabilities (name, description, amount_cad) VALUES (?, ?, ?)",
                                (l_name.strip(), l_desc.strip() or None, l_amt),
                            )
                        st.success(f"Added {l_name}.")
                        st.rerun()

    with right:
        st.markdown("#### Assets vs Liabilities")
        chart_df = pd.DataFrame(
            {"Side": ["Assets", "Liabilities"], "CAD": [total_assets, total_liabs]}
        ).set_index("Side")
        st.bar_chart(chart_df, height=200)

        st.markdown("#### D/E Gauge")
        gauge_zones = [
            ("Low", 0.5, "#22c55e"),
            ("Caution", 1.0, "#eab308"),
            ("High", float("inf"), "#ef4444"),
        ]
        zone_name = "Low"
        for name, threshold, _ in gauge_zones:
            if dte >= threshold:
                zone_name = name
        st.metric("D/E Zone", zone_name, f"{dte:.2f}")
