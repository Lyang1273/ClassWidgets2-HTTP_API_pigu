import json
import re

from loguru import logger

from ..response import success, error
from . import register


_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")


_TYPE_MAP = {
    "str": str,
    "string": str,
    "text": str,
    "int": int,
    "integer": int,
    "float": float,
    "double": float,
    "number": float,
    "bool": bool,
    "boolean": bool,
    "list": list,
    "array": list,
    "dict": dict,
    "object": dict,
    "any": object,
}


def _param(body, query, *keys):
    """从 body（POST）或 query（GET）中按顺序取第一个有值参数"""
    for key in keys:
        value = body.get(key) if body is not None else query.get(key)
        if value is not None and value != "":
            return value
    return None


def _cast_scalar(token):
    """把逗号分隔的裸串按类型智能转换。"""
    text = token.strip()
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    return text


def _parse_args(raw):
    """把 args 参数统一成列表，支持不进行 URL 转义的写法。

    - 列表/元组（POST JSON 数组）-> 原样
    - 以 "[" / "{" 开头的字符串 -> 按 JSON 解析（含逗号的字符串用 ["a,b"] 形式）
    - 其它字符串 -> 按逗号分隔，并对每项做智能类型转换（true/false、int、float）
    """
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if text.startswith("[") or text.startswith("{"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return [raw]
            return list(parsed) if isinstance(parsed, (list, tuple)) else [parsed]
        return [_cast_scalar(token) for token in text.split(",")]
    return [raw]


def _parse_types(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        names = [p.strip() for p in raw.split(",") if p.strip()]
    elif isinstance(raw, (list, tuple)):
        names = [str(p).strip() for p in raw if str(p).strip()]
    else:
        names = [str(raw).strip()]

    types = []
    for name in names:
        key = name.lower()
        if key not in _TYPE_MAP:
            raise ValueError(f"不支持的类型: {name}")
        types.append(_TYPE_MAP[key])
    return types


def handle_register(ctx, query, body):
    name = _param(body, query, "name", "action", "id")
    if not name:
        return error(400, "缺少必要参数: name")

    raw_types = _param(body, query, "params", "parameter_types", "types")
    try:
        parameter_types = _parse_types(raw_types)
    except ValueError as e:
        return error(400, str(e))

    try:
        ctx.api.actions.register(name, *parameter_types)
    except Exception as e:
        logger.error(f"注册 Action 失败: {name} - {e}")
        return error(500, f"注册 Action 失败: {str(e)}")

    logger.success(f"Action 已注册: {name} ({[t.__name__ for t in parameter_types]})")
    return success(
        {"name": name, "parameters": [t.__name__ for t in parameter_types]},
        message=f"Action '{name}' 已注册",
    )


def handle_get(ctx, query, body):
    name = _param(body, query, "name", "action", "id")
    if not name:
        return error(400, "缺少必要参数: name")

    try:
        action = ctx.api.actions.get(name)
    except Exception as e:
        logger.error(f"获取 Action 失败: {name} - {e}")
        return error(500, f"获取 Action 失败: {str(e)}")

    if action is None:
        return error(404, f"未找到 Action: {name}")

    logger.success(f"Action 已获取: {name}")
    return success({"name": name, "exists": True})


def handle_emit(ctx, query, body):
    name = _param(body, query, "name", "action", "id")
    if not name:
        return error(400, "缺少必要参数: name")

    args = _parse_args(_param(body, query, "args", "arguments"))

    try:
        action = ctx.api.actions.get(name)
    except Exception as e:
        logger.error(f"获取 Action 失败: {name} - {e}")
        return error(500, f"获取 Action 失败: {str(e)}")

    if action is None:
        return error(404, f"未找到 Action: {name}")

    try:
        action.emit(*args)
    except Exception as e:
        logger.error(f"触发 Action 失败: {name} - {e}")
        return error(500, f"触发 Action 失败: {str(e)}")

    logger.success(f"Action 已触发: {name} {args}")
    return success(message=f"Action '{name}' 已触发")


register("/cwsdk/action/register", "GET")(handle_register)
register("/cwsdk/action/register", "POST")(handle_register)
register("/cwsdk/action/get", "GET")(handle_get)
register("/cwsdk/action/get", "POST")(handle_get)
register("/cwsdk/action/emit", "GET")(handle_emit)
register("/cwsdk/action/emit", "POST")(handle_emit)
