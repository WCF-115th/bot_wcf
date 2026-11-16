import functools

import discord

from bot.data.models import OPERATION_MANAGEMENT_ROLES, Operation


def requires(*checks):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            for check in checks:
                ok, message = await check(interaction)
                if not ok:
                    if message == discord.ui.LayoutView:
                        await interaction.response.send_message(view=message)
                    else:
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


async def not_in_op_thread(interaction: discord.Interaction):
    operation = await Operation.fetch_by_thread(interaction.channel_id)
    if operation is not None:
        return False, "There is already an existing operation in this channel."
    return True, None


async def not_orbatless_op(interaction: discord.Interaction):
    operation = await Operation.fetch_by_thread(interaction.channel_id)

    if not operation.has_orbat:
        return (
            False,
            "You can't use this command because this is an orbatless operation",
        )

    return True, None


async def privileges(interaction: discord.Interaction):
    if interaction.user.id == 317580648074313728:
        return False, "You lost your chud privileges abstract..."
    elif interaction.user.id == 1180697002632302713:
        return False, "You lost your chud privileges spindly..."
    return True, None


async def op_not_locked(interaction: discord.Interaction):
    operation = await Operation.fetch_by_thread(interaction.channel_id)
    if operation and operation.status == "locked":
        return False, "Signups for this operation are locked."
    return True, None
