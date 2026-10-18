from loguru import logger

from ..response import success, error
from . import register


DEFAULT_LIMIT = 100


def _get_limit(query, body):
    raw = body.get("limit") if body is not None else query.get("limit")
    if raw is None or raw == "":
        return DEFAULT_LIMIT

    try:
        limit = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"无效的 limit: {raw}")

    if limit <= 0:
        raise ValueError(f"limit 必须为正整数: {limit}")
    return limit


def handle_logs(ctx, query, body):
    try:
        limit = _get_limit(query, body)
    except ValueError as e:
        return error(400, str(e))

    try:
        logs = ctx.api.diagnostics.get_logs(limit=limit)
    except Exception as e:
        logger.error(f"读取诊断日志失败: {e}")
        return error(500, f"读取诊断日志失败: {str(e)}")

    count = len(logs) if logs else 0
    logger.success(f"诊断日志读取成功，共 {count} 条")
    return success(logs)


register("/cwsdk/diagnostics", "GET")(handle_logs)
register("/cwsdk/diagnostics", "POST")(handle_logs)
