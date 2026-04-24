#!/usr/bin/env python3
"""Generate public/summary.json from local portfolio.db for cloud deployment.
Fetches live prices, computes allocations + ratios, commits + pushes."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import calcs, prices
from app.db import init_db
from app.fx import get_usdcad

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "refresh.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def generate_summary(conn) -> dict:
    """Generate public summary payload matching spec §4.2."""
    logger.info("Loading holdings and computing allocations...")
    holdings_all = calcs.load_holdings(conn)
    fx = get_usdcad(conn)

    # Fetch live prices
    logger.info("Fetching live prices...")
    try:
        tickers = sorted({h.yahoo_ticker for h in holdings_all if h.ticker != "cash"})
        quotes = prices.get_quotes(tickers)
        prices.persist_quotes(conn, quotes)
        holdings_all = calcs.load_holdings(conn)
    except Exception as e:
        logger.warning(f"Price fetch failed: {e}. Using cached prices.")

    # Allocations
    allocs = calcs.allocations(holdings_all, fx.rate)
    port = calcs.summarize(holdings_all, fx.rate)
    unreg_value = calcs.summarize(
        [h for h in holdings_all if h.account_type == "Unreg"], fx.rate
    ).portfolio_cad
    lev = calcs.leverage(conn, port.portfolio_cad, unreg_value)
    nw = calcs.net_worth(conn, port.portfolio_cad)

    # Build tickers list (exclude cash)
    tickers_held = sorted({h.ticker for h in holdings_all if h.ticker != "cash"})

    # Build prices dict (fresh from DB)
    price_rows = conn.execute(
        "SELECT ticker, price FROM prices WHERE ticker IN ({})".format(
            ",".join("?" * len(tickers_held)) if tickers_held else "NULL"
        ),
        list(tickers_held) if tickers_held else [],
    ).fetchall()
    prices_dict = {r["ticker"]: r["price"] for r in price_rows if r["price"] is not None}

    # Watchlist favorites
    watchlist_rows = conn.execute(
        """SELECT w.ticker, p.price, w.target_price
           FROM watchlist w
           LEFT JOIN prices p ON p.ticker = w.ticker
           WHERE w.is_favorite = 1
           ORDER BY w.ticker LIMIT 10"""
    ).fetchall()
    watchlist_items = []
    for r in watchlist_rows:
        ticker = r["ticker"]
        current = r["price"]
        target = r["target_price"]
        if current and target:
            gap_pct = (current - target) / target
            watchlist_items.append({
                "ticker": ticker,
                "current": round(current, 2),
                "target": round(target, 2),
                "gap_pct": round(gap_pct, 4),
            })

    # Ratios
    ytd_return = (port.unrealized_pl_cad / port.portfolio_cad * 100) if port.portfolio_cad else 0

    return {
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ratios": {
            "leverage_ratio": round(lev.leverage_ratio, 2),
            "heloc_utilization_pct": round(lev.heloc_util_pct, 4),
            "portfolio_return_ytd_pct": round(ytd_return, 4),
            "debt_to_equity": round(nw.debt_to_equity, 4),
            "mortgage_ltv": round(nw.mortgage_ltv, 4),
        },
        "allocations": {
            "by_account": {k: round(v, 4) for k, v in allocs["by_account"].items()},
            "by_asset_class": {k: round(v, 4) for k, v in allocs["by_asset_class"].items()},
            "by_country": {k: round(v, 4) for k, v in allocs["by_country"].items()},
            "by_currency": {k: round(v, 4) for k, v in allocs["by_currency"].items()},
        },
        "tickers_held": list(tickers_held),
        "prices": prices_dict,
        "watchlist": watchlist_items,
    }


def main() -> int:
    """Generate summary.json, commit, push."""
    try:
        repo_root = Path(__file__).resolve().parent.parent
        public_dir = repo_root / "public"
        public_dir.mkdir(exist_ok=True)
        summary_path = public_dir / "summary.json"

        logger.info("Connecting to portfolio.db...")
        conn = init_db()

        logger.info("Generating summary...")
        summary = generate_summary(conn)

        logger.info(f"Writing {summary_path}...")
        summary_path.write_text(json.dumps(summary, indent=2))

        logger.info("Committing changes...")
        os.chdir(repo_root)
        subprocess.run(
            ["git", "add", "public/summary.json"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"chore: auto-refresh summary.json\n\nAs of {summary['as_of']}\n"
                f"Portfolio: {summary['allocations']['by_asset_class']}\n\n"
                f"Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>",
            ],
            capture_output=True,
        )

        logger.info("Pushing to GitHub...")
        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True,
            capture_output=True,
        )

        logger.info(f"✓ Summary refreshed: {summary['as_of']}")
        return 0

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.stderr.decode() if e.stderr else e}")
        return 1
    except Exception as e:
        logger.error(f"Refresh failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
