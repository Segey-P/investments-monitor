# Investments Monitor — TODO

## Current state (2026-04-24)
Phases 1–3 complete. Dashboard + Holdings + Leverage + Net Worth tabs redesigned per user feedback. Holdings: Day % column, smart decimal formatting. Leverage: simplified tiles, What-if scenario tab, borrowing settings co-located. Net Worth: mortgage + property removed, fully flexible manual assets/liabilities with add/edit/delete, 4-tile KPI strip (removed Mortgage LTV). Settings: borrowing moved to Leverage, public summary removed, imports simplified.

## Top tasks (next)
- [ ] watchilist - remove from cockpit only keep on public view
- [ ] allow switching the categorization of the pie chart in the public view the same way as it is in cockpit
- [ ] remove 'cash' asset from net worth tab. I can add it manually if needed
- [ ] remove 'stale' column from watchlist
- [ ] test if the new upload of investment summary will fully update the data (need to clean previous accounts and ticker and upload new)
- [ ]  **Phase 4 — Path C web deploy** (after tab reviews land)

---

## Phase Breakdown

### Phase 1 — Data backbone (local only, no auth) ✅
- [x] Scaffold `app/`, `scripts/`, `data/` layout; add `.gitignore` for `data/`
- [x] SQLite schema per Module 1 §2: `accounts`, `holdings`, `prices`, `heloc_draws`, `heloc_account`, `margin_account`, `cash_aggregate`, `property`, `mortgage`, `watchlist`, `imports`, `settings`, `snapshots`
- [x] Seed script with mock Questrade-shaped CSV fixture
- [x] `BrokerImporter` base + `QuestradeImporter` stub (final wiring blocked on real export)
- [x] yfinance wrapper with cache + retry (TTL dropped to 60s for live-ish dashboard)
- [x] BOC FX fetch (cached daily)
- [x] Streamlit app skeleton (V2 dark palette, top nav, account pills, KPI strip)
- [x] Dashboard reading live data (was "Cockpit" — renamed)

### Phase 2 — Holdings + Leverage + calculations ✅
- [x] Holdings screen (sortable, filterable, CAD conversion for USD tickers)
- [x] Leverage screen (HELOC + Margin tabs): drawdown ledger, balance forms, KPIs, what-if slider
- [x] Leverage ratio (incl. margin), unrealized P/L, D/E (incl. margin), LTV calcs
- [x] Asset-class tagging during import + user review
- [x] Multi-dim allocation widget (asset class / country / currency — account dropped per design)
- [x] Manual-entry forms: HELOC, margin, cash, property, mortgage

### Phase 3 — Watchlist + Net Worth + Settings ✅
- [x] Watchlist screen with target vs current, favorites pin
- [x] Net Worth screen: ledger + D/E gauge + stacked bars
- [x] Settings screen: password, session timeout, HELOC + margin borrowing settings, refresh interval, FX display, imports list, regenerate summary button
- [x] Auth + session timeout with 60-second warning banner
- [x] Colorblind-safe P/L treatment applied globally

### Dashboard feedback pass (2026-04-23) ✅
- [x] Rename Cockpit → Dashboard (file + tab label)
- [x] FX rate hyperlink to `ca.finance.yahoo.com/quote/CAD=X/`; drop "BOC" mention; keep date
- [x] "Unreg" → "Non-Reg" UI label (DB value unchanged)
- [x] Leverage ratio disclaimer: empty when safe, shown for caution / high
- [x] App-wide "G/L" → "P/L" rename (calcs field, view labels)
- [x] Remove "Monthly HELOC Interest" KPI tile
- [x] Top holdings as full table (Ticker · Acct · Mkt Value · Today · P/L · % Port); tickers hyperlinked to Yahoo
- [x] Daily change column live from Yahoo (60s cache)
- [x] Allocation widget: drop "By Account" dimension; remove table beneath chart
- [x] Watchlist mini on Dashboard (top 5 favorites); favorite toggle in Watchlist tab edit form
- [x] Yahoo ticker hyperlinks shared via `theme.yahoo_link()` (used in Dashboard, Holdings, Watchlist)

### Phase 4 — Path C deploy (pending)
- [ ] `scripts/refresh.py` — full refresh + summary regen + `git push`
- [ ] `launchd` plist + install docs
- [ ] `public/summary.json` generator matching master-spec §4.2 schema exactly
- [ ] Streamlit Cloud deployment reading summary only (env flag `IM_DATA_SOURCE=cloud`)
- [ ] Password on Streamlit Cloud
- [ ] Login screen pre-auth public summary
- [ ] Smoke test: Mac-off scenario (stale banner appears in cloud)

### Phase 5 — Polish / defer gate
Decision gate: does Streamlit fidelity hold up, or do we re-platform to FastAPI + React?
- [ ] CSV import for IBKR
- [ ] FX rate current + link to BOC chart
- [ ] Snapshot retention policy
- [ ] Claude Code daily-routine documentation

## Blocked on user
- [ ] Real Questrade CSV export — required to finalize the import parser's column map
