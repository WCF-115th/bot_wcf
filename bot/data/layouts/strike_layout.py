import traceback
from functools import partial

from bot.data.models import Player
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


async def strike_callback(
    interaction: discord.Interaction,
    answers: dict,
    amount: int,
    player: Player,
    strike_type,
):
    await change_strikes(player, amount, strike_type)
    updated_player = await Player.fetch(player.guild_id, player.discord_id)
    await interaction.response.edit_message(view=StrikeLayout(updated_player))
    try:
        user = interaction.client.get_user(player.discord_id)
        await user.send("Youve been striked!")
    except discord.Forbidden:
        await interaction.user.send(
            f"{user.mention} couldn't receive the strike notification."
        )
