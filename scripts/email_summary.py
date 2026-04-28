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
        tickers = sorted({h.yahoo_ticker for h in holdings_all if h.ticker != "cash"})
        quotes = prices.get_quotes(tickers)
        prices.persist_quotes(conn, quotes)
        holdings_all = calcs.load_holdings(conn)
    except Exception as e:
        logger.warning(f"Price fetch failed: {e}. Using cached prices.")

    # Computations
    port = calcs.summarize(holdings_all, fx.rate)
    unreg_value = calcs.summarize(
        [h for h in holdings_all if h.account_type == "Unreg"], fx.rate
    ).portfolio_cad
    lev = calcs.leverage(conn, port.portfolio_cad, unreg_value)
    nw = calcs.net_worth(conn, port.portfolio_cad)

    # Biggest movers (by % price change, excluding cash)
    biggest_movers = []
    for h in holdings_all:
        if h.ticker == "cash" or not h.price_native or not h.prev_close_native or h.prev_close_native == 0:
            continue
        daily_pct = (h.price_native / h.prev_close_native - 1.0) * 100
        biggest_movers.append({
            "ticker": h.ticker,
            "price": h.price_native,
            "daily_pct": daily_pct,
        })

    biggest_movers = sorted(biggest_movers, key=lambda x: abs(x["daily_pct"]), reverse=True)[:5]

    # Watchlist (all favorites)
    watchlist_rows = conn.execute(
        """SELECT w.ticker, p.price, w.target_price
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
            .kpi-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; margin-bottom: 24px; }}
            .kpi {{ background: #f9f9f9; padding: 12px; border-radius: 4px; border-left: 3px solid #3b82f6; }}
            .kpi-value {{ font-size: 18px; font-weight: 600; color: #1a1a1a; }}
            .kpi-label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
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

            <h2>Biggest Movers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th class="value">Price</th>
                        <th class="value">Daily Change</th>
                    </tr>
                </thead>
                <tbody>
                    {_biggest_movers_html(biggest_movers)}
                </tbody>
            </table>

            <h2>Watchlist</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th class="value">Current</th>
                        <th class="value">Target</th>
                        <th class="value">Gap</th>
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


def _biggest_movers_html(movers: list[dict]) -> str:
    """Generate biggest movers table rows."""
    if not movers:
        return "<tr><td colspan='3' style='text-align: center; color: #999;'>No data</td></tr>"

    html = ""
    for m in movers:
        daily_color = "positive" if m["daily_pct"] >= 0 else "negative"
        arrow = "▲" if m["daily_pct"] >= 0 else "▼"
        html += f"""
        <tr>
            <td class="ticker">{m['ticker']}</td>
            <td class="value">${m['price']:.2f}</td>
            <td class="value {daily_color}">{arrow} {abs(m['daily_pct']):+.2f}%</td>
        </tr>
        """
    return html


def _watchlist_html(rows: list) -> str:
    """Generate watchlist table rows."""
    if not rows:
        return "<tr><td colspan='4' style='text-align: center; color: #999;'>No favorites</td></tr>"

    html = ""
    for r in rows:
        ticker = r["ticker"]
        current = r["price"]
        target = r["target_price"]
        if current and target:
            gap_pct = (current - target) / target * 100
            gap_color = "positive" if gap_pct >= 0 else "negative"
            arrow = "▲" if gap_pct >= 0 else "▼"
            html += f"""
            <tr>
                <td class="ticker">{ticker}</td>
                <td class="value">${current:.2f}</td>
                <td class="value">${target:.2f}</td>
                <td class="value {gap_color}">{arrow} {abs(gap_pct):.1f}%</td>
            </tr>
            """
    return html or "<tr><td colspan='4' style='text-align: center; color: #999;'>No favorites</td></tr>"


def send_email(html_body: str, to_email: str, smtp_user: str, smtp_password: str) -> bool:
    """Send email via SMTP."""
    try:
        logger.info(f"Sending email to {to_email}...")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Portfolio Summary — {datetime.now().strftime('%Y-%m-%d')}"
        msg["From"] = smtp_user
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [to_email], msg.as_string())

        logger.info("✓ Email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def main() -> int:
    """Generate and send portfolio summary email."""
    try:
        # Get credentials from environment
        smtp_user = os.getenv("GMAIL_USER")
        smtp_password = os.getenv("GMAIL_PASSWORD")
        to_email = os.getenv("GMAIL_RECIPIENT", "sergey.pochikovskiy@gmail.com")

        if not smtp_user or not smtp_password:
            logger.error(
                "Missing GMAIL_USER or GMAIL_PASSWORD env vars. "
                "Set them: export GMAIL_USER=... && export GMAIL_PASSWORD=..."
            )
            return 1

        conn = init_db()
        html = generate_email_html(conn)
        return 0 if send_email(html, to_email, smtp_user, smtp_password) else 1

    except Exception as e:
        logger.error(f"Email routine failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
