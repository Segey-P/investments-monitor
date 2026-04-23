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
| account_type | TEXT | `RRSP` / `TFSA` / `Unreg` / `Crypto` |
| broker | TEXT | e.g. `Questrade` / `IBKR` |
| label | TEXT | user-friendly name |

### `holdings`
One row per position per account. Updated by CSV import; ACB is manual (present in the import file or entered during import review).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| account_id | INTEGER FK | |
| ticker | TEXT | Yahoo-compatible (e.g. `RY.TO`, `MSFT`, `BTC-CAD`) |
| quantity | REAL | |
| acb_per_share | REAL | in the ticker's native currency |
| currency | TEXT | `CAD` or `USD` |
| asset_class | TEXT | `Cash` / `Stock` / `ETF` / `LeveragedETF` / `Crypto` |
| country | TEXT | ISO-2, user-tagged at import (default `CA` for `.TO` tickers, `US` otherwise) |
| as_of | TIMESTAMP | import timestamp |

### `prices` (cache)
| Column | Type | Notes |
|---|---|---|
| ticker | TEXT PK | |
| price | REAL | in native currency |
| fetched_at | TIMESTAMP | 15-min cache for Streamlit; refreshed fully by scheduler |

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

### `cash_aggregate`
Single-row table.
| Column | Type | Notes |
|---|---|---|
| balance_cad | REAL | aggregate across all accounts; user-maintained |

### `property` / `mortgage`
Single-row each. See Module 2.

### `watchlist`
| Column | Type | Notes |
|---|---|---|
| ticker | TEXT PK | |
| target_price | REAL | user-set limit |
| notes | TEXT | free-text |

### `settings`
Key-value. Holds password hash, session-timeout minutes, HELOC rate, refresh interval, last FX rate + timestamp.

### `snapshots`
Daily point-in-time rollups written by the scheduler. Stores CAD totals (never served to cloud; used for local historical view only if needed later).
| Column | Type |
|---|---|
| date | DATE PK |
| net_worth_cad | REAL |
| portfolio_cad | REAL |
| heloc_drawn_cad | REAL |
| leverage_ratio | REAL |

## 3. Functional Requirements

### A. Account Management

- Account types: **RRSP, TFSA, Unregistered, Crypto**. Fixed enum in v0.1.
- Multiple accounts of the same type supported (e.g., two RRSPs at different brokers).
- Multi-profile (Family / Parents') **deferred**. Schema retains `portfolio_id` for future use.

### B. Asset Tracking

- **Equity / ETF / Crypto:** Treated uniformly — ticker, quantity, ACB. Populated via broker CSV import (see `specs/data-pipeline.md`). Prices fetched from yfinance.
- **Cash:** **Aggregate single balance**, manually entered. Per-account cash tracking deferred.
- **Asset class tagging:** `Cash`, `Stock`, `ETF`, `LeveragedETF`, `Crypto`. Tagged at import; user reviews and corrects in the Holdings screen. Used for the Asset-class allocation view.
- **Country / currency tagging:** `country` and `currency` fields enable By-Country and By-Currency allocation views. Country defaulted by ticker suffix at import; overridable.

### C. Leverage & HELOC Integration

- Dedicated ledger: date + amount (positive draw, negative repayment) + free-text purpose. No tax-deductibility flag.
- **Leverage Ratio** = `(HELOC drawn CAD) / (Portfolio value CAD − HELOC drawn CAD)`. Displayed as gauge and KPI. Zones: Safe 0–1.5×, Caution 1.5–2×, High 2×+.
- **What-if slider:** Simulate drawing an additional amount; recompute leverage ratio and monthly interest in-session only (no DB write).
- **Monthly interest** = `drawn × rate / 12`. Displayed, not stored per period.
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
