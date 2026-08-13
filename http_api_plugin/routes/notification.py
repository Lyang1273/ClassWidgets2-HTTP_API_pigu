from ClassWidgets.SDK import NotificationLevel
from loguru import logger
from ..response import success, error
from . import register


def handle_notification(ctx, query, body):
    if body is not None:
        data = body
    else:
        # GET 兼容：从查询参数获取数据
        data = {
            'level': query.get('level', 'INFO'),
            'title': query.get('title', '') or '来自 HTTP API 的通知',
            'message': query.get('message', ''),
            'duration': query.get('duration', '5000'),
            'closable': query.get('closable', 'true').lower() in ('true', '1', 'yes'),
        }

    level_str = data.get('level', 'INFO').upper()
    level_map = {
        'INFO': NotificationLevel.INFO,
        'ANNOUNCEMENT': NotificationLevel.ANNOUNCEMENT,
        'WARNING': NotificationLevel.WARNING,
        'SYSTEM': NotificationLevel.SYSTEM,
    }
    level = level_map.get(level_str, NotificationLevel.INFO)

    title = data.get('title', '来自 HTTP API 的通知')
    message = data.get('message', '')
    try:
        duration = int(data.get('duration', 5000))
    except (ValueError, TypeError):
        duration = 5000
    closable = bool(data.get('closable', True))

    if ctx.notification_provider is None:
        return error(500, "通知提供者未注册")

    ctx.notification_provider.push(
        level=level,
        title=title,
        message=message,
        duration=duration,
        closable=closable
    )
    logger.success(f"通知发送成功: {title} - {message}")
    return success(message="通知已发送")


register("/cwsdk/notification", "GET")(handle_notification)
register("/cwsdk/notification", "POST")(handle_notification)
register("/cwsdk/notifi", "GET")(handle_notification)
register("/cwsdk/notifi", "POST")(handle_notification)
