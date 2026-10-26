import json
import re
from datetime import datetime
from functools import partial

from discord import ui

from bot.data.layouts.operations_layout import DisplayOperation, SheetLinkModal
from bot.data.models import Operation
from bot.services.db.queries_tur import count_signups
from bot.services.operations import update_operation
from bot.services.sheets import spreadsheet_url
from bot.utils.messageui.components import *
from bot.utils.messageui.layouts import layout

DATE_RE = re.compile(r"<t:(\d+):[a-zA-Z]>")


def _date_to_input(discord_date: str) -> str:
    match = DATE_RE.search(discord_date or "")
    if not match:
        return ""
    return datetime.fromtimestamp(int(match.group(1))).strftime("%d/%m/%y")


def _format_discord_date(date_str: str, fmt: str = "d") -> str:
    try:
        dt = datetime.strptime(date_str, "%d/%m/%y")
    except (ValueError, TypeError):
        return date_str

    timestamp = int(dt.timestamp())
    return f"<t:{timestamp}:{fmt}>"


def _action_row(*buttons) -> ui.ActionRow:
    row = ui.ActionRow()
    for label, style, callback in buttons:
        btn = ui.Button(label=label, style=style)
        btn.callback = callback
        row.add_item(btn)
    return row


@layout
def EditOperation(operation: Operation, signup_count: int):
    locked = operation.status == "locked"
    orbat = f"[Open sheet]({spreadsheet_url(operation.spreadsheet_id)}) · {len(operation.roles or {})} roles" if operation.has_orbat else "No ORBAT"

    items = [
        create_text(f"""
# 🛠️ Edit operation

**{operation.name}**
📅 {operation.date}
{"🔒 Signups locked" if locked else "🟢 Signups open"}

> 👥 Signed up: **{signup_count}**
> 🖼️ Images: **{len(operation.images or [])}**
> 📋 {orbat}
"""),
    ]

    buttons = [
        ("Edit details", discord.ButtonStyle.primary, partial(edit_details_callback, operation_id=operation.id)),
        ("Unlock signups" if locked else "Lock signups", discord.ButtonStyle.success if locked else discord.ButtonStyle.danger, partial(toggle_lock_callback, operation_id=operation.id)),
    ]
    if operation.has_orbat:
        buttons.append(("Re-link sheet", discord.ButtonStyle.secondary, partial(relink_callback, operation_id=operation.id)))

    return {"items": items, "extra": [_action_row(*buttons)]}


async def _update_op_post(client: discord.Client, operation: Operation, rename: bool = False):
    """Refresh the public op post (and thread name) after a change."""
    try:
        thread = await client.fetch_channel(operation.signup_thread_id)
        message = await thread.fetch_message(thread.id)  # a forum post's first message shares the thread's id
        await message.edit(view=DisplayOperation(operation))
        if rename and thread.name != operation.name:
            await thread.edit(name=operation.name)
    except discord.HTTPException:
        print(traceback.format_exc())


async def edit_details_callback(interaction: discord.Interaction, operation_id: int):
    operation = await Operation.fetch(operation_id)
    await interaction.response.send_modal(EditOperationModal(operation))


async def toggle_lock_callback(interaction: discord.Interaction, operation_id: int):
    await interaction.response.defer()
    operation = await Operation.fetch(operation_id)
    new_status = "pending" if operation.status == "locked" else "locked"
    await update_operation(operation.id, status=new_status)

    operation = await Operation.fetch(operation_id)
    await _update_op_post(interaction.client, operation)
    await interaction.edit_original_response(view=EditOperation(operation, await count_signups(operation.id)))


async def relink_callback(interaction: discord.Interaction, operation_id: int):
    await interaction.response.send_modal(SheetLinkModal(operation_id=operation_id))


class EditOperationModal(discord.ui.Modal, title="Edit operation"):
    def __init__(self, operation: Operation):
        super().__init__()
        self.operation_id = operation.id
        self.name = ui.TextInput(label="Operation Name", default=operation.name, max_length=100)
        self.date = ui.TextInput(label="Date (DD/MM/YY)", default=_date_to_input(operation.date), max_length=8)
        self.lore = ui.TextInput(
            label="Operation Lore",
            style=discord.TextStyle.paragraph,
            default=operation.desc,
            max_length=2000,
        )
        self.arsenal = ui.TextInput(label="Arsenal", style=discord.TextStyle.paragraph, default=operation.arsenal)
        self.images = ui.Label(
            text="New images (optional)",
            description="Leave empty to keep the current images",
            component=ui.FileUpload(max_values=5, required=False),
        )
        for item in (self.name, self.date, self.lore, self.arsenal, self.images):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            try:
                date = _format_discord_date(self.date.value)
            except ValueError:
                await interaction.response.send_message("Invalid date format, use DD/MM/YY.", ephemeral=True)
                return

            await interaction.response.defer()

            fields = {
                "name": self.name.value,
                "desc": self.lore.value,
                "arsenal": self.arsenal.value,
                "date": date,
            }
            uploads = self.images.component.values
            if uploads:
                fields["images"] = json.dumps([a.url for a in uploads])

            await update_operation(self.operation_id, **fields)
            operation = await Operation.fetch(self.operation_id)
            await _update_op_post(interaction.client, operation, rename=True)
            await interaction.edit_original_response(view=EditOperation(operation, await count_signups(operation.id)))
        except Exception:
            print(traceback.format_exc())
