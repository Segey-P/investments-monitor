-- Investments Monitor v0.1 schema
-- Matches specs/module-1-investment-leverage-engine-specification.md §2
-- Divergence: holdings has a yahoo_ticker column and UNIQUE(account_id,ticker,currency)
-- to support same-ticker/different-currency rows (e.g. AMZN CDR + AMZN USD in TFSA).

CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  portfolio_id TEXT NOT NULL DEFAULT 'self',
  account_type TEXT NOT NULL CHECK (account_type IN ('RRSP','TFSA','Unreg','Crypto')),
  broker TEXT NOT NULL,
  label TEXT NOT NULL,
  UNIQUE (portfolio_id, broker, label)
);

CREATE TABLE IF NOT EXISTS holdings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  yahoo_ticker TEXT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('CAD','USD')),
  quantity REAL NOT NULL,
  acb_per_share REAL NOT NULL,
  asset_class TEXT NOT NULL CHECK (asset_class IN ('Cash','Stock','ETF','LeveragedETF','Crypto','Options')),
  country TEXT NOT NULL CHECK (country IN ('CA','US','Other')),
  category TEXT NOT NULL DEFAULT 'Other' CHECK (category IN ('Cash','Dividend','Growth','Other')),
  description TEXT,
  as_of TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (account_id, ticker, currency)
);
CREATE INDEX IF NOT EXISTS idx_holdings_account ON holdings(account_id);
CREATE INDEX IF NOT EXISTS idx_holdings_yahoo ON holdings(yahoo_ticker);

CREATE TABLE IF NOT EXISTS prices (
  ticker TEXT PRIMARY KEY,
  price REAL,
  prev_close REAL,
  currency TEXT,
  fetched_at TIMESTAMP NOT NULL,
  stale INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS heloc_draws (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date DATE NOT NULL,
  amount_cad REAL NOT NULL,
  purpose TEXT
);

CREATE TABLE IF NOT EXISTS heloc_account (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  limit_cad REAL,
  rate_pct REAL,
  util_warn_pct REAL NOT NULL DEFAULT 80
);

CREATE TABLE IF NOT EXISTS margin_account (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  broker TEXT,
  balance_cad REAL NOT NULL DEFAULT 0,
  limit_cad REAL,
  rate_pct REAL,
  call_threshold_pct REAL NOT NULL DEFAULT 70,
  warn_buffer_pct REAL NOT NULL DEFAULT 50
);

CREATE TABLE IF NOT EXISTS cash_aggregate (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  balance_cad REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS property (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  value_cad REAL,
  as_of TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mortgage (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  balance_cad REAL,
  rate_pct REAL,
  renewal_date DATE,
  lender TEXT,
  as_of TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist (
  ticker TEXT PRIMARY KEY,
  target_price REAL,
  notes TEXT,
  is_favorite INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS imports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  broker TEXT NOT NULL,
  account_id INTEGER REFERENCES accounts(id),
  rows INTEGER NOT NULL,
  imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS snapshots (
  date DATE PRIMARY KEY,
  net_worth_cad REAL,
  portfolio_cad REAL,
  heloc_drawn_cad REAL,
  margin_balance_cad REAL,
  leverage_ratio REAL
);

CREATE TABLE IF NOT EXISTS manual_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  amount_cad REAL NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manual_liabilities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  amount_cad REAL NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO heloc_account (id, limit_cad, rate_pct, util_warn_pct)
  VALUES (1, NULL, NULL, 80);
INSERT OR IGNORE INTO margin_account (id, broker, balance_cad, limit_cad, rate_pct, call_threshold_pct, warn_buffer_pct)
  VALUES (1, 'Questrade', 0, NULL, NULL, 70, 50);
INSERT OR IGNORE INTO cash_aggregate (id, balance_cad) VALUES (1, 0);
INSERT OR IGNORE INTO property (id) VALUES (1);
INSERT OR IGNORE INTO mortgage (id) VALUES (1);
