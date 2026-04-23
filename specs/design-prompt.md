# Design Prompt — Investments Monitor (Second Pass)

Ready-to-paste prompt for Claude (claude.ai → "design" artifact) to produce a
focused second round of visual artifacts. Scope is **locked** — this pass is
about closing specific visual gaps, not re-opening decisions.

Attach the referenced spec files alongside this prompt.

## Prompt

```
Design updated HTML/React prototypes for "Investments Monitor" — a personal
portfolio-monitoring dashboard for a Canadian investor with HELOC-leveraged
positions. This is the SECOND design pass; the first pass produced a wireframe
set (attach `specs/Investments Monitor Wireframes.html`) and core decisions
have been locked.

I am not a developer; prioritize clarity and tight information density.

## Product context (unchanged)
- Single user (me). Canadian tax context: RRSP, TFSA, Unregistered, Crypto.
- HELOC leverage is the differentiator — show leverage ratio + what-if.
- Real estate + mortgage tracked for Net Worth.
- Watchlist of "Potential Buys" with target buy price.

## Decisions locked — do not re-open these

- **Cockpit layout:** V2 "Dark Command Strip" (Linear-style dark palette).
  No Bloomberg sidebar, no light variant, no mobile layout in this pass.
- **Privacy model:** Path C. Cloud summary exposes proportions, ratios,
  tickers, and public prices only. No CAD dollar totals, no quantities,
  no ACB. See master-spec §4.2 for the exact payload schema.
- **HELOC tax-deductibility:** out of scope. User handles tax externally.
  Do NOT include deductible flags, tax-saving widgets, or marginal-rate
  inputs anywhere.
- **Stack:** Streamlit v0.1 → FastAPI+React post-v1. Framework-neutral
  HTML/React mocks are still fine.
- **Storage:** SQLite local, no app-level encryption.
- **Multi-profile (Family/Parents'):** deferred. Do not design a toggle.
- **Sector concentration:** deferred. Do not design a sector widget.
- **Leverage historical sparkline:** deferred. Do not design a trend chart.
- **Detail drawer / cost basis history:** deferred (ACB is entered once).
- **Per-ticker currency toggle:** deferred (all totals in CAD, BOC rate).

## Deliverables (this pass only)

Focused gaps from the first pass. One artifact per screen unless noted.

1. **Holdings — dark re-skin.** First pass was light-themed; re-skin to the
   V2 dark palette used on Cockpit and Net Worth. Columns: Ticker · Name ·
   Account · Qty · ACB/sh · Mkt Price · Mkt Value (CAD) · Unrealized G/L ·
   G/L % · % Portfolio · Asset Class. The asset_class column is NEW —
   values are `Cash` / `Stock` / `ETF` / `LeveragedETF` / `Crypto`.
2. **HELOC & Leverage — dark re-skin.** Re-skin from light to dark. Drop
   the "Interest deductibility summary" panel and any tax-ded ledger
   column; the drawdown ledger is now Date · Amount · Purpose (free-text).
   Keep KPI strip, drawdown ledger, what-if slider.
3. **Watchlist — dark re-skin.** Re-skin from light to dark. Columns
   unchanged: Ticker · Name · Current · Target · Gap % · 52-wk Range · Vol
   · Notes.
4. **Login Gate — dark re-skin.** Re-skin from light to dark. Pre-auth
   public summary card (proportions + leverage ratio) remains visible.
5. **Settings — new detailed design.** First pass has a rough stub; this
   one needs proper IA. Sections:
   - Security: change password, session timeout (min, default 15)
   - HELOC: rate (% p.a.), limit
   - Refresh: scheduled on/off, interval, last refresh timestamp, manual
     "Refresh now" button
   - FX: source (BOC daily, read-only), current rate + fetched timestamp,
     link to BOC chart
   - Imports: list of CSV files in `data/imports/` with per-file Import
     action. Questrade is the first supported broker.
   - Public summary (Path C): path, last regeneration timestamp,
     "Regenerate + push" button
   - About: version, branch, last commit
   Use inline helper text for non-obvious fields (session timeout, HELOC
   rate, refresh interval).
6. **Multi-dim Allocation widget — focused interaction design.** On the
   Cockpit, the allocation widget must switch between four dimensions via
   pills: Account, Asset class, Country, Currency. Show:
   - Active pill state vs inactive
   - The stacked bar + legend updating when dimension changes
   - Suggested animation/transition behaviour (or explicit "no animation,
     snap swap" if that's your recommendation)
   - Color mapping: should colors be stable per category across dimensions,
     or reset per dimension? Recommend one and annotate why.

## Constraints (unchanged)

- Visual style: dark, Linear-style. No gradients, no stock photos.
- Mobile: not in scope for this pass.
- Currency: CAD primary. USD holdings converted at BOC daily rate and
  shown as CAD in all aggregates. Small "USD" tag on the row is fine.
- All numbers: thousands separators + 2 decimals.
- Red/green for G/L must be colorblind-safe (use shape + color).
- No real data — use plausible mock values consistent with first pass
  (~CAD 500k portfolio, ~CAD 150k HELOC, ~CAD 880k property).
- Continue to annotate privacy with ☁ cloud-safe / 🔒 local-only badges
  on every widget, card, and KPI tile.

## Privacy — what the cloud deployment sees

Reference master-spec §4.2. Summary payload contains:
- Ratios: leverage_ratio, heloc_utilization_pct, portfolio_return_ytd_pct,
  debt_to_equity, mortgage_ltv_pct
- Allocations (proportions, not dollars): by_account, by_asset_class,
  by_country, by_currency
- Tickers held + current prices (public market data)
- Watchlist: ticker, current, target, gap_pct

Never cloud-safe: net worth, portfolio value, HELOC drawn, mortgage balance,
property value, unrealized G/L in dollars, quantities, ACB.

Design every screen so widgets clearly indicate which side of the Path C
line they fall on.

## Interactions to prototype (this pass)

- Dimension pills on the allocation widget (see Deliverable 6).
- Session timeout banner: at timeout − 60s, show a dismissable banner
  "Session expires in 60s · [Stay signed in]". Design the banner and the
  expired-state redirect to Login.
- HELOC what-if slider (refine from first pass — tighter feedback between
  slider position and the resulting leverage ratio).
- Settings → "Regenerate + push" button states: idle, working, success,
  error. This is the mechanism that updates the cloud summary.

## Output

One artifact per deliverable. Keep components consistent with first-pass
V2 (same typography, KPI card pattern, privacy badges). Annotate assumptions
inline. If you see a gap in the locked decisions above, flag it as a
comment — do NOT resolve it unilaterally.
```

