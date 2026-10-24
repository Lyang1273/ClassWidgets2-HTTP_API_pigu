"""``/system`` 根路径下的系统操作路由。

包含两部分：

- **系统信息与操作**：系统名称 / 版本、管理员权限、前台窗口标题、锁屏、打开网址、主题；
- **媒体播控**（``/system/media``）：对应 UDA 文档
  [媒体播控](https://unidesktop.sr-studio.cn/zh-cn/guides/media/)，读取正在播放、
  查询播放状态、发送播控指令。平台差异（Windows SMTC / Linux MPRIS v2）由
  UDA 的 ``uda.media`` 命名空间抹平。

媒体播控接口一览
----------------

==========  ==============================  ================================
方法        路径                            说明
==========  ==============================  ================================
GET         ``/system/media``               正在播放 + 播放状态的合并快照
GET         ``/system/media/now_playing``   正在播放的曲目元数据
GET         ``/system/media/status``        播放状态（四个值之一）
GET         ``/system/media/commands``      可用指令与状态取值
GET/POST    ``/system/media/play``          开始播放
GET/POST    ``/system/media/pause``         暂停播放
GET/POST    ``/system/media/play_pause``    播放 / 暂停切换
GET/POST    ``/system/media/next``          下一曲
GET/POST    ``/system/media/previous``      上一曲
GET/POST    ``/system/media/stop``          停止播放
GET/POST    ``/system/media/send``          按指令名发送（``{"command": "..."}``）
GET/POST    ``/system/media/command``       同上，指令也可走查询参数
==========  ==============================  ================================

媒体播控的错误分层
------------------

「没有播放器」**不是**错误：``now_playing`` 返回 ``data: null``，``status``
返回 ``unknown``，均为 200。只有动态库缺失、后端故障才返回 500；播放器拒绝
指令（或没有播放器可接收）返回 400，便于调用方区分「已送达」与「被拒绝」。
"""

import ctypes
import platform
import webbrowser
from loguru import logger

from ..response import success, error
from ..uni_desktop import uda_call, uda_data, uda_media_command
from . import register


def handle_system_name(ctx, query, body):
    logger.success("GET /system/system_name 请求成功")
    return success(platform.system())


def handle_system_version(ctx, query, body):
    logger.success("GET /system/system_version 请求成功")
    return success(platform.version())


def handle_system_release(ctx, query, body):
    logger.success("GET /system/system_release 请求成功")
    return success(platform.release())


def handle_is_admin(ctx, query, body):
    if platform.system() != "Windows":
        return 200, {"code": 1, "message": "当前操作系统不支持该api", "data": None}
    else:
        logger.success("GET /system/is_admin 请求成功")
        return success('True' if ctypes.windll.shell32.IsUserAnAdmin() else 'False')


def handle_window_title(ctx, query, body):
    if platform.system() != "Windows":
        return 200, {"code": 1, "message": "当前操作系统不支持该api", "data": None}
    else:
        user32 = ctypes.windll.user32
        title = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(user32.GetForegroundWindow(), title, 256)
        title = title.value

        logger.success("GET /system/window_title 请求成功")
        return success(title)


def handle_lock_screen(ctx, query, body):
    return uda_call(lambda u: u.session.lock(), what="锁屏")


"""
def handle_screenshot(ctx, query, body):
    screenshot = pyautogui.screenshot()

    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    base64_str = base64.b64encode(image_bytes).decode('utf-8')
    return success(base64_str)
"""


def handle_open_website(ctx, query, body):
    link = query.get('link', '')
    if not link:
        return error(400, "缺少 link 参数")

    webbrowser.open(link)
    logger.success(f"GET /system/open_website 请求成功: {link}")
    return success('True')


def handle_theme(ctx, query, body):
    logger.success(f"GET /system/theme 请求成功")
    return uda_call(lambda u: u.theme, what="获取主题")

