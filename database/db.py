"""
database/db.py

Database connection manager.

Why a connection manager instead of opening connections directly?
- One place to configure the connection (WAL mode, timeouts, row factory)
- Easy to swap SQLite for PostgreSQL later without touching other modules
- Context manager pattern ensures connections are always closed cleanly

Usage:
    from database.db import get_connection

    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM businesses").fetchall()
        # Connection closes automatically when the with block exits
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config.settings import settings

logger = logging.getLogger(__name__)


def _configure_connection(conn: sqlite3.Connection) -> None:
    """
    Apply settings to a new connection.
    Called every time a connection is created.
    """
    # Return rows as dict-like objects so you can do row["column_name"]
    # instead of row[0] — makes code much more readable
    conn.row_factory = sqlite3.Row

    # Enable WAL (Write-Ahead Logging) mode
    # This allows reads and writes to happen concurrently without locking
    # the database. Important when the agent is querying while we seed.
    conn.execute("PRAGMA journal_mode=WAL")

    # Enforce foreign key constraints
    # SQLite ignores them by default — we want them enforced
    conn.execute("PRAGMA foreign_keys=ON")

    # Set a timeout so we don't hang forever if the DB is locked
    conn.execute("PRAGMA busy_timeout=5000")


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a configured database connection.

    Usage:
        with get_connection() as conn:
            result = conn.execute("SELECT * FROM businesses").fetchall()

    The connection is committed and closed automatically.
    If an exception occurs, the transaction is rolled back.
    """
    db_path = settings.DB_ABSOLUTE_PATH

    # Ensure the directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    _configure_connection(conn)

    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Database error — transaction rolled back: %s", e)
        raise
    finally:
        conn.close()


def initialise_database() -> None:
    """
    Create all tables by running schema.sql.
    Safe to call multiple times — uses IF NOT EXISTS.
    Call this once at application startup.
    """
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        conn.executescript(schema_sql)

    logger.info("Database initialised at: %s", settings.DB_ABSOLUTE_PATH)


def get_table_names() -> list[str]:
    """Return all table names in the database. Useful for debugging."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [row["name"] for row in rows]


def get_row_counts() -> dict[str, int]:
    """
    Return row counts for all tables.
    Useful for confirming seed data was inserted correctly.
    """
    tables = get_table_names()
    counts = {}

    with get_connection() as conn:
        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) as n FROM {table}"
            ).fetchone()["n"]
            counts[table] = count

    return counts
