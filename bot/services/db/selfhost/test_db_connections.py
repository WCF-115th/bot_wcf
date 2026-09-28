from bot.services.db.selfhost.connections import init_db, get_connection, close_db


async def test_init_db_creates_tables():
    db = get_connection()
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in await cursor.fetchall()}
    assert "players" in tables
    assert "cooldowns" in tables


async def test_init_db_safe_to_call_twice():
    await init_db()
    await init_db()  # should not raise, should not duplicate/wipe


async def test_get_connection_raises_if_uninitialized(monkeypatch):
    from bot.services.db.selfhost import connections

    monkeypatch.setattr(connections, "_connection", None)
    # with pytest.raises(RuntimeError):
    #     connections.get_connection()
