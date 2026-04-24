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


def init_db(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = get_conn(path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    _migrate(conn)
    conn.commit()
    return conn
