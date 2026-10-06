import traceback
from typing import Callable

import discord
from discord import ui


def create_container(*, accent=None, items=None) -> ui.Container:
    container = ui.Container()
    if accent:
        container.accent_colour = accent
    if items:
        for item in items:
            container.add_item(item)
    return container


def create_text(content: str) -> ui.TextDisplay:
    return ui.TextDisplay(content)


def create_separator(
    *,
    spacing: discord.SeparatorSpacing = discord.SeparatorSpacing.small,
    visible: bool = True
) -> ui.Separator:
    return ui.Separator(spacing=spacing, visible=visible)


def create_select_menu(
    *options: dict, placeholder: str = None, id: str = "NO ID", callback=None
):
    """
    Creates a select menu for BaseLayout type objects.

    Args:
        options: dicts with:
            - label (str)
            - desc (str, optional)
            - value (str, optional)
            - emoji (str, optional)
        placeholder: placeholder text shown when nothing is selected
        id: custom_id for this select, key in view.answers
        callback: optional async function(interaction, value) called immediately
                  on selection if not None.
    """
    row = ui.ActionRow()
    select = ui.Select(
        custom_id=id,
        placeholder=placeholder,
        options=[
            discord.SelectOption(
                label=opt["label"],
                description=(
                    (opt["desc"][:97] + "...")
                    if opt.get("desc") and len(opt["desc"]) > 100
                    else opt.get("desc")
                ),
                value=opt.get("value", opt["label"]),
                emoji=opt.get("emoji"),
                default=opt.get("default", False),
            )
            for opt in options
        ],
    )

    # callback handling
    async def _cb(interaction: discord.Interaction):
        view = select.view  # BaseLayout object
        view.answers[id] = select.values[0]

        if callback:
            await callback(interaction, select.values[0])
        else:
            await interaction.response.defer()

    select.callback = _cb

    # select menu creation
    row.add_item(select)
    return row


def create_selectmenuv2(
    *options: dict, placeholder: str = None, id: str = "NO ID", callback=None
):
    row = ui.ActionRow()

    option_lookup = {}

    discord_options = []

    for index, opt in enumerate(options):
        value = str(index)
        option_lookup[value] = opt

        discord_options.append(
            discord.SelectOption(
                label=opt["label"],
                description=(
                    (opt["desc"][:97] + "...")
                    if opt.get("desc") and len(opt["desc"]) > 100
                    else opt.get("desc")
                ),
                value=value,
                emoji=opt.get("emoji"),
            )
        )

    select = ui.Select(
        custom_id=id,
        placeholder=placeholder,
        options=discord_options,
    )

    async def _cb(interaction: discord.Interaction):
        view = select.view

        selected = option_lookup[select.values[0]]

        view.answers[id] = selected

        if callback:
            await callback(interaction, selected)
        else:
            await interaction.response.defer()

    select.callback = _cb

    row.add_item(select)
    return row


def create_button(
    *,
    label: str,
    custom_id: str = None,
    emoji: discord.Emoji | str = None,
    style: discord.ButtonStyle = discord.ButtonStyle.success,
    callback=None,
    function: str = None,
    delete_origin: bool = False,
    returnmsg: bool = True
):
    """
    Creates a button for BaseLayout type objects.

    Args:
        label: text shown on the button
        custom_id: custom_id for this button, used to identify it in interactions
        emoji: optional emoji shown on the button
        style: discord.ButtonStyle (default: success)
        callback: optional async function(interaction, answers, function=...) run on click
        function: optional function that will be called inside the callback
        delete_origin: if True, deletes the original message before sending the result
    """
    btn = ui.Button(style=style, label=label, emoji=emoji, custom_id=custom_id)

    # callback handling
    async def _cb(interaction: discord.Interaction):
        view = btn.view  # BaseLayout object

        if callback:

            if function:
                await callback(
                    interaction,
                    view.answers,
                    button_id=custom_id,
                    function=function,
                    delete_origin=delete_origin,
                    returnmsg=returnmsg,
                )
            else:
                await callback(interaction, view.answers)

        else:
            await interaction.response.defer()

    btn.callback = _cb

    # button creation
    row = ui.ActionRow()
    row.add_item(btn)
    return row


def create_section(*, text: str = "\u200b", thumbnail_url: str) -> ui.Section:
    return ui.Section(
        ui.TextDisplay(text),
        accessory=ui.Thumbnail(media=discord.UnfurledMediaItem(url=thumbnail_url)),
    )


def add_items(layout: ui.LayoutView, items: list):
    for item in items:
        layout.add_item(item)


def create_image(*images: discord.Attachment | str) -> ui.MediaGallery:
    gallery = ui.MediaGallery()

    for image in images:
        url = image.url if isinstance(image, discord.Attachment) else image

        gallery.add_item(ui.MediaGalleryItem(media=discord.UnfurledMediaItem(url=url)))

    return gallery
