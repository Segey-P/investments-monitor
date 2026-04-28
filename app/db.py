import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "portfolio.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_conn(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(watchlist)").fetchall()}
    if "is_favorite" not in cols:
        conn.execute(
            "ALTER TABLE watchlist ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0"
        )
        conn.commit()

    # Add 'Options' to asset_class CHECK constraint
    try:
        conn.execute("INSERT INTO holdings (account_id, ticker, yahoo_ticker, currency, quantity, acb_per_share, asset_class, country) VALUES (NULL, '', '', '', 0, 0, 'Options', 'CA')")
        conn.rollback()
    except sqlite3.IntegrityError:
        # Constraint doesn't allow 'Options' yet, need to migrate
        try:
            conn.execute("ALTER TABLE holdings RENAME TO holdings_old")
            conn.execute("""
                CREATE TABLE holdings (
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
                )
            """)
            conn.execute("INSERT INTO holdings SELECT * FROM holdings_old")
            conn.execute("DROP TABLE holdings_old")
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def init_db(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = get_conn(path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    _migrate(conn)
    conn.commit()
    return conn
