import asyncio

from bot.services.db.queries_tur import get_row, upsert_row_ai
from bot.services.sheets import extract_sheet_id, find_header_map, get_values

ROSTER_COLUMNS = {
    "name": "NAME",
    "discord_id": "DISCORD ID",
}


async def sync_roster(
    spreadsheet_link: str, guild_id: int, sheet_name: str = "Roster"
) -> int:
    spreadsheet_id = extract_sheet_id(spreadsheet_link)
    col_map, header_row = await asyncio.to_thread(
        find_header_map, spreadsheet_id, sheet_name, set(ROSTER_COLUMNS.values())
    )

    name_col = col_map[ROSTER_COLUMNS["name"]]
    id_col = col_map[ROSTER_COLUMNS["discord_id"]]

    last_col_letter = chr(ord("A") + max(col_map.values()))
    data_start = header_row + 1

    values = await asyncio.to_thread(
        get_values, spreadsheet_id, f"{sheet_name}!A{data_start}:{last_col_letter}1000"
    )
    print(f"roster: read {len(values)} rows, first: {values[:1]}")

    count = 0
    for row in values:
        name = row[name_col].strip() if len(row) > name_col else ""
        user_id = row[id_col].strip() if len(row) > id_col else ""

        if not name or not user_id:
            continue

        await upsert_row_ai(
            "roster",
            "guild_id,user_id",
            guild_id=guild_id,
            user_id=int(user_id),
            roster_name=name,
        )
        count += 1

    return count


async def get_roster_name(guild_id: int, user_id: int, fallback: str) -> str:
    row = await get_row("roster", {"guild_id": guild_id, "user_id": user_id})
    return row["roster_name"] if row else fallback
