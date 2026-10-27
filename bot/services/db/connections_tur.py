import os
from pathlib import Path

import dotenv
import libsql_client

from bot.data.models import SCHEMA

_client: libsql_client.Client | None = None


# init functions


async def init_db():
    """
    Creates the shared Turso client and ensures every table in SCHEMA
    exists. Safe to call on every bot startup — uses IF NOT EXISTS, so
    existing tables/data are never touched.
    """
    global _client
    _client = libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://"),
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )

    for table, definition in SCHEMA.items():
        cols = ", ".join(f"{name} {dtype}" for name, dtype in definition["columns"].items())
        extra = ""
        if "primary_key" in definition:
            pk_cols = ", ".join(definition["primary_key"])
            extra = f", PRIMARY KEY ({pk_cols})"
        await _client.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols}{extra})")

    result = await get_connection().execute("SELECT name FROM sqlite_master WHERE type='table'")


async def migrate_db():
    """
    Adds any columns present in SCHEMA but missing from the actual table
    on disk. Handles additive schema changes only (new columns/tables) —
    renames or type changes need a manual migration.
    """
    client = get_connection()
    for table, definition in SCHEMA.items():
        result = await client.execute(f"PRAGMA table_info({table})")
        existing_cols = {row[1] for row in result.rows}
        for col_name, col_type in definition["columns"].items():
            if col_name not in existing_cols:
                await client.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")


def get_connection() -> libsql_client.Client:
    """Returns the shared Turso client. Raises if init_db() hasn't run yet."""
    if _client is None:
        raise RuntimeError("Database not initialized — call init_db() first")
    return _client


async def close_db():
    """Closes the shared Turso client. Call on bot shutdown."""
    if _client:
        await _client.close()
