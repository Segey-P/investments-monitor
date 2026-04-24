"""CLI: import a Questrade Investment Summary XLSX into portfolio.db.

Usage:
    .venv/bin/python -m scripts.import_questrade <path/to/file.xlsx>
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root on path so `app` and `scripts` imports work when run as a module.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db import init_db  # noqa: E402
from scripts.importers.questrade import QuestradeImporter  # noqa: E402
from scripts.importers.persist import FileAlreadyImported, persist_result  # noqa: E402


def main(path: Path) -> None:
    if not path.exists():
        sys.exit(f"File not found: {path}")

    conn = init_db()
    importer = QuestradeImporter()
    if not importer.detect_format(path):
        print(f"warning: filename does not look like Questrade — continuing anyway.")
    parsed = importer.parse(path)

    try:
        result = persist_result(conn, path, parsed)
        print(f"✓ Imported {result['holdings']} holdings across {result['accounts']} accounts.")
        print(f"Cash aggregate set to ${result['cash_total']:,.2f} CAD.")
    except FileAlreadyImported as e:
        sys.exit(f"File already imported on {e.imported_at}. Skipping.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m scripts.import_questrade <file.xlsx>")
    main(Path(sys.argv[1]))
