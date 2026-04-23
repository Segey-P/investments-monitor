# Module 2: Dashboard & Asset Manager Specification

## 1. Objective

Provide the user-facing views for monitoring, plus management of non-market assets (property, mortgage). Visual language follows **V2 "Dark Command Strip"** (Linear-inspired dark palette), applied consistently across all screens.

## 2. Screens

### A. Cockpit (landing)

- **Top nav:** Cockpit · Holdings · Leverage · Net Worth · Watchlist · Settings. Right side: portfolio scope label (v0.1 always "Individual"), cloud-privacy indicator (☁ Public / 🔒 Local).
- **Account-scope pills:** All · RRSP · TFSA · Unregistered · Crypto.
- **KPI strip (6 tiles):** Net Worth · Portfolio · Leverage Ratio · HELOC Drawn · Unrealized G/L · Monthly HELOC Interest. Each tile carries a privacy badge.
- **Allocation widget (multi-dim):** Stacked bar + legend. Dropdown toggles the dimension:
  - By Account (RRSP / TFSA / Unreg / Crypto)
  - By Asset Class (Cash / Stock / ETF / LeveragedETF / Crypto)
  - By Country (CA / US / Other)
  - By Currency (CAD / USD)
- **HELOC panel:** Current ratio gauge + what-if slider. No historical sparkline in v0.1.
- **Asset / Liability summary:** Portfolio, Property, Cash, Mortgage, HELOC → Net Worth. Condensed version of the Net Worth screen.
- **Watchlist mini:** 3 nearest-to-target rows with current / target / gap.
- **Top Holdings preview:** Top 4–5 positions by market value. Click → Holdings screen.

### B. Holdings

- Filter pills by account type.
- Sortable columns: Ticker · Name · Acct · Qty · ACB/sh · Mkt Price · Mkt Value · Unrealized G/L · G/L % · % Portfolio · Asset Class.
- Account tag as colored pill.
- USD positions show CAD-converted value as the Mkt Value column (BOC rate). No per-ticker currency toggle.
- Colorblind-safe G/L: ▲ (gain, green `#22c55e`) / ▼ (loss, red `#ef4444`). Shape + color.
- Footer summary bar: Total Portfolio · Unrealized G/L · Position count · Account count.
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
