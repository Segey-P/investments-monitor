"""V2 'Dark Command Strip' palette — applied via Streamlit CSS injection."""
import streamlit as st
from typing import Optional

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

# DB enum value → user-facing label.
ACCOUNT_LABELS = {"Unreg": "Non-Reg"}


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
          .kpi-sub a {{ color: var(--text-dim); border-bottom: 1px dotted #4b5563; text-decoration: none; }}
          .kpi-sub a:hover {{ color: var(--text); border-bottom-color: var(--text-dim); }}
          .gain {{ color: var(--green); }}
          .loss {{ color: var(--red); }}
          .warn {{ color: var(--amber); }}
          .badge {{
            display: inline-block; padding: 2px 6px; border-radius: 3px;
            font-size: 10px; font-weight: 600; letter-spacing: 0.04em;
            font-family: "DM Mono", monospace;
          }}
          .badge-rrsp   {{ background: {PALETTE['rrsp']}33;   color: {PALETTE['rrsp']}; }}
          .badge-tfsa   {{ background: {PALETTE['tfsa']}33;   color: {PALETTE['tfsa']}; }}
          .badge-unreg  {{ background: {PALETTE['unreg']}33;  color: {PALETTE['unreg']}; }}
          .badge-crypto {{ background: {PALETTE['crypto']}33; color: {PALETTE['crypto']}; }}
          .ticker-link {{ color: inherit; text-decoration: none; border-bottom: 1px dotted #4b5563; }}
          .ticker-link:hover {{ color: var(--blue); border-bottom-color: var(--blue); }}
          .mono {{ font-family: "DM Mono", ui-monospace, monospace; }}
          [data-testid="stDataFrame"] {{ background: var(--bg-panel); }}
          .stTabs [data-baseweb="tab-list"] {{ background: var(--bg-panel); border-bottom: 1px solid var(--border); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def account_label(account_type: str) -> str:
    return ACCOUNT_LABELS.get(account_type, account_type)


def account_badge(account_type: str) -> str:
    label = account_label(account_type).upper()
    cls = {"RRSP": "badge-rrsp", "TFSA": "badge-tfsa",
           "Unreg": "badge-unreg", "Crypto": "badge-crypto"}.get(account_type, "")
    return f'<span class="badge {cls}">{label}</span>'


def yahoo_link(display: str, yahoo_ticker: Optional[str] = None) -> str:
    """Anchor to Yahoo Finance. `display` is shown text; `yahoo_ticker` overrides URL symbol."""
    href = f"https://finance.yahoo.com/quote/{yahoo_ticker or display}"
    return (f'<a href="{href}" target="_blank" rel="noopener noreferrer" '
            f'class="ticker-link mono">{display}</a>')


def kpi_tile(label: str, value: str, sub: str = "", tone: str = "") -> str:
    tone_class = {"gain": "gain", "loss": "loss", "warn": "warn"}.get(tone, "")
    return (
        f'<div class="kpi-tile">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {tone_class}">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>'
    )


def fmt_cad(x: Optional[float]) -> str:
    if x is None:
        return "—"
    decimals = 2 if abs(x) < 1000 else 0
    return f"${x:,.{decimals}f}"


def fmt_pct(x: Optional[float], digits: int = 1) -> str:
    if x is None:
        return "—"
    return f"{x * 100:.{digits}f}%"


def fmt_ratio(x: Optional[float]) -> str:
    if x is None or x == 0:
        return "—"
    return f"{x:.2f}×"


def fmt_change_pct(price: Optional[float], prev: Optional[float]) -> str:
    """Day-change % cell HTML — arrow + green/red, mono."""
    if price is None or not prev:
        return '<span class="mono" style="color:#6b7280;">—</span>'
    pct = (price / prev - 1.0) * 100.0
    color = PALETTE["green"] if pct >= 0 else PALETTE["red"]
    arrow = "▲" if pct >= 0 else "▼"
    return f'<span class="mono" style="color:{color};">{arrow} {abs(pct):.2f}%</span>'


def leverage_disclaimer(ratio: float) -> str:
    """Empty when safe; copy when caution / high."""
    if ratio is None or ratio <= 0 or ratio < 1.5:
        return ""
    if ratio < 2.0:
        return '<span class="warn">⚠ Caution zone (1.5–2×)</span>'
    return '<span class="loss">⚠ High leverage (≥2×)</span>'