def handle_accent_color(ctx, query, body):
    logger.success(f"GET /system/accent_color 请求成功")
    return uda_call(lambda u: u.accent_color, what="获取强调色")


#: 对外的指令名 -> UDA 指令名。
#:
#: 文档同时列出 ``"play_pause"``（SDK 便捷方法名）与 ``"toggle"``（完整指令集
#: 里的名字），两者都指同一个「切换」动作，这里都接受，统一映射到 ``toggle``。
_COMMAND_ALIASES = {
    "play": "play",
    "pause": "pause",
    "play_pause": "toggle",
    "toggle": "toggle",
    "next": "next",
    "previous": "previous",
    "prev": "previous",
    "stop": "stop",
}

#: 文档定义的四个播放状态，按此顺序展示。
_STATUSES = ("playing", "paused", "stopped", "unknown")


def _track_to_dict(track):
    """把 :class:`uda.MediaTrack` 转成 JSON 词典；无播放器时为 None。"""
    if track is None:
        return None

    # SDK 的 MediaTrack 只发布 artist 单字段（多位艺人已用 ", " 连接），没有
    # artists 列表；这里按文档的跨平台语义补齐成列表，同时保留 artist 原值。
    raw_artist = track.artist or ""
    artists = [part.strip() for part in raw_artist.split(",") if part.strip()]

    return {
        "title": track.title or "",
        "artists": artists,
        "artist": raw_artist,
        "album": track.album or "",
        "duration_ms": track.duration_ms,
        "position_ms": track.position_ms,
    }


def _normalize_command(raw):
    """把调用方给的指令名规范成 UDA 指令名；无法识别时返回 None。"""
    if not isinstance(raw, str):
        return None
    return _COMMAND_ALIASES.get(raw.strip().lower())


def _missing_command_error():
    known = "、".join(_COMMAND_ALIASES)
    return error(400, f"缺少 command 参数，可用指令：{known}")


def _unknown_command_error(raw):
    known = "、".join(_COMMAND_ALIASES)
    return error(400, f"未知的播控指令 {raw!r}，可用指令：{known}")


def handle_now_playing(ctx, query, body):
    """GET/POST /system/media/now_playing —— 当前播放的曲目快照。

    没有播放器时 ``data`` 为 ``null``（这是正常返回值，不是错误）。
    """
    logger.success("GET /system/media/now_playing 请求成功")
    return uda_data(lambda u: _track_to_dict(u.media.now_playing), what="读取正在播放")


def handle_media_status(ctx, query, body):
    """GET/POST /system/media/status —— 播放状态。

    返回 ``playing`` / ``paused`` / ``stopped`` / ``unknown`` 之一。
    ``unknown`` 表示无法判定（含「没有播放器」），与「已暂停」是不同状态，切勿混用。
    """
    logger.success("GET /system/media/status 请求成功")
    return uda_data(lambda u: u.media.status, what="查询播放状态")


def handle_media(ctx, query, body):
    """GET/POST /system/media —— 合并快照，供需要实时更新的 UI 一次取全。

    元数据是一次性快照，没有变更监听；需要实时刷新的界面请轮询此接口
    （UDA 建议间隔 ≥ 1 秒）。

    响应 ``data``::

        {
          "has_session": true,
          "status": "playing",
          "now_playing": { "title": ..., "artists": [...], "album": ...,
                           "duration_ms": ..., "position_ms": ... }
        }

    没有播放器时 ``has_session`` 为 ``false``、``now_playing`` 为 ``null``。
    """
    def snapshot(u):
        # 两次读取是两个独立调用，播放器可能刚好切换曲目，快照不需要强一致。
        track = _track_to_dict(u.media.now_playing)
        status = u.media.status
        return {
            "has_session": track is not None,
            "status": status,
            "now_playing": track,
        }

    logger.success("GET /system/media 请求成功")
    return uda_data(snapshot, what="读取媒体状态")


