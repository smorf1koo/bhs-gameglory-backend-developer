"""SQLite connection helpers."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("GAMEGLORY_DB", "gameglory.db"))
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
