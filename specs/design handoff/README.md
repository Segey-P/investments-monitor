# Design Handoff: Investments Monitor

## Overview

A personal, self-hosted investment dashboard for a Canadian investor using Questrade (RRSP, TFSA, Unregistered) and a crypto account. It tracks portfolio holdings, leverage (HELOC + margin), net worth, and a watchlist of target-price tickers.

**Stack:** Streamlit · Python 3.12 · SQLite · Tailscale (remote access)  
**Access model:** Fully local — no cloud writes, no external API beyond Questrade + BOC FX rate.

---

## About These Files

The files in `design_files/` are **high-fidelity HTML/React prototypes** — not production code. They show the intended look, layout, and interactions with precision. Your task is to **recreate these designs in Streamlit** using its native components (st.metric, st.dataframe, st.plotly_chart, st.columns, st.slider, st.number_input, etc.) and Streamlit's theming.

Where a specific interaction is not natively possible in Streamlit (e.g. inline editing, animated sliders), use the closest available Streamlit pattern and note the delta in a comment.

Open `Investments Monitor v3.html` in a browser to see the full interactive reference. Every screen is accessible via the top nav tabs.

---

## Design Tokens

### Colors

```python
BG          = "#0f0f0f"   # page background
BG_PANEL    = "#161616"   # card / panel background
BG_RAISED   = "#1e1e1e"   # raised element (table headers, input bg)
BG_HOVER    = "#252525"   # row hover
BORDER      = "#2a2a2a"   # standard border
BORDER_MID  = "#333333"   # slightly heavier border
TEXT        = "#f0f0f0"   # primary text
TEXT_SUB    = "#888888"   # secondary / label text
TEXT_FAINT  = "#444444"   # very faint / placeholder

BLUE        = "#3b82f6"   # primary accent (portfolio, links)
BLUE_DIM    = "#0f1e3d"   # blue background tint
GREEN       = "#22c55e"   # gains, positive values
GREEN_DIM   = "#0d2a18"   # green background tint
RED         = "#ef4444"   # losses, liabilities, danger
RED_DIM     = "#2d1414"   # red background tint
AMBER       = "#f59e0b"   # warnings, watchlist alerts
AMBER_DIM   = "#2d200a"   # amber background tint

# Account badge colors
RRSP_COLOR  = "#a78bfa"   # violet
TFSA_COLOR  = "#14b8a6"   # teal
UNREG_COLOR = "#f97316"   # orange
CRYPTO_COLOR= "#8b5cf6"   # purple
```

### Typography

```
Primary font:  DM Sans (Google Fonts) — labels, nav, body text
Monospace font: DM Mono (Google Fonts) — all numeric values, tickers, code

Font sizes:
  Nav labels:     13px / DM Sans
  Section heads:  11px / DM Sans / weight 600 / uppercase / letter-spacing 0.8px
  KPI value:      20px / DM Mono / weight 700
  Table values:   12–13px / DM Mono
  Labels/meta:    10–11px / DM Sans
  Sub-labels:     10px / DM Sans / color TEXT_SUB
```

### Spacing & Borders

```
Page padding:    20px all sides
Card gap:        12px
Cell padding:    7–9px vertical, 12px horizontal (table cells)
Border radius:   4px (cards/panels), 3px (inputs/buttons), 12px (pill chips)
Border:          1px solid BORDER
Card top-accent: 2px solid <accent color> (KPI cards)
```

---

## Screens

### 1. Login (Lock Screen)

**Purpose:** Password gate before accessing any data.

**Layout:** Centered, single-column, 360px wide card on full viewport.