## Reference docs to attach

| File | Why |
|---|---|
| `specs/investment-asset-monitor-master-specification.md` | Path C payload schema (§4.2), session policy, repo layout |
| `specs/module-1-investment-leverage-engine-specification.md` | SQLite schema, asset_class / country / currency columns |
| `specs/module-2-dashboard-asset-manager-specification.md` | Screen inventory, Settings screen sections |
| `specs/data-pipeline.md` | CSV import flow, refresh schedule, summary regen |
| `specs/Investments Monitor Wireframes.html` | First-pass wireframes (V2 cockpit, current state of other screens) |
| `CLAUDE.md` | User profile, tone, stack |

## First-pass artifacts to treat as context, not to re-design

- Cockpit V2 (dark) — canonical. Do not re-design.
- Net Worth (already dark) — canonical. Do not re-design.

## Guardrail for the designer

If any of the "Decisions locked" section tempts new proposals, flag them as
a question at the top of your output. Do not silently substitute an
alternative. The goal of this pass is to close visual gaps against a fixed
scope, not to re-negotiate it.

## Workflow after the design run

1. Review the returned artifacts against the locked scope.
2. Merge accepted artifacts into `specs/Investments Monitor Wireframes.html`
   (replace the still-light Holdings/HELOC/Watchlist/Login; add Settings
   detail; refine Cockpit allocation widget).
3. Only then start Phase 1 build per `TODO.md`.
