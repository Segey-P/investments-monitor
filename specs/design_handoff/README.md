# Handoff: Investments Monitor

## Overview

A personal investment monitoring dashboard (codename **IM**) for a Canadian investor tracking a leveraged portfolio across RRSP, TFSA, Unregistered and Crypto accounts, plus a HELOC and margin loan. The app has a strict **privacy model** (Path C): some data is cloud-safe (ratios, tickers, proportions) and some is local-only (dollar values, quantities, ACB, G/L).

---

## About the Design Files

The files in this bundle are **HTML/JSX prototypes** — high-fidelity design references created to show intended look, layout and interactive behavior. They are **not production code**. The developer's task is to recreate these designs in the target codebase (the spec describes a Python + Streamlit + SQLite stack, but the UI layer should match the design's intent). All mock data lives in `im-data.jsx`; in production it will come from SQLite via the backend.

---

## Fidelity

**High-fidelity.** Colors, typography, spacing, component structure and interactions are all intentional and should be matched closely. The design uses `DM Sans` (UI text) and `DM Mono` (numbers, tickers, code). Dark theme only.

---

## Design Tokens

### Colors
```
bg:        #0f0f0f   — page background
bgPanel:   #161616   — card/panel background
bgRaised:  #1e1e1e   — table row alt, input background
bgHover:   #252525   — row hover
border:    #2a2a2a   — default border
borderMid: #333333   — stronger dividers
text:      #f0f0f0   — primary text
textSub:   #888888   — secondary/label text
textFaint: #444444   — hints, placeholders
blue:      #3b82f6   — primary accent, links, active nav
blueDim:   #0f1e3d   — blue tinted background
green:     #22c55e   — gain, success, safe
greenDim:  #0d2a18   — green tinted background
red:       #ef4444   — loss, error, warning
redDim:    #2d1414   — red tinted background
amber:     #f59e0b   — caution, warning, USD badge
amberDim:  #2d200a   — amber tinted background
```

### Account badge colors
```
RRSP:          #a78bfa (purple)
TFSA:          #14b8a6 (teal)
Unregistered:  #f97316 (orange)
Crypto:        #8b5cf6 (violet)
```

### Asset class badge colors
```
Stock:   #3b82f6 (blue)
ETF:     #22c55e (green)
Crypto:  #8b5cf6 (violet)
```

### Allocation dimension colors
```
by_account:     RRSP #a78bfa, TFSA #14b8a6, Unreg #f97316, Crypto #8b5cf6
by_assetClass:  Stock #3b82f6, ETF #22c55e, Crypto #8b5cf6
by_country:     CA #ef4444, US #3b82f6, other #6b7280
by_currency:    CAD #14b8a6, USD #f97316
```

### Typography
```
Font families:  DM Sans (sans-serif UI), DM Mono (monospace numbers/tickers)
Nav labels:     DM Sans 13px #666 / #3b82f6 active
Section heads:  DM Sans 11px 600 #888 uppercase letter-spacing 0.8
KPI label:      DM Sans 11px #888
KPI value:      DM Mono 20px 700
Table header:   DM Sans 10px 600 #888 letter-spacing 0.4
Table cell:     DM Mono 12px (numbers), DM Sans 12px (text)
Badge:          DM Mono 10px
```

### Spacing
```
Page padding:   20px
Panel padding:  12–16px
Row padding:    9px 12px (table), 10px 16px (list rows)
Gap (grid):     10–12px
```

### Border radius
```
Panels/cards:   4px
Badges:         3px
Pills (scope):  12px
Inputs:         3px
```

---

## Privacy Model (Path C)

Every data point is tagged ☁ cloud-safe or 🔒 local-only.

**Cloud-safe** (visible without auth, shareable in public summary JSON):
- Leverage ratio, HELOC utilization %, debt-to-equity ratio, mortgage LTV
- Allocation proportions (%, not dollar amounts)
- Tickers and market prices
- Watchlist tickers, current prices, target prices, gap %
- Position count

**Local-only** (blurred in public view, require auth):
- All dollar amounts (portfolio value, net worth, mkt value, G/L, ACB)
- Quantities
- Mortgage balance, HELOC drawn balance (dollar amounts)

