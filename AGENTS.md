# Agent Context — Investments Monitor

See `/AI_workspace/AGENTS.md` for workspace-level context. See `specs/` for full specifications.

## What This Project Is

Consolidated tracker for RRSP, TFSA, unregistered investments, crypto, real estate, and liabilities (HELOC, mortgage). Focus on HELOC leverage analysis and net worth tracking. Canadian context (ACB calculation, tax treatment).

## Deployment — Unresolved Design Tension

The master spec currently mandates **Zero-Cloud Storage** for financial data. This conflicts with the cloud-first workflow goal (mobile-accessible dashboards). See section 4.1 of `specs/investment-asset-monitor-master-specification.md` for the three resolution paths.

**Do not proceed with any cloud deployment work until the user chooses a path.**

## Rules

1. Read all files in `specs/` before making changes.
2. Use `decimal.Decimal` for all monetary calculations — never float.
3. Do not commit financial data (real account balances, positions) to this repo. Use anonymized or synthetic data in examples.
4. Respect Canadian tax rules for ACB calculation.
