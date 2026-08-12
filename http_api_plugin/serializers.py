import dataclasses
import enum
from datetime import date, datetime, time


def to_jsonable(obj):
    """递归地把任意对象转换为可 JSON 序列化的结构。

    支持：基础类型、datetime、枚举、字典、列表/元组/集合、
    pydantic 模型（model_dump / dict）、dataclass、普通对象（__dict__ / __slots__），
    其余兜底用 str()。
    """
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (str, int, float)):
        return obj
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, enum.Enum):
        return to_jsonable(obj.value)
    if isinstance(obj, dict):
        return {to_jsonable(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [to_jsonable(v) for v in obj]

    try:
        if hasattr(obj, "model_dump"):
            return to_jsonable(obj.model_dump())
        if hasattr(obj, "dict"):
            return to_jsonable(obj.dict())
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return {f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
        if hasattr(obj, "__dict__"):
            return {k: to_jsonable(v) for k, v in vars(obj).items()}
        if hasattr(obj, "__slots__"):
            return {s: to_jsonable(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s)}
    except (AttributeError, TypeError, ValueError):
        pass

    return str(obj)
