# 大烧货留下的高高高高高级代码
"""UDA（UniDesktop API）的统一接入层。

插件通过 UDA 提供跨平台的桌面能力（当前用于 `/system/lock_screen` 锁屏）。
本模块把「找到动态库 → 校验架构 → 按需加载 → 统一错误处理」这几件重复工作收在
一处，路由层只需要一行：

    from ..uni_desktop import uda_call

    def handle_xxx(ctx, query, body):
        return uda_call(lambda u: u.session.lock())

设计要点：

- **懒加载 + 单例**：首次调用才加载动态库，进程内只加载一次，线程安全。
- **显式选库**：SDK 只探测 ``target/`` 与系统搜索路径，不会自动使用与自己同目录
  的动态库，所以这里替它定位 ``http_api_plugin/uda/`` 下对应平台的库文件。
- **先校验架构再加载**：加载架构不符的动态库会抛出无法按名称捕获的 OSError，
  因此只读文件头判断位数，不匹配就跳过。
- **统一失败表现**：缺库、后端不支持、调用报错，都返回规范的 500 JSON，
  绝不让异常穿透到 HTTP 处理器。

动态库查找顺序：
    1. 环境变量 ``UDA_LIBRARY``（原样使用，调用方自担架构风险）；
    2. ``http_api_plugin/uda/`` 下与当前平台、解释器位数匹配的库文件。
"""

from __future__ import annotations

import os
import struct
import sys
import threading
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from .response import error, success

__all__ = [
    "available",
    "bootstrap",
    "get_uda",
    "is_supported",
    "release",
    "status_code",
    "uda_call",
    "uda_data",
    "uda_media_command",
    "unavailable_reason",
]

#: 动态库所在目录（与 SDK 的 uda.py 及 uda_ffi 产物放在一起）。
UDA_DIR = Path(__file__).resolve().parent / "uda"

#: 各平台的动态库文件名（与 UDA 的 ``crates/uda-ffi`` 产物一致）。
_LIBRARY_NAMES = {
    "win32": ("uda_ffi.dll",),
    "linux": ("libuda_ffi.so",),
    "darwin": ("libuda_ffi.dylib",),
}

#: ELF ``e_machine`` / PE ``IMAGE_FILE_MACHINE`` -> 该库要求的解释器位数。
#: 用于在真正加载之前拦下架构不符的库。
_ELF_MACHINE_BITS = {3: 32, 40: 32, 62: 64, 183: 64}
_PE_MACHINE_BITS = {0x14C: 32, 0x8664: 64, 0xAA64: 64}

_uda = None
_uda_lock = threading.Lock()


# ----------------------------------------------------------------------
# 动态库定位
# ----------------------------------------------------------------------
def interpreter_bits() -> int:
    """返回当前 Python 解释器的位数（32 / 64）。"""
    return 64 if sys.maxsize > 2**32 else 32


def library_bits(path) -> int | None:
    """读取动态库头部，返回它要求的解释器位数；无法判断时返回 None。

    只读头部，不会真正加载库——架构不符的库加载失败时抛出的是无法按名称捕获的
    OSError，因此必须在加载前自行判断。
    """
    try:
        with open(path, "rb") as f:
            head = f.read(20)
            if head[:4] == b"\x7fELF" and len(head) >= 20:
                order = "little" if head[5] == 1 else "big"
                return _ELF_MACHINE_BITS.get(int.from_bytes(head[18:20], order))
            if head[:2] == b"MZ":  # PE（Windows DLL）
                f.seek(0x3C)
                offset = struct.unpack("<I", f.read(4))[0]
                f.seek(offset)
                if f.read(4) != b"PE\0\0":
                    return None
                return _PE_MACHINE_BITS.get(struct.unpack("<H", f.read(2))[0])
    except (OSError, struct.error):
        return None
    return None


def resolve_library() -> Path | None:
    """返回要加载的动态库路径；插件未附带合适的库时返回 None。

    设置 ``UDA_LIBRARY`` 时原样使用；否则在本平台的候选文件名中挑出与当前解释器
    位数一致的那一个。
    """
    override = os.environ.get("UDA_LIBRARY")
    if override:
        return Path(override)

    wanted = interpreter_bits()
    for name in _LIBRARY_NAMES.get(sys.platform, ()):
        candidate = UDA_DIR / name
        if not candidate.is_file():
            continue
        bits = library_bits(candidate)
        if bits is None or bits == wanted:
            return candidate
        logger.warning(
            f"跳过架构不符的 UDA 动态库 {candidate.name}"
            f"（需要 {bits} 位解释器，当前为 {wanted} 位）"
        )
    return None