**Components:**
- Wordmark: `IM` in DM Mono 36px bold, letterSpacing -2px
- Subtitle: `Investments Monitor · personal` — DM Sans 13px TEXT_SUB
- Card (BG_PANEL, 1px BORDER, border-radius 6px, 28/24px padding):
  - Lock icon 🔒 32px centered, opacity 0.3
  - Title: `This data is private` — DM Sans 15px weight 600
  - Body copy: `All holdings, balances and net worth live locally on this machine. Enter your password to unlock.` — DM Sans 12px TEXT_SUB, line-height 1.5
  - Password input: full width, DM Mono 14px, 10/12px padding, BORDER border, RED border on error
  - Error message: `Incorrect password` — DM Sans 11px RED
  - Submit button: `Unlock →` full width, 11px padding, BLUE bg, white text, DM Sans 14px weight 600. Loading state: `Unlocking…` with BG_RAISED bg
- Footer: `Session auto-locks after 15 min of inactivity` — DM Sans 11px TEXT_FAINT, centered

**Behavior:** Any non-empty password unlocks (demo). On real implementation, bcrypt verify against stored hash.

---

### 2. Top Navigation

**Layout:** Fixed 44px bar, full width, z-index 100. BG `#141414`, 1px BORDER bottom.

**Left side:**
- Logo: `IM` — DM Mono 14px bold, marginRight 24px
- Nav tabs: `Cockpit · Holdings · Leverage · Net Worth · Watchlist · Settings`
  - Each tab: 44px height, 0–14px horizontal padding, DM Sans 13px
  - Active: BLUE text, 2px BLUE bottom border, shows one-liner subtitle in 9px TEXT_FAINT below label
  - Inactive: `#666` text, transparent border

**Right side:**
- `Review N changes` button — amber toggle (only relevant to prototype; omit in production)
- **Hide values toggle:** `👁 Hide values` / `🙈 Values hidden`
  - Off state: TEXT `#666`, border `#333`, transparent bg
  - On state: AMBER text, border `#555`, bg `#1a1a1a`
- Last refresh timestamp: DM Mono 10px TEXT_FAINT

**Session banner** (when session near expiry, shown below nav bar, 36px):
- Background AMBER_DIM, border AMBER, full width
- Text: `⚠ Session expires in M:SS · auto-lock enabled`
- Buttons: `Stay signed in` (BLUE), `Dismiss` (neutral)

---

### 3. Cockpit (Dashboard)

**Purpose:** Single-glance portfolio health view.

**Layout:** 1-column CSS grid with 3 rows:
1. KPI strip (4 cards, equal width)
2. 3-column middle (`1fr 1fr 1fr`)
3. Top 15 holdings table (full width)

#### KPI Strip (4 cards)

Each card: BG_RAISED, 1px BORDER, border-radius 4px, 12/14px padding, 2px top accent border.

| Card | Value | Sub | Accent |
|------|-------|-----|--------|
| Portfolio value | `$XXX,XXX` (blurred in hide mode) | `N positions` | none |
| Today's Δ | `+/−$X,XXX` green/red | `X.XX% on portfolio` | GREEN or RED |
| Biggest mover | Ticker symbol | `▲/▼ X.XX% today` | GREEN or RED |
| Leverage ratio | `X.XX×` | `$XXX,XXX borrowed` | GREEN/AMBER/RED (< 1.5 / 1.5–2.0 / ≥ 2.0) |

Leverage card also shows a small SVG gauge (semicircle, 80×42px) with a needle. Green→Amber→Red gradient arc, 1×–3× range.

#### Middle Row — Column 1: Allocation Widget

Panel with header `ALLOCATION` + pill buttons `Asset class | Country | Currency`.

Active pill: BLUE text, BLUE border, BLUE_DIM bg. Inactive: TEXT_FAINT.

Below pills: horizontal segmented bar 16px tall (flex, 1px gaps, each segment `flex: pct`, opacity 0.75).

Below bar: list of rows — 7px color square + label + right-aligned `XX.X%` in DM Mono 12px.

Footer note: `Proportions only` — DM Sans 10px TEXT_FAINT italic.

