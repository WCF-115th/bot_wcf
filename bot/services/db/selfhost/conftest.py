import pytest
from bot.services.db.selfhost.connections import init_db, close_db, get_connection


@pytest.fixture(autouse=True)
async def selfhost_db():
    await init_db()
    yield
    db = get_connection()
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (table_name,) in await cursor.fetchall():
        await db.execute(f"DELETE FROM {table_name}")
    await db.commit()
    await close_db()
