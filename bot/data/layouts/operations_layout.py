import json
import traceback
from datetime import datetime
from functools import partial

import discord
from discord import components

from bot.data.models import Operation
from bot.services.db.queries_tur import count_signups
from bot.services.operations import add_operation_thread_id, create_operation, link_operation_sheet, make_operation_orbatless
from bot.services.sheets import spreadsheet_url
from bot.utils.messageui.layouts import *


def _format_discord_date(date_str: str, fmt: str = "d") -> str:
    try:
        dt = datetime.strptime(date_str, "%d/%m/%y")
    except (ValueError, TypeError):
        return date_str

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

    label = discord.ui.Label(
        text="Upload image file",
        component=discord.ui.FileUpload(
            max_values=5,
            required=False,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            discord_date = _format_discord_date(self.date.value)

            attachments = self.label.component.values
            image_urls = [a.url for a in attachments] if attachments else []

            id = await create_operation(
                self.name.value,
                self.lore.value,
                self.arsenal.value,
                discord_date,
                json.dumps(image_urls),
                interaction.user.id,
            )

            await interaction.response.send_message(
                view=SheetLinking(id),
                ephemeral=False,
            )
        except Exception:
            print(traceback.format_exc())


@layout
def SheetLinking(operation_id: int):
    items = [
        create_text("""
# 📋 Link your Attendance & ORBAT sheet

1. [Open the template](https://docs.google.com/spreadsheets/d/1Esp4debnAbhl5zJOQpVIu4gtmMDHvHhy3LyVJ8c6aGM/copy) and click **Make a copy**
2. Rename the copy with your op's name
3. Click **Share** (top right)
4. Paste this email and give it **Editor** access:
`wcf-service@wcf-bot.iam.gserviceaccount.com`
5. Click **Send** (no need to notify)
6. Copy your sheet's link
7. Come back here and click **I've shared it**
"""),
    ]

    extra = [
        create_button(
            label="I've shared it",
            style=discord.ButtonStyle.green,
            callback=partial(confirm_callback, operation_id=operation_id),
        )
    ]
    extra = [
        create_button_row(
            create_button(
                label="I've shared it",
                style=discord.ButtonStyle.green,
                callback=partial(confirm_callback, operation_id=operation_id),
                wrap=False,
            ),
            create_button(
                label="Don't use an orbat",
                style=discord.ButtonStyle.danger,
                callback=partial(confirm_callback, operation_id=operation_id, orbat=False),
                wrap=False,
            ),
        )
    ]

    return {"items": items, "extra": extra}


async def confirm_callback(
    interaction: discord.Interaction,
    _answers,
    operation_id: int,
    orbat: bool = True,
):
    if orbat:
        await interaction.response.send_modal(SheetLinkModal(operation_id=operation_id))
        return

    await interaction.response.defer(ephemeral=True)

    try:
        await interaction.message.delete()
        await make_operation_orbatless(operation_id)

        operation = await Operation.fetch(operation_id)

        op_thread = interaction.client.get_channel(OP_THREADS_ID)
        if op_thread is None:
            raise RuntimeError("Operation threads channel was not found")

        message, thread = await op_thread.create_thread(
            name=operation.name,
            view=DisplayOperation(operation),
        )

        await add_operation_thread_id(thread.id, operation.id)

    except Exception:
        print(traceback.format_exc())
        await interaction.followup.send(
            "Failed to create the operation. Please check the logs.",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        "Operation created!",
        ephemeral=True,
    )


OP_THREADS_ID = 1474849828143104193


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
        from bot.data.layouts.edit_op_layout import EditOperation, update_op_post

        try:
            await interaction.response.defer(ephemeral=True)

            ok = await link_operation_sheet(self.operation_id, self.link.value)
            if not ok:
                await interaction.followup.send("Error, check google sheet link or permissions !", ephemeral=True)
                return

            operation = await Operation.fetch(self.operation_id)

            if operation.signup_thread_id:  # already posted, so this is a re-link
                await update_op_post(interaction.client, operation)
                await interaction.edit_original_response(view=EditOperation(operation, await count_signups(operation.id)))
                await interaction.followup.send("Sheet re-linked!", ephemeral=True)
                return

            # first link: create the op post
            await interaction.delete_original_response()
            op_forum = interaction.client.get_channel(OP_THREADS_ID)
            thread, _ = await op_forum.create_thread(name=operation.name, view=DisplayOperation(operation))
            await add_operation_thread_id(thread.id, operation.id)
            await interaction.followup.send("Successfully linked sheet! Operation created!", ephemeral=True)
        except Exception:
            print(traceback.format_exc())


@layout
def DisplayOperation(operation: Operation):
    locked = operation.status == "locked"
    items = [
        create_text(f"""
# 🪖 {operation.name}

📅 {operation.date}

{"🔒 Signups locked" if locked else "🟢 Signups open"}

{operation.desc}

**Loadout**
> {operation.arsenal}
"""),
    ]
    # adding orbat link
    if operation.has_orbat:
        items.append(create_text(f"\n-# 📋 [Attendance & ORBAT]({spreadsheet_url(operation.spreadsheet_id)})"))
    # adding image
    image_urls = json.loads(operation.image_url) if operation.image_url else []
    if image_urls:
        items.append(create_image(*image_urls))

    if not locked:
        items += [create_separator(), create_text("Ready to deploy? Run `/signup` and follow the prompts. <@&1473741029638410313>")]

    return {"items": items}
