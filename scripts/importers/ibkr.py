import csv
from pathlib import Path
from .base import BrokerImporter, ParsedAccount, ParsedHolding, ParseResult
from .etf_tickers import LEVERAGED_ETF_TICKERS, CASH_TICKERS, DIVIDEND_TICKERS, GROWTH_TICKERS

# IBKR account-type mapping
ACCOUNT_TYPE_MAP = {
    "Individual": "Unreg",
    "Joint": "Unreg",
    "RRSP": "RRSP",
    "TFSA": "TFSA",
}

class IBKRImporter(BrokerImporter):
    broker = "Interactive Brokers"

    @staticmethod
    def detect_format(path: Path) -> bool:
        if path.suffix.lower() != ".csv":
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                first_line = f.readline()
                return "Introduction,Header" in first_line
        except:
            return False

    def parse(self, path: Path) -> ParseResult:
        result = ParseResult()
        
        sections = {}
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                section = row[0]
                if section not in sections:
                    sections[section] = []
                sections[section].append(row)

        # 1. Parse Account Info from Introduction section
        intro_data = [row for row in sections.get("Introduction", []) if row[1] == "Data"]
        if not intro_data:
            raise ValueError("No account data found in IBKR file (Introduction section)")
        
        # Introduction,Data,Name,Account,Alias,BaseCurrency,AccountType,...
        # Headers: 0:Section, 1:Type, 2:Name, 3:Account, 4:Alias, 5:BaseCurrency, 6:AccountType
        acct_row = intro_data[0]
        acct_num = acct_row[3]
        raw_type = acct_row[6]
        mapped_type = ACCOUNT_TYPE_MAP.get(raw_type, "Unreg")
        
        result.accounts[acct_num] = ParsedAccount(
            broker=self.broker,
            account_type=mapped_type,
            label=f"{raw_type} — {acct_num}",
            cash_cad=0.0,
            broker_account_number=acct_num,
        )

        # 2. Parse Positions and Cash from Open Position Summary section
        positions_rows = sections.get("Open Position Summary", [])
        header = None
        for row in positions_rows:
            if row[1] == "Header":
                header = row
                continue
            if row[1] == "Data" and header:
                data = dict(zip(header, row))
                if data.get("Date") == "Total":
                    continue
                
                fin_instrument = data.get("FinancialInstrument")
                currency = data.get("Currency")
                symbol = data.get("Symbol")
                description = data.get("Description")
                
                # Clean numeric values
                def _parse_float(val):
                    if not val or val.strip() == "": return 0.0
                    return float(val.replace(",", "").strip())

                quantity = _parse_float(data.get("Quantity", "0"))
                
                if fin_instrument == "Cash":
                    # IBKR "Value" in this section for cash is usually already converted to Base Currency 
                    # if it's the total row, but for individual rows it might be native.
                    # Looking at the sample:
                    # Open Position Summary,Data,04/24/2026,Cash,USD,USD,United States Dollar,Cash,1662.632565,1.3669,2272.652453099, , ,1.3669
                    # Value 2272.65 is indeed 1662.63 * 1.3669.
                    # So we take "Value" as CAD if base currency is CAD.
                    val_cad = _parse_float(data.get("Value", "0"))
                    result.accounts[acct_num].cash_cad += val_cad
                elif fin_instrument in ["ETFs", "Stocks", "Options"]:
                    cost_basis = _parse_float(data.get("Cost Basis", "0"))
                    acb = cost_basis / quantity if quantity != 0 else 0
                    
                    asset_class = "Stock"
                    if fin_instrument == "ETFs":
                        asset_class = "ETF"
                        if symbol.upper() in LEVERAGED_ETF_TICKERS:
                            asset_class = "LeveragedETF"
                    elif fin_instrument == "Options":
                        asset_class = "Options"
                    
                    category = "Other"
                    if symbol.upper() in CASH_TICKERS:
                        category = "Cash"
                    elif symbol.upper() in DIVIDEND_TICKERS:
                        category = "Dividend"
                    elif symbol.upper() in GROWTH_TICKERS:
                        category = "Growth"
                        
                    country = "US" if currency == "USD" else "CA"
                    
                    yahoo_ticker = self.to_yahoo_ticker(symbol, currency, description)

                    result.holdings.append(ParsedHolding(
                        broker_account_number=acct_num,
                        ticker=symbol,
                        yahoo_ticker=yahoo_ticker,
                        currency=currency,
                        quantity=quantity,
                        acb_per_share=acb,
                        asset_class=asset_class,
                        country=country,
                        category=category,
                        description=description,
                    ))

        return result
