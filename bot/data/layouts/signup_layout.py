import asyncio
import random

import discord

from bot.data.callbacks.signup_callbacks import drop_out_callback, signup_callback
from bot.data.models import Operation
from bot.services.db.queries_tur import get_rows
from bot.services.signup import generate_certifications
from bot.utils.messageui.components import *
from bot.utils.messageui.layouts import BaseLayoutV1, layout

SIGNUP_MESSAGE = [
    "{username} has joined the Battlefield!",
    "{username} has finished their MEPS",
    "This OPs Barracks bunny is {username}!",
    "{username} is going to be left for dead during this op!",
    "{username} is NOT Solid snake",
    "He was gay? {username}?",
    "Watch it {username}",
    "{username} spent 20 years in the can",
    "History is written by the victor, {username} is not gonna be one",
    "Fuck you Pheonix - {username}",
    "This person is a chud ---> {username}",
    "Kill 3 billion people {username}",
    "A femboy is going to pounce on {username} during the op",
    "this guy loves cakes {username}",
    "get a JOB   {username}",
    "1v1 me dust 2 {username}",
    "by signing up, you agree to being shot violently at your home address {username}",
    "this person is pretentious --->{username}",
    "this person has 2000h on vrchat ----> {username}",
    "{username} is a horrible pilot - Spindly",
    "This guy is a stupid french fuck who will overdose you with Fent ----> {username}",
    "This guy is a cag larper -----> {username}",
    "This guy sucks at tarkov -----> {username}",
    "This guy will give you pervitn in pre-op ------> {username}",
]


@layout
def Signup(
    user: discord.User,
    operation: Operation,
    *,
    available_role: dict[str, str] | None,
    role1: str | None = None,
    role2: str | None = None,
    role3: str | None = None,
    roster_name: str | None = None,
):
    def _format_certifications(earned: list[str]) -> str:
        if not earned:
            return "**Certifications**\n> None"
        lines = "\n".join(f"> ✅ {cert}" for cert in earned)
        return f"**Certifications**\n{lines}"

    items = [
        create_text(f"-# {user.name}"),
        create_text(f"""
# 🪖 {operation.name}

{_format_certifications(generate_certifications(user))}

Select your preferred roles below, in order of priority.
"""),
    ]

    def _role_options(all_roles: dict[str, str], selected: str | None):
        return [
            {"label": r, "value": r, "desc": desc, "default": r == selected}
            for r, desc in all_roles.items()
        ]

    choices = [role1, role2, role3]
    labels = ["🥇 1st choice", "🥈 2nd choice", "🥉 3rd choice"]

    for i, (label, selected) in enumerate(zip(labels, choices), start=1):
        items.append(
            create_select_menu(
                *_role_options(available_role, selected),
                placeholder=label,
                id=f"role_select_{i}",
            )
        )

    extra = [
        create_button(
            label="✅ Sign up",
            style=discord.ButtonStyle.success,
            callback=signup_callback,
        ),
        create_button(
            label="🚪 Drop out",
            style=discord.ButtonStyle.danger,
            callback=drop_out_callback,
        ),
    ]

    return {"items": items, "extra": extra, "answers": {"roster_name": roster_name}}


@layout
def SignedUp(interaction: discord.Interaction):
    message = random.choice(SIGNUP_MESSAGE).format(username=interaction.user.mention)
    if interaction.user.id == 824794855309049876:
        message = "this guy is a stupid chud pilot who only makes custom gear for himself -----> {username}".format(
            username=interaction.user.mention
        )
    items = [create_text(message)]
    return {"items": items}


@layout
def DropOut(interaction):
    items = [create_text(f"{interaction.user.mention} dropped out!")]
    return {"accent": discord.Color.red(), "items": items}


@layout
def SignupList(operation: Operation, signup_list: str):
    items = [
        create_text(f"""
# 📋 {operation.name}

**Signed-up operators**
{signup_list}
"""),
    ]
    return {"items": items}


async def generate_signuplist(operation: Operation) -> str:
    rows = await get_rows("signups", {"operation_id": operation.id})
    if not rows:
        return "> No signups yet."
    return "\n".join(f"> • {row['roster_name']}" for row in rows)