**Public view toggle** in the top nav switches between full view and public view. In public view:
- KPI cards with local data show blurred values (`filter: blur(5–6px)`)
- Holdings table shows ticker, account badge, today %, but blurs mkt value, G/L, ACB, % port
- Cockpit top holdings: same per-cell blur pattern
- An amber banner appears at top of affected panels explaining what's hidden

---

## Screens / Views

### 1. Login Gate (`im-login.jsx`)

**Purpose:** Password-protect local data. Show cloud-safe public summary pre-auth.

**Layout:** Full-viewport centered column, max-width 540px.

**Sections (top to bottom):**
1. Wordmark — `IM` in DM Mono 28px bold, subtitle `Investments Monitor · personal` DM Sans 13px #888
2. **Public summary card** — left border accent `#3b82f6` 3px, background `#161616`
   - Header row: `☁ Public summary` label + cloud badge
   - 3-col KPI grid: Leverage ratio (colored by zone), HELOC utilization %, Position count
   - Allocation bar: stacked horizontal bar by asset class (proportions), legend below
   - **Holdings table**: Ticker | Price (CAD) | Today % — 3 columns, alternating row bg
   - **Watchlist table**: Ticker | Current | Today % | Target | Gap — 5 columns
3. **Login form** — password input + "Unlock →" button (blue, full width). Any non-empty password unlocks in the prototype; real implementation uses bcrypt.

---

### 2. Top Navigation (`im-ui.jsx → TopNav`)

**Layout:** Fixed top bar, height 44px, `#141414` background, `1px solid #2a2a2a` bottom border.

**Left:** `IM` wordmark (DM Mono 14px bold), then nav tabs: Cockpit · Holdings · Leverage · Net Worth · Watchlist · Settings. Active tab: `#3b82f6` text + `2px solid #3b82f6` bottom border.

**Right:** `☁ Public view / Full view` toggle pill + timestamp.

**Account scope strip** (shown on Holdings and Leverage only, not Cockpit): `All accounts · RRSP · TFSA · Unregistered · Crypto` pills, height 34px, `#141414` bg. Active pill uses account badge color.

---

### 3. Cockpit (`im-cockpit.jsx`)

**Layout:** CSS grid `240px 240px 1fr`, gap 12px. No account scope strip.

**Row 1 — KPI strip** (spans full width, 3 cards `1fr 1fr 1fr`):
- Net Worth — 🔒 local, blurred in public view
- Portfolio value — 🔒 local, blurred
- Unrealized G/L — 🔒 local, blurred. Value color: green if positive, red if negative

**Row 2 — Col 1: Allocation widget**
- Section header + 3 dimension pills inline: Asset class · Country · Currency
- Pills: `border 1px solid`, `border-radius 10px`, active = blue tint + border
- Stacked horizontal bar (snap swap, NO transition between dimensions — rationale: dimensions are categorically incomparable)
- Legend rows: colored square + label + right-aligned %
- Note: "Proportions only · no dollar amounts in cloud view"

**Row 2 — Col 2: Leverage gauge**
- SVG semicircle gauge, gradient track (green→amber→red), needle pointing to current ratio
- Ratio value centered below needle in DM Mono 20px bold, colored by zone
- Zone labels: Safe (left) / High (right)
- Below gauge: HELOC / Margin / Total rows with rate sub-labels
- "HELOC & Margin detail →" button at bottom

**Row 2+3 — Col 3: Top holdings** (spans 2 rows)
- Amber banner in public view: "🔒 Values hidden in public view · tickers and today's change visible"
- Table: Ticker | Acct | Mkt Value | Today | G/L | % Port
- Public view: Mkt Value, G/L, % Port cells individually `filter: blur(5px)`
- Today column always visible (cloud-safe)

**Row 3 — Col 1+2: Watchlist mini**
- 4 items max, "All →" link
- Per row: ticker (bold) + current price, range bar (blue = target, amber = current), "▼ X% away" label

---

### 4. Holdings (`im-holdings.jsx`)

**Layout:** Full-width, padding 20px.

**Summary bar** (above table): Positions · Total value · ACB total · Unrealized G/L — all blurred in public view. Right: 🔒 local badge + explanation.

**No in-screen account filter** — filtering done via scope strip in top nav.

**Table columns:** Ticker | Name | Account | Asset class | Qty | ACB/sh | Mkt price | Today | Mkt value (CAD) | Unreal G/L | G/L % | % Port

