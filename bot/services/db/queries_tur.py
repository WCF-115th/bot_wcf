from typing import Any, Optional

from bot.data.models import SCHEMA
from bot.services.db.connections_tur import get_connection

# query functions


async def get_row(table: str, where: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Fetches a single row matching all given conditions, as a dict keyed
    by column name. Returns None if no row matches.

    Args:
        table: name of the table to read from
        where: dict of column=value pairs that must all match
            (e.g. {"user_id": 123} or {"user_id": 123, "item_id": 5})
    """
    client = get_connection()
    where_clause = " AND ".join(f"{col} = ?" for col in where)
    result = await client.execute(f"SELECT * FROM {table} WHERE {where_clause}", list(where.values()))
    if not result.rows:
        return None
    return dict(zip(result.columns, result.rows[0]))


async def get_rows(
    table: str,
    where: Optional[dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    """
    Fetches all rows matching the given conditions, as a list of dicts
    keyed by column name. Returns an empty list if no rows match.

    Args:
        table: name of the table to read from
        where: dict of column=value pairs that must all match
            (e.g. {"guild_id": 123})
        order_by: order by including column and  sorting
        limit: max number of rows to return
    """
    client = get_connection()
    query = f"SELECT * FROM {table}"
    params: list[Any] = []

    if where:
        where_clause = " AND ".join(f"{col} = ?" for col in where)
        query += f" WHERE {where_clause}"
        params.extend(where.values())

    if order_by:
        query += f" ORDER BY {order_by}"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    result = await client.execute(query, params)
    if not result.rows:
        return []
    return [dict(zip(result.columns, row)) for row in result.rows]


async def upsert_row(
    table: str,
    conflict_col: str,
    *,
    returning: str | None = None,
    **values: Any,
) -> None:
    """
    Upserts a row.

    Args:
        table: name of the table to write to
        conflict_col: the column that determines uniqueness/primary key, Must be included in values.
        **values: column=value pairs to insert/update.
    """
    client = get_connection()
    cols = list(values.keys())
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(cols)
    update_clause = ", ".join(f"{col} = excluded.{col}" for col in cols if col != conflict_col)

    sql = f"""
            INSERT INTO {table} ({col_names}) VALUES ({placeholders})
            ON CONFLICT({conflict_col}) DO UPDATE SET {update_clause}
            """
    if returning:
        sql += f" RETURNING {returning}"

    result = await client.execute(sql, list(values.values()))

    if returning and result.rows:
        return result.rows[0][returning]


async def upsert_row_ai(
    table: str,
    conflict_col: str,
    *,
    returning: str | None = None,
    **values: Any,
) -> Any | None:
    client = get_connection()

    cols = list(values)
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(cols)

    conflict_cols = {col.strip() for col in conflict_col.split(",")}

    update_cols = [col for col in cols if col not in conflict_cols]

    if update_cols:
        update_clause = ", ".join(f"{col} = excluded.{col}" for col in update_cols)
        conflict_action = f"DO UPDATE SET {update_clause}"
    else:
        conflict_action = "DO NOTHING"

    sql = f"""
        INSERT INTO {table} ({col_names})
        VALUES ({placeholders})
        ON CONFLICT({conflict_col}) {conflict_action}
    """

    if returning:
        sql += f" RETURNING {returning}"

    result = await client.execute(
        sql,
        list(values.values()),
    )

    if returning and result.rows:
        return result.rows[0][returning]

    return None


async def increment_column(table: str, where_col: str, where_val: Any, column: str, amount: int) -> None:
    """
    Increments (or decrements, with a negative amount) a single numeric
    column on an existing row, without touching any other column.
    """
    client = get_connection()
    await client.execute(
        f"UPDATE {table} SET {column} = {column} + ? WHERE {where_col} = ?",
        [amount, where_val],
    )


async def last_insert_rowid() -> int:
    """
    Returns the rowid of the most recently inserted row on this connection.
    """
    client = get_connection()
    result = await client.execute("SELECT last_insert_rowid()")
    return result.rows[0][0]


async def delete_signup(operation_id: int, discord_id: int):
    client = get_connection()
    await client.execute(
        "DELETE FROM signups WHERE operation_id = ? AND discord_id = ?",
        [operation_id, discord_id],
    )


async def delete_operation(operation_id: int):
    client = get_connection()
    await client.execute("DELETE FROM signups WHERE operation_id = ?", [operation_id])
    await client.execute("DELETE FROM operations WHERE id = ?", [operation_id])


async def get_player_signups(discord_id: int) -> list[dict]:
    client = get_connection()
    rows = await client.execute(
        """
        SELECT o.id, o.name, o.date, o.status, o.signup_thread_id,
               s.role1, s.role2, s.role3
        FROM signups s
        JOIN operations o ON o.id = s.operation_id
        WHERE s.discord_id = ?
        ORDER BY o.date
        """,
        (discord_id,),
    )
    cols = ("id", "name", "date", "status", "thread_id", "role1", "role2", "role3")
    return [dict(zip(cols, r)) for r in rows]


async def count_signups(operation_id: int) -> int:
    result = await get_connection().execute("SELECT COUNT(*) FROM signups WHERE operation_id = ?", [operation_id])
    return result.rows[0][0]
