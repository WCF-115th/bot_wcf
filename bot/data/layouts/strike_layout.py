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
        create_text(f"{player.roster_name}"),
        create_text(f"\u200b- Behaviour strikes: {player.b_strikes}"),
        create_text(f"\u200b- Attendance strikes: {player.a_strikes}"),
    ]  # whatever this already has

    row = ui.ActionRow()
    row.add_item(
        _make_strike_button(
            "Add attendance strike",
            discord.ButtonStyle.success,
            amount=1,
            player=player,
            strike_type="attendance",
        )
    )
    row.add_item(
        _make_strike_button(
            "Add behaviour strike",
            discord.ButtonStyle.success,
            amount=1,
            player=player,
            strike_type="behaviour",
        )
    )
    row.add_item(
        _make_strike_button(
            "Remove attendance strike",
            discord.ButtonStyle.danger,
            amount=-1,
            player=player,
            strike_type="attendance",
        )
    )
    row.add_item(
        _make_strike_button(
            "Remove behaviour strike",
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
    try:
        await change_strikes(player, amount, strike_type)
        updated_player = await Player.fetch(player.guild_id, player.discord_id)
        await interaction.response.edit_message(view=StrikeLayout(updated_player))
    except Exception:
        print(traceback.format_exc())
