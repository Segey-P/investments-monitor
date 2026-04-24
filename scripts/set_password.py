"""Interactive password setter. Stores bcrypt hash in settings table.

Usage:
    .venv/bin/python -m scripts.set_password
"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import bcrypt  # noqa: E402

from app.db import init_db  # noqa: E402


def main() -> None:
    conn = init_db()

    pw1 = getpass.getpass("New password: ")
    if len(pw1) < 8:
        sys.exit("Password must be at least 8 characters.")
    pw2 = getpass.getpass("Confirm password: ")
    if pw1 != pw2:
        sys.exit("Passwords do not match.")

    hashed = bcrypt.hashpw(pw1.encode("utf-8"), bcrypt.gensalt())
    with conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('password_hash', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (hashed.decode("utf-8"),),
        )
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('session_timeout_min', '15') "
            "ON CONFLICT(key) DO NOTHING",
        )
    print("Password set. Session timeout defaulted to 15 minutes.")


if __name__ == "__main__":
    main()
