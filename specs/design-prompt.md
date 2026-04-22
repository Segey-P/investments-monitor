# Design Prompt — Investments Monitor

Ready-to-paste prompt for Claude (claude.ai → "design" artifact) to
kick off visual prototypes. Attach the referenced spec files alongside.

## Prompt

```
Design interactive HTML/React prototypes for "Investments Monitor" — a
personal portfolio-monitoring dashboard for a Canadian investor with
HELOC-leveraged positions. I am not a developer; prioritize clarity and
tight information density over flourish.

## Product context
- Single user (me). Canadian tax context: RRSP, TFSA, Unregistered, Crypto.
- HELOC leverage is the differentiator — show debt-to-equity, interest
  expense, and tax-deductibility flag for unregistered accounts.
- Also tracks real estate value and mortgage balance for Net Worth.
- Watchlist of "Potential Buys" with target buy price.

## Deliverables (one artifact per screen)
1. Cockpit (landing): Net Worth, allocation pie, Leverage Ratio gauge,
   portfolio selector (individual account / consolidated / Family).
2. Holdings table: ticker, qty, ACB, market price, unrealized G/L,
   account tag. Sortable, filterable by account type.
3. HELOC & Leverage view: drawdown ledger, interest expense, leverage
   ratio trend, tax-deductible interest summary.
4. Net Worth / Asset-Liability ledger: property + mortgage manual entry,
   household debt-to-equity visualization.
5. Watchlist: target buy price vs current, 52-wk range, volatility badge.
6. Login gate (simple password screen).

## Constraints
- Visual style: clean, data-dense, neutral palette. Think Bloomberg
  terminal meets Linear. No gradients, no stock photos.
- Mobile-aware: cockpit and watchlist must work on phone; detailed
  holdings view can be desktop-first.
- Currency: CAD primary, USD secondary with FX badge.
- All numbers formatted with thousands separators and 2 decimals.
- Red/green for G/L must be colorblind-safe (use shape + color).
- No real data — use plausible mock values (TSX + NYSE tickers,
  ~CAD 500k portfolio, ~CAD 150k HELOC).
- Out of scope for v1 prototypes: transactions, tax-lot editing,
  multi-user, onboarding flow.

## Privacy tension to reflect in the design
There is an unresolved architecture choice (specs §4.1):
- Path A: local-only (Tailscale access)
- Path B: encrypted cloud payload
- Path C: tiered exposure — summary public, details local (recommended)

Design the cockpit so it works under Path C: the summary view must be
meaningful on its own without exposing tickers, quantities, or ACB.
Indicate visually which widgets are "cloud-safe" vs "local-only".

## Interactions to prototype
- Toggle account scope (All / RRSP / TFSA / Unregistered / Crypto).
- Toggle Family vs individual portfolio.
- Click a holding → drawer with cost basis history and position detail.
- HELOC "what-if" slider: show how leverage ratio shifts if I draw
  another $X.

## Output
Produce separate artifacts per screen. Keep components consistent
across screens (same typography, same KPI card pattern). Annotate
assumptions inline.
```

## Reference docs to attach

| File | Why |
|---|---|
| `specs/investment-asset-monitor-master-specification.md` | Architecture + §4.1 privacy tension |
| `specs/module-1-investment-leverage-engine-specification.md` | HELOC mechanics, ACB, leverage ratio definition |
| `specs/module-2-dashboard-asset-manager-specification.md` | Cockpit, watchlist, property/mortgage requirements |
| `CLAUDE.md` | User profile, tone, stack |

## Known tensions the design must navigate

- **Stack mismatch:** master spec says Python/SQLite + Flask/FastAPI;
  `CLAUDE.md` says Streamlit + Streamlit Cloud. Design in
  framework-neutral HTML/React — implementation can pick later.
- **Privacy vs mobile:** §4.1 — design for Path C unless stated otherwise.
- **Canadian specifics:** RRSP/TFSA/Unregistered account types, CAD/USD
  split, HELOC interest tax-deductibility flag.

## Workflow notes

1. Name artifacts after screens so they map 1:1 to future Streamlit pages.
2. Ask for mock data inline — no API wiring in prototypes keeps iteration fast.
3. Require annotated assumptions — forces explicit decisions to approve/reject.
4. No premature abstractions — prototype each screen concretely before
   extracting a component library.
5. After prototypes are approved, add "Design approved — implement cockpit"
   to `TODO.md` so the Project Hub picks it up.
