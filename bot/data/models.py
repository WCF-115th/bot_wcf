import json
from dataclasses import dataclass

from discord import player

OPERATION_MANAGEMENT_ROLES = [
    1473796269800685658,
    1473746808093016125,
    1473330484812582952,
    1473330569877389430,
    1473330648344170587,
]

CERTIFICATIONS = {
    "Fixed Wing Pilot": 1473746267216547983,
    "Rotary Pilot": 1473746330852524092,
    "Armor Crew": 1473746363681607858,
    "Medic Certified": 1473746405561729225,
    "Engineer Certified": 1473746491746287786,
    "JTAC Certified": 1473746555004522557,
    "Recon Certified": 1473746604564676880,
    "Artillery Certified": 1473746663792443442,
}


SCHEMA = {
    "operations": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT",
            "desc": "TEXT",
            "arsenal": "TEXT",
            "signup_thread_id": "INTEGER",
            "spreadsheet_id": "TEXT",
            "date": "TEXT",
            "status": "TEXT DEFAULT 'Pending link'",
            "roles": "TEXT",
        },
    },
    "signups": {
        "columns": {
            "operation_id": "INTEGER",
            "discord_id": "INTEGER",
            "roster_name": "TEXT",
            "role1": "TEXT",
            "role2": "TEXT",
            "role3": "TEXT",
        },
        "primary_key": ["operation_id", "discord_id"],
    },
    "roster": {
        "columns": {
            "guild_id": "INTEGER",
            "discord_id": "INTEGER",
            "roster_name": "TEXT",
            "a_strikes": "INTEGER DEFAULT 0",
            "b_strikes": "INTEGER DEFAULT 0",
        },
        "primary_key": ["guild_id", "discord_id"],
    },
}


@dataclass
class Operation:
    id: int
    name: str
    desc: str
    arsenal: str
    signup_thread_id: int
    spreadsheet_id: str
    date: str
    status: str
    roles: dict

    def __post_init__(self):
        if isinstance(self.roles, str):
            self.roles = json.loads(self.roles)

    @classmethod
    async def fetch(cls, operation_id: int) -> "Operation | None":
        from bot.services.db.queries_tur import get_row

        row = await get_row("operations", {"id": operation_id})
        if row is None:
            return None
        return cls(**row)

    @classmethod
    async def fetch_by_thread(cls, thread_id: int) -> "Operation | None":
        from bot.services.db.queries_tur import get_row

        row = await get_row("operations", {"signup_thread_id": thread_id})
        if row is None:
            return None
        return cls(**row)


@dataclass
class Player:
    guild_id: int
    discord_id: int
    roster_name: str
    a_strikes: int
    b_strikes: int

    @classmethod
    async def fetch(cls, guild_id: int, discord_id: int) -> "Player | None":
        from bot.services.db.queries_tur import get_row

        row = await get_row("roster", {"guild_id": guild_id, "discord_id": discord_id})
        if row is None:
            return None
        return cls(**row)


def get_columns(table: str) -> list[str]:
    """Returns the ordered list of column names defined for a table."""
    return list(SCHEMA[table]["columns"].keys())


def get_primary_key(table: str):
    """Returns the primary key column name, or a list for composite keys."""
    if "primary_key" in SCHEMA[table]:
        return SCHEMA[table]["primary_key"]
    for name, dtype in SCHEMA[table]["columns"].items():
        if "PRIMARY KEY" in dtype:
            return name
    return None
