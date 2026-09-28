import os
import aiosqlite
from bot.data.models import SCHEMA

DB_PATH = "bot.db"
print(f"DB loaded from {os.path.abspath(DB_PATH)}")
_connection: aiosqlite.Connection | None = None

# init functions


async def init_db():
    """
    Creates the shared DB connection and ensures every table in SCHEMA
    exists. Safe to call on every bot startup — uses IF NOT EXISTS, so
    existing tables/data are never touched.
    """
    global _connection
    _connection = await aiosqlite.connect(DB_PATH)
    await _connection.execute("PRAGMA journal_mode=WAL;")

    for table, definition in SCHEMA.items():
        cols = ", ".join(
            f"{name} {dtype}" for name, dtype in definition["columns"].items()
        )
        extra = ""
        if "primary_key" in definition:
            pk_cols = ", ".join(definition["primary_key"])
            extra = f", PRIMARY KEY ({pk_cols})"
        await _connection.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols}{extra})")

    await _connection.commit()


async def migrate_db():
    """
    Adds any columns present in SCHEMA but missing from the actual table
    on disk. Handles additive schema changes only (new columns/tables) —
    renames or type changes need a manual migration.
    """
    db = get_connection()
    for table, definition in SCHEMA.items():
        cursor = await db.execute(f"PRAGMA table_info({table})")
        existing_cols = {row[1] for row in await cursor.fetchall()}
        for col_name, col_type in definition["columns"].items():
            if col_name not in existing_cols:
                await db.execute(
                    f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                )
    await db.commit()


def get_connection() -> aiosqlite.Connection:
    """Returns the shared DB connection. Raises if init_db() hasn't run yet."""
    if _connection is None:
        raise RuntimeError("Database not initialized — call init_db() first")
    return _connection


async def close_db():
    """Closes the shared DB connection. Call on bot shutdown."""
    if _connection:
        await _connection.execute("PRAGMA wal_checkpoint(FULL);")
        await _connection.close()
