from bot.services.permissions import has_zeus_role
from bot.utils.messageui.layouts import *


@layout
def HelpLayout(interaction: discord.Interaction):
    items = [
        create_text("""
# ❓ Need help? Here's how I work

**Signing up**
> `/signup` — pick your preferred roles for the operation in this thread
> `/dropout` — leave the op, either with this or the drop out button on the signup screen

**General**
> `/info` — show a player's roster profile and signups (yours by default)
> `/help` — show this message
"""),
    ]

    if has_zeus_role(interaction.user):
        items.append(create_separator())
        items.append(create_text("""
**⚡ Zeus only**
> `/create-op` — create a new operation and follow the prompts
> `/updateroles` — sync available roles after editing the Roles list on your op sheet
> `/sendopmessage` — re-post this operation's info message in the thread
> `/listslots` — list everyone signed up for this operation
> `/syncroster` — sync the server roster from a roster sheet link
> `/strike` — add or remove attendance and behaviour strikes for a player
> `/changelog` — post a changelog announcement
> `/deleteop` — delete an operation and its signups
"""))

    return {"items": items}
