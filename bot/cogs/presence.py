import discord
from discord.ext import commands, tasks

status_index = 0


class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_index = 0
        self.change_status.start()

    @tasks.loop(seconds=30)
    async def change_status(self):
        statuses = await _make_statuses()
        await self.bot.change_presence(activity=statuses[self.status_index])
        self.status_index = (self.status_index + 1) % len(statuses)

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Presence(bot))


async def _make_statuses():
    return [
        discord.Game(name="I am you and you are me"),
        discord.Game(name="Lotta money in this shit"),
        discord.Game(name="This sure is an Armed Assault, 3"),
        discord.Game(name="Don't play reforger..."),
        discord.Game(name="Vrchat"),
        discord.Activity(type=discord.ActivityType.listening, name="Chuds"),
        discord.Activity(type=discord.ActivityType.watching, name="Chuds"),
        discord.Activity(type=discord.ActivityType.streaming, name="Chuds"),
        discord.Activity(
            type=discord.ActivityType.competing, name="Break a leg supremacy!"
        ),
        discord.Activity(
            type=discord.ActivityType.competing,
            name="DONT JOIN OTHER UNITS WCF SUPREMACY",
        ),
        discord.Game(name="we luhhh webknight"),
        discord.Game(name="we luhhh Phenosi"),
        discord.Game(name="Chud bot is currently scanning for chuds..."),
        discord.Game(name="get off vrchat -_-"),
        discord.Game(name="Made by a cs2 semi-chud player"),
        discord.Game(name="Made in france 🤢"),
        discord.Game(name="Femboy spotted 👀"),
        discord.Game(name="Woman Spotted 👀"),
        discord.Game(name="Male Spotted 👀"),
        discord.Game(name="Stop looking at my status, weirdo"),
    ]
