from __future__ import annotations

import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import PALETTE, fmt_cad, kpi_tile


def _ledger_row(label: str, sub: str, value_html: str) -> str:
    return (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:9px 14px;border-bottom:1px solid {PALETTE["border"]};">'
        f'<div>'
        f'<div style="font-family:\'DM Sans\',sans-serif;font-size:12px;color:{PALETTE["text"]};">{label}</div>'
        f'<div style="font-family:\'DM Sans\',sans-serif;font-size:10px;color:{PALETTE["textDim"]};">{sub}</div>'
        f'</div>'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:13px;">{value_html}</span>'
        f'</div>'
    )


def render(conn) -> None:
    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)

    prop_row = conn.execute("SELECT value_cad, as_of FROM property WHERE id=1").fetchone()
    mort_row = conn.execute("SELECT balance_cad, rate_pct, renewal_date FROM mortgage WHERE id=1").fetchone()
    cash_row = conn.execute("SELECT balance_cad FROM cash_aggregate WHERE id=1").fetchone()

    manual_assets_rows = conn.execute(
        "SELECT id, name, amount_cad FROM manual_assets ORDER BY id"
    ).fetchall()
    manual_liabs_rows = conn.execute(
        "SELECT id, name, amount_cad FROM manual_liabilities ORDER BY id"
    ).fetchall()
    manual_assets_total = sum(float(r["amount_cad"] or 0) for r in manual_assets_rows)
    manual_liabs_total = sum(float(r["amount_cad"] or 0) for r in manual_liabs_rows)

    if "nw_prop_val" not in st.session_state:
        st.session_state.nw_prop_val = float(prop_row["value_cad"] or 0)
    if "nw_mort_bal" not in st.session_state:
        st.session_state.nw_mort_bal = float(mort_row["balance_cad"] or 0)
    if "nw_cash" not in st.session_state:
        st.session_state.nw_cash = float(cash_row["balance_cad"] or 0)

    nw = calcs.net_worth(conn, port.portfolio_cad)
    heloc_drawn = float(nw.heloc_drawn_cad)
    margin_drawn = float(nw.margin_balance_cad)

    total_assets = (
        port.portfolio_cad
        + st.session_state.nw_cash
        + st.session_state.nw_prop_val
        + manual_assets_total
    )
    total_liabs = (
        st.session_state.nw_mort_bal
        + heloc_drawn
        + margin_drawn
        + manual_liabs_total
    )
    net_w = total_assets - total_liabs
    dte = (total_liabs / net_w) if net_w > 0 else 0.0

    st.markdown("### Net Worth")

    tiles = [
        kpi_tile("Net Worth", fmt_cad(net_w), "Assets − liabilities"),
        kpi_tile("Total assets", fmt_cad(total_assets), "Portfolio + property + cash"),
        kpi_tile("Total liabilities", fmt_cad(total_liabs), "Mortgage + HELOC + margin"),
        kpi_tile("Debt-to-equity", f"{dte:.2f}×", "Liabilities ÷ equity"),
    ]
    cols = st.columns(4)
    for col, html in zip(cols, tiles):
        col.markdown(html, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    hide = st.session_state.get("hide_values", False)
    blur = "filter:blur(4px);" if hide else ""

    privacy_badge = (
        '<span style="color:#f59e0b;font-size:10px;">🙈 Values hidden</span>'
        if hide else ""
    )

    st.markdown(
        f'<div style="padding:9px 14px;border-bottom:1px solid {PALETTE["border"]};'
        f'display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-family:\'DM Sans\',sans-serif;font-size:11px;font-weight:600;'
        f'color:{PALETTE["textDim"]};letter-spacing:0.8px;text-transform:uppercase;">'
        f'Asset / Liability Ledger</span>{privacy_badge}</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        # ── ASSETS ──────────────────────────────────────────────────
        st.markdown(
            f'<div style="padding:6px 14px 4px;font-size:10px;color:{PALETTE["green"]};'
            f'letter-spacing:1px;text-transform:uppercase;">ASSETS</div>',
            unsafe_allow_html=True,
        )

        # Portfolio (auto, read-only)
        col1, col2 = st.columns([0.7, 0.3])
        col1.markdown(
            f'<div style="padding:6px 14px;">'
            f'<div style="font-size:12px;color:{PALETTE["text"]};">Portfolio (auto)</div>'
            f'<div style="font-size:10px;color:{PALETTE["textDim"]};">RRSP+TFSA+Non-Reg+Crypto</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col2.markdown(
            f'<div style="padding:6px 14px;text-align:right;font-family:\'DM Mono\',monospace;'
            f'font-size:13px;color:{PALETTE["text"]};{blur}">{fmt_cad(port.portfolio_cad)}</div>',
            unsafe_allow_html=True,
        )

        # Cash (editable)
        col1, col2 = st.columns([0.7, 0.3])
        col1.markdown(
            f'<div style="padding:6px 14px;">'
            f'<div style="font-size:12px;color:{PALETTE["text"]};">Cash / HISA</div>'
            f'<div style="font-size:10px;color:{PALETTE["textDim"]};">manual · editable</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with col2:
            st.session_state.nw_cash = st.number_input(
                "Cash value", value=st.session_state.nw_cash, step=1000.0,
                format="%.2f", label_visibility="collapsed", key="nw_cash_input",
            )

        # Property (slider + input)
        st.markdown(
            f'<div style="padding:8px 14px 4px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<div style="font-size:12px;color:{PALETTE["text"]};">Primary residence</div>'
            f'<div style="font-size:10px;color:{PALETTE["textDim"]};">manual estimate · editable</div>'
            f'</div>'
            f'<span style="font-family:\'DM Mono\',monospace;font-size:13px;'
            f'color:{PALETTE["green"]};{blur}">{fmt_cad(st.session_state.nw_prop_val)}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        if not hide:
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.nw_prop_val = float(st.slider(
                    "Property value (slider)", min_value=0, max_value=3_000_000,
                    value=int(st.session_state.nw_prop_val), step=5000, key="nw_prop_slider",
                ))
            with col2:
                st.session_state.nw_prop_val = st.number_input(
                    "Property value (type)", value=float(st.session_state.nw_prop_val),
                    step=5000.0, format="%.0f", label_visibility="collapsed", key="nw_prop_input",
                )

        # Manual other assets
        for r in manual_assets_rows:
            col1, col2 = st.columns([0.7, 0.3])
            col1.markdown(
                f'<div style="padding:6px 14px;">'
                f'<div style="font-size:12px;color:{PALETTE["text"]};">{r["name"]}</div>'
                f'<div style="font-size:10px;color:{PALETTE["textDim"]};">other asset · manual</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            col2.markdown(
                f'<div style="padding:6px 14px;text-align:right;font-family:\'DM Mono\',monospace;'
                f'font-size:13px;color:{PALETTE["text"]};{blur}">{fmt_cad(float(r["amount_cad"]))}</div>',
                unsafe_allow_html=True,
            )

        # Assets total
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:8px 14px;'
            f'font-family:\'DM Mono\',monospace;font-size:13px;font-weight:700;color:{PALETTE["green"]};">'
            f'<span style="font-family:\'DM Sans\',sans-serif;font-size:13px;font-weight:600;">'
            f'Total assets</span>'
            f'<span style="{blur}">{fmt_cad(total_assets)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # ── LIABILITIES ─────────────────────────────────────────────
        st.markdown(
            f'<div style="padding:6px 14px 4px;font-size:10px;color:{PALETTE["red"]};'
            f'letter-spacing:1px;text-transform:uppercase;">LIABILITIES</div>',
            unsafe_allow_html=True,
        )

        # Mortgage (slider + input)
        mort_sub = ""
        if mort_row["rate_pct"] and mort_row["renewal_date"]:
            mort_sub = f'{mort_row["rate_pct"]:.2f}% fixed · renews {mort_row["renewal_date"]}'
        st.markdown(
            f'<div style="padding:8px 14px 4px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<div style="font-size:12px;color:{PALETTE["text"]};">Mortgage balance</div>'
            f'<div style="font-size:10px;color:{PALETTE["textDim"]};">{mort_sub or "manual · editable"}</div>'
            f'</div>'
            f'<span style="font-family:\'DM Mono\',monospace;font-size:13px;'
            f'color:{PALETTE["red"]};{blur}">({fmt_cad(st.session_state.nw_mort_bal)})</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        if not hide:
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.nw_mort_bal = float(st.slider(
                    "Mortgage balance (slider)", min_value=0, max_value=1_500_000,
                    value=int(st.session_state.nw_mort_bal), step=1000, key="nw_mort_slider",
                ))
            with col2:
                st.session_state.nw_mort_bal = st.number_input(
                    "Mortgage balance (type)", value=float(st.session_state.nw_mort_bal),
                    step=1000.0, format="%.0f", label_visibility="collapsed", key="nw_mort_input",
                )

        # Manual other liabilities
        for r in manual_liabs_rows:
            col1, col2 = st.columns([0.7, 0.3])
            col1.markdown(
                f'<div style="padding:6px 14px;">'
                f'<div style="font-size:12px;color:{PALETTE["text"]};">{r["name"]}</div>'
                f'<div style="font-size:10px;color:{PALETTE["textDim"]};">other liability · manual</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            col2.markdown(
                f'<div style="padding:6px 14px;text-align:right;font-family:\'DM Mono\',monospace;'
                f'font-size:13px;color:{PALETTE["red"]};{blur}">({fmt_cad(float(r["amount_cad"]))})</div>',
                unsafe_allow_html=True,
            )

        # HELOC + Margin (auto)
        for label, val, sub in [
            ("HELOC (auto)", heloc_drawn, "from Leverage screen"),
            ("Margin (auto)", margin_drawn, "Questrade unregistered"),
        ]:
            col1, col2 = st.columns([0.7, 0.3])
            col1.markdown(
                f'<div style="padding:6px 14px;">'
                f'<div style="font-size:12px;color:{PALETTE["text"]};">{label}</div>'
                f'<div style="font-size:10px;color:{PALETTE["textDim"]};">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            col2.markdown(
                f'<div style="padding:6px 14px;text-align:right;font-family:\'DM Mono\',monospace;'
                f'font-size:13px;color:{PALETTE["red"]};{blur}">({fmt_cad(val)})</div>',
                unsafe_allow_html=True,
            )

        # Liabilities total
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:8px 14px;'
            f'font-family:\'DM Mono\',monospace;font-size:13px;font-weight:700;color:{PALETTE["red"]};">'
            f'<span style="font-family:\'DM Sans\',sans-serif;font-size:13px;font-weight:600;">'
            f'Total liabilities</span>'
            f'<span style="{blur}">({fmt_cad(total_liabs)})</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # Net worth
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:10px 14px;'
            f'font-family:\'DM Mono\',monospace;font-size:16px;font-weight:700;'
            f'color:{PALETTE["blue"]};{blur}">'
            f'<span style="font-family:\'DM Sans\',sans-serif;font-size:14px;font-weight:700;">'
            f'Net worth</span>'
            f'<span>{fmt_cad(net_w)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Save portfolio/property/cash/mortgage
    if st.button("💾 Save changes", key="nw_save"):
        with conn:
            conn.execute("UPDATE property SET value_cad = ? WHERE id = 1", (st.session_state.nw_prop_val,))
            conn.execute("UPDATE mortgage SET balance_cad = ? WHERE id = 1", (st.session_state.nw_mort_bal,))
            conn.execute("UPDATE cash_aggregate SET balance_cad = ? WHERE id = 1", (st.session_state.nw_cash,))
        st.success("✓ Net worth updated")
        st.rerun()

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Manage other assets & liabilities ──────────────────────────
    with st.expander("Manage other assets & liabilities", expanded=False):
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Other Assets**")
            if manual_assets_rows:
                for r in manual_assets_rows:
                    c1, c2, c3 = st.columns([3, 2, 1])
                    new_name = c1.text_input(
                        "Name", value=r["name"], key=f"ma_name_{r['id']}",
                        label_visibility="collapsed",
                    )
                    new_amt = c2.number_input(
                        "Amount", value=float(r["amount_cad"]), step=1000.0,
                        format="%.2f", key=f"ma_amt_{r['id']}",
                        label_visibility="collapsed",
                    )
                    if c3.button("✕", key=f"ma_del_{r['id']}"):
                        with conn:
                            conn.execute("DELETE FROM manual_assets WHERE id = ?", (r["id"],))
                        st.rerun()
                    if new_name != r["name"] or abs(new_amt - float(r["amount_cad"])) > 0.001:
                        if st.button("Save", key=f"ma_save_{r['id']}"):
                            with conn:
                                conn.execute(
                                    "UPDATE manual_assets SET name=?, amount_cad=? WHERE id=?",
                                    (new_name.strip(), new_amt, r["id"]),
                                )
                            st.rerun()
            st.markdown("**Add asset**")
            c1, c2, c3 = st.columns([3, 2, 1])
            add_a_name = c1.text_input("Asset name", key="ma_new_name",
                                       placeholder="e.g. Vehicle", label_visibility="collapsed")
            add_a_amt = c2.number_input("Amount ($CAD)", value=0.0, step=1000.0,
                                        format="%.2f", key="ma_new_amt",
                                        label_visibility="collapsed")
            if c3.button("Add", key="ma_add"):
                if add_a_name.strip():
                    with conn:
                        conn.execute(
                            "INSERT INTO manual_assets (name, amount_cad) VALUES (?, ?)",
                            (add_a_name.strip(), add_a_amt),
                        )
                    st.rerun()

        with col_b:
            st.markdown("**Other Liabilities**")
            if manual_liabs_rows:
                for r in manual_liabs_rows:
                    c1, c2, c3 = st.columns([3, 2, 1])
                    new_name = c1.text_input(
                        "Name", value=r["name"], key=f"ml_name_{r['id']}",
                        label_visibility="collapsed",
                    )
                    new_amt = c2.number_input(
                        "Amount", value=float(r["amount_cad"]), step=1000.0,
                        format="%.2f", key=f"ml_amt_{r['id']}",
                        label_visibility="collapsed",
                    )
                    if c3.button("✕", key=f"ml_del_{r['id']}"):
                        with conn:
                            conn.execute("DELETE FROM manual_liabilities WHERE id = ?", (r["id"],))
                        st.rerun()
                    if new_name != r["name"] or abs(new_amt - float(r["amount_cad"])) > 0.001:
                        if st.button("Save", key=f"ml_save_{r['id']}"):
                            with conn:
                                conn.execute(
                                    "UPDATE manual_liabilities SET name=?, amount_cad=? WHERE id=?",
                                    (new_name.strip(), new_amt, r["id"]),
                                )
                            st.rerun()
            st.markdown("**Add liability**")
            c1, c2, c3 = st.columns([3, 2, 1])
            add_l_name = c1.text_input("Liability name", key="ml_new_name",
                                       placeholder="e.g. Car loan", label_visibility="collapsed")
            add_l_amt = c2.number_input("Amount ($CAD)", value=0.0, step=1000.0,
                                        format="%.2f", key="ml_new_amt",
                                        label_visibility="collapsed")
            if c3.button("Add", key="ml_add"):
                if add_l_name.strip():
                    with conn:
                        conn.execute(
                            "INSERT INTO manual_liabilities (name, amount_cad) VALUES (?, ?)",
                            (add_l_name.strip(), add_l_amt),
                        )
                    st.rerun()
