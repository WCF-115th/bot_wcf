import discord

from bot.data.models import Player
from bot.services.db.queries_tur import upsert_row_ai


async def change_strikes(player: Player, number: int, strike_type: str):
    if strike_type == "attendance":
        await upsert_row_ai(
            "roster",
            "guild_id,discord_id",
            guild_id=player.guild_id,
            discord_id=player.discord_id,
            roster_name=player.roster_name,
            a_strikes=player.a_strikes + number,
        )
    elif strike_type == "behaviour":
        await upsert_row_ai(
            "roster",
            "guild_id,discord_id",
            guild_id=player.guild_id,
            discord_id=player.discord_id,
            roster_name=player.roster_name,
            b_strikes=player.b_strikes + number,
        )