**Streamlit note:** Use `st.plotly_chart` with a horizontal stacked bar chart for this. The tab switcher becomes `st.radio` with `horizontal=True`.

#### Middle Row — Column 2: Watchlist Preview

Panel with header `Watchlist` + `All →` link button.

6 tickers, each row:
- Left: ticker as `<a>` link to Yahoo Finance, DM Mono 13px BLUE bold; target price in 10px TEXT_FAINT below
- Right: current price DM Mono 13px; gap dot + label (`● At target` green / `▼ X.X%` amber/red) in 10px

**Streamlit note:** `st.dataframe` with a custom column for gap color, or `st.write` with HTML.

#### Middle Row — Column 3: Leverage What-If (Mini)

Panel with header `Leverage what-if` + `Full →` link.

Two sliders:
- `Draw HELOC` — range 0 to available credit, step $500, BLUE accent
- `If markets fall` — range 0–50%, step 1%, RED accent

Result box (colored bg based on ratio severity):
- `Stressed ratio` / `Current ratio` label — DM Sans 11px TEXT_SUB
- Ratio value — DM Mono 20px bold, color-coded
- Delta vs current — DM Sans 10px, shown only when sliders > 0
- `Reset` button when any slider > 0

**Streamlit note:** `st.slider` for both; recompute leverage ratio on change. Use `st.metric` for the ratio display.

#### Bottom: Top 15 Holdings Table

Summary bar above table: `Positions N · Total value $X · Unrealized G/L ▲/▼$X (X.X%)`

Table columns: `Ticker | Acct | Mkt Value | Today | G/L | % Port`

- Ticker: DM Mono 13px bold + `USD` badge (amber, 8px) if USD-denominated
- Acct: colored badge pill (RRSP violet / TFSA teal / Unregistered orange / Crypto purple)
- Mkt Value, G/L: blurred in hide-values mode
- Today: ▲/▼ colored GREEN/RED
- % Port: percentage value

Sorted by Mkt Value descending. Top 15 only (link to Holdings screen for all).

**Streamlit note:** `st.dataframe` with `column_config` for color. For blurring in hide mode: CSS injection via `st.markdown` with `unsafe_allow_html`.

---

### 4. Holdings Screen

**Purpose:** Full sortable position list with G/L and ACB.

**Layout:** Single column with summary bar + scrollable table.

**Account scope strip** (fixed below nav, 34px): pill buttons for `All accounts | RRSP | TFSA | Unregistered | Crypto`. Active pill uses account color. **Streamlit:** `st.radio` horizontal or `st.selectbox`.

**Summary bar** (BG_PANEL, 10/16px padding): `Positions N · Total value · ACB total · Unrealized G/L`. Privacy hint right-aligned.

**Table columns:**
| Col | Type | Notes |
|-----|------|-------|
| Ticker | DM Mono bold | + USD badge |
| Name | DM Mono TEXT_SUB | truncated at 160px |
| Account | Colored badge | |
| Asset class | Colored badge (Stock blue / ETF green / Crypto purple / Lev.ETF amber) | |
| Qty | DM Mono | hidden in hide mode |
| ACB/sh | DM Mono TEXT_SUB | hidden in hide mode |
| Mkt price | DM Mono | + USD sub-line if applicable |
| Today | ▲/▼ green/red | |
| Mkt value | DM Mono bold | hidden in hide mode |
| Unreal G/L | ▲/▼ green/red | hidden in hide mode |
| G/L % | ▲/▼ green/red | hidden in hide mode |
| % Port | DM Mono + 3px mini bar | hidden in hide mode |

Click column header to sort ascending/descending. Footer: `USD converted at X.XXXX (BOC) · click headers to sort`.

**Streamlit note:** `st.dataframe` with `use_container_width=True`. Column sorting is built-in. For blurring: CSS injection only (no native Streamlit widget). For account filter: session state + `st.radio`.

---

### 5. Leverage Screen

**Purpose:** Manual entry of HELOC and margin balances + interactive what-if.

