"""yfinance wrapper: batched price fetch with 15-min in-memory cache."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

CACHE_TTL_SECONDS = 60  # "live-ish": every Streamlit rerun, deduped within 60s
_cache: dict[str, tuple[float, "PriceQuote"]] = {}


@dataclass
class PriceQuote:
    ticker: str
    price: float | None
    prev_close: float | None
    currency: str | None
    stale: bool = False


def _fetch_batch(tickers: list[str]) -> dict[str, PriceQuote]:
    """yfinance call. Isolated so tests can monkeypatch."""
    import yfinance as yf

    out: dict[str, PriceQuote] = {}
    if not tickers:
        return out
    # fast_info avoids the slow history() call; good enough for price + prev close
    data = yf.Tickers(" ".join(tickers))
    for t in tickers:
        try:
            info = data.tickers[t].fast_info
            price = float(info.last_price) if info.last_price else None
            prev = float(info.previous_close) if info.previous_close else None
            currency = getattr(info, "currency", None)
            out[t] = PriceQuote(t, price, prev, currency, stale=(price is None))
        except Exception:
            out[t] = PriceQuote(t, None, None, None, stale=True)
    return out


def get_quotes(tickers: Iterable[str]) -> dict[str, PriceQuote]:
    """Return quotes for all tickers. Uses 15-min cache; never raises.
    Skips 'cash' ticker (no Yahoo quote available)."""
    now = time.time()
    need: list[str] = []
    out: dict[str, PriceQuote] = {}
    for t in tickers:
        if t == "cash":
            continue
        cached = _cache.get(t)
        if cached and (now - cached[0] < CACHE_TTL_SECONDS):
            out[t] = cached[1]
        else:
            need.append(t)
    if need:
        fresh = _fetch_batch(need)
        for t, q in fresh.items():
            _cache[t] = (now, q)
            out[t] = q
    return out


def persist_quotes(conn, quotes: dict[str, PriceQuote]) -> None:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn:
        for q in quotes.values():
            conn.execute(
                """
                INSERT INTO prices (ticker, price, prev_close, currency, fetched_at, stale)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                  price      = excluded.price,
                  prev_close = excluded.prev_close,
                  currency   = excluded.currency,
                  fetched_at = excluded.fetched_at,
                  stale      = excluded.stale
                """,
                (q.ticker, q.price, q.prev_close, q.currency, ts, int(q.stale)),
            )


def load_cached_prices(conn) -> dict[str, PriceQuote]:
    rows = conn.execute(
        "SELECT ticker, price, prev_close, currency, stale FROM prices"
    ).fetchall()
    return {
        r["ticker"]: PriceQuote(
            r["ticker"], r["price"], r["prev_close"], r["currency"], bool(r["stale"])
        )
        for r in rows
    }
