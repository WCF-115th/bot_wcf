from bot.services.permissions import has_zeus_role
from bot.utils.messageui.layouts import *


@layout
def HelpLayout(interaction: discord.Interaction):
    items = [
        create_text("""
# ❓ Need help? Here's how I work

**Signing up**
> `/signup` — pick your preferred roles for an operation
> `/dropout` — leave the op, either with this or the drop out button on the signup screen
"""),
    ]

    if has_zeus_role(interaction.user):
        items.append(create_separator())
        items.append(create_text("""
**⚡ Zeus only**
> `/create-op` — create a new operation and follow the prompts
> `/updateroles` — sync available roles after editing the Roles list on your op sheet
> `/sendopmessage` — post a custom embed announcing the operation
"""))

    return {"items": items}
