"""
GyanVault database layer.

Central place for the SQLite connection helpers and schema.  Keeping this in
its own package avoids circular imports between ``app.py`` and the blueprints.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import g

DB_PATH = Path(__file__).resolve().parent / "gyanvault.db"

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    icon TEXT NOT NULL DEFAULT 'book'
);

CREATE TABLE IF NOT EXISTS resources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL UNIQUE,
    category    TEXT NOT NULL,
    format      TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    image_url   TEXT NOT NULL DEFAULT '',
    resource_url TEXT NOT NULL DEFAULT '',
    difficulty  TEXT NOT NULL DEFAULT 'Beginner',
    tags        TEXT NOT NULL DEFAULT '',
    views       INTEGER NOT NULL DEFAULT 0,
    downloads   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    session_id  TEXT NOT NULL DEFAULT 'local',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resource_id, session_id),
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resources_category   ON resources(category);
CREATE INDEX IF NOT EXISTS idx_resources_format     ON resources(format);
CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON resources(difficulty);
CREATE INDEX IF NOT EXISTS idx_resources_title      ON resources(title);
"""


def connect() -> sqlite3.Connection:
    """Open a raw SQLite connection with row access by column name."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    """Return the per-request connection, creating it on first use."""
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(error=None) -> None:  # noqa: ARG001 - Flask passes the exception
    """Close the connection at the end of the request."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Create the schema if it does not exist yet.  Safe to call repeatedly."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite Row into a JSON friendly dictionary."""
    return dict(row) if row is not None else None