- Sortable by any column (click header, ▼/▲ indicator)
- Alternating row bg: transparent / `#1e1e1e`
- Row hover: `#252525`
- USD badge on USD-denominated positions
- Public view: amber banner at top; Qty, ACB, Mkt value, G/L, G/L %, % Port cells blurred. Ticker, Name, Account, Asset class, Mkt price, Today always visible.
- Footer: "USD converted at X.XXXX (BOC) · click headers to sort"

**G/L display:** ▲ for gain (green `#22c55e`), ▼ for loss (red `#ef4444`) — shape + color for colorblind safety.

---

### 5. Leverage (`im-leverage.jsx`)

**Layout:** CSS grid `1fr 320px`, gap 12px.

**KPI strip** (6 cards, full width):
- HELOC drawn 🔒 | HELOC available 🔒 | Margin balance 🔒 | Total borrowed 🔒 | Leverage ratio ☁ (accent colored) | Margin buffer 🔒

**Left panel — tabbed: HELOC | Margin loan**

Both tabs use identical structure:
- Sub-header: "Update balances — [source]"
- 2-column grid: two `$` number inputs (Amount drawn/balance + Credit/borrowing limit)
- Utilization bar: `Bar` component, amber color, 8px height
- Stats below bar: "Drawn $X / Available $X"
- Margin call warning (amber box) when buffer < 50%
- Save button (turns green on save, resets after 2s)
- Footer row: rate info + update reminder

**Right panel — HELOC what-if slider**
- "Draw additional" label + current value (DM Mono 18px bold)
- HTML range input, full width, accent color blue
- Min $0, max = available HELOC, step $500
- Live result box (background color-shifts by ratio zone):
  - Leverage ratio (large, 22px bold, colored)
  - Delta from current ratio if changed
  - Impact rows: New HELOC balance, Total borrowed, Interest delta/mo
  - Warning if ratio ≥ 2.0×
- Footer: "Assumes rate stays at X%. Not financial advice."

---

### 6. Net Worth (`inline in Investments Monitor v2.html`)

**Layout:** CSS grid `360px 1fr`, gap 12px.

**KPI strip** (5 cards): Net Worth 🔒 | Total assets 🔒 | Total liabilities 🔒 | Debt-to-equity ☁ | Mortgage LTV 🔒

**Left — A/L ledger:**
- "ASSETS" label (green, uppercase, letter-spacing)
- Portfolio (auto, local), Cash (manual ✎, local)
- Primary residence (manual ✎): slider $300k–$2M, green accent, local
- "Total assets" summary row (green, bold)
- "LIABILITIES" label (red)
- Mortgage balance (manual ✎): slider $0–$1M, red accent, local
- HELOC (auto, cloud) + Margin (auto, cloud)
- "Total liabilities" summary row (red)
- "Net worth" final row (blue, 16px bold)

**Right col (2 panels):**

*Asset/Liability breakdown:*
- Two stacked bars: Assets (portfolio/property/cash) and Liabilities (mortgage/HELOC/margin)
- Each bar: flex children sized by value, colored, with legend

*Mortgage & property detail:*
- 6 rows: Property value / Mortgage balance / Home equity / LTV / Rate / Renewal
- Values blurred in public view

---

### 7. Watchlist (`im-watchlist.jsx`)

**Layout:** Full-width table, padding 20px.

**Header:** ☁ cloud badge + "Tickers, prices and targets are cloud-safe" + "+ Add ticker" button (right)

**Add ticker form** (collapsible): Ticker input + Target price input + Notes input + Add button

**Table columns:** Ticker | Name | Current | Today | Target | Gap % | 52-wk Range | Vol. | Notes | Actions

- **Target price is editable inline**: Click "Edit" → target cell becomes `<input type="number">`, notes cell becomes `<input>`. Save / Cancel buttons appear.
- **Delete**: ✕ button → confirm "Delete / Cancel" inline (no modal)
- **52-wk range bar**: 4px height, two vertical markers — blue at target position, amber at current position. Labels: `$lo52 · ▐ target · ▐ now · $hi52`
- **Vol badge**: ● Low (green) · ◆ Med (amber) · ▲ High (red) — shape + color
- **Today %**: ▲/▼ + percentage, green/red
- Footer legend row

---

### 8. Settings (`im-settings.jsx`)

**Layout:** Sidebar nav (200px) + content area (flex 1, max-width 680px, padding 24px 32px).