def _make_handler(command):
    """生成一个固定指令的处理函数。"""
    def handle(ctx, query, body):
        return uda_media_command(command)

    handle.__name__ = f"handle_media_{command}"
    handle.__doc__ = f"发送 {command} 指令（GET/POST 均可）。"
    return handle


handle_media_play = _make_handler("play")
handle_media_pause = _make_handler("pause")
handle_media_toggle = _make_handler("toggle")
handle_media_next = _make_handler("next")
handle_media_previous = _make_handler("previous")
handle_media_stop = _make_handler("stop")


def handle_media_send(ctx, query, body):
    """POST /system/media/send —— 按指令名发送。

    请求体：``{"command": "play"}``；也可用 ``{"cmd": "..."}``。

    指令名同时接受文档里的两套写法（``play_pause`` 与 ``toggle`` 等价）。
    成功只代表播放器**接受**了指令，之后仍可能失败。
    """
    if isinstance(body, dict):
        raw = body.get("command", body.get("cmd"))
    elif isinstance(body, str):
        raw = body
    else:
        # 空请求体（无参数调用）按「缺 command」处理，不是格式错误。
        raw = query.get("command") or query.get("cmd")
    if raw is None or raw == "":
        return _missing_command_error()

    command = _normalize_command(raw)
    if command is None:
        return _unknown_command_error(raw)

    return uda_media_command(command)


def handle_media_command(ctx, query, body):
    """GET/POST /system/media/command —— 指令可走查询参数，便于直接浏览器/curl 调用。

    ``?command=play_pause`` 或 ``?cmd=toggle``。
    """
    raw = query.get("command") or query.get("cmd")
    if raw is None:
        raw = (body or {}).get("command") or (body or {}).get("cmd")
    if raw is None or raw == "":
        return _missing_command_error()

    command = _normalize_command(raw)
    if command is None:
        return _unknown_command_error(raw)

    return uda_media_command(command)


def handle_media_commands(ctx, query, body):
    """GET /system/media/commands —— 列出可用指令与播放状态取值。

    便于调用方（或调试页）自省，避免硬编码常量列表。
    """
    logger.success("GET /system/media/commands 请求成功")
    return success({
        "commands": sorted(set(_COMMAND_ALIASES)),
        "statuses": list(_STATUSES),
    })


register("/system/is_admin", "GET")(handle_is_admin)
register("/system/window_title", "GET")(handle_window_title)
register("/system/lock_screen", "GET")(handle_lock_screen)
register("/system/open_website", "GET")(handle_open_website)
register("/system/system_name", "GET")(handle_system_name)
register("/system/system_version", "GET")(handle_system_version)
register("/system/system_release", "GET")(handle_system_release)
# register("/system/screenshot", "GET")(handle_screenshot)
register("/system/theme", "GET")(handle_theme)

# ---- 媒体播控 ----
register("/system/media", "GET")(handle_media)
register("/system/media", "POST")(handle_media)

register("/system/media/now_playing", "GET")(handle_now_playing)
register("/system/media/now_playing", "POST")(handle_now_playing)

register("/system/media/status", "GET")(handle_media_status)
register("/system/media/status", "POST")(handle_media_status)

register("/system/media/commands", "GET")(handle_media_commands)

for _path, _handler in (
    ("play", handle_media_play),
    ("pause", handle_media_pause),
    ("play_pause", handle_media_toggle),
    ("next", handle_media_next),
    ("previous", handle_media_previous),
    ("stop", handle_media_stop),
):
    register(f"/system/media/{_path}", "GET")(_handler)
    register(f"/system/media/{_path}", "POST")(_handler)

register("/system/media/send", "GET")(handle_media_send)
register("/system/media/send", "POST")(handle_media_send)
register("/system/media/command", "GET")(handle_media_command)
register("/system/media/command", "POST")(handle_media_command)

"""大烧货留下的高级代码（"""
"""你妈的怎么给我搬到最后一行了"""
