import traceback

from bot.utils.callbacks import *
from bot.utils.messageui.components import *


class BaseLayoutV1(ui.View):
    def __init__(self):
        super().__init__()
        self.answers = {}


class BaseLayoutV2(ui.LayoutView):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
        self.answers = {}


def layout(func):
    """
    Turns a function into a BaseLayoutV2 allowing it to use functions instead of classes.
    The function should return a dict with:
        items  — list of items inside the container (required)
        accent — discord.Color for the container (optional)
        extra  — top-level items outside the container, e.g. buttons (optional)
    Example:
        @layout
        def ProfileCreation():
            return {
                "accent": discord.Color.purple(),
                "items": [create_text("Hello"), create_separator()],
                "extra": [create_button(label="Go", ...)],
            }
        view = ProfileCreation()
    """

    def __init__(self, *args, **kwargs):
        BaseLayoutV2.__init__(self)
        result = func(*args, **kwargs)
        self.answers.update(result.get("answers", {}))
        container = create_container(accent=result.get("accent", discord.Color.green()))
        add_items(container, result["items"])
        add_items(container, [create_separator(), create_text("-# An .ateron project")])
        self.add_item(container)

        for item in result.get("extra", []):
            self.add_item(item)

    return type(func.__name__, (BaseLayoutV2,), {"__init__": __init__})


async def send_layout(ctx, layout, ephemeral=False):
    try:
        await ctx.send(view=layout)
    except Exception as e:
        print(traceback.format_exc())
