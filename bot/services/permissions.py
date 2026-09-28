import functools

import discord

from bot.data.models import Operation

OPERATION_MANAGEMENT_ROLES = [
    1473796269800685658,
    1473746808093016125,
    1473330484812582952,
    1473330569877389430,
    1473330648344170587,
]


def requires(*checks):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            for check in checks:
                ok, message = await check(interaction)
                if not ok:
                    await interaction.response.send_message(message)
                    return
            return await func(self, interaction, *args, **kwargs)

        return wrapper

    return decorator


def has_zeus_role(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return any(rid in role_ids for rid in OPERATION_MANAGEMENT_ROLES)


async def zeus_only(interaction: discord.Interaction):
    if not has_zeus_role(interaction.user):
        return False, "Zeus role required."
    return True, None


async def in_op_thread(interaction: discord.Interaction):
    operation = await Operation.fetch_by_thread(interaction.channel_id)
    if operation is None:
        return False, "No operation found in this channel."
    return True, None
