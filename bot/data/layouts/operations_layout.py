import traceback
from datetime import datetime
from functools import partial

import discord

from bot.data.models import Operation
from bot.services.operations import create_operation, link_operation_sheet
from bot.services.sheets import spreadsheet_url
from bot.utils.messageui.layouts import *


def _format_discord_date(date_str: str, fmt: str = "d") -> str:
    dt = datetime.strptime(date_str, "%d/%m/%y")
    timestamp = int(dt.timestamp())
    return f"<t:{timestamp}:{fmt}>"


class CreateOperationModal(discord.ui.Modal, title="Create Operation"):
    name = discord.ui.TextInput(
        label="Operation Name",
        placeholder="Name of your operation",
        required=True,
    )

    lore = discord.ui.TextInput(
        label="Operation Lore",
        placeholder="Text or link about your operations lore",
        style=discord.TextStyle.paragraph,
        max_length=2000,
    )

    arsenal = discord.ui.TextInput(
        label="Operation Arsenal",
        placeholder="Arsenal Name",
        style=discord.TextStyle.short,
        max_length=100,
    )

    date = discord.ui.TextInput(
        label="Operation Date",
        placeholder="MM/DD/YYYY",
        style=discord.TextStyle.short,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        thread_id = interaction.channel_id
        discord_date = _format_discord_date(self.date.value)
        try:
            id = await create_operation(
                self.name.value,
                self.lore.value,
                self.arsenal.value,
                discord_date,
                thread_id,
            )

            await interaction.response.send_message(
                view=SheetLinking(id),
                ephemeral=False,
            )
        except Exception:
            print(traceback.format_exc())


@layout
def SheetLinking(operation_id: int):
    items = [create_text("""
1. Open the template: https://docs.google.com/spreadsheets/d/1Esp4debnAbhl5zJOQpVIu4gtmMDHvHhy3LyVJ8c6aGM/copy
2. Click File > Make a copy (or Ctrl+Alt+Shift+C)
3. Rename the copy with your op's name
4. Click the Share button (top right)
5. Paste this email and give it editor access: `wcf-service@wcf-bot.iam.gserviceaccount.com`
6. Click Send (no need to notify)
7. Copy your sheet's link (Copy link button, or just the URL bar)
8. Come back here and click on 'I've shared it'
""")]

    extra = [
        create_button(
            label="I've shared it",
            style=discord.ButtonStyle.green,
            callback=partial(confirm_callback, operation_id=operation_id),
        )
    ]

    return {"items": items, "extra": extra}


async def confirm_callback(
    interaction: discord.Interaction, _answers, operation_id: int
):
    await interaction.response.send_modal(SheetLinkModal(operation_id=operation_id))


class SheetLinkModal(discord.ui.Modal, title="Link Sheet"):
    link = discord.ui.TextInput(
        label="Google Sheet Link",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        required=True,
    )

    def __init__(self, operation_id: int):
        super().__init__()
        self.operation_id = operation_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            ok = await link_operation_sheet(self.operation_id, self.link.value)
            msg = (
                "Successfully linked sheet !"
                if ok
                else "Error, check google sheet link or permissions !"
            )
            await interaction.followup.send(msg, ephemeral=True)

            operation = await Operation.fetch(self.operation_id)
            await interaction.message.edit("Operation post succesfully created!")
        except Exception:
            import traceback

            print(traceback.format_exc())


@layout
def DisplayOperation(operation: Operation):
    items = [
        create_text(f"""
# 🪖 {operation.name}

📅 {operation.date}

{operation.desc}

**Loadout**
> {operation.arsenal}

To sign up do `/signup` and follow the prompts.

-# 📋 [Attendance & ORBAT]({spreadsheet_url(operation.spreadsheet_id)})
    """),
    ]
    return {"items": items}
