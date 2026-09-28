import traceback

import discord


async def generic_interaction_callback(
    interaction: discord.Interaction,
    answers: dict,
    message: str = None,
    function=None,
    button_id: str = None,
    delete_origin: bool = False,
    *,
    returnmsg: bool
):
    try:
        result_msg = (
            await function(interaction.user, **answers) if function else message
        )

        if delete_origin:
            await interaction.response.defer()
            await interaction.delete_original_response()
            if returnmsg:
                await interaction.followup.send(result_msg, ephemeral=False)
        elif returnmsg:
            await interaction.response.send_message(result_msg, ephemeral=False)
    except Exception:
        print(traceback.format_exc())
