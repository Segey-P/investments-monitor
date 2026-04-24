"""Bank of Canada Valet FX (USD/CAD). Cached in settings table, refreshed daily."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone

BOC_VALET_URL = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1"
FALLBACK_RATE = 1.37  # last-resort if no cached value and network fails


@dataclass
class FxRate:
    rate: float
    as_of: str          # observation date (YYYY-MM-DD) from BOC
    fetched_at: str     # ISO timestamp we stored it
    stale: bool = False


def _get_setting(conn, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _put_setting(conn, key: str, value: str) -> None:
    with conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def _fetch_boc() -> FxRate | None:
    import requests
    try:
        r = requests.get(BOC_VALET_URL, timeout=10)
        r.raise_for_status()
        payload = r.json()
        obs = payload.get("observations", [])
        if not obs:
            return None
        latest = obs[-1]
        rate = float(latest["FXUSDCAD"]["v"])
        return FxRate(
            rate=rate,
            as_of=latest["d"],
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            stale=False,
        )
    except Exception:
        return None


def get_usdcad(conn) -> FxRate:
    """Return USD→CAD rate. Fetch from BOC if cache is older than today."""
    cached_raw = _get_setting(conn, "fx_usdcad")
    if cached_raw:
        data = json.loads(cached_raw)
        if data.get("as_of") == date.today().isoformat():
            return FxRate(**data)
    fresh = _fetch_boc()
    if fresh is not None:
        _put_setting(conn, "fx_usdcad", json.dumps(fresh.__dict__))
        return fresh
    if cached_raw:
        data = json.loads(cached_raw)
        data["stale"] = True
        return FxRate(**data)
    return FxRate(
        rate=FALLBACK_RATE,
        as_of=date.today().isoformat(),
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        stale=True,
    )
