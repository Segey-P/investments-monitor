# Module 2: Dashboard & Asset Manager Specification

## 1. Objective

Provide the user-facing views for monitoring, plus management of non-market assets (property, mortgage). Visual language follows **V2 "Dark Command Strip"** (Linear-inspired dark palette), applied consistently across all screens.

## 2. Screens

### A. Dashboard (landing)

- **Top nav:** Dashboard · Holdings · Leverage · Net Worth · Watchlist · Settings. Right side: portfolio scope label (v0.1 always "Individual"), cloud-privacy indicator (☁ Public / 🔒 Local).
- **Account-scope pills:** All · RRSP · TFSA · Non-Reg · Crypto. (DB value `Unreg` is rendered as "Non-Reg".)
- **KPI strip (5 tiles):** Net Worth · Portfolio · Unrealized P/L · Leverage Ratio · HELOC Drawn. Each tile carries a privacy badge.
  - **Net Worth** sub-line: `FX <rate> · <as_of>`. The `<rate>` number is a hyperlink to `https://ca.finance.yahoo.com/quote/CAD=X/`. (No "BOC" mention.)
  - **Leverage Ratio** sub-line: shown only when ratio enters caution (≥1.5×) or high (≥2×) zones. Empty when safe.
- **Allocation widget (multi-dim):** Bar chart only — no table beneath. Toggle (radio pills) for dimension:
  - By Asset Class (Cash / Stock / ETF / LeveragedETF / Crypto)
  - By Country (CA / US / Other)
  - By Currency (CAD / USD)
  - **Removed:** "By Account" — redundant with the scope pills.
- **Watchlist mini:** Top 5 favorites (`is_favorite = 1`, ordered by ticker) with daily change %, current price, target, and gap. UI caps favorites at 5.
- **Top Holdings table:** Top 10 positions by market value. Columns: Ticker · Acct · Mkt Value · Today · P/L · % Port. Tickers hyperlink to Yahoo Finance (`finance.yahoo.com/quote/<yahoo_ticker>`). USD positions get a small `USD` badge next to the ticker.
- **Live prices:** Every Dashboard render triggers `prices.get_quotes(...)` for held + favorited tickers; in-process cache caps the fetch rate at 1× per 60s. No manual refresh button on Dashboard.

### B. Holdings

- Filter pills by account type (DB value `Unreg` rendered as "Non-Reg").
- Sortable columns: Ticker · ↗ (Yahoo link) · Acct · Cur · Qty · ACB/sh · Mkt Price · Mkt Value · P/L · P/L % · % Portfolio · Asset Class.
- Account tag as colored pill.
- USD positions show CAD-converted value as the Mkt Value column (BOC rate). No per-ticker currency toggle.
- Colorblind-safe P/L: ▲ (gain, green `#22c55e`) / ▼ (loss, red `#ef4444`). Shape + color.
- Footer summary bar: Total Portfolio · P/L · Position count · Account count.
- **No detail drawer** — ACB is entered once, no transaction history.

### C. Leverage (HELOC + Margin)

Tabbed screen: **HELOC | Margin**. Both borrowing sources roll up into a shared KPI strip.

- **KPI strip (6 tiles):** HELOC drawn · HELOC available · Margin balance · Total borrowed · Leverage Ratio · Margin buffer.
- **HELOC tab:**
  - Update balances (amount drawn, credit limit).
  - Utilization bar + stats (drawn / available).
  - **Drawdown ledger:** Date · Amount · Purpose (free-text). No tax-deductible column.
  - **What-if slider:** Additional draw; shows new balance, new ratio, new monthly interest, safety zone.
- **Margin tab:**
  - Update balances (current balance, borrowing limit, broker).
  - Utilization bar + stats.
  - Margin-call warning (amber banner) when buffer drops below `warn_buffer_pct` (default 50%).
  - Balance-only (no drawdown ledger).
- Leverage historical trend chart removed from v0.1 (deferred).
- "Interest deductibility summary" panel removed from v0.1 (dropped).

### D. Watchlist

- Columns: Ticker · Name · Current · Target · Gap % · 52-wk Range · Vol · Notes.
- 52-wk range bar with markers for target (blue) and current (yellow).
- Volatility badge: shape + color (▲ high, ◆ med, ● low).
- Add/remove ticker actions.

### E. Net Worth Ledger

- KPI strip: Net Worth · Total Assets · Total Liabilities · Debt-to-Equity · Mortgage LTV.
- **Asset/Liability ledger** (left): Portfolio (auto) · Cash (manual) · Other assets (manual) · Property (manual with slider/input) · Mortgage (manual with slider) · HELOC (auto from Leverage screen) · Margin (auto from Leverage screen) · Other debt (manual).
- **Visualizations** (right): Assets vs Liabilities stacked bar · Household D/E gauge (Low 0–0.5 / Caution 0.5–1 / High 1+) · Mortgage & Property detail (value, balance, equity, LTV, renewal date, rate — all manual).

### F. Settings (new screen)

Single form. All fields editable, "Save" at bottom.

- **Security:** Change password · Session timeout (minutes, default 15)
- **Borrowing:**
  - *HELOC:* Limit ($CAD) · Rate (% annual) · Utilization warning threshold (% default 80)
  - *Margin:* Broker · Borrowing limit ($CAD) · Rate (% annual) · Broker call threshold (% equity default 70) · Warning banner threshold (% buffer default 50)
- **Refresh:** Interval (hours) · Enable scheduled refresh (toggle)
- **FX:** Source = Bank of Canada daily (read-only). Displays current rate + fetched timestamp + link to BOC chart.
- **Imports:** List of files in `data/imports/` with Import/Re-import action per file. Maps to Questrade/IBKR parsers.
- **Public summary:** Path to `public/summary.json` · Last regeneration timestamp · "Regenerate now" button.
- **About:** Version, branch, last commit.

### G. Login Gate

- Password field + Unlock button.
- **Pre-auth public summary visible:** Net worth proportions, leverage ratio, watchlist alert count — sourced from the same `public/summary.json` so the user gets a read-only glance without signing in.
- Post-auth: session cookie with configurable timeout.

## 3. Session timeout UX

- Inactivity timer starts after last user interaction.
- At `timeout − 60s`: in-app banner "Session expires in 60s · [Stay signed in]". Clicking extends.
- At expiry: redirect to Login; any open form state discarded.

## 4. FX display

- BOC daily rate fetched once per day and cached.
- Persistent footer element on Holdings and Net Worth screens: `1 USD = 1.37 CAD · BOC · Apr 22, 2026 [↗ chart]` with external link to the BOC FX page.
- USD holdings converted at this rate for all CAD aggregates. No per-ticker currency toggle.

## 5. Manual override semantics

Recap from master spec §4.4: only manually-entered values are editable. Imported and priced data is fixed at the source.

## 6. Deferred (design-aware, not implemented in v0.1)

- Mobile-optimized layouts (V3 in wireframes dropped)
- Leverage historical sparkline
- Sector concentration widget
- Family / Parents' view toggle
- Row → cost-basis detail drawer
- Transaction editing
- FX rate history chart
