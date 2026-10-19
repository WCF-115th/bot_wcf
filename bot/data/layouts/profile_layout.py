from bot.data.models import Player
from bot.services.db.queries_tur import get_player_signups
from bot.utils.messageui.components import *
from bot.utils.messageui.layouts import layout


@layout
def profile_layout(player: Player, member: discord.Member, signups):
    """Player profile card."""
    header = f"## {player.roster_name}\n{member.mention}"

    strikes = f"**Attendance strikes:** {player.a_strikes}\n" f"**Behaviour strikes:** {player.b_strikes}"

    if signups:
        lines = []
        for s in signups:
            roles = " / ".join(r for r in (s["role1"], s["role2"], s["role3"]) if r)
            thread = f"<#{s['thread_id']}>" if s["thread_id"] else s["name"]
            lines.append(f"• {thread} — {s['date']} · *{roles}*")
        ops = "### Signed-up operations\n" + "\n".join(lines)
    else:
        ops = "### Signed-up operations\n*No upcoming signups.*"

    return {
        "items": [
            create_text(header),
            create_text(strikes),
            create_text(ops),
        ]
    }
