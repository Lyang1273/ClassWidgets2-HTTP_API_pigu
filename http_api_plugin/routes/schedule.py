from loguru import logger

from ..response import success
from ..serializers import to_jsonable
from . import register


def handle_schedule_get(ctx, query, body):
    schedule_get = ctx.api.schedule.get()
    logger.success("GET /schedule/get 请求成功")
    return success(to_jsonable(schedule_get))


def handle_schedule_reload(ctx, query, body):
    ctx.api.schedule.reload()
    logger.success("GET /schedule/reload 请求成功")
    return success(message="课程表已重新加载")


register("/cwsdk/schedule/get", "GET")(handle_schedule_get)
register("/cwsdk/schedule/reload", "GET")(handle_schedule_reload)