def unavailable_reason() -> str:
    """说明为什么没有可用的 UDA 动态库，用于日志与接口错误信息。"""
    names = _LIBRARY_NAMES.get(sys.platform)
    if not names:
        return f"当前平台（{sys.platform}）暂不支持 UDA"
    return (
        f"未找到适用于当前解释器（{interpreter_bits()} 位）的 UDA 动态库"
        f"（目录 {UDA_DIR}，候选文件：{', '.join(names)}）"
    )


# ----------------------------------------------------------------------
# 加载与调用
# ----------------------------------------------------------------------
def bootstrap() -> bool:
    """让 UDA 可以按官方文档的方式零配置使用。

    官方示例直接 ``from uda import Uda`` 再 ``Uda()``，但 SDK 默认只在 ``target/``
    与系统搜索路径里找动态库，不会看自己所在的目录。本函数补上这一步：

    1. 把 ``http_api_plugin/uda/`` 加入 ``sys.path``，使 ``import uda`` 可用；
    2. 把匹配当前平台与解释器位数的动态库写入环境变量 ``UDA_LIBRARY``，
       使无参 ``Uda()`` 能定位到库（已手动设置时保持不动）。

    幂等，可重复调用。返回是否找到可用的动态库；找不到时只记日志，不影响插件
    其它功能，``from uda import Uda`` 仍可导入（但 ``Uda()`` 会失败）。

    调用一次之后，插件内任何位置都可以照抄官方写法::

        from uda import Uda

        with Uda() as uda:
            print("主题:", uda.theme)
            uda.notify("你好，桌面", "这是通过 UDA 发出的第一条系统通知。")
    """
    if str(UDA_DIR) not in sys.path:
        sys.path.insert(0, str(UDA_DIR))

    library = resolve_library()
    if library is None:
        logger.warning(f"{unavailable_reason()}；`from uda import Uda` 仍可导入，但 `Uda()` 会失败")
        return False

    # 用 setdefault：调用方显式设置的 UDA_LIBRARY 优先，不被覆盖。
    os.environ.setdefault("UDA_LIBRARY", str(library))
    return True


def get_uda():
    """返回进程内共享的 Uda 实例；加载失败时返回 None（原因已写入日志）。

    加载成功后会在模块级缓存，后续调用直接复用。
    """
    global _uda
    if _uda is not None:
        return _uda
    with _uda_lock:
        if _uda is not None:
            return _uda
        library = resolve_library()
        if library is None:
            logger.error(f"{unavailable_reason()}，UDA 相关功能不可用")
            return None
        try:
            if str(UDA_DIR) not in sys.path:
                sys.path.insert(0, str(UDA_DIR))
            from uda import Uda

            _uda = Uda(library_path=library)
        except Exception as e:  # noqa: BLE001 - 加载失败只降级，不影响其它接口
            logger.error(f"UDA 动态库加载失败（{library}）: {e}")
            return None
    return _uda


def available() -> bool:
    """UDA 能否使用（动态库存在且已成功加载）。"""
    return get_uda() is not None


def is_supported(action: str) -> bool:
    """当前平台是否支持某个会话动作（``lock`` / ``suspend`` 等）。

    查询本身无副作用；平台不支持或 UDA 不可用时返回 False，不抛异常。
    """
    uda = get_uda()
    if uda is None:
        return False
    try:
        return bool(uda.session.supports(action))
    except Exception as e:  # noqa: BLE001 - 未知动作或后端缺失都按不支持处理
        logger.warning(f"查询 UDA 能力 {action!r} 失败: {e}")
        return False


def release() -> None:
    """释放 UDA 持有的常亮锁与托盘资源。重复调用安全。"""
    global _uda
    with _uda_lock:
        uda, _uda = _uda, None
    if uda is None:
        return
    try:
        uda.release_all()
    except Exception as e:  # noqa: BLE001 - 清理失败不应阻断退出流程
        logger.warning(f"释放 UDA 资源失败: {e}")


