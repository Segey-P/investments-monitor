"""Persist ParseResult to the database."""
from __future__ import annotations

from pathlib import Path

from .base import ParseResult


class FileAlreadyImported(Exception):
    """Raised when the file has already been imported."""
    def __init__(self, filename: str, imported_at: str):
        self.filename = filename
        self.imported_at = imported_at
        super().__init__(f"File '{filename}' already imported on {imported_at}")


def persist_result(conn, path: Path, result: ParseResult) -> dict:
    """Write ParseResult to the database.

    Args:
        conn: SQLite connection
        path: Path to the source file (name is logged in imports table)
        result: ParseResult from an importer

    Returns:
        Dict with keys: accounts, holdings, cash_total

    Raises:
        FileAlreadyImported: if the filename is already in the imports table
    """
    existing = conn.execute(
        "SELECT imported_at FROM imports WHERE filename = ?",
        (path.name,),
    ).fetchone()
    if existing:
        raise FileAlreadyImported(path.name, existing["imported_at"])

    def _upsert_account(broker: str, acct_type: str, label: str) -> int:
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

    def _upsert_holding(account_id: int, h) -> None:
        conn.execute(
            """
            INSERT INTO holdings (account_id, ticker, yahoo_ticker, currency, quantity,
                                  acb_per_share, asset_class, category, country, description, as_of)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(account_id, ticker, currency) DO UPDATE SET
              yahoo_ticker = excluded.yahoo_ticker,
              quantity     = excluded.quantity,
              acb_per_share= excluded.acb_per_share,
              asset_class  = excluded.asset_class,
              category     = excluded.category,
              country      = excluded.country,
              description  = excluded.description,
              as_of        = CURRENT_TIMESTAMP
            """,
            (account_id, h.ticker, h.yahoo_ticker, h.currency, h.quantity,
             h.acb_per_share, h.asset_class, h.category, h.country, h.description),
        )

    with conn:
        acct_ids = {}
        for num, acct in result.accounts.items():
            acct_ids[num] = _upsert_account(acct.broker, acct.account_type, acct.label)

        holdings_count = 0
        for h in result.holdings:
            if h.broker_account_number not in acct_ids:
                continue
            _upsert_holding(acct_ids[h.broker_account_number], h)
            holdings_count += 1

        total_cash = sum(a.cash_cad for a in result.accounts.values())
        conn.execute(
            "UPDATE cash_aggregate SET balance_cad = ? WHERE id = 1",
            (total_cash,),
        )

        first_acct_id = next(iter(acct_ids.values())) if acct_ids else None
        conn.execute(
            "INSERT INTO imports (filename, broker, account_id, rows) VALUES (?, ?, ?, ?)",
            (path.name, "Questrade", first_acct_id, holdings_count),
        )

    return {
        "accounts": len(acct_ids),
        "holdings": holdings_count,
        "cash_total": total_cash,
    }
