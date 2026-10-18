from loguru import logger

from ..response import success, error
from ..serializers import to_jsonable
from . import register


def handle_runtime(ctx, query, body):
    runtime = ctx.api.runtime

    response_data = {
        'current_time': runtime.current_time,
        'current_day_of_week': runtime.current_day_of_week,
        'current_week': runtime.current_week,
        'current_week_of_cycle': runtime.current_week_of_cycle,
        'time_offset': runtime.time_offset,
        'schedule_meta': runtime.schedule_meta,
        'current_day_entries': runtime.current_day_entries,
        'current_entry': runtime.current_entry,
        'current_subject': runtime.current_subject,
        'current_title': runtime.current_title,
        'next_entries': runtime.next_entries,
        'current_status': runtime.current_status,
        'progress': runtime.progress,
        'remaining_time': runtime.remaining_time,
    }

    logger.success("GET /embedded/runtime 请求成功")
    return success(response_data)


def _get_subjects(ctx) -> list:
    """获取当前课表的科目列表"""
    schedule = to_jsonable(ctx.api.schedule.get())
    if not isinstance(schedule, dict):
        return []
    return schedule.get("subjects") or []


def _normalize_ids(raw) -> list:
    """把 id/ids 参数统一成列表"""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(",") if s.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(s).strip() for s in raw if str(s).strip()]
    return []


def handle_subject_name(ctx, query, body):
    """
    根据 subjectId 查科目名称
    用法:
      GET  /embedded/subject/name?id=pe
      GET  /embedded/subject/name?id=pe,math,chinese
      POST /embedded/subject/name  {"ids": ["pe", "math"]}
    """
    if body is not None:
        raw = body.get("id") or body.get("ids")
    else:
        raw = query.get("id") or query.get("ids")

    ids = _normalize_ids(raw)
    if not ids:
        return error(400, "缺少必要参数: id")

    subjects = _get_subjects(ctx)
    index = {s.get("id"): s for s in subjects if s.get("id")}

    result = {}
    for sid in ids:
        subject = index.get(sid)
        if subject:
            result[sid] = {
                "name": subject.get("name", ""),
                "simplifiedName": subject.get("simplifiedName") or "",
                "color": subject.get("color") or "",
                "icon": subject.get("icon") or "",
            }
        else:
            result[sid] = None

    if len(ids) == 1:
        sid = ids[0]
        info = result.get(sid)
        if info is None:
            return error(404, f"未找到科目: {sid}")
        return success({"id": sid, **info})

    return success(result)


def handle_subject_list(ctx, query, body):
    """列出所有科目 id 与名称"""
    subjects = _get_subjects(ctx)
    items = [
        {
            "id": s.get("id", ""),
            "name": s.get("name", ""),
            "simplifiedName": s.get("simplifiedName") or "",
            "color": s.get("color") or "",
            "icon": s.get("icon") or "",
        }
        for s in subjects
    ]
    logger.success(f"GET /embedded/subject/list 请求成功，共 {len(items)} 个科目")
    return success(items)


register("/embedded/runtime", "GET")(handle_runtime)
register("/embedded/subject/name", "GET")(handle_subject_name)
register("/embedded/subject/name", "POST")(handle_subject_name)
register("/embedded/subject/list", "GET")(handle_subject_list)