**Layout:** 2-column grid (`1fr 320px`): tabbed entry form left, what-if panel right.

#### KPI Strip (5 cards, full width)
| Card | Value |
|------|-------|
| HELOC drawn | `$X` / `of $X limit` |
| HELOC available | `$X` / `X% utilized` |
| Margin balance | `$X` / `Broker · X%` |
| Total borrowed | `$X` / `HELOC + margin` |
| Leverage ratio | `X.XX×` / `Portfolio ÷ own equity` — color-accented |

#### Left: Tabbed Entry (HELOC / Margin Loan)

Tab bar: 2 buttons, full-width flex. Active: BLUE text + 2px BLUE bottom border.

**HELOC tab:**
- Section heading `UPDATE BALANCES — FROM YOUR LENDER STATEMENT` — 11px uppercase TEXT_SUB
- 2-col grid: `Amount drawn` + `Credit limit` — each has label, italic help text, `$ [number input] CAD`
- Utilization bar: AMBER color, 8px height, label + percentage
- Single `Save` button — turns green with ✓ for 2s after click

**Margin tab:** Same pattern — `Balance outstanding` + `Margin limit` inputs; margin call buffer warning if buffer < 50%.

**Streamlit note:** `st.tabs` for HELOC/Margin. `st.number_input` for balances. `st.progress` for utilization bar. `st.session_state` to persist values.

#### Right: What-If Stress Test Panel

Two sliders:
1. **Draw additional HELOC** (0 → available credit, step $500, BLUE)
2. **If markets fall…** (0–50%, step 1%, RED) — with sub-label `Debt stays fixed; portfolio value shrinks → ratio rises`

Result box (color-coded bg):
- Label: `Stressed ratio` or `Current ratio`
- Value: large DM Mono ratio
- Delta line vs base ratio (when any slider > 0)
- Sub-rows: `HELOC balance · Total borrowed · Stressed port. val · Interest delta/mo`
- Warning `⚠ Ratio exceeds 2.0×` at RED threshold
- `Reset` button + disclaimer `Not financial advice`

---

### 6. Net Worth Screen

**Purpose:** Full balance sheet — assets vs liabilities.

**Layout:** 2-column grid (`380px 1fr`): ledger left, visualization right.

#### KPI Strip (4 cards)
| Net Worth | Total assets | Total liabilities | Debt-to-equity |
|-----------|-------------|-------------------|----------------|
| `$X` BLUE | `$X` | `$X` RED | `X.XX×` color-coded |

#### Left: Asset/Liability Ledger

**ASSETS section** (green label row):
- Portfolio (auto) — read-only, DM Mono 13px
- Cash / HISA — **click-to-edit inline** (click value → text input, Enter to commit)
- Primary residence — **number input + range slider** (combined: type any value OR drag)
- Total assets row — DM Mono 13px weight 700 GREEN

**LIABILITIES section** (red label row):
- Mortgage balance — number input + range slider (shows rate + renewal date below)
- HELOC (auto) — read-only, RED
- Margin (auto) — read-only, RED
- Total liabilities row — DM Mono 13px weight 700 RED
- Net worth row — DM Mono 16px weight 700 BLUE

**Streamlit note:** Use `st.number_input` + `st.slider` side-by-side for property and mortgage. Inline-editing is not native to Streamlit; use `st.number_input` directly.

#### Right Column

**Asset/Liability breakdown:** Horizontal stacked bar (20px) for assets + liabilities separately, with color legend below. Use Plotly horizontal bar chart.

**Mortgage & property detail table:** 6 rows — Property value / Mortgage balance / Home equity / LTV ratio / Rate / Renewal. LTV color-coded (green < 65%, amber 65–80%, red > 80%).

---

### 7. Watchlist Screen

**Purpose:** Track target buy prices vs current prices.

**Layout:** Full-width table with add/edit/delete controls.

