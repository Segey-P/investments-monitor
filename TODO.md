# Investments Monitor — TODO

## Current state (2026-04-24)
✅ **Phases 1–5a complete.** 

Dashboard + Holdings + Leverage + Net Worth + Settings (local Streamlit app). Cash tracked as individual holdings (ticker='cash'). Live prices (yfinance) + FX (BOC). Password-protected access. **Daily email summary at 12:30 PM PT** with allocations, top 10 holdings (daily % + daily P/L), and all watchlist favorites.

**Phase 5a** (Design v3 improvements): Dashboard KPI rework (Today's Δ + Biggest mover), Leverage stress test (portfolio drawdown slider), Net Worth redesign (inline editing, privacy legend, slider+input controls).

**Architecture:** Local-only (SQLite on Mac). No cloud, no public view. Privacy-first.

## Status
App is production-ready for personal use. Phase 5a (design improvements) live. Phase 5b (Settings refactor, Holdings column toggle, nav subtitles) deferred. Phase 5c decision gate: continue Streamlit or commit to FastAPI+React v1 re-platform.

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

### UI refinements (2026-04-24) ✅
- [x] Remove watchlist tab entirely (keep watchlist DB for later use in public view)
- [x] Remove watchlist mini from Dashboard
- [x] Remove public view toggle + status display ("Individual · 🔒 Local")
- [x] Hide Streamlit toolbar buttons (deploy, settings, etc.) via CSS
- [x] Remove account count from Holdings tab summary
- [x] Add cash as individual portfolio holdings on import (ticker='cash', price=1.0)
- [x] Skip Yahoo Finance linking for cash ticker (plain text display)
- [x] Skip price fetching for cash entries

### Phase 4 — Daily Email Routine ✅ (2026-04-24)

**Goal:** Daily automated email at 12:30 PM PT with live portfolio data.

- [x] `scripts/email_summary.py` — fetches live prices + FX, generates HTML, sends via SMTP
- [x] `launchd` plist — runs daily at 12:30 PM PT (no terminal needed, Mac just on)
- [x] Email content: allocations (asset class + account) + top 10 holdings (daily % + daily P/L) + all watchlist favorites
- [x] Setup guide: EMAIL-SETUP.md (Gmail app password, launchd install, testing, troubleshooting)
- [x] Daily email live and tested ✅

### Phase 5a — Design v3 KPI / Leverage / Net Worth improvements ✅ (2026-04-24)
- [x] Dashboard KPI rework: Add "Today's Δ" (portfolio daily P&L in $) + "Biggest mover" (largest % change today)
- [x] Leverage: Add portfolio drawdown stress test slider (0–50% market drop scenario)
- [x] Net Worth: Redesign ledger with ASSETS/LIABILITIES sections (per v3 spec)
- [x] Net Worth: Inline number inputs for Cash, Property value, Mortgage balance
- [x] Net Worth: Combined slider + number input for Property and Mortgage (no ceiling limit)
- [x] Net Worth: Privacy legend badge in panel header when hide-values mode on
- [x] Net Worth: Save button to persist changes to DB (cash_aggregate, property, mortgage tables)

### Phase 5b — Polish / defer gate (Deferred)
Deferred pending decision gate: does Streamlit fidelity hold up, or do we re-platform to FastAPI + React v1?

**If pursuing further Streamlit improvements:**
- [ ] Settings refactor: One "Save changes" button per section (Security, Borrowing, Refresh, FX, Imports, About)
- [ ] Holdings column visibility toggle ("Columns ▾" button to hide/show optional columns)
- [ ] Nav screen subtitles (active tab shows one-liner description) — requires custom CSS nav

**If committed to v1 re-platform (FastAPI + React):**
- [ ] Watchlist screen rebuild in React (with taller sparkbar, gap % color-coding)
- [ ] Nav bar with subtitles (React component, trivial)
- [ ] Exact design fidelity (pixel-perfect match to v3 prototype)

**Standing tasks (independent of v1/v0.1 decision):**
- [ ] CSV import for IBKR (blocked on real Questrade CSV test)
- [ ] FX rate history + BOC chart link
- [ ] Snapshot retention policy
- [ ] Claude Code daily-routine documentation

## Future Enhancements (v0.2+)

- [ ] CSV import for IBKR (Interactive Brokers)
- [ ] Historical snapshots + trend analysis
- [ ] Mobile app (Claude mobile + API)
- [ ] Slack/Discord webhook option for daily summary
- [ ] More email customization (frequency, recipients, format)
- [ ] Tax lot tracking + ACB detail view
- [ ] Sector concentration analytics

## Blocked on user
- [ ] Real Questrade CSV export (optional — current parser working with test data)
