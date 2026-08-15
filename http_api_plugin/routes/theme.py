from ..response import success
from . import register


def handle_current(ctx, query, body):
    theme = ctx.api.theme.current()
    return success(theme)


register("/cwsdk/theme/current", "GET")(handle_current)