def uda_call(func: Callable[[Any], Any], what: str = "UDA 调用"):
    """在 UDA 上执行一次调用，并把它转换成规范的 HTTP 响应。

    Args:
        func: 接收 :class:`Uda` 实例并返回 JSON 友好值的函数，可作 lambda::

                uda_call(lambda u: u.session.lock())
                uda_call(lambda u: u.theme)

        what: 失败信息中使用的操作名，例如 ``"锁屏"``。

    Returns:
        形如 ``(200, {"code": 0, "message": "success", "data": ...})`` 的成功响应；
        成功但无返回值时 ``data`` 为 ``"True"``。UDA 不可用或调用失败时返回
        ``(500, {"code": 500, "message": "<具体原因>", "data": None})``。

    示例::

        from ..uni_desktop import uda_call

        def handle_lock_screen(ctx, query, body):
            return uda_call(lambda u: u.session.lock(), what="锁屏")
    """
    uda = get_uda()
    if uda is None:
        return error(500, f"{unavailable_reason()}，{what}接口不可用")

    try:
        result = func(uda)
    except Exception as e:  # noqa: BLE001 - 任何后端错误都转成 500，不穿透处理器
        logger.warning(f"{what}失败: {e}")
        return error(500, f"{what}失败: {e}")

    logger.success(f"{what}成功")
    return success("True" if result is None else result)


# ----------------------------------------------------------------------
# 状态码与可空读取
# ----------------------------------------------------------------------
#: UDA 错误状态码常量；SDK 里也有一份，这里单独写死以免依赖其内部导入顺序。
_ERR_INVALID_ARGUMENT = -1
_ERR_NOT_SUPPORTED = -2


def status_code(exc: BaseException) -> int | None:
    """取出 :class:`uda.UdaError` 的状态码；其它异常返回 None。

    UDA 的失败都会带上 C-ABI 状态码，路由层据此区分「调用方参数不对」「没有
    播放器 / 播放器拒绝」「后端故障」，而不是一律 500。
    """
    code = getattr(exc, "status", None)
    return code if isinstance(code, int) else None


def uda_data(func: Callable[[Any], Any], what: str = "UDA 调用"):
    """读取型接口用：把一次 UDA 调用转成成功响应。

    与 :func:`uda_call` 的区别只在数据形态：这里把返回值原样放进 ``data``，
    不把 ``None`` 改写成 ``"True"``。「没有值」是合法答案，例如没有播放器时
    ``data`` 就是 ``null``，而不是一个假的成功标记。

    UDA 不可用时返回 500；调用失败（含后端故障）同样返回 500。
    """
    uda = get_uda()
    if uda is None:
        return error(500, f"{unavailable_reason()}，{what}接口不可用")

    try:
        result = func(uda)
    except Exception as e:  # noqa: BLE001 - 后端错误统一转 500
        logger.warning(f"{what}失败: {e}")
        return error(500, f"{what}失败: {e}")

    return success(result)


def uda_media_command(command: str):
    """投递一条播控指令，并区分「已送达」与「被拒绝」。

    ``uda.media.send`` 对下情况都抛 ``UdaError``：没有播放器、或播放器不接受
    该指令（状态码 ``-2``）。这不算服务端故障，而是当前环境无法执行这条指令，
    所以映射为 400，让调用方能从状态码直接区分，不必去解析 ``message``。

    成功时只代表播放器**接受**了指令，之后仍可能失败（UDA 文档的语义）。
    """
    uda = get_uda()
    if uda is None:
        return error(500, f"{unavailable_reason()}，媒体播控接口不可用")

    try:
        uda.media.send(command)
    except Exception as e:  # noqa: BLE001 - 按状态码分层，其余仍按 500
        code = status_code(e)
        if code == _ERR_NOT_SUPPORTED:
            logger.info(f"媒体播控指令 {command} 未被接受: {e}")
            return error(
                400,
                f"指令 {command} 未被接受：当前没有可控制的播放器，或播放器不支持该指令（{e}）",
            )
        if code == _ERR_INVALID_ARGUMENT:
            logger.warning(f"媒体播控指令 {command} 不合法: {e}")
            return error(400, f"指令 {command} 不合法：{e}")
        logger.warning(f"媒体播控指令 {command} 失败: {e}")
        return error(500, f"媒体播控指令 {command} 失败: {e}")

    logger.success(f"媒体播控指令 {command} 已发送")
    return success("True", message=f"已发送指令 {command}")
