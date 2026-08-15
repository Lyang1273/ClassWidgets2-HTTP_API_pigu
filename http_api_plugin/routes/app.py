from ..response import success
from . import register


def handle_restart(ctx, query, body):
    ctx.api.application.restart()
    return success("已下发重启命令")


def handle_info(ctx, query, body):
    info = ctx.api.application.get_info()
    return success(info)


register("/cwsdk/app/info", "GET")(handle_info)
register("/cwsdk/app/restart", "GET")(handle_restart)
