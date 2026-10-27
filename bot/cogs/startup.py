from discord.ext import commands
from rich.panel import Panel
from rich.table import Table

from bot.utils.console import connecting, console


class Startup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._announced = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._announced:  # on_ready also fires on reconnects
            return
        self._announced = True
        connecting.stop()

        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_row("Bot", f"{self.bot.user} [dim]({self.bot.user.id})[/]")
        table.add_row("Guilds", str(len(self.bot.guilds)))
        table.add_row("Latency", f"{self.bot.latency * 1000:.0f} ms")
        table.add_row("Commands", " ".join(f"/{c.name}" for c in self.bot.tree.get_commands()))
        console.print(Panel(table, title="[bold green]Online[/]", expand=False))


async def setup(bot):
    await bot.add_cog(Startup(bot))
