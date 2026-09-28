import asyncio
import json
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from bot.data.callbacks.signup_callbacks import drop_out_callback
from bot.data.layouts.operations_layout import CreateOperationModal
from bot.data.layouts.signup_layout import Signup
from bot.data.models import Operation
from bot.services.db.queries_tur import get_row
from bot.services.operations import upsert_row
from bot.services.permissions import *
from bot.services.role_handling import (
    available_roles,
    extract_roles,
    get_role_requirements,
    parse_role_requirements,
)
from bot.services.roster_handling import get_roster_name, sync_roster
from bot.services.sheets import spreadsheet_url
from bot.services.signup import generate_certifications, get_user_signup_roles


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create-op", description="testing")
    @requires(zeus_only)
    async def _command_create_op(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateOperationModal())

    @app_commands.command(name="signup", description="testing")
    @requires(in_op_thread)
    async def _command_signup(self, interaction: discord.Interaction):
        try:
            operation = await Operation.fetch_by_thread(interaction.channel_id)
            if operation is None:
                await interaction.response.send_message(
                    "No operation found in this channel.", ephemeral=True
                )
                return

            role1, role2, role3 = await get_user_signup_roles(
                operation.id, interaction.user.id
            )
            roster_name = await get_roster_name(
                interaction.guild_id, interaction.user.id, interaction.user.name
            )
            available_role = available_roles(interaction.user, operation.roles)

            await interaction.response.send_message(
                view=Signup(
                    interaction.user,
                    operation,
                    available_role=available_role,
                    role1=role1,
                    role2=role2,
                    role3=role3,
                    roster_name=roster_name,
                ),
                ephemeral=True,
            )
        except Exception:
            print(traceback.format_exc())

    @app_commands.command(name="updateroles", description="testing")
    @requires(zeus_only, in_op_thread)
    async def _command_updateroles(self, interaction: discord.Interaction):
        try:
            operation = await Operation.fetch_by_thread(interaction.channel_id)

            if operation is None:
                await interaction.response.send_message(
                    "No operation found in this channel.", ephemeral=True
                )
                return

            role_list = await asyncio.to_thread(
                get_role_requirements, operation.spreadsheet_id, "Roles!A2:O33"
            )

            await upsert_row(
                "operations",
                "id",
                id=operation.id,
                roles=json.dumps(role_list),
            )

            await interaction.response.send_message(
                "Role list updated.", ephemeral=True
            )
        except Exception:
            print(traceback.format_exc())

    @app_commands.command(name="syncroster", description="testing")
    @requires(zeus_only)
    async def _command_syncroster(
        self, interaction: discord.Interaction, roster_link: str
    ):
        await interaction.response.defer(ephemeral=True)
        count = await sync_roster(roster_link, interaction.guild_id)
        await interaction.followup.send(f"Roster synced ({count} entries).")

    @app_commands.command(name="dropout", description="testing")
    @requires(in_op_thread)
    async def _command_dropout(self, interaction: discord.Interaction):
        await drop_out_callback(interaction, {})


async def setup(bot):
    await bot.add_cog(Commands(bot))
