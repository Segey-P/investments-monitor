# Module 1: Investment & Leverage Engine Specification

## 1. Objective

Manage core investment data, compute portfolio metrics, and track HELOC-leveraged positions.

## 2. Data model (SQLite)

Single-user. Schema keeps a `portfolio_id` column on relevant tables as a forward hook for future multi-profile support (Family / Parents') — default value `'self'` in v0.1.

### `accounts`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| portfolio_id | TEXT | default `'self'` |
| account_type | TEXT | Enum: `RRSP` / `TFSA` / `Unreg` / `Crypto`. `Unreg` rendered as "Unregistered" in UI. |
| broker | TEXT | e.g. `Questrade` / `IBKR` |
| label | TEXT | user-friendly name (disambiguates multiple accounts of the same type) |

### `holdings`
One row per position per account. Updated by CSV import; ACB is manual (present in the import file or entered during import review).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| account_id | INTEGER FK → accounts.id | |
| ticker | TEXT | Yahoo-compatible (e.g. `RY.TO`, `MSFT`, `BTC-CAD`) |
| quantity | REAL | |
| acb_per_share | REAL | in the ticker's native currency |
| currency | TEXT | Enum: `CAD` / `USD` |
| asset_class | TEXT | Enum: `Cash` / `Stock` / `ETF` / `LeveragedETF` / `Crypto` |
| country | TEXT | Enum: `CA` / `US` / `Other`. Default `CA` for `.TO`/`.V` tickers, `US` otherwise. User can override. |
| as_of | TIMESTAMP | import timestamp |

Index: `(account_id, ticker)` unique — import replaces existing row for the same pair.

### `prices` (cache)
| Column | Type | Notes |
|---|---|---|
| ticker | TEXT PK | |
| price | REAL | in native currency |
| prev_close | REAL | previous session close in native currency (drives "Today %" column) |
| fetched_at | TIMESTAMP | 15-min cache for Streamlit; refreshed fully by scheduler |
| stale | INTEGER | 0/1 flag; set to 1 after 2 consecutive yfinance failures for this ticker |

### `heloc_draws`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| date | DATE | |
| amount_cad | REAL | positive = draw, negative = repayment |
| purpose | TEXT | free-text, for user's records only |

### `heloc_account`
Single-row table.
| Column | Type | Notes |
|---|---|---|
| limit_cad | REAL | e.g. 150000 |
| rate_pct | REAL | annual, e.g. 6.95 |
| util_warn_pct | REAL | utilization warning threshold, default 80 |

### `margin_account`
Single-row table. Balance-only (no drawdown ledger).
| Column | Type | Notes |
|---|---|---|
| broker | TEXT | e.g. `Questrade` |
| balance_cad | REAL | current balance |
| limit_cad | REAL | approved limit |
| rate_pct | REAL | annual |
| call_threshold_pct | REAL | broker call threshold as equity fraction, default 70 |
| warn_buffer_pct | REAL | in-app warning banner threshold as buffer fraction, default 50 |

### `cash_aggregate`
Single-row table.
| Column | Type | Notes |
|---|---|---|
| balance_cad | REAL | aggregate across all accounts; user-maintained |

### `property`
Single-row table. Manual entry.
| Column | Type | Notes |
|---|---|---|
| value_cad | REAL | user estimate |
| as_of | TIMESTAMP | last manual update |

### `mortgage`
Single-row table. Manual entry.
| Column | Type | Notes |
|---|---|---|
| balance_cad | REAL | current balance |
| rate_pct | REAL | annual |
| renewal_date | DATE | |
| lender | TEXT | free-text |
| as_of | TIMESTAMP | last manual update |

### `watchlist`
| Column | Type | Notes |
|---|---|---|
| ticker | TEXT PK | |
| target_price | REAL | user-set limit, native currency |
| notes | TEXT | free-text |

### `imports`
Log of broker CSV imports. Drives the Settings → Imports list.
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| filename | TEXT | relative to `data/imports/` |
| broker | TEXT | e.g. `Questrade` |
| account_id | INTEGER FK → accounts.id | |
| rows | INTEGER | rows written/updated in `holdings` |
| imported_at | TIMESTAMP | |

### `settings`
Key-value. Holds password hash, session-timeout minutes, refresh interval, last FX rate + timestamp, stale-banner threshold. (Borrowing settings live on `heloc_account` / `margin_account`; borrowing rates no longer stored here.)

### `snapshots`
Point-in-time rollups. PK is `date`; scheduler UPSERTs on each run so the last run of a given day wins. Stores CAD totals (never served to cloud; used for local historical view only if needed later).
| Column | Type |
|---|---|
| date | DATE PK |
| net_worth_cad | REAL |
| portfolio_cad | REAL |
| heloc_drawn_cad | REAL |
| margin_balance_cad | REAL |
| leverage_ratio | REAL |

## 3. Functional Requirements

### A. Account Management

- Account types: DB values `RRSP` / `TFSA` / `Unreg` / `Crypto`. `Unreg` is rendered as "Unregistered" in the UI. Fixed enum in v0.1.
- Multiple accounts of the same type supported (e.g., two RRSPs at different brokers); disambiguated by `label`.
- Multi-profile (Family / Parents') **deferred**. Schema retains `portfolio_id` for future use.

### B. Asset Tracking

- **Equity / ETF / Crypto:** Treated uniformly — ticker, quantity, ACB. Populated via broker CSV import (see `specs/data-pipeline.md`). Prices fetched from yfinance.
- **Cash:** **Aggregate single balance**, manually entered. Per-account cash tracking deferred.
- **Asset class tagging:** `Cash`, `Stock`, `ETF`, `LeveragedETF`, `Crypto`. Tagged at import; user reviews and corrects in the Holdings screen. Used for the Asset-class allocation view.
- **Country / currency tagging:** `country` and `currency` fields enable By-Country and By-Currency allocation views. Country defaulted by ticker suffix at import; overridable.

### C. Leverage: HELOC + Margin

Two borrowing sources are tracked independently but contribute to the same leverage formulas.

- **HELOC:** dedicated drawdown ledger (date + amount + free-text purpose). No tax-deductibility flag.
- **Margin:** single current balance, manually updated. No drawdown ledger.
- **Leverage Ratio** = `Portfolio CAD / (Portfolio CAD − HELOC drawn CAD − Margin balance CAD)`. Displayed as gauge and KPI. Zones: Safe 0–1.5×, Caution 1.5–2×, High 2×+.
- **Margin buffer** = `(unreg account value − Margin balance) / unreg account value`. Warning banner when `buffer < warn_buffer_pct/100` (default 50%).
- **What-if slider (HELOC):** Simulate drawing an additional amount; recompute leverage ratio and monthly interest in-session only (no DB write).
- **Monthly interest** = `drawn × (rate_pct / 100) / 12`, computed separately for HELOC and margin. Displayed, not stored per period.
- **Tax-deductibility calculations are explicitly out of scope.** User handles tax treatment externally.

## 4. Analytics & Breakdowns

- Allocation dimensions (four): by account, by asset class, by country, by currency. UI selector switches between them on a single widget. Sector concentration deferred.
- Total Unrealized Gain/Loss = `Σ (quantity × (current_price − acb_per_share) × fx_to_cad)`.
- YTD return as proportion (for public summary).
- All totals in CAD. USD holdings converted at BOC daily rate.

## 5. Refresh behaviour

- **Manual:** "Refresh prices" button in the app — re-fetches yfinance for all held + watchlist tickers, updates `prices` cache, regenerates public summary.
- **Scheduled:** `launchd` job every 4–6h during TSX/NYSE market hours. Writes `snapshots` row + regenerates `public/summary.json` + `git commit && push` so Streamlit Cloud picks up the fresh summary.
- If Mac is off: summary goes stale. Acceptable.

## 6. Deferred

- Sector concentration
- Multi-profile / Family
- Transaction log, tax-lot editing, cost-basis detail drawer
- Leverage historical sparkline
- Per-account cash balances
- HELOC tax-deductibility (permanently out of scope per user)