**Sidebar:** Fixed-width, `#161616` bg, `1px solid #2a2a2a` right border. Active item: `2px solid #3b82f6` left border, blue text.

**Sections:**

**Security**
- Change password: two-col (input + Update button)
- Session timeout: number input (minutes) + Save button. Default 15 min. Warning banner appears 60s before expiry.

**Borrowing** (HELOC + Margin combined in one section, with sub-headers)
- *HELOC sub-section:* Credit limit ($CAD input + Save) · Utilization warning threshold (% input + Save, default 80%)
- *Margin loan sub-section:* Borrowing limit ($CAD + Save) · Broker call threshold (% equity + Save, default 70%) · Warning banner threshold (% buffer + Save, default 50%)

**Refresh**
- Scheduled refresh toggle (custom toggle switch: 44×24px pill, animated thumb)
- Refresh interval (number input, disabled when toggle off)
- Last refresh timestamp + "Refresh now" button

**FX**
- Current USD/CAD rate (read-only, DM Mono 20px bold)
- Source: Bank of Canada daily · fetched timestamp · BOC chart link
- Note: rate not manually overridable

**Imports**
- Instruction: place CSVs in `data/imports/`
- Table: File | Broker | Rows | Imported | Re-import button
- Footer: "Supported: Questrade Activity CSV"

**Public summary**
- Output path (read-only)
- Last pushed timestamp
- "Regenerate + push" button with 4 states: idle (blue) → working (spinner) → success (green) → error (red, retry label)
- Payload preview: `<pre>` block showing exact JSON structure with no dollar amounts

**About**
- Version, branch, last commit, stack, storage, remote access (all read-only DM Mono rows)

---

### 9. Session Banner (`im-ui.jsx → SessionBanner`)

Appears fixed below the top nav (top: 44px) when session is within 60s of expiry.

- Amber background (`#2d200a`) + amber border when warning
- Red background when expired
- "Stay signed in" (blue button) + "Dismiss" (ghost button)
- Dismiss hides the banner for the session but does NOT extend the session
- "Stay signed in" resets the full timer

---

## Interactions & Behavior

### Navigation
- Top nav tabs: instant screen swap, no page reload
- Scope strip: filters holdings and leverage tables by account; persisted in React state
- Screen selection persisted to `localStorage` key `im_screen`

### Public view toggle
- Flips `publicView` boolean in root App state
- Propagates to all screens via prop
- Per-cell `filter: blur(5–6px)` on local-only values
- Amber info banners replace full-screen overlays

### Session timer
- Countdown in seconds, starts on login
- Warning banner appears at T−60s
- Auto-logout at T=0, redirects to login screen
- "Stay signed in" resets timer
- "Dismiss" hides banner (session still expires)

### Watchlist edit
- "Edit" button: opens inline edit mode for that row only
- Tab/Enter to move between fields
- "Save" commits; "Cancel" reverts
- "✕" → shows "Delete / Cancel" confirm inline; "Delete" removes row from state

### What-if slider (Leverage screen)
- Real-time: drag updates leverage ratio, total borrowed, interest delta instantly
- Result box background color-shifts green→amber→red as ratio crosses thresholds
- Ratio thresholds: <1.5× = safe (green), 1.5–2.0× = caution (amber), ≥2.0× = high (red)

### Allocation widget (Cockpit)
- 3 dimension pills: Asset class · Country · Currency
- Switching dimensions: **snap swap, no animation** (dimensions are categorically incomparable; a transition would imply false continuity)

### Save buttons (Settings)
- Optimistic: immediately turn green + "✓ Saved" label
- Reset to default state after 2000ms
- No real persistence in the prototype; wire to backend API in production

### Regenerate + push (Settings → Public summary)
- idle → working (1.8s spinner delay in prototype)
- → success or error (random in prototype; deterministic in production)
- States reset to idle after 3.5s

---

## State Management

### Root App state
```
loggedIn:      boolean
screen:        'cockpit' | 'holdings' | 'leverage' | 'networth' | 'watchlist' | 'settings'
scope:         'all' | 'rrsp' | 'tfsa' | 'unreg' | 'crypto'
publicView:    boolean
sessionLeft:   number | null  (seconds remaining, null = no banner)
bannerDismissed: boolean
```

