"""Portfolio calculations in CAD. Pure functions over DB rows + price/fx cache."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HoldingRow:
    id: int
    account_id: int
    account_type: str
    account_label: str
    ticker: str
    yahoo_ticker: str
    currency: str
    quantity: float
    acb_per_share: float
    asset_class: str
    category: str
    country: str
    description: str
    price_native: float | None
    prev_close_native: float | None
    price_stale: bool

    def mkt_value_native(self) -> float | None:
        return None if self.price_native is None else self.quantity * self.price_native

    def mkt_value_cad(self, usdcad: float) -> float | None:
        v = self.mkt_value_native()
        if v is None:
            return None
        return v if self.currency == "CAD" else v * usdcad

    def cost_native(self) -> float:
        return self.quantity * self.acb_per_share

    def cost_cad(self, usdcad: float) -> float:
        c = self.cost_native()
        return c if self.currency == "CAD" else c * usdcad

    def unrealized_pl_cad(self, usdcad: float) -> float | None:
        v = self.mkt_value_cad(usdcad)
        if v is None:
            return None
        return v - self.cost_cad(usdcad)

    def day_change_pct(self) -> float | None:
        if self.price_native is None or not self.prev_close_native:
            return None
        return (self.price_native / self.prev_close_native - 1.0) * 100.0


def load_holdings(conn) -> list[HoldingRow]:
    rows = conn.execute("""
        SELECT h.id, h.account_id, a.account_type, a.label AS account_label,
               h.ticker, h.yahoo_ticker, h.currency, h.quantity, h.acb_per_share,
               h.asset_class, h.category, h.country, h.description,
               p.price      AS price_native,
               p.prev_close AS prev_close_native,
               COALESCE(p.stale, 1) AS price_stale
        FROM holdings h
        JOIN accounts a ON a.id = h.account_id
        LEFT JOIN prices p ON p.ticker = h.yahoo_ticker
    """).fetchall()
    return [
        HoldingRow(
            id=r["id"], account_id=r["account_id"], account_type=r["account_type"],
            account_label=r["account_label"], ticker=r["ticker"],
            yahoo_ticker=r["yahoo_ticker"], currency=r["currency"],
            quantity=r["quantity"], acb_per_share=r["acb_per_share"],
            asset_class=r["asset_class"], category=r["category"],
            country=r["country"],
            description=r["description"] or "",
            price_native=1.0 if r["ticker"] == "cash" else r["price_native"],
            prev_close_native=1.0 if r["ticker"] == "cash" else r["prev_close_native"],
            price_stale=False if r["ticker"] == "cash" else bool(r["price_stale"]),
        )
        for r in rows
    ]


@dataclass
class PortfolioSummary:
    portfolio_cad: float
    unrealized_pl_cad: float
    position_count: int
    account_count: int
    missing_prices: int
    cash_cad: float = 0.0


def summarize(holdings: list[HoldingRow], usdcad: float) -> PortfolioSummary:
    total = 0.0
    pl = 0.0
    cash = 0.0
    missing = 0
    for h in holdings:
        mv = h.mkt_value_cad(usdcad)
        if mv is None:
            missing += 1
            continue
        total += mv
        if h.ticker == "cash":
            cash += mv
        else:
            cost = h.cost_cad(usdcad)
            pl += mv - cost
    return PortfolioSummary(
        portfolio_cad=total,
        unrealized_pl_cad=pl,
        position_count=len(holdings),
        account_count=len({h.account_id for h in holdings}),
        missing_prices=missing,
        cash_cad=cash,
    )


def allocations(holdings: list[HoldingRow], usdcad: float) -> dict[str, dict[str, float]]:
    """Return proportion dicts (summing to 1.0 within each dimension)."""
    dims = {
        "by_account":     {},
        "by_asset_class": {},
        "by_category":    {},
        "by_country":     {},
        "by_currency":    {},
    }
    total = 0.0
    for h in holdings:
        mv = h.mkt_value_cad(usdcad)
        if mv is None:
            continue
        total += mv
        dims["by_account"][h.account_type]      = dims["by_account"].get(h.account_type, 0) + mv
        dims["by_asset_class"][h.asset_class]   = dims["by_asset_class"].get(h.asset_class, 0) + mv
        dims["by_category"][h.category]         = dims["by_category"].get(h.category, 0) + mv
        dims["by_country"][h.country]           = dims["by_country"].get(h.country, 0) + mv
        dims["by_currency"][h.currency]         = dims["by_currency"].get(h.currency, 0) + mv
    if total <= 0:
        return dims
    return {d: {k: v / total for k, v in vals.items()} for d, vals in dims.items()}


@dataclass
class LeverageSummary:
    heloc_drawn_cad: float
    heloc_limit_cad: float
    heloc_util_pct: float
    heloc_monthly_interest_cad: float
    margin_balance_cad: float
    margin_limit_cad: float
    margin_monthly_interest_cad: float
    margin_buffer_pct: float | None
    total_borrowed_cad: float
    leverage_ratio: float


def heloc_drawn(conn) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cad), 0) AS s FROM heloc_draws"
    ).fetchone()
    return float(row["s"] or 0)


def leverage(conn, portfolio_cad: float, unreg_value_cad: float) -> LeverageSummary:
    h = conn.execute("SELECT * FROM heloc_account WHERE id = 1").fetchone()
    m = conn.execute("SELECT * FROM margin_account WHERE id = 1").fetchone()
    drawn = heloc_drawn(conn)
    h_limit = float(h["limit_cad"] or 0)
    h_rate = float(h["rate_pct"] or 0)
    util = (drawn / h_limit) if h_limit > 0 else 0.0
    h_int = drawn * (h_rate / 100.0) / 12.0

    m_bal = float(m["balance_cad"] or 0)
    m_limit = float(m["limit_cad"] or 0)
    m_rate = float(m["rate_pct"] or 0)
    m_int = m_bal * (m_rate / 100.0) / 12.0

    total = drawn + m_bal
    denom = portfolio_cad - drawn - m_bal
    ratio = (portfolio_cad / denom) if denom > 0 else 0.0

    buf = None
    if unreg_value_cad > 0:
        buf = max((unreg_value_cad - m_bal) / unreg_value_cad, 0.0)

    return LeverageSummary(
        heloc_drawn_cad=drawn, heloc_limit_cad=h_limit, heloc_util_pct=util,
        heloc_monthly_interest_cad=h_int,
        margin_balance_cad=m_bal, margin_limit_cad=m_limit,
        margin_monthly_interest_cad=m_int,
        margin_buffer_pct=buf,
        total_borrowed_cad=total, leverage_ratio=ratio,
    )


@dataclass
class NetWorth:
    portfolio_cad: float
    cash_cad: float
    property_cad: float
    mortgage_cad: float
    heloc_drawn_cad: float
    margin_balance_cad: float
    total_assets_cad: float
    total_liabilities_cad: float
    net_worth_cad: float
    debt_to_equity: float
    mortgage_ltv: float


def net_worth(conn, portfolio_cad: float, portfolio_cash_cad: float = 0.0) -> NetWorth:
    cash = float(conn.execute("SELECT balance_cad FROM cash_aggregate WHERE id=1").fetchone()["balance_cad"] or 0)
    prop = conn.execute("SELECT value_cad FROM property WHERE id=1").fetchone()["value_cad"] or 0
    mort = conn.execute("SELECT balance_cad FROM mortgage WHERE id=1").fetchone()["balance_cad"] or 0
    drawn = heloc_drawn(conn)
    margin_bal = float(conn.execute("SELECT balance_cad FROM margin_account WHERE id=1").fetchone()["balance_cad"] or 0)
    assets = (portfolio_cad - portfolio_cash_cad) + cash + float(prop)
    liabs = float(mort) + drawn + margin_bal
    nw = assets - liabs
    dte = (liabs / nw) if nw > 0 else 0.0
    ltv = (float(mort) / float(prop)) if prop else 0.0
    return NetWorth(
        portfolio_cad=portfolio_cad, cash_cad=cash, property_cad=float(prop),
        mortgage_cad=float(mort), heloc_drawn_cad=drawn, margin_balance_cad=margin_bal,
        total_assets_cad=assets, total_liabilities_cad=liabs, net_worth_cad=nw,
        debt_to_equity=dte, mortgage_ltv=ltv,
    )


def today_delta(holdings: list[HoldingRow], usdcad: float) -> float:
    """Sum of all holdings' daily dollar change (today's P&L in CAD)."""
    total = 0.0
    for h in holdings:
        mv = h.mkt_value_cad(usdcad)
        if mv is None or h.day_change_pct() is None:
            continue
        daily_change_cad = mv * (h.day_change_pct() / 100.0)
        total += daily_change_cad
    return total


def biggest_mover(holdings: list[HoldingRow]) -> HoldingRow | None:
    """Return holding with largest absolute % change today."""
    valid = [h for h in holdings if h.day_change_pct() is not None]
    if not valid:
        return None
    return max(valid, key=lambda h: abs(h.day_change_pct()))
