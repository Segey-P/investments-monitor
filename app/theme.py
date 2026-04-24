"""V2 'Dark Command Strip' palette — applied via Streamlit CSS injection."""
import streamlit as st

PALETTE = {
    "bg":        "#0f0f0f",
    "bgPanel":   "#161616",
    "bgRaised":  "#1e1e1e",
    "border":    "#2a2a2a",
    "text":      "#f0f0f0",
    "textDim":   "#9ca3af",
    "blue":      "#3b82f6",
    "green":     "#22c55e",
    "red":       "#ef4444",
    "amber":     "#f59e0b",
    # Account tags
    "rrsp":      "#a78bfa",
    "tfsa":      "#14b8a6",
    "unreg":     "#f97316",
    "crypto":    "#8b5cf6",
}


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
          :root {{
            --bg: {PALETTE['bg']}; --bg-panel: {PALETTE['bgPanel']};
            --bg-raised: {PALETTE['bgRaised']}; --border: {PALETTE['border']};
            --text: {PALETTE['text']}; --text-dim: {PALETTE['textDim']};
            --green: {PALETTE['green']}; --red: {PALETTE['red']};
            --blue: {PALETTE['blue']}; --amber: {PALETTE['amber']};
          }}
          html, body, [data-testid="stAppViewContainer"] {{
            background: var(--bg); color: var(--text);
            font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }}
          [data-testid="stHeader"] {{ background: var(--bg); }}
          .kpi-tile {{
            background: var(--bg-panel); border: 1px solid var(--border);
            border-radius: 6px; padding: 12px 14px; height: 100%;
          }}
          .kpi-label {{ color: var(--text-dim); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }}
          .kpi-value {{ font-family: "DM Mono", ui-monospace, monospace; font-size: 22px; font-weight: 500; margin-top: 4px; }}
          .kpi-sub   {{ color: var(--text-dim); font-size: 11px; margin-top: 2px; font-family: "DM Mono", monospace; }}
          .gain {{ color: var(--green); }}
          .loss {{ color: var(--red); }}
          .badge {{
            display: inline-block; padding: 2px 6px; border-radius: 3px;
            font-size: 10px; font-weight: 600; letter-spacing: 0.04em;
            font-family: "DM Mono", monospace;
          }}
          .badge-rrsp   {{ background: {PALETTE['rrsp']}33;   color: {PALETTE['rrsp']}; }}
          .badge-tfsa   {{ background: {PALETTE['tfsa']}33;   color: {PALETTE['tfsa']}; }}
          .badge-unreg  {{ background: {PALETTE['unreg']}33;  color: {PALETTE['unreg']}; }}
          .badge-crypto {{ background: {PALETTE['crypto']}33; color: {PALETTE['crypto']}; }}
          .mono {{ font-family: "DM Mono", ui-monospace, monospace; }}
          [data-testid="stDataFrame"] {{ background: var(--bg-panel); }}
          .stTabs [data-baseweb="tab-list"] {{ background: var(--bg-panel); border-bottom: 1px solid var(--border); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def account_badge(account_type: str) -> str:
    label = {"Unreg": "UNREG"}.get(account_type, account_type.upper())
    cls = {"RRSP": "badge-rrsp", "TFSA": "badge-tfsa",
           "Unreg": "badge-unreg", "Crypto": "badge-crypto"}.get(account_type, "")
    return f'<span class="badge {cls}">{label}</span>'


def kpi_tile(label: str, value: str, sub: str = "", tone: str = "") -> str:
    tone_class = {"gain": "gain", "loss": "loss"}.get(tone, "")
    return (
        f'<div class="kpi-tile">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {tone_class}">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>'
    )


def fmt_cad(x: float | None) -> str:
    if x is None:
        return "—"
    return f"${x:,.0f}"


def fmt_pct(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "—"
    return f"{x * 100:.{digits}f}%"


def fmt_ratio(x: float | None) -> str:
    if x is None or x == 0:
        return "—"
    return f"{x:.2f}×"
