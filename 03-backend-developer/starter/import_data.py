"""Import shared-data/games.csv and tags.csv into SQLite.

Usage:
    python import_data.py [--data-dir ../../shared-data] [--db gameglory.db]

Requirement: a second run must not create duplicates or fail.
"""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from app.db import DB_PATH, connect, init_schema

DEFAULT_DATA = Path(os.environ.get("GAMEGLORY_DATA", Path(__file__).resolve().parents[2] / "shared-data"))


def split_list(value: str) -> list[str]:
    """Lists in the CSV (tags, genres, platforms) are separated by '|'."""
    return [x for x in value.split("|") if x] if value else []


def import_data(data_dir: Path, db_path: Path | str) -> int:
    """Load tags and games; return the number of processed games."""
    conn = connect(db_path)
    init_schema(conn)
    n = 0
    with conn:  # one transaction: all or nothing
        with (data_dir / "tags.csv").open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pass  # TODO: insert or update the tag (slug, name, category)
        with (data_dir / "games.csv").open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                # TODO: insert or update the game and its tag links;
                # empty reviews_positive_ratio -> NULL, tags -> split_list(row["tags"])
                n += 1
    conn.close()
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()
    print(f"processed {import_data(args.data_dir, args.db)} games from CSV into {args.db}")
