import asyncio
import json
import traceback
from concurrent.futures import thread

import discord
from discord import app_commands

from bot.services.db.queries_tur import (
    get_rows,
    last_insert_rowid,
    upsert_row,
    upsert_row_ai,
)
from bot.services.role_handling import get_role_requirements
from bot.services.sheets import get_valid_sheet_id


async def create_operation(
    name: str, lore: str, arsenal: str, date: str, image_url: str
):
    await upsert_row_ai(
        "operations",
        "id",
        name=name,
        desc=lore,
        arsenal=arsenal,
        date=date,
        image_url=image_url,
    )
    id = await last_insert_rowid()
    return id


async def add_operation_thread_id(thread_id: str, operation_id):
    try:
        await upsert_row_ai(
            "operations", "id", id=operation_id, signup_thread_id=thread_id
        )
    except Exception:
        print(traceback.format_exc())
    return


async def link_operation_sheet(operation_id: int, link: str) -> bool:
    sheet_id = await asyncio.to_thread(get_valid_sheet_id, link)
    if sheet_id is None:
        return False
    role_list = get_role_requirements(sheet_id, "Roles!A2:O33")
    await upsert_row(
        "operations",
        "id",
        id=operation_id,
        spreadsheet_id=sheet_id,
        roles=json.dumps(role_list),
        status="Sheet Linked",
    )
    return True


async def make_operation_orbatless(operation_id: int):
    try:
        await upsert_row_ai("operations", "id", id=operation_id, has_orbat=False)
    except Exception:
        print(traceback.format_exc())
    return


async def generate_op_names():
    operations = await get_rows("operations", order_by="id DESC", limit=25)
    return operations


async def op_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    ops = await get_rows("operations", order_by="id DESC")
    return [
        app_commands.Choice(name=op["name"][:100], value=str(op["id"]))
        for op in ops
        if current.lower() in op["name"].lower()
    ][:25]
