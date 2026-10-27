## Imports
import asyncio
import os
import traceback
import warnings
from pathlib import Path

import discord
import dotenv
from discord.ext import commands

import server
from bot.services.db.connections_tur import init_db, migrate_db
from bot.services.sheets import init_sheets
from bot.utils.console import connecting
from server import keep_alive

warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.api_core\._python_package_support")
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
        from rich.console import Console
        from rich.text import Text

        global console

        console = Console(log_time_format=lambda dt: Text(f"[{dt:%H:%M:%S}.{dt.microsecond // 1000:03d}]"))

        with console.status("[bold]Starting up...") as status:
            try:
                cogs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "cogs")
                status.update("Loading Cogs")
                console.log("[green]✓[/] Cogs")
                for filename in os.listdir(cogs_dir):
                    if filename.endswith(".py") and not filename.startswith("_"):
                        try:
                            await bot.load_extension(f"bot.cogs.{filename[:-3]}")
                        except Exception:
                            print(traceback.format_exc())
            except Exception:
                print(traceback.format_exc())

            status.update("Google Sheets")
            await init_sheets()
            console.log("[green]✓[/] Google Sheets")
            status.update("Database")
            await init_db()
            console.log("[green]✓[/] Database")
            status.update("Database Migrations")
            await migrate_db()
            console.log("[green]✓[/] Database Migrations")
        # bot startup, must be the last line of main()
        try:
            connecting.start()
            await bot.start(os.getenv("DISCORD_TOKEN"))
        except discord.errors.HTTPException as e:
            connecting.stop()
            if e.status == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                print(f"Rate limited; waiting {retry_after}s")
                await asyncio.sleep(retry_after + 30)
                print("Retry delay complete; redeploy manually")
            raise


@bot.event
async def on_ready():
    assert bot.user is not None
    # startup message, can be customized or removed
    synced = await bot.tree.sync()


"""
keep_alive()
"""
loop = asyncio.new_event_loop()
server.set_loop(loop)
loop.run_until_complete(main())
