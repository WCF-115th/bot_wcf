import traceback
from functools import partial

from bot.data.models import Player
from bot.services.operations import generate_op_names
from bot.services.strikes import change_strikes
from bot.utils.messageui.layouts import *


def _make_strike_button(label, style, **kwargs):
    btn = ui.Button(style=style, label=label)

    async def _cb(interaction: discord.Interaction):
        view = btn.view
        await strike_callback(interaction, view.answers, **kwargs)

    btn.callback = _cb
    return btn


@layout
def StrikeLayout(player: Player):
    items = [
        create_text(f"""
# 📋 Strike Record

**{player.roster_name}**

> 🟥 Behaviour strikes: **{player.b_strikes}**
> 🟨 Attendance strikes: **{player.a_strikes}**
"""),
    ]

    row = ui.ActionRow()
    row.add_item(
        _make_strike_button(
            "➕ Attendance",
            discord.ButtonStyle.success,
            amount=1,
            player=player,
            strike_type="attendance",
        )
    )
    row.add_item(
        _make_strike_button(
            "➖ Attendance",
            discord.ButtonStyle.danger,
            amount=-1,
            player=player,
            strike_type="attendance",
        )
    )
    row.add_item(
        _make_strike_button(
            "➕ Behaviour",
            discord.ButtonStyle.success,
            amount=1,
            player=player,
            strike_type="behaviour",
        )
    )
    row.add_item(
        _make_strike_button(
            "➖ Behaviour",
            discord.ButtonStyle.danger,
            amount=-1,
            player=player,
            strike_type="behaviour",
        )
    )

    extra = [row]
    return {"items": items, "extra": extra}


class SelectOperationModal(discord.ui.Modal, title="Select operation"):
    def __init__(
        self, operations: list[dict], player: Player, strike_type: str, amount: int
    ):
        super().__init__()
        self.player = player
        self.strike_type = strike_type
        self.amount = amount
        self.names = {str(op["id"]): op["name"] for op in operations}
        self.op = discord.ui.Label(
            text="Operation",
            component=discord.ui.Select(
                options=[
                    discord.SelectOption(label="No operation", value="No operation"),
                    *[
                        discord.SelectOption(
                            label=op["name"][:100],
                            value=str(op["id"]),
                        )
                        for op in operations
                    ],
                ],
            ),
        )
        self.add_item(self.op)

    async def on_submit(self, interaction: discord.Interaction):
        op_name = self.names[self.op.component.values[0]]

        await change_strikes(self.player, self.amount, self.strike_type)
        updated_player = await Player.fetch(
            self.player.guild_id, self.player.discord_id
        )
        await interaction.response.edit_message(view=StrikeLayout(updated_player))

        await notify_strike(interaction, updated_player, self.strike_type, op_name)


async def notify_strike(
    interaction: discord.Interaction,
    player: Player,
    strike_type: str,
    op_name: str | None = None,
):
    user = await interaction.client.fetch_user(player.discord_id)
    try:
        await user.send(view=StrikeMessage(player, strike_type, op_name))
    except discord.Forbidden:
        await interaction.followup.send(
            f"{user.mention} couldn't receive the strike notification.", ephemeral=True
        )


async def strike_callback(
    interaction: discord.Interaction,
    answers: dict,
    amount: int,
    player: Player,
    strike_type,
):
    if strike_type == "attendance" and amount == 1:
        operations = await generate_op_names()
        if operations:
            await interaction.response.send_modal(
                SelectOperationModal(operations, player, strike_type, amount)
            )
            return

    await change_strikes(player, amount, strike_type)
    updated_player = await Player.fetch(player.guild_id, player.discord_id)
    await interaction.response.edit_message(view=StrikeLayout(updated_player))

    if amount == 1:
        await notify_strike(interaction, updated_player, strike_type)


@layout
def StrikeMessage(player: Player, strike_type: str, op_name: str | None = None):
    total = player.a_strikes + player.b_strikes
    absent = (
        f"**{op_name}**" if op_name != "No operation" else "an op you signed up for"
    )
    if strike_type == "attendance":
        items = [
            create_text(f"""
# ⚠️ Attendance Strike

You've received an **attendance strike** for being absent from `{op_name}` you signed up for, or not re-slotting into overflow.

> You currently have **{total}** strike{"s" if total != 1 else ""}.

To have it removed, play **2 missions per strike**, unless told otherwise.

-# 🟨 2+ strikes: locked into Operator until fully active again
-# 🟥 6+ strikes: reverted to Newbie, roles withheld until proven active again
"""),
        ]
    else:
        items = [
            create_text(f"""
# ⚠️ Behaviour Strike

You've received a **behaviour strike**, issued for in-op conduct that goes against the rules of the Charter and/or Unit, beyond the point of a verbal warning.

Strikes stay on your record and are only removed after the behaviour is corrected over **3 months**, or at staff discretion.

> You currently have **{total}** strike{"s" if total != 1 else ""}.

-# 🟨 2+ strikes: you are rank locked to newbie
-# 🟥 3 strikes: banned from the unit
"""),
        ]

    return {"items": items}
