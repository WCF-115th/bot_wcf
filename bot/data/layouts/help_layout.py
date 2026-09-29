from bot.services.permissions import has_zeus_role
from bot.utils.messageui.layouts import *


@layout
def HelpLayout(interaction: discord.Interaction):
    items = [create_text("""
# Need help? Heres how I work:

**Operation Maintenance**
To signup to an op do `/signup` and fill in your wanted roles
To drop out, either do `/dropout` or drop out from the signup screen
""")]
    if has_zeus_role(interaction.user):
        items.append(create_text("""
**Zeus only:**
To create an operation do `/create-op` and follow the instructions
To change available roles go to your ops sheet, remove the unwanted roles from the roles list and do `/updateroles`
Operation announcement got deleted? do /resendopmessage to resend it))
"""))
    return {"items": items}