**Header:** Privacy note left, `+ Add ticker` button right (toggles add form).

**Add form** (panel, flex row): Ticker input · Target price input · Notes input · `Add` button.

**Table columns:** `Ticker (Yahoo Finance link) | Name | Current | Today | Target | Gap % | Notes | Actions`

- Ticker: `<a>` link to `https://finance.yahoo.com/quote/{ticker}`
- Gap %: color dot + label — ● green (at/below target) · amber (< 10% away) · red (> 10% away)
- Notes: italic TEXT_SUB, `—` if empty
- Actions: `Edit | ✕` buttons (inactive) → `Save | Cancel` (editing) → `Delete | Cancel` (deleting)

Inline editing: Target price and Notes become inputs in-row.

**Footer:** `Click Edit to update target price or notes` — italic TEXT_FAINT.

**Empty state:** Centered empty state with ◎ icon, title, description.

**Streamlit note:** `st.data_editor` for in-place editing. Add row via a form above. Delete via checkbox + button. Yahoo Finance links via `column_config.LinkColumn`.

---

### 8. Settings Screen

**Purpose:** Configure security, borrowing rates, data refresh, FX, imports.

**Layout:** 2-column — 200px sidebar nav left, content area right (maxWidth 700px).

**Sidebar nav:** Button list, each `8/18px` padding, `2px left border` BLUE on active. DM Sans 13px.

**Sections:** Security · Borrowing · Refresh · FX · Imports · About

Each section has an `h2` title (DM Sans 16px weight 600) and content in a Panel with `FormRow` components. Each FormRow: label (13px) + optional italic help text (11px TEXT_FAINT) + control right-aligned.

**Save pattern:** One `Save changes` button per section at the bottom of the Panel. On click: turns green with `✓ Saved · Settings updated` for 2.2s.

#### Security
- Change password (password input + Update button)
- Session timeout (number input, minutes)

#### Borrowing
Two sub-sections (HELOC / Margin loan):
- HELOC: Credit limit · Interest rate (% p.a.) · Utilization warning threshold (%)
- Margin: Borrowing limit · Broker call threshold (%) · Warning banner threshold (%)

#### Refresh
- Scheduled refresh toggle (custom pill toggle — blue when on)
- Refresh interval (minutes, only enabled when toggle on, opacity 0.4 when off)
- Last refresh timestamp + `Refresh now` button

#### FX
- Rate source (read-only: `Bank of Canada daily rate`)
- USD/CAD rate display (DM Mono 20px bold) + fetch timestamp + BOC chart link

#### Imports (CSV)
- **Upload zone:** Drag-and-drop area, 2px dashed BORDER, center-aligned. On drag-over: BLUE border + BLUE_DIM bg. Click also opens file picker. Accepts `.csv` only.
- On upload: green confirmation row per file — `✓ filename.csv · X.X KB · HH:MM:SS`
- Previously imported files table: `File | Broker | Rows | Imported | Re-import button`
- Empty state if no files: ⬆ icon + `No import files found` + instructions

#### About
Read-only metadata rows: Version · Branch · Last commit · Stack · Storage · Remote access.

---

## Data Model

