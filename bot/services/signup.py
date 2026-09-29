import asyncio
import traceback

import discord

from bot.data.models import CERTIFICATIONS
from bot.services.db.queries_tur import delete_signup, get_row
from bot.services.sheets import *

SIGNUP_COLUMNS = {
    "username": "Name",
    "role1": "Slot 1",
    "role2": "Slot 2",
    "role3": "Slot 3",
}


def generate_certifications(member: discord.Member):
    role_ids = {r.id for r in member.roles}
    earned = [
        cert_name
        for cert_name, cert_id in CERTIFICATIONS.items()
        if cert_id in role_ids
    ]
    return earned


async def get_user_signup_roles(
    operation_id: int, user_id: int
) -> tuple[str | None, str | None, str | None]:
    signup = await get_row(
        "signups", {"operation_id": operation_id, "user_id": user_id}
    )
    if signup is None:
        return None, None, None
    return signup["role1"], signup["role2"], signup["role3"]


async def drop_signup(operation, user_id: int, guild_id: int, roster_name: str):
    """
    Removes a signup from both the DB and the signup sheet.
    """
    await delete_signup(operation.id, user_id)

    try:
        await asyncio.to_thread(drop_signup_row, operation.spreadsheet_id, roster_name)
    except Exception:
        print(traceback.format_exc())


def upsert_signup_row(
    spreadsheet_id: str,
    username: str,
    role1: str,
    role2: str,
    role3: str,
    *,
    sheet_name: str = "Signup",
):
    discord_log(
        f"📋 Signup values before Sheets update:\n"
        f"spreadsheet_id=`{spreadsheet_id}`\n"
        f"roster_name=`{username!r}`\n"
        f"role1=`{role1!r}`\n"
        f"role2=`{role2!r}`\n"
        f"role3=`{role3!r}`"
    )
    col_map, header_row = find_header_map(
        spreadsheet_id, sheet_name, set(SIGNUP_COLUMNS.values())
    )

    username_col = col_map[SIGNUP_COLUMNS["username"]]
    role_cols = [
        col_map[SIGNUP_COLUMNS["role1"]],
        col_map[SIGNUP_COLUMNS["role2"]],
        col_map[SIGNUP_COLUMNS["role3"]],
    ]

    target_row = find_row_by_value_or_empty(
        spreadsheet_id, sheet_name, col_map, username_col, username, header_row
    )

    cells = [
        (username_col, f"'{username}"),
        (role_cols[0], role1),
        (role_cols[1], role2),
        (role_cols[2], role3),
    ]

    write_row_cells(spreadsheet_id, sheet_name, target_row, cells)


def drop_signup_row(
    spreadsheet_id: str,
    username: str,
    *,
    sheet_name: str = "Signup",
):
    try:
        col_map, header_row = find_header_map(
            spreadsheet_id, sheet_name, set(SIGNUP_COLUMNS.values())
        )

        username_col = col_map[SIGNUP_COLUMNS["username"]]
        role_cols = [
            col_map[SIGNUP_COLUMNS["role1"]],
            col_map[SIGNUP_COLUMNS["role2"]],
            col_map[SIGNUP_COLUMNS["role3"]],
        ]

        row_index = find_row_by_value(
            spreadsheet_id, sheet_name, col_map, username_col, username, header_row
        )

        if row_index is None:
            return

        cols_to_clear = [username_col] + role_cols
        write_row_cells(
            spreadsheet_id, sheet_name, row_index, [(c, "") for c in cols_to_clear]
        )
    except Exception:
        print(traceback.format_exc())