### Per-screen state
- Holdings: `sortKey`, `sortDir`
- Leverage: `tab`, `whatIfDraw`, `helocDrawn`, `helocLimit`, `marginBal`, `marginLimit`, saved flags
- Net Worth: `propVal`, `mortgageV`
- Watchlist: `items[]`, `editId`, `editTarget`, `editNote`, `deleteId`, `showAdd`, add-form fields
- Settings: various field values + `saved{}` map + `pushState`

---

## Data Model (from `im-data.jsx`)

### Holdings
```typescript
{
  ticker:     string        // e.g. "RY.TO"
  name:       string        // full company name
  acct:       'rrsp' | 'tfsa' | 'unreg' | 'crypto'
  qty:        number
  acbPS:      number        // adjusted cost base per share, CAD
  priceCAD:   number        // current market price in CAD
  currency:   'CAD' | 'USD'
  priceUSD?:  number        // if USD position
  assetClass: 'Stock' | 'ETF' | 'Crypto'
  country:    'CA' | 'US' | '—'
  changePct:  number        // today's % change (signed)
}
```

### HELOC
```typescript
{
  limit:  number   // credit ceiling CAD
  drawn:  number   // current balance CAD
  rate:   number   // annual interest rate %
}
```

### Margin
```typescript
{
  broker:         string
  acct:           'unreg'
  balance:        number   // current balance CAD
  limit:          number   // approved limit CAD
  rate:           number   // annual interest rate %
  callThreshold:  number   // 0–1, e.g. 0.70
}
```

### Watchlist item
```typescript
{
  ticker:    string
  name:      string
  price:     number        // current price
  target:    number        // target buy price
  lo52:      number        // 52-week low
  hi52:      number        // 52-week high
  vol:       'Low' | 'Med' | 'High'
  note:      string
  currency?: 'USD'         // only set for USD positions
  changePct: number        // today's % change
}
```

### Property
```typescript
{
  value:           number   // manual estimate CAD
  mortgageBalance: number   // manual CAD
  rate:            number   // % annual
  renewalDate:     string
}
```

---

## Derived Calculations

```typescript
// Portfolio total (CAD)
portTotal = sum(h.qty * h.priceCAD)

// Leverage ratio
ratio = portTotal / (portTotal - helocDrawn - marginBalance)

// Margin call buffer
buffer = (unregAcctValue - marginBalance) / unregAcctValue

// Net worth
netWorth = portTotal + propertyValue + cash - mortgageBalance - helocDrawn - marginBalance

// Debt-to-equity
dte = (mortgageBalance + helocDrawn + marginBalance) / netWorth

// Monthly interest
helocMo  = helocDrawn  * helocRate  / 100 / 12
marginMo = marginBalance * marginRate / 100 / 12

// FX: all USD prices multiplied by FX_USD_CAD (Bank of Canada daily rate)
```

---

## Files in This Bundle

| File | Purpose |
|---|---|
| `Investments Monitor v2.html` | Main prototype shell + router + Net Worth screen inline |
| `im-data.jsx` | All mock data, derived calculations, formatting helpers |
| `im-ui.jsx` | Design tokens, shared primitives (KPICard, Panel, TopNav, ScopeStrip, SessionBanner, etc.) |
| `im-cockpit.jsx` | Cockpit screen + AllocationWidget |
| `im-holdings.jsx` | Holdings table screen |
| `im-leverage.jsx` | HELOC & Margin leverage screen |
| `im-watchlist.jsx` | Watchlist screen with inline edit/delete |
| `im-login.jsx` | Login gate + public summary |
| `im-settings.jsx` | Settings screen (6 sections) |
| `Investments Monitor Wireframes.html` | Early wireframe exploration (reference only) |

---

## Assets

No external images or icons. All UI elements are pure CSS/SVG. Fonts loaded from Google Fonts:
- `DM Sans` weights 400, 500, 600, 700
- `DM Mono` weights 400, 500, 700

Google Fonts import URL:
```
https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500;700&display=swap
```

---

## Backend Notes (for implementer)

The prototype assumes:
- **SQLite** local database for holdings, HELOC draws, margin entries
- **Questrade CSV import** as primary data ingestion (place files in `data/imports/`)
- **Bank of Canada API** for daily USD/CAD FX: `https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json`
- **No cloud writes** of dollar amounts or quantities; only the public summary JSON (ratios + proportions + tickers/prices) is ever written to a remotely accessible location
- **Tailscale** required for remote access to the full app
- Password stored as bcrypt hash; session timeout configurable (default 15 min)
