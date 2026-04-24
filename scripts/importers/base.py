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

    @staticmethod
    @abstractmethod
    def detect_format(path: Path) -> bool: ...

    @abstractmethod
    def parse(self, path: Path) -> ParseResult: ...
