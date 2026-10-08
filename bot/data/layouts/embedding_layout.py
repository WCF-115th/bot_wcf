from bot.services.permissions import has_zeus_role
from bot.utils.messageui.layouts import *


class CreateChangelogModal(discord.ui.Modal, title="Create Changelog"):
    try:
        name = discord.ui.TextInput(
            label="Changelog Title",
            placeholder="Name of changelog",
            max_length=100,
            required=True,
        )

        desc = discord.ui.TextInput(
            label="Changelog Description",
            placeholder="Quick description about your changelog",
            style=discord.TextStyle.long,
            max_length=200,
        )

        content = discord.ui.TextInput(
            label="Changelog Content",
            placeholder="Everything in your changelog",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True,
        )

        label = discord.ui.Label(
            text="Upload image file",
            component=discord.ui.FileUpload(
                max_values=1,
                required=False,
            ),
        )

        async def on_submit(self, interaction: discord.Interaction):
            image = self.label.component.values[0].url
            await interaction.channel.send(
                view=ChangelogLayout(
                    self.name.value, self.desc.value, self.content.value, image
                )
            )
            await interaction.response.send_message("Changelog sent!", ephemeral=True)

    except:
        print(traceback.format_exc())


@layout
def ChangelogLayout(title: str, desc: str, content: str, image: str | None = None):
    items = []
    if image:
        items.append(create_image(image))
    items.extend(
        [
            create_text(f"## {title}"),
            create_text(desc),
            create_separator(),
            create_text(content),
        ]
    )
    return {"items": items}
