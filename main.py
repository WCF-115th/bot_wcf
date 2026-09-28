## Imports

import asyncio
import os
import traceback
from pathlib import Path

import discord
import dotenv
from discord.ext import commands

import server
from bot.services.db.connections_tur import init_db, migrate_db
from bot.services.sheets import init_sheets
from server import keep_alive

## Bot Settings

description = """your_bot_description_here"""

# Intents are required for certain features, you can adjust them as needed.
intents = discord.Intents.default()

# Basic bot intents, necessary for bot's functionality
intents.members = True
intents.message_content = True

## Startup

# .env should contain the bot token as DISCORD_TOKEN
# loads env variable for local hosting, on Render these are set in the dashboard and accessed as env variables as well
dotenv.load_dotenv(Path(__file__).parent / "cfg/.env", verbose=True)

bot = commands.Bot(
    command_prefix="!",
    description=description,
    intents=intents,
    application_id=int(os.getenv("APPLICATION_ID")),
)

# to add a cog, use bot.load_extension('cogs.your_cog_name') in the main() function below.


async def main():
    async with bot:
        try:
            cogs_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "bot", "cogs"
            )
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    try:
                        await bot.load_extension(f"bot.cogs.{filename[:-3]}")
                        print(f"Loaded: {filename}")
                    except Exception:
                        print(f"Failed to load {filename}:")
                        print(traceback.format_exc())  # Example cog
        except Exception:
            print(traceback.format_exc())

        await init_sheets()
        await init_db()
        await migrate_db()

        # bot startup, must be the last line of main()
        await bot.start(os.getenv("DISCORD_TOKEN"))


@bot.event
async def on_ready():
    assert bot.user is not None
    # startup message, can be customized or removed
    print(f"Logged in as {bot.user} (ID: {bot.user.id}), bot is ready")

    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands: {[cmd.name for cmd in synced]}")

    print("Bot fully launched!")


keep_alive()
loop = asyncio.new_event_loop()
server.set_loop(loop)
loop.run_until_complete(main())
asyncio.run(main())
