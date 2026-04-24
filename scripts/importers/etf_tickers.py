# Hand-curated lists used only to refine asset_class at import time.
# Match against the bare ticker (what the broker shows).

LEVERAGED_ETF_TICKERS = {
    # US 2x/3x
    "TQQQ", "SQQQ", "UPRO", "SPXL", "SPXU", "SOXL", "SOXS",
    "FAS", "FAZ", "TMF", "TMV", "LABU", "LABD", "UDOW", "SDOW",
    "UVXY", "SVXY",
    # Canadian Horizons/BetaPro 2x
    "HSU", "HSD", "HXU", "HXD", "HNU", "HND", "HQU", "HQD", "HEU", "HED",
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
