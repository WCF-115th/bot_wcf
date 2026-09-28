from typing import Any, Optional

from bot.data.models import SCHEMA, get_columns
from bot.services.db.connections_tur import get_connection

# query functions


async def get_row(table: str, where: dict[str, Any]) -> dict[str, Any]:
    """
    Fetches a single row matching all given conditions, as a dict keyed
    by column name (read from SCHEMA, not the cursor). Returns None if
    no row matches.

    Args:
        table: name of the table to read from
        where: dict of column=value pairs that must all match
            (e.g. {"user_id": 123} or {"user_id": 123, "item_id": 5})
    """
    db = get_connection()
    where_clause = " AND ".join(f"{col} = ?" for col in where)
    async with db.execute(
        f"SELECT * FROM {table} WHERE {where_clause}", tuple(where.values())
    ) as cursor:
        row = await cursor.fetchone()
        return dict(zip(get_columns(table), row)) if row else None


async def upsert_row(table: str, conflict_col: str, **values: Any) -> None:
    """
    Upserts a row.

    Args:
        table: name of the table to write to
        conflict_col: the column that determines uniqueness/primary key, Must be included in values.
        **values: column=value pairs to insert/update.
    """
    db = get_connection()
    cols = list(values.keys())
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(cols)
    update_clause = ", ".join(
        f"{col} = excluded.{col}" for col in cols if col != conflict_col
    )

    await db.execute(
        f"""
        INSERT INTO {table} ({col_names}) VALUES ({placeholders})
        ON CONFLICT({conflict_col}) DO UPDATE SET {update_clause}
        """,
        tuple(values.values()),
    )
    await db.commit()


async def increment_column(
    table: str, where_col: str, where_val: Any, column: str, amount: int
) -> None:
    """
    Increments (or decrements, with a negative amount) a single numeric
    column on an existing row, without touching any other column.
    """
    db = get_connection()
    await db.execute(
        f"UPDATE {table} SET {column} = {column} + ? WHERE {where_col} = ?",
        (amount, where_val),
    )
    await db.commit()


async def delete_rows_by_user_id(
    user_id: int, exclude_tables: Optional[list[str]] = None
) -> None:
    db = get_connection()
    exclude_tables = exclude_tables or ["players"]

    for table, metadata in SCHEMA.items():
        if "user_id" not in metadata["columns"] or table in exclude_tables:
            continue
        await db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))

    await db.execute("DELETE FROM players WHERE user_id = ?", (user_id,))
    await db.commit()
