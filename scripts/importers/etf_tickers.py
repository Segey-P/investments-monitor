# Hand-curated lists used only to refine asset_class and category at import time.
# Match against the bare ticker (what the broker shows).

# --- TICKER CLASSIFICATIONS ---

# 3x or 2x daily reset instruments (High Risk)
LEVERAGED_ETF_TICKERS = {
    "TQQQ", "UPRO", "SPXL"
}

# Cash equivalents, HISA ETFs, and Ultra-Short Term Bonds
CASH_TICKERS = {
    "UCSH.U", "UCSH", "PSA", "CASH", "PCSA", "TST",
    "CHP.U", "CHP", "PSA.U", "XSB", "VSB"
}

# Income-focused: Banks, Energy, Telcos, and REITs
DIVIDEND_TICKERS = {
    "CU", "CDZ", "FDV", "XDV", "VDY", "DVY", "XID", "VID",
    "RY", "TD", "BNS", "NA", "BMO", "CNQ", "ENB", "TRP",
    "T", "BCE", "FTS", "CAR", "AQN", "REI.UN", "HR.UN",
    "AP.UN", "NWH.UN"
}

# 1x Beta Growth and Thematic (Tech, Crypto, Commodities, and International)
GROWTH_TICKERS = {
    "QQQ", "XIT", "SHOP", "CQQQ",   # Tech & Growth
    "COPP", "COPX", "PICK", "PPLT", # Materials & Metals
    "QTUM", "SIXG", "GNOM",         # Quantum, 5G, Genomics
    "IBIT", "FBTC", "BITQ",         # Bitcoin & Crypto Equity
    "FXI"                           # China Large-Cap
}

KNOWN_ETF_TICKERS = {
    # Canadian broad-market / sector
    "XIU", "XIC", "VCN", "ZCN", "VFV", "VSP", "XEQT", "XGRO", "XBAL",
    "XIT", "CDZ", "XHC", "FBTC", "ETHH.B", "HSUV.U", "UCSH.U",
    # US broad / sector
    "VOO", "VTI", "SPY", "QQQ", "IWM", "GLD", "SLV",
    "XLK", "XLV", "XLF", "XLE", "XLY", "XLI", "XLP", "XLU",
    "COPP", "COPX", "PICK", "PPLT", "QTUM", "SIXG", "FXI", "CQQQ",
    "IBIT", "FBTC", "BITQ", "GNOM",
}
