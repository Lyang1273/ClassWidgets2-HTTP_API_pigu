__version__ = "0.4.0"

from .uni_desktop import bootstrap as _bootstrap_uda

# 让 `from uda import Uda` + `Uda()`（官方文档写法）在本插件内可直接使用。
# 只准备导入路径与动态库位置，不加载库本身。必须在 plugin 之前执行，
# 保证插件生命周期内的任何代码都能直接用 UDA。
_bootstrap_uda()

from .plugin import Plugin  # noqa: E402

__all__ = ["Plugin"]
