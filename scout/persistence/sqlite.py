# ./scout/persistence/sqlite.py
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS watches (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL,
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    source TEXT NOT NULL,
    watch_version INTEGER NOT NULL,
    payload TEXT NOT NULL,
    FOREIGN KEY (watch_id) REFERENCES watches(id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_watch_captured
ON snapshots(watch_id, captured_at);
"""


@contextmanager
def connect(db_path: str | Path) -> Generator[sqlite3.Connection]:
    """Open and reliably close a SQLite connection."""

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path: str | Path) -> None:
    """Create the database directory and Scout's persistence tables."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with connect(path) as connection:
        connection.executescript(SCHEMA)
