"""CLI: import a Questrade Investment Summary XLSX into portfolio.db.

Usage:
    .venv/bin/python -m scripts.import_questrade <path/to/file.xlsx>
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root on path so `app` and `scripts` imports work when run as a module.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db import init_db  # noqa: E402
from scripts.importers.questrade import QuestradeImporter  # noqa: E402


def _upsert_account(conn, broker: str, acct_type: str, label: str) -> int:
    row = conn.execute(
        "SELECT id FROM accounts WHERE broker = ? AND label = ?",
        (broker, label),
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO accounts (portfolio_id, account_type, broker, label) VALUES ('self', ?, ?, ?)",
        (acct_type, broker, label),
    )
    return cur.lastrowid


def _upsert_holding(conn, account_id: int, h) -> None:
    conn.execute(
        """
        INSERT INTO holdings (account_id, ticker, yahoo_ticker, currency, quantity,
                              acb_per_share, asset_class, country, description, as_of)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(account_id, ticker, currency) DO UPDATE SET
          yahoo_ticker = excluded.yahoo_ticker,
          quantity     = excluded.quantity,
          acb_per_share= excluded.acb_per_share,
          asset_class  = excluded.asset_class,
          country      = excluded.country,
          description  = excluded.description,
          as_of        = CURRENT_TIMESTAMP
        """,
        (account_id, h.ticker, h.yahoo_ticker, h.currency, h.quantity,
         h.acb_per_share, h.asset_class, h.country, h.description),
    )


def main(path: Path) -> None:
    if not path.exists():
        sys.exit(f"File not found: {path}")

    conn = init_db()
    existing = conn.execute("SELECT filename FROM imports WHERE filename = ?", (path.name,)).fetchone()
    if existing:
        sys.exit(f"File '{path.name}' has already been imported. Skipping.")

    importer = QuestradeImporter()
    if not importer.detect_format(path):
        print(f"warning: filename does not look like Questrade — continuing anyway.")
    parsed = importer.parse(path)

    with conn:
        acct_ids = {}
        for num, acct in parsed.accounts.items():
            acct_ids[num] = _upsert_account(conn, acct.broker, acct.account_type, acct.label)

        for h in parsed.holdings:
            if h.broker_account_number not in acct_ids:
                print(f"  skip {h.ticker}: unknown account {h.broker_account_number}")
                continue
            _upsert_holding(conn, acct_ids[h.broker_account_number], h)

        total_cash = sum(a.cash_cad for a in parsed.accounts.values())
        conn.execute(
            "UPDATE cash_aggregate SET balance_cad = ? WHERE id = 1",
            (total_cash,),
        )

        # Log the import
        first_acct_id = next(iter(acct_ids.values())) if acct_ids else None
        conn.execute(
            "INSERT INTO imports (filename, broker, account_id, rows) VALUES (?, ?, ?, ?)",
            (path.name, "Questrade", first_acct_id, len(parsed.holdings)),
        )

    print(f"Imported {len(parsed.holdings)} holdings across {len(parsed.accounts)} accounts.")
    print(f"Cash aggregate set to ${total_cash:,.2f} CAD.")
    print(f"DB: {conn.execute('PRAGMA database_list').fetchone()['file']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m scripts.import_questrade <file.xlsx>")
    main(Path(sys.argv[1]))
