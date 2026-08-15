from loguru import logger
from ..response import success, error
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


def handle_list(ctx, query, body):
    schedule_list = ctx.api.schedulemanagement.list()
    return success(schedule_list)


def handle_switch(ctx, query, body):
    if body is not None:
        name = body.get('name')
    else:
        name = query.get('name')

    if not name:
        return error(400, "缺少必要参数: name")

    try:
        ctx.api.schedulemanagement.switch(name)
        logger.success(f"课程表切换成功: {name}")
        return success(message="已切换课程表")
    except Exception as e:
        logger.error(f"切换课程表失败: {e}")
        return error(500, f"切换课程表失败: {str(e)}")


def handle_add(ctx, query, body):
    if body is not None:
        name = body.get('name')
    else:
        name = query.get('name')

    if not name:
        return error(400, "缺少必要参数: name")

    try:
        ctx.api.schedulemanagement.add(name)
        logger.success(f"课程表添加成功: {name}")
        return success(message=f"课程表 '{name}' 已添加")
    except Exception as e:
        logger.error(f"添加课程表失败: {e}")
        return error(500, f"添加课程表失败: {str(e)}")


def handle_save(ctx, query, body):
    if body is not None:
        name = body.get('name')
    else:
        name = query.get('name')

    if not name:
        return error(400, "缺少必要参数: name")

    try:
        ctx.api.schedulemanagement.save(name)
        logger.success(f"课程表保存成功: {name}")
        return success(message=f"当前课程表已保存为 '{name}'")
    except Exception as e:
        logger.error(f"保存课程表失败: {e}")
        return error(500, f"保存课程表失败: {str(e)}")


register("/cwsdk/schedule/get", "GET")(handle_schedule_get)
register("/cwsdk/schedule/reload", "GET")(handle_schedule_reload)
register("/cwapi/schedulemanage/list", "GET")(handle_list)
register("/cwapi/schedulemanage/add", "GET")(handle_add)
register("/cwapi/schedulemanage/add", "POST")(handle_add)
register("/cwapi/schedulemanage/save", "GET")(handle_save)
register("/cwapi/schedulemanage/save", "POST")(handle_save)
register("/cwapi/schedulemanage/switch", "POST")(handle_save)
register("/cwapi/schedulemanage/switch", "GET")(handle_save)
