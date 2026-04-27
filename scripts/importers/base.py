from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ParsedAccount:
    broker: str
    account_type: str   # RRSP / TFSA / Unreg / Crypto
    label: str
    cash_cad: float = 0.0
    broker_account_number: str = ""

@dataclass
class ParsedHolding:
    broker_account_number: str
    ticker: str
    yahoo_ticker: str
    currency: str
    quantity: float
    acb_per_share: float
    asset_class: str
    country: str
    category: str
    description: str = ""

@dataclass
class ParseResult:
    accounts: dict = field(default_factory=dict)   # broker_account_number -> ParsedAccount
    holdings: list = field(default_factory=list)   # list[ParsedHolding]

class BrokerImporter(ABC):
    broker: str = ""

    # Common Yahoo ticker overrides shared across brokers
    YAHOO_SYMBOL_OVERRIDES = {
        "HSUV.U": "HSUV-U.TO",
        "UCSH.U": "UCSH-U.TO",
        "ETHH.B": "ETHH-B.TO",
    }

    @staticmethod
    @abstractmethod
    def detect_format(path: Path) -> bool: ...

    @abstractmethod
    def parse(self, path: Path) -> ParseResult: ...

    def to_yahoo_ticker(self, ticker: str, currency: str, description: str = "") -> str:
        """Map a broker display ticker to a Yahoo Finance symbol."""
        t = (ticker or "").strip()
        if not t:
            return t
        
        # Check explicit overrides
        if t in self.YAHOO_SYMBOL_OVERRIDES:
            return self.YAHOO_SYMBOL_OVERRIDES[t]
        
        if currency == "USD":
            # Options often have spaces and extra info, Yahoo uses specific format
            # For now, just return as is or handle basic cleaning
            return t
            
        # Canadian tickers
        desc = (description or "").upper()
        if "CDR" in desc:
            base = t.split(".")[0]
            return f"{base}.NE"
            
        if t.endswith((".TO", ".V", ".NE", ".CN")):
            return t
            
        # Yahoo uses dash for class/unit suffixes on TSX listings
        return f"{t.replace('.', '-')}.TO"
