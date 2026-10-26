import asyncio
import json
import traceback

import discord
from discord import app_commands
from discord.ext import commands

from bot.data.callbacks.signup_callbacks import drop_out_callback, signup_callback
from bot.data.layouts.edit_op_layout import EditOperation
from bot.data.layouts.embedding_layout import CreateChangelogModal
from bot.data.layouts.help_layout import HelpLayout
from bot.data.layouts.operations_layout import CreateOperationModal, DisplayOperation
from bot.data.layouts.profile_layout import profile_layout
from bot.data.layouts.signup_layout import SignedUp, Signup, SignupList, generate_signuplist
from bot.data.layouts.strike_layout import StrikeLayout
from bot.data.models import Operation, Player
from bot.services import operations
from bot.services.db.queries_tur import count_signups, delete_operation, get_player_signups, upsert_row_ai
from bot.services.operations import op_autocomplete, upsert_row
from bot.services.permissions import *
from bot.services.role_handling import available_roles, extract_roles, get_role_requirements, parse_role_requirements
from bot.services.roster_handling import get_roster_name, sync_roster
from bot.services.sheets import spreadsheet_url
from bot.services.signup import generate_certifications, get_user_signup_roles


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create-op", description="(Zeus) Create a new operation")
    @requires(zeus_only, not_in_op_thread)
    async def _command_create_op(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(CreateOperationModal())
        except:
            print(traceback.format_exc())

    @app_commands.command(name="signup", description="Sign up for the operation in this thread")
    @requires(in_op_thread, op_not_locked)
    async def _command_signup(self, interaction: discord.Interaction):
        try:
            operation = await Operation.fetch_by_thread(interaction.channel_id)
            if operation is None:
                await interaction.response.send_message("No operation found in this channel.", ephemeral=True)
                return
            roster_name = await get_roster_name(interaction.guild_id, interaction.user.id, interaction.user.name)
            if operation.has_orbat:
                role1, role2, role3 = await get_user_signup_roles(operation.id, interaction.user.id)
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
            else:
                await signup_callback(interaction)
        except:
            print(traceback.format_exc())

    @app_commands.command(name="updateroles", description="(Zeus) Re-sync available roles from the op's Roles sheet")
    @requires(zeus_only, in_op_thread, not_orbatless_op)
    async def _command_updateroles(self, interaction: discord.Interaction):
        try:
            operation = await Operation.fetch_by_thread(interaction.channel_id)

            if operation is None:
                await interaction.response.send_message("No operation found in this channel.", ephemeral=True)
                return

            role_list = await asyncio.to_thread(get_role_requirements, operation.spreadsheet_id, "Roles!A2:O33")

            await upsert_row(
                "operations",
                "id",
                id=operation.id,
                roles=json.dumps(role_list),
            )

            await interaction.response.send_message("Role list updated.", ephemeral=True)
        except Exception:
            print(traceback.format_exc())

    @app_commands.command(name="syncroster", description="(Zeus) Sync the server roster from a roster sheet link")
    @requires(zeus_only)
    async def _command_syncroster(self, interaction: discord.Interaction, roster_link: str):
        await interaction.response.defer(ephemeral=True)
        count = await sync_roster(roster_link, interaction.guild_id)
        await interaction.followup.send(f"Roster synced ({count} entries).")

    @app_commands.command(name="dropout", description="Drop out of the operation in this thread")
    @requires(in_op_thread)
    async def _command_dropout(self, interaction: discord.Interaction):
        try:
            await drop_out_callback(interaction, {})
        except:
            print(traceback.format_exc())

    @app_commands.command(name="sendopmessage", description="(Zeus) Re-post this operation's info message")
    @requires(zeus_only, in_op_thread)
    async def _command_sendopmessage(self, interaction: discord.Interaction):
        try:
            operation = await Operation.fetch_by_thread(interaction.channel_id)
            await interaction.channel.send(view=DisplayOperation(operation))
            await interaction.response.send_message("Operation message resent!", ephemeral=True)
        except:
            print(traceback.format_exc())

    @app_commands.command(name="help", description="Show how the bot works")
    async def _command_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=HelpLayout(interaction), ephemeral=True)

    @app_commands.command(name="listslots", description="(Zeus) List everyone signed up for this operation")
    @requires(zeus_only, in_op_thread)
    async def _command_listslots(self, interaction: discord.Interaction):
        operation = await Operation.fetch_by_thread(interaction.channel_id)
        signup_list = await generate_signuplist(operation)
        await interaction.response.send_message(view=SignupList(operation, signup_list))

    @app_commands.command(name="strike", description="(Zeus) Add or remove strikes for a player")
    @requires(zeus_only)
    async def _command_strike(self, interaction: discord.Interaction, member: discord.Member):
        try:
            player = await Player.fetch(interaction.guild_id, member.id)
            await interaction.response.send_message(view=StrikeLayout(player), ephemeral=True)
        except Exception:
            print(traceback.format_exc())

    @app_commands.command(name="chud", description="Call someone a chud")
    @requires(abstract)
    async def _command_chud(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        await interaction.response.send_message(f"{member.mention} is a chud")
        await member.send("https://klipy.com/gifs/sorry-you-are-a-chud")

    @app_commands.command(name="changelog", description="(Zeus) Post a changelog announcement")
    @requires(zeus_only)
    async def _command_changelog(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(CreateChangelogModal())
        except Exception:
            print(traceback.format_exc())

    @app_commands.command(name="deleteop", description="(Zeus) Delete an operation and its signups")
    @app_commands.autocomplete(op=op_autocomplete)
    @requires(zeus_only)
    async def _command_deleteop(self, interaction: discord.Interaction, op: str):
        if not op.isdigit():
            await interaction.response.send_message("Pick an operation from the list.", ephemeral=True)
            return

        operation = await Operation.fetch(int(op))
        if operation is None:
            await interaction.response.send_message("Operation not found.", ephemeral=True)
            return

        await delete_operation(operation.id)
        await interaction.response.send_message(f"Deleted **{operation.name}**.", ephemeral=True)

    @app_commands.command(name="info", description="Show a player's roster profile and signups")
    async def _command_info(self, interaction: discord.Interaction, member: discord.Member | None = None):
        try:
            member = member or interaction.user
            player = await Player.fetch(interaction.guild_id, member.id)
            if not player:
                await interaction.response.send_message("Not on the roster.", ephemeral=True)
                return
            signups = await get_player_signups(player.discord_id)
            await interaction.response.send_message(view=profile_layout(player, member, signups), ephemeral=True)
        except:
            print(traceback.format_exc())

    @app_commands.command(name="editop", description="(Zeus) Edit or lock the operation in this thread")
    @requires(zeus_only, in_op_thread)
    async def _command_editop(self, interaction: discord.Interaction):
        operation = await Operation.fetch_by_thread(interaction.channel_id)
        count = await count_signups(operation.id)
        await interaction.response.send_message(view=EditOperation(operation, count), ephemeral=True)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await thread.join()


async def setup(bot):
    await bot.add_cog(Commands(bot))
