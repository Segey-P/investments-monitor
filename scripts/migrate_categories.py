"""Migrate existing holdings by categorizing them based on known lists."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db import init_db
from scripts.importers.etf_tickers import CASH_TICKERS, DIVIDEND_TICKERS, GROWTH_TICKERS


def categorize(ticker: str, asset_class: str) -> str:
    t = ticker.upper()
    if t in CASH_TICKERS or asset_class == "Cash":
        return "Cash"
    if t in DIVIDEND_TICKERS:
        return "Dividend"
    if t in GROWTH_TICKERS:
        return "Growth"
    return "Other"


def main() -> None:
    conn = init_db()
    rows = conn.execute("SELECT id, ticker, asset_class FROM holdings WHERE category = 'Other'").fetchall()

    for row in rows:
        cat = categorize(row["ticker"], row["asset_class"])
        if cat != "Other":
            conn.execute(
                "UPDATE holdings SET category = ? WHERE id = ?",
                (cat, row["id"]),
            )

    conn.commit()
    updated = conn.execute(
        "SELECT COUNT(*) as cnt FROM holdings WHERE category != 'Other'"
    ).fetchone()["cnt"]
    print(f"✓ Categorized {updated} holdings.")


if __name__ == "__main__":
    main()
