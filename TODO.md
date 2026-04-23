# Investments Monitor — TODO

## Top 10 Prioritized Tasks
1. [ ] **Scaffold Layout:** Create `app/`, `scripts/`, `data/` and setup `.gitignore`
2. [ ] **SQLite Schema:** Implement Module 1 §2 schema (accounts, holdings, heloc, etc.)
3. [ ] **Seed Data:** Create seed script with mock Questrade-shaped CSV fixture
4. [ ] **Broker Importers:** Build `BrokerImporter` base and `QuestradeImporter` stub
5. [ ] **Market Data:** Implement `yfinance` wrapper with caching and BOC FX fetch
6. [ ] **UI Skeleton:** Build Streamlit skeleton (V2 dark palette, nav, account pills)
7. [ ] **Cockpit Screen:** Connect "Cockpit" to live SQLite data (no auth yet)
8. [ ] **Holdings Screen:** Implement holdings view with CAD conversion for USD tickers
9. [ ] **Deployment Prep:** Develop `scripts/refresh.py` for summary regeneration
10. [ ] **Public Summary:** Implement `public/summary.json` generator for Path C deployment

---

## Phase Breakdown

### Phase 1 — Data backbone (local only, no auth)
- [ ] Scaffold `app/`, `scripts/`, `data/` layout; add `.gitignore` for `data/`
- [ ] SQLite schema per Module 1 §2: `accounts`, `holdings`, `prices`, `heloc_draws`, `heloc_account`, `cash_aggregate`, `property`, `mortgage`, `watchlist`, `settings`, `snapshots`
- [ ] Seed script with mock Questrade-shaped CSV fixture
- [ ] `BrokerImporter` base + `QuestradeImporter` stub (fully wire after user provides real export)
- [ ] yfinance wrapper with 15-min cache + retry
- [ ] BOC FX fetch (cached daily)
- [ ] Streamlit app skeleton (V2 dark palette, top nav, account pills, KPI strip)
- [ ] Cockpit screen reading live data (no auth yet)

### Phase 2 — Holdings + HELOC + calculations
- [ ] Holdings screen (sortable, filterable, CAD conversion for USD tickers)
- [ ] HELOC screen: drawdown ledger, KPIs, what-if slider
- [ ] Leverage ratio, unrealized G/L, D/E, LTV calcs
- [ ] Asset-class tagging during import + user review
- [ ] Multi-dim allocation widget (account / asset class / country / currency)
- [ ] Manual-entry forms: HELOC, cash, property, mortgage

### Phase 3 — Watchlist + Net Worth + Settings
- [ ] Watchlist screen with target vs current, 52-wk range, vol badge
- [ ] Net Worth screen: ledger + D/E gauge + stacked bars
- [ ] Settings screen: password, session timeout, HELOC rate, refresh interval, FX display, imports list, regenerate summary button
- [ ] Auth + session timeout with 60-second warning banner
- [ ] Colorblind-safe G/L treatment applied globally

### Phase 4 — Path C deploy
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
- [ ] Claude Code daily-routine documentation (how to run common analysis prompts against local SQLite)

## Blocked on user
- [ ] Real Questrade CSV export — required to finalize the import parser's column map
