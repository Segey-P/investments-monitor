"""Cloud mode: load summary.json instead of local DB."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SummaryData:
    """Parsed public/summary.json payload."""
    as_of: str
    ratios: dict
    allocations: dict
    tickers_held: list[str]
    prices: dict[str, float]
    watchlist: list[dict]
    is_stale: bool


def load_summary(repo_root: Path | None = None) -> SummaryData | None:
    """Load public/summary.json. Return None if not found or invalid."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    summary_path = repo_root / "public" / "summary.json"
    if not summary_path.exists():
        return None

    try:
        data = json.loads(summary_path.read_text())
        from datetime import datetime, timezone, timedelta

        # Check staleness: >6h old
        as_of = datetime.fromisoformat(data["as_of"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = (now - as_of).total_seconds() / 3600
        is_stale = age_hours > 6

        return SummaryData(
            as_of=data["as_of"],
            ratios=data.get("ratios", {}),
            allocations=data.get("allocations", {}),
            tickers_held=data.get("tickers_held", []),
            prices=data.get("prices", {}),
            watchlist=data.get("watchlist", []),
            is_stale=is_stale,
        )
    except Exception as e:
        return None