```python
# Core data structures (from mock data)

Account = {
    "id": str,          # "rrsp" | "tfsa" | "unreg" | "crypto"
    "label": str,
}

Holding = {
    "ticker": str,
    "name": str,
    "acct": str,        # Account id
    "qty": float,
    "acbPS": float,     # Adjusted cost basis per share (CAD)
    "priceCAD": float,  # Current price in CAD (converted if USD)
    "priceUSD": float,  # Original USD price (if applicable)
    "currency": str,    # "CAD" | "USD"
    "assetClass": str,  # "Stock" | "ETF" | "Crypto" | "LeveragedETF" | "Cash"
    "country": str,     # "CA" | "US" | "—"
    "changePct": float, # Today's % change
}

# Derived fields (computed, not stored):
# mktVal    = qty * priceCAD
# gl        = mktVal - (qty * acbPS)
# glPct     = gl / (qty * acbPS) * 100
# acbTotal  = qty * acbPS

HELOC = {
    "limit": int,
    "drawn": int,
    "rate": float,      # Annual % rate
}

Margin = {
    "broker": str,
    "balance": int,
    "limit": int,
    "rate": float,
    "callThreshold": float,  # e.g. 0.70 = 70%
}

Property = {
    "value": int,            # Manual estimate
    "mortgageBalance": int,  # Manual entry
    "rate": float,
    "renewalDate": str,
}

WatchlistItem = {
    "ticker": str,
    "name": str,
    "price": float,
    "target": float,
    "vol": str,         # "Low" | "Med" | "High"
    "note": str,
    "changePct": float,
    "currency": str,    # optional
}
```

## Key Computed Values

```python
# FX
FX_USD_CAD = 1.378  # from Bank of Canada daily API

# Portfolio
portfolio_total = sum(h.qty * h.priceCAD for h in holdings)

# Leverage ratio
# total_borrowed = heloc.drawn + margin.balance
# equity = portfolio_total - total_borrowed
# ratio  = portfolio_total / equity  (i.e. assets / own equity)

# Net worth
total_assets = portfolio_total + property.value + cash
total_liab   = property.mortgageBalance + heloc.drawn + margin.balance
net_worth    = total_assets - total_liab
debt_to_equity = total_liab / (total_assets - total_liab)
ltv = property.mortgageBalance / property.value * 100
```

---

## Privacy / Hide Values Mode

A session-level toggle (`st.session_state["hide_values"]`) blurs sensitive fields:
- All dollar amounts (portfolio value, G/L, net worth, liabilities)
- Quantities, ACB
- Tickers and percentage changes remain visible

Implementation: conditionally render `"●●●●"` or `st.markdown` with CSS blur filter.

---

## Streamlit-Specific Notes

1. **Theming:** Set in `.streamlit/config.toml`:
   ```toml
   [theme]
   base = "dark"
   backgroundColor = "#0f0f0f"
   secondaryBackgroundColor = "#161616"
   textColor = "#f0f0f0"
   font = "sans serif"
   ```

2. **Custom CSS:** Use `st.markdown('<style>...</style>', unsafe_allow_html=True)` for DM Sans/DM Mono fonts, table styling, badge pills, and blur effects.

3. **Navigation:** Use `st.navigation` (Streamlit 1.36+) or `st.radio` in sidebar with `label_visibility="collapsed"` for the tab bar. The top fixed nav bar with subtitles requires custom CSS injection.

4. **Session management:** Use `st.session_state` for login state, hide-values toggle, scope filter, and all manual-entry values (HELOC drawn, property value, etc.).

5. **Auto-refresh:** Use `st_autorefresh` (streamlit-autorefresh package) or `time.sleep` + `st.rerun()` for scheduled price refresh.

6. **Questrade integration:** Use the `questrade-api` Python package or direct REST calls to fetch positions and balances.

7. **BOC FX rate:** Fetch from `https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1` — cache with `@st.cache_data(ttl=86400)`.

---

## Files in This Package

| File | Description |
|------|-------------|
| `Investments Monitor v3.html` | Full interactive prototype — open in browser |
| `im-data.jsx` | Mock data & computed values reference |
| `im-ui-v3.jsx` | Design tokens, all base UI components |
| `im-cockpit-v3.jsx` | Cockpit screen |
| `im-holdings-v3.jsx` | Holdings screen |
| `im-leverage-v3.jsx` | Leverage screen |
| `im-watchlist-v3.jsx` | Watchlist screen |
| `im-settings-v3.jsx` | Settings screen |
| `im-login.jsx` | Login/lock screen |
| `Investments Monitor Wireframes.html` | Earlier wireframe reference (layout intent) |
