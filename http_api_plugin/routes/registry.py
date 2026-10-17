import threading
from loguru import logger


class RegistryError(Exception):
    """注册表错误基类"""


class ReservedPrefixError(RegistryError):
    """路径命中保留前缀"""
    def __init__(self, path: str, prefix: str):
        self.path = path
        self.prefix = prefix
        super().__init__(f"{path} 命中保留前缀 {prefix}")


class RootConflictError(RegistryError):
    """根路径被占用"""
    def __init__(self, root_path: str):
        self.root_path = root_path
        super().__init__(f"根路径 {root_path} 已占用")


class RouteConflictError(RegistryError):
    """完整路径被占用。"""
    def __init__(self, full_path: str):
        self.full_path = full_path
        super().__init__(f"路由 {full_path} 已存在")


class InvalidPathError(RegistryError):
    """路径格式不合法"""
    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"{path} 不合法: {reason}")


_ROOTS = {}
_FLAT_ROUTES = {}
_WILDCARD_ROUTES = {}
_LOCK = threading.RLock()
_RESERVED_PREFIXES = ("/cwsdk", "/system", "/internal", "/cw", "/debug", "/embedded")


def _normalize(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/") or "/"


def _check_reserved(path: str) -> None:
    for prefix in _RESERVED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            raise ReservedPrefixError(path, prefix)


def _normalize_methods(methods):
    """把 methods 参数规范成大写方法名集合；None 表示不限定方法。"""
    if methods is None:
        return None
    if isinstance(methods, str):
        methods = [methods]
    normalized = {str(m).strip().upper() for m in methods if str(m).strip()}
    if not normalized:
        raise InvalidPathError("", "methods 不能为空")
    return normalized


class RootRegistry:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self._routes = {}

    def _full_path(self, sub_path: str) -> str:
        sub_path = _normalize(sub_path)
        return self.root_path if sub_path == "/" else self.root_path + sub_path

    def register(self, sub_path: str, handler_func, methods=None):
        """注册路径。

        methods 为 None 时注册为不限定方法的通配路由；
        否则为方法名（或方法名列表），同一个 handler 会注册到每个方法上。
        """
        if not callable(handler_func):
            raise TypeError("handler_func 必须可调用")
        full_path = self._full_path(sub_path)
        _check_reserved(full_path)
        method_set = _normalize_methods(methods)

        with _LOCK:
            if method_set is None:
                if full_path in _WILDCARD_ROUTES or any(
                    path == full_path for path, _ in _FLAT_ROUTES
                ):
                    raise RouteConflictError(full_path)
                _WILDCARD_ROUTES[full_path] = handler_func
                self._routes[(full_path, None)] = handler_func
            else:
                if full_path in _WILDCARD_ROUTES:
                    raise RouteConflictError(full_path)
                for method in method_set:
                    if (full_path, method) in _FLAT_ROUTES:
                        raise RouteConflictError(f"{full_path} [{method}]")
                for method in method_set:
                    _FLAT_ROUTES[(full_path, method)] = handler_func
                    self._routes[(full_path, method)] = handler_func

        logger.info(f"已注册 {full_path} {sorted(method_set) if method_set else 'ALL'} ; {handler_func}")
        return full_path

    def unregister(self, sub_path: str, methods=None) -> None:
        """取消注册路径。

        methods 为 None 时移除该路径下的全部方法（含通配）。
        """
        full_path = self._full_path(sub_path)
        method_set = _normalize_methods(methods)

        with _LOCK:
            if method_set is None:
                _WILDCARD_ROUTES.pop(full_path, None)
                self._routes.pop((full_path, None), None)
                for key in [k for k in _FLAT_ROUTES if k[0] == full_path]:
                    _FLAT_ROUTES.pop(key, None)
                    self._routes.pop(key, None)
            else:
                for method in method_set:
                    _FLAT_ROUTES.pop((full_path, method), None)
                    self._routes.pop((full_path, method), None)

        logger.info(f"已移除 {full_path}")

    def destroy(self) -> None:
        """清空该根下所有路径"""
        with _LOCK:
            for key in list(self._routes.keys()):
                path, method = key
                if method is None:
                    _WILDCARD_ROUTES.pop(path, None)
                else:
                    _FLAT_ROUTES.pop(key, None)
            self._routes.clear()
            _ROOTS.pop(self.root_path, None)

def add_root(root_path: str) -> RootRegistry:
    root_path = _normalize(root_path)
    if root_path == "/":
        raise InvalidPathError(root_path, "根路径不能为 /")
    _check_reserved(root_path)
    with _LOCK:
        if root_path in _ROOTS:
            raise RootConflictError(root_path)
        root = RootRegistry(root_path)
        _ROOTS[root_path] = root
        return root


def get_handler(path: str, method: str = None):
    with _LOCK:
        if method is not None:
            handler = _FLAT_ROUTES.get((path, str(method).upper()))
            if handler is not None:
                return handler
        return _WILDCARD_ROUTES.get(path)


def clear_all() -> None:
    with _LOCK:
        _ROOTS.clear()
        _FLAT_ROUTES.clear()
        _WILDCARD_ROUTES.clear()