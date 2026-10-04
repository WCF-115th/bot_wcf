import asyncio

import discord

from bot.data.models import Operation
from bot.services.db.queries_tur import get_row, upsert_row_ai
from bot.services.role_handling import extract_roles
from bot.services.sheets import discord_log
from bot.services.signup import drop_signup, upsert_signup_row
from bot.utils.messageui.components import *
from bot.utils.messageui.layouts import layout


async def signup_callback(interaction: discord.Interaction, answers: dict):
    await interaction.response.edit_message(view=ProcessingView(), content=None)

    operation = await Operation.fetch_by_thread(interaction.channel_id)
    roster_name = answers.get("roster_name") or interaction.user.name

    role1, role2, role3 = extract_roles(answers)

    existing = await get_row(
        "signups", {"operation_id": operation.id, "discord_id": interaction.user.id}
    )

    await upsert_row_ai(
        "signups",
        "operation_id,discord_id",
        operation_id=operation.id,
        discord_id=interaction.user.id,
        roster_name=roster_name,
        role1=role1,
        role2=role2,
        role3=role3,
    )
    await asyncio.to_thread(
        upsert_signup_row,
        operation.spreadsheet_id,
        roster_name,
        role1,
        role2,
        role3,
    )

    if existing is None:
        from bot.data.layouts.signup_layout import SignedUp

        await interaction.delete_original_response()
        await interaction.channel.send(view=SignedUp(interaction))
    else:
        await interaction.edit_original_response(view=SignUpUpdated())


async def drop_out_callback(interaction: discord.Interaction, answers: dict):
    operation = await Operation.fetch_by_thread(interaction.channel_id)

    existing = await get_row(
        "signups", {"operation_id": operation.id, "discord_id": interaction.user.id}
    )

    if existing is None:
        await interaction.response.send_message(
            "You're not signed up for this operation.", ephemeral=True
        )
        return

    await interaction.response.send_message(view=ProcessingView(), ephemeral=True)

    roster_row = await get_row(
        "roster", {"guild_id": interaction.guild_id, "discord_id": interaction.user.id}
    )

    roster_name = roster_row["roster_name"] if roster_row else interaction.user.name

    await drop_signup(operation, interaction.user.id, interaction.guild_id, roster_name)

    from bot.data.layouts.signup_layout import DropOut

    await interaction.delete_original_response()
    await interaction.channel.send(view=DropOut(interaction))


@layout
def ProcessingView():
    return {"items": [create_text("⏳ Processing your request, please wait...")]}


@layout
def SignUpUpdated():
    return {"items": [create_text("Sign-up updated")]}
