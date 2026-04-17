# Claude Context — Investments Monitor

## User Profile

- **Role:** Senior IT Consultant (Banking sector), Canadian (Squamish, BC — Pacific Time)
- **Style:** Direct, precise, no softening. Tables and bullet points.
- **Technical level:** Not a developer — use plain language when explaining options.
- **Units:** Metric. Currency: CAD. Tax context: Canadian (ACB, T5008, TFSA, RRSP rules).

## What This Project Is

Consolidated tracker for RRSP, TFSA, unregistered investments, crypto, real estate, and liabilities (HELOC, mortgage). Focus on HELOC leverage analysis and net worth tracking.

## Before Making Changes

1. Read all files in `specs/` — they are authoritative.
2. Read `AGENTS.md` (agent-neutral mirror of this file).

## Deployment — Unresolved Design Tension

The master spec currently mandates **Zero-Cloud Storage** for financial data. This conflicts with the cloud-first workflow goal (mobile-accessible dashboards). See section 4.1 of `specs/investment-asset-monitor-master-specification.md` for the three resolution paths.

**Do not proceed with any cloud deployment work until the user chooses a path.**

## Rules

- Use `decimal.Decimal` for all monetary calculations — never float.
- Do not commit real financial data (actual account balances, positions). Use anonymized or synthetic data in examples.
- Respect Canadian tax rules for ACB calculation.
