# Data Pipeline Specification

Covers how data enters the system, how prices are refreshed, and how the public summary is produced.

## 1. Data flow overview

```
Broker CSV exports ──▶ data/imports/*.csv
                                │
                     import parser (Python)
                                │
                                ▼
                     data/portfolio.db  (SQLite, .gitignored)
                          ▲           │
                          │           │
               manual edits           │ on refresh / schedule
                (HELOC, cash,         │
                 property, etc.)      ▼
                          │    yfinance prices ──▶ prices cache
                          │           │
                          │           ▼
                          │     snapshots row written
                          │           │
                          │           ▼
                          │    public/summary.json  (regenerated)
                          │           │
                          │           ▼
                          │     git commit && push (private repo)
                          │           │
                          ▼           ▼
                 Local Streamlit   Streamlit Cloud
                 (full data)       (summary only, password-gated)
```

## 2. Broker CSV import

### 2.1 Questrade (first supported broker)

Build a reusable parser keyed on column-name detection so adding brokers is additive, not forked. Target architecture:

```
scripts/importers/
├── base.py           # BrokerImporter ABC: detect_format(), parse(file) → list[Holding]
├── questrade.py      # QuestradeImporter
└── ibkr.py           # (later)
```

**Workflow:**
1. User drops CSV into `data/imports/questrade_2026-04-23.csv`.
2. User opens Settings → Imports, clicks Import on the row, reviews a preview table (detected asset_class and country per row — user can correct), clicks Confirm.
3. Parser writes/updates rows in `holdings`. Existing rows for the same `(account_id, ticker)` are replaced (ACB from the export is authoritative).
4. Prices fetched immediately for any new tickers.

**Format:** Questrade **Position** CSV (holdings snapshot). Activity CSV (transaction log requiring running-ACB rollup) is deferred to v1.

**Questrade-specific mapping: pending a sample export file.** The user will provide a real Questrade CSV; the parser's column map will be defined from that. Target fields to extract per row: account type, ticker (normalized to Yahoo format, e.g. `RY` → `RY.TO`), quantity, average cost (ACB per share), currency.

### 2.2 IBKR (deferred)

Same base class, separate column map. Build only after Questrade parser is solid.

### 2.3 Asset class + country defaults at import

| Heuristic | Default | User can override |
|---|---|---|
| Ticker ends with `.TO` / `.V` | `country=CA`, `currency=CAD` | yes |
| Crypto pair (`BTC-CAD`, `ETH-CAD`, etc.) | `asset_class=Crypto`, `country=Other` | yes |
| Ticker in known leveraged-ETF list (HSU.TO, TQQQ, UPRO, ...) | `asset_class=LeveragedETF` | yes |
| Ticker in known ETF list (XIU.TO, VFV.TO, XEQT.TO, ...) | `asset_class=ETF` | yes |
| Fallback | `asset_class=Stock`, `country=US`, `currency=USD` | yes |

Known-ETF list lives in `scripts/importers/etf_tickers.py`, hand-curated, editable.

## 3. Price refresh

- Library: `yfinance` (wrapped with retry + 15-min in-memory cache).
- Called for union of held tickers + watchlist tickers.
- Failure handling: if yfinance errors for a ticker, last cached price is retained and the UI shows a "stale" badge on the KPI strip.
- Crypto uses Yahoo pairs in CAD (`BTC-CAD`, `ETH-CAD`) — no secondary API needed.

## 4. FX

- Source: Bank of Canada Valet — `https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json`.
- Fetched once per day. Cached in `settings` table.
- Failure: retain last good rate, surface stale badge (same pattern as yfinance).
- No historical FX in v0.1.

## 5. Scheduler (macOS `launchd`)

### 5.1 Job definition

File: `scripts/com.investments-monitor.refresh.plist` → installed into `~/Library/LaunchAgents/`.

- **Trigger:** Hourly during NA market hours (9:30 am – 4:00 pm ET, Mon–Fri) + one post-close run. Exact cadence configurable via Settings (default 4h during market hours, 1x post-close).
- **Command:** `python -m scripts.refresh` from repo root.

### 5.2 What `refresh.py` does

1. Load settings.
2. Fetch yfinance prices for all held + watchlist tickers; update `prices` cache.
3. Fetch BOC FX rate if stale.
4. Compute portfolio totals, leverage ratio, allocations.
5. Write a row to `snapshots`.
6. Regenerate `public/summary.json` per the master-spec §4.2 schema. **No dollar totals.**
7. `git add public/summary.json && git commit -m "data: refresh summary $(date -Iseconds)" && git push` to the **private** repo.
8. Log to `scripts/refresh.log` (size-capped).

### 5.3 Failure modes

- No network: log error, exit 0 (don't retry-storm).
- yfinance returns partial: write what we have, mark others stale.
- Git push conflict: `git pull --rebase` then retry once; if still failing, log and exit.

## 6. Deployment

### 6.1 Local

- `streamlit run app/main.py` — reads `data/portfolio.db` directly.
- Protected by the password gate in Module 2 §G.

### 6.2 Streamlit Community Cloud (summary only)

- App reads `public/summary.json` instead of the SQLite DB. Data-source resolution is an env flag (`IM_DATA_SOURCE=local|cloud`) set per deployment.
- Streamlit Cloud password enabled via the platform's native secret.
- Only the screens/widgets that can render from the summary payload are available: Cockpit (allocation + ratios only), Watchlist summary, and a read-only stale-safe banner. Holdings, HELOC ledger, Net Worth ledger, and Settings return "Not available in cloud view — open local app."

## 7. Testing data

For development without real exports:
- `scripts/fixtures/mock_questrade.csv` — committed sample export with fake holdings.
- `scripts/fixtures/seed.py` — writes a fresh `data/portfolio.db` with the mock data for smoke testing.

## 8. Open items

- Questrade CSV column mapping — waiting on real export file from user.
- IBKR parser — later.
- Snapshot retention policy (keep N days?) — not urgent; negligible size.
