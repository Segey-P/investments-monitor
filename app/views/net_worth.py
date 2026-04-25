from __future__ import annotations

import streamlit as st

from app import calcs
from app.fx import get_usdcad
from app.theme import PALETTE, fmt_cad, kpi_tile


def render(conn) -> None:
    fx = get_usdcad(conn)
    hs = calcs.load_holdings(conn)
    port = calcs.summarize(hs, fx.rate)

    # Load property and mortgage from DB
    prop_row = conn.execute("SELECT value_cad, as_of FROM property WHERE id=1").fetchone()
    mort_row = conn.execute("SELECT balance_cad, rate_pct, renewal_date FROM mortgage WHERE id=1").fetchone()
    cash_row = conn.execute("SELECT balance_cad FROM cash_aggregate WHERE id=1").fetchone()

    # Initialize session state for editable values
    if "nw_prop_val" not in st.session_state:
        st.session_state.nw_prop_val = float(prop_row["value_cad"] or 0)
    if "nw_mort_bal" not in st.session_state:
        st.session_state.nw_mort_bal = float(mort_row["balance_cad"] or 0)
    if "nw_cash" not in st.session_state:
        st.session_state.nw_cash = float(cash_row["balance_cad"] or 0)

    nw = calcs.net_worth(conn, port.portfolio_cad)
    heloc_drawn = float(nw.heloc_drawn_cad)
    margin_drawn = float(nw.margin_balance_cad)

    # Recalculate with session state values
    total_assets = port.portfolio_cad + st.session_state.nw_cash + st.session_state.nw_prop_val
    total_liabs = st.session_state.nw_mort_bal + heloc_drawn + margin_drawn
    net_w = total_assets - total_liabs
    dte = (total_liabs / net_w) if net_w > 0 else 0.0
    ltv = (st.session_state.nw_mort_bal / st.session_state.nw_prop_val * 100) if st.session_state.nw_prop_val > 0 else 0.0

    st.markdown("### Net Worth")

    # KPI tiles
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

    left, right = st.columns([380, 1], gap="medium")

    with left:
        # Ledger panel
        st.markdown("#### Asset / Liability Ledger")

        privacy_badge = ""
        if "hide_values" in st.session_state and st.session_state.hide_values:
            privacy_badge = '<span style="color:#f59e0b; font-size:10px; float:right;">🙈 Values hidden</span>'

        st.markdown(f"""
        <div style="background:{PALETTE['bgPanel']};border:1px solid {PALETTE['border']};border-radius:4px;overflow:hidden;">
            <div style="padding:9px 14px;border-bottom:1px solid {PALETTE['border']};display:flex;justify-content:space-between;align-items:center;">
                <span style="font-family:'DM Sans',sans-serif;font-size:11px;font-weight:600;color:{PALETTE['textDim']};letter-spacing:0.8px;text-transform:uppercase;">Asset / Liability Ledger</span>
                {privacy_badge}
            </div>
        """, unsafe_allow_html=True)

        # Assets section
        st.markdown(f"""
        <div style="padding:8px 14px 4px;font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['green']};letter-spacing:1px;border-bottom:1px solid {PALETTE['border']};text-transform:uppercase;">ASSETS</div>
        """, unsafe_allow_html=True)

        # Portfolio (auto, read-only)
        col1, col2 = st.columns([0.7, 0.3])
        col1.markdown(f"""
        <div style="padding:9px 14px;border-bottom:1px solid {PALETTE['border']};">
            <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:{PALETTE['text']};">Portfolio (auto)</div>
            <div style="font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['textDim']};">RRSP+TFSA+Unreg+Crypto</div>
        </div>
        """, unsafe_allow_html=True)
        col2.markdown(f"""
        <div style="padding:9px 14px;border-bottom:1px solid {PALETTE['border']};text-align:right;font-family:'DM Mono',monospace;font-size:13px;color:{PALETTE['text']};{'filter:blur(4px);' if st.session_state.get('hide_values', False) else ''}">{fmt_cad(port.portfolio_cad)}</div>
        """, unsafe_allow_html=True)

        # Cash (inline editable)
        col1, col2 = st.columns([0.7, 0.3])
        col1.markdown(f"""
        <div style="padding:9px 14px;border-bottom:1px solid {PALETTE['border']};">
            <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:{PALETTE['text']};">Cash / HISA</div>
            <div style="font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['textDim']};">manual · click to edit</div>
        </div>
        """, unsafe_allow_html=True)
        with col2:
            st.session_state.nw_cash = st.number_input(
                "Cash value", value=st.session_state.nw_cash, step=1000.0,
                format="%.2f", label_visibility="collapsed", key="nw_cash_input"
            )

        # Property (slider + input)
        st.markdown(f"""
        <div style="padding:10px 14px;border-bottom:1px solid {PALETTE['border']};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:{PALETTE['text']};">Primary residence</div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['textDim']};">manual estimate</div>
                </div>
                <span style="font-family:'DM Mono',monospace;font-size:13px;color:{PALETTE['green'] if not st.session_state.get('hide_values') else PALETTE['textDim']};{'filter:blur(4px);' if st.session_state.get('hide_values', False) else ''}">{fmt_cad(st.session_state.nw_prop_val)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.get("hide_values", False):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.nw_prop_val = st.slider(
                    "Property value (slider)", min_value=0, max_value=3_000_000,
                    value=int(st.session_state.nw_prop_val), step=5000, key="nw_prop_slider"
                )
            with col2:
                st.session_state.nw_prop_val = st.number_input(
                    "Property value (type)", value=st.session_state.nw_prop_val, step=5000.0,
                    format="%.0f", label_visibility="collapsed", key="nw_prop_input"
                )

        # Assets total
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:8px 14px;border-bottom:1px solid {PALETTE['borderMid']};font-family:'DM Mono',monospace;font-size:13px;font-weight:700;color:{PALETTE['green']};">
            <span style="font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;">Total assets</span>
            <span style="{'filter:blur(4px);' if st.session_state.get('hide_values', False) else ''}">{fmt_cad(total_assets)}</span>
        </div>
        """, unsafe_allow_html=True)

        # Liabilities section
        st.markdown(f"""
        <div style="padding:8px 14px 4px;font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['red']};letter-spacing:1px;border-bottom:1px solid {PALETTE['border']};text-transform:uppercase;">LIABILITIES</div>
        """, unsafe_allow_html=True)

        # Mortgage (slider + input)
        st.markdown(f"""
        <div style="padding:10px 14px;border-bottom:1px solid {PALETTE['border']};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:{PALETTE['text']};">Mortgage balance</div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['textDim']};">{mort_row['rate_pct']:.2f}% fixed · renews {mort_row['renewal_date']}</div>
                </div>
                <span style="font-family:'DM Mono',monospace;font-size:13px;color:{PALETTE['red'] if not st.session_state.get('hide_values') else PALETTE['textDim']};{'filter:blur(4px);' if st.session_state.get('hide_values', False) else ''}">({fmt_cad(st.session_state.nw_mort_bal)})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.get("hide_values", False):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.nw_mort_bal = st.slider(
                    "Mortgage balance (slider)", min_value=0, max_value=1_500_000,
                    value=int(st.session_state.nw_mort_bal), step=1000, key="nw_mort_slider"
                )
            with col2:
                st.session_state.nw_mort_bal = st.number_input(
                    "Mortgage balance (type)", value=st.session_state.nw_mort_bal, step=1000.0,
                    format="%.0f", label_visibility="collapsed", key="nw_mort_input"
                )

        # HELOC + Margin (auto)
        for label, val in [("HELOC (auto)", heloc_drawn), ("Margin (auto)", margin_drawn)]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:9px 14px;border-bottom:1px solid {PALETTE['border']};">
                <div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:{PALETTE['text']}">{label}</div>
                    <div style="font-family:'DM Sans',sans-serif;font-size:10px;color:{PALETTE['textDim']}">{'from Leverage screen' if 'HELOC' in label else 'Questrade unregistered'}</div>
                </div>
                <span style="font-family:'DM Mono',monospace;font-size:13px;color:{PALETTE['red']};{'filter:blur(4px);' if st.session_state.get('hide_values', False) else ''}">({fmt_cad(val)})</span>
            </div>
            """, unsafe_allow_html=True)

        # Liabilities total
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:8px 14px;border-bottom:1px solid {PALETTE['borderMid']};font-family:'DM Mono',monospace;font-size:13px;font-weight:700;color:{PALETTE['red']};">
            <span style="font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;">Total liabilities</span>
            <span style="{'filter:blur(4px);' if st.session_state.get('hide_values', False) else ''}">({fmt_cad(total_liabs)})</span>
        </div>
        """, unsafe_allow_html=True)

        # Net worth
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:12px 14px;font-family:'DM Mono',monospace;font-size:16px;font-weight:700;color:{PALETTE['blue']};{'filter:blur(5px);' if st.session_state.get('hide_values', False) else ''}">
            <span style="font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;">Net worth</span>
            <span>{fmt_cad(net_w)}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Save button
        if st.button("💾 Save changes", key="nw_save"):
            with conn:
                conn.execute("UPDATE property SET value_cad = ? WHERE id = 1", (st.session_state.nw_prop_val,))
                conn.execute("UPDATE mortgage SET balance_cad = ? WHERE id = 1", (st.session_state.nw_mort_bal,))
                conn.execute("UPDATE cash_aggregate SET balance_cad = ? WHERE id = 1", (st.session_state.nw_cash,))
            st.success("✓ Net worth updated")
            st.rerun()
