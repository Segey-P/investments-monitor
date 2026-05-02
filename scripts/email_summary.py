#!/usr/bin/env python3
"""Daily portfolio summary email. Fetches live data, generates HTML, sends via SMTP."""
from __future__ import annotations

import logging
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import calcs, prices
from app.db import init_db
from app.fx import get_usdcad
from app.mail import send_email
from app.theme import PALETTE, fmt_cad, fmt_pct, fmt_ratio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "email_summary.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def generate_email_html(conn) -> str:
    """Generate HTML email body with portfolio summary."""
    logger.info("Loading holdings and computing summary...")
    holdings_all = calcs.load_holdings(conn)
    fx = get_usdcad(conn)

    # Fetch live prices
    logger.info("Fetching live prices...")
    try:
        tickers = sorted({h.yahoo_ticker for h in holdings_all if h.ticker != "cash" and h.asset_class != "Options"})
        quotes = prices.get_quotes(tickers)
        prices.persist_quotes(conn, quotes)
        holdings_all = calcs.load_holdings(conn)
    except Exception as e:
        logger.warning(f"Price fetch failed: {e}. Using cached prices.")

    # Computations
    # Build movers list (by % price change, excluding cash)
    movers = []
    for h in holdings_all:
        if h.ticker == "cash" or not h.price_native or not h.prev_close_native or h.prev_close_native == 0:
            continue
        daily_pct = (h.price_native / h.prev_close_native - 1.0) * 100
        movers.append({"ticker": h.ticker, "price": h.price_native, "daily_pct": daily_pct})

    top_gainers = sorted([m for m in movers if m["daily_pct"] > 0], key=lambda x: x["daily_pct"], reverse=True)[:5]
    top_losers = sorted([m for m in movers if m["daily_pct"] < 0], key=lambda x: x["daily_pct"])[:5]

    # Watchlist (all favorites, with daily move)
    watchlist_rows = conn.execute(
        """SELECT w.ticker, p.price, p.prev_close, w.target_price
           FROM watchlist w
           LEFT JOIN prices p ON p.ticker = w.ticker
           WHERE w.is_favorite = 1
           ORDER BY w.ticker"""
    ).fetchall()

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            h1 {{ margin: 0 0 8px 0; font-size: 24px; color: #1a1a1a; }}
            .timestamp {{ color: #666; font-size: 12px; margin-bottom: 20px; }}
            h2 {{ margin: 24px 0 12px 0; font-size: 16px; color: #1a1a1a; border-bottom: 1px solid #e5e5e5; padding-bottom: 8px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            th {{ background: #f9f9f9; padding: 8px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #e5e5e5; }}
            td {{ padding: 8px; border-bottom: 1px solid #f0f0f0; }}
            .ticker {{ font-weight: 600; color: #1a1a1a; }}
            .value {{ font-family: "SF Mono", Monaco, monospace; text-align: right; }}
            .positive {{ color: #22c55e; }}
            .negative {{ color: #ef4444; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Portfolio Summary</h1>
            <div class="timestamp">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M PT')}</div>

            <h2>Top 5 Gainers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th class="value">Price</th>
                        <th class="value">Daily Change</th>
                    </tr>
                </thead>
                <tbody>
                    {_movers_html(top_gainers, "No gainers today")}
                </tbody>
            </table>

            <h2>Top 5 Losers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th class="value">Price</th>
                        <th class="value">Daily Change</th>
                    </tr>
                </thead>
                <tbody>
                    {_movers_html(top_losers, "No losers today")}
                </tbody>
            </table>

            <h2>Watchlist</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th class="value">Current</th>
                        <th class="value">Daily Move</th>
                        <th class="value">Target</th>
                        <th class="value">Gap to Target</th>
                    </tr>
                </thead>
                <tbody>
                    {_watchlist_html(watchlist_rows)}
                </tbody>
            </table>

            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e5e5; font-size: 12px; color: #999;">
                <p>FX: 1 USD = {fx.rate:.4f} CAD · {fx.as_of}</p>
                <p>Generated by Investments Monitor</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def _movers_html(movers: list[dict], empty_msg: str) -> str:
    if not movers:
        return f"<tr><td colspan='3' style='text-align: center; color: #999;'>{empty_msg}</td></tr>"

    html = ""
    for m in movers:
        css = "positive" if m["daily_pct"] >= 0 else "negative"
        arrow = "▲" if m["daily_pct"] >= 0 else "▼"
        html += f"""
        <tr>
            <td class="ticker">{m['ticker']}</td>
            <td class="value">${m['price']:.2f}</td>
            <td class="value {css}">{arrow} {m['daily_pct']:+.2f}%</td>
        </tr>
        """
    return html


def _watchlist_html(rows: list) -> str:
    if not rows:
        return "<tr><td colspan='5' style='text-align: center; color: #999;'>No favorites</td></tr>"

    html = ""
    for r in rows:
        ticker = r["ticker"]
        current = r["price"]
        prev_close = r["prev_close"]
        target = r["target_price"]

        price_cell = f"${current:.2f}" if current else "—"

        if current and prev_close and prev_close != 0:
            daily_pct = (current / prev_close - 1.0) * 100
            daily_css = "positive" if daily_pct >= 0 else "negative"
            daily_arrow = "▲" if daily_pct >= 0 else "▼"
            daily_cell = f'<span class="{daily_css}">{daily_arrow} {daily_pct:+.2f}%</span>'
        else:
            daily_cell = "—"

        if current and target and target != 0:
            gap_pct = (current / target - 1.0) * 100
            gap_css = "positive" if gap_pct >= 0 else "negative"
            gap_arrow = "▲" if gap_pct >= 0 else "▼"
            target_cell = f"${target:.2f}"
            gap_cell = f'<span class="{gap_css}">{gap_arrow} {gap_pct:+.2f}%</span>'
        else:
            target_cell = f"${target:.2f}" if target else "—"
            gap_cell = "—"

        html += f"""
        <tr>
            <td class="ticker">{ticker}</td>
            <td class="value">{price_cell}</td>
            <td class="value">{daily_cell}</td>
            <td class="value">{target_cell}</td>
            <td class="value">{gap_cell}</td>
        </tr>
        """
    return html


def is_market_open() -> bool:
    """Check if market is likely open (Weekday and not holiday)."""
    # For now, just check weekends.
    now = datetime.now()
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    # Optional: Simple holiday check could go here
    return True


def main() -> int:
    """Generate and send portfolio summary email."""
    try:
        if not is_market_open() and "--force" not in sys.argv:
            logger.info("Market is closed (weekend). Skipping email. Use --force to send anyway.")
            return 0

        conn = init_db()
        html = generate_email_html(conn)
        subject = f"Portfolio Summary — {datetime.now().strftime('%Y-%m-%d')}"
        return 0 if send_email(subject, html) else 1

    except Exception as e:
        logger.error(f"Email routine failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
