from loguru import logger

from . import register


def handle_runtime(ctx, query, body):
    runtime = ctx.api.runtime

    response_data = {}
    field_map = {
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
    for key, default in field_map.items():
        if ctx.config.is_field_enabled(key):
            response_data[key] = default

    logger.success("GET /runtime 请求成功")
    return 200, response_data


register("/cwsdk/runtime", "GET")(handle_runtime)
