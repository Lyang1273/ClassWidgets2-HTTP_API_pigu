# http_api_mod 模块使用教程

本教程将通过通俗易懂的方式教你使用 http_api_mod 模块，有关该模块的文档，[参见此处](/docs/doc.md)

## 1. 准备工作

`http_api_mod` 依赖插件 `HTTP API`(http.lyang1273) 运作，请确保已经安装该插件。

## 2. 导入模块

在你的插件入口文件中的 `on_load()` 方法中导入该模块：

```python
import sys
http_api_mod = sys.modules.get("http_api_mod")

# 你也可以使用
import http_api_mod

# 或
import importlib
http_api_mod = importlib.import_module("http_api_mod")
```

> [!WARNING]
> 由于 Class Widgets 2 的插件系统不支持设置前置插件以及控制插件加载顺序，可能会导致导入失败。建议延迟导入或容错。

## 3. 注册接口路径

导入成功后，使用 `add_root()` 添加一个根路径，返回一个 `Root` 对象：

```python
root = http_api_mod.add_root("/test")
```

- 根路径是全局唯一的，如果某个插件已经占用了 `/test`，你的插件再调用 `add_root("/test")` 则会抛出 `RootConflictError`

> [!TIP]
> 根路径建议用插件自己的特有标识，比如插件 id、插件名等，例如 `/http-lyang1273` 或 `/http_api`。

添加根路径后，使用 `register` 方法注册子路径，并将其绑定到对应的功能函数上：

```python
root.register("/hello", self.handle_hello)
```

`register()` 还支持第三个参数 `methods`，用于限定 HTTP 方法。不传时表示通配所有方法：

```python
# 通配所有方法（GET/POST/PUT/DELETE 都命中）
root.register("/hello", self.handle_hello)

# 只允许 GET
root.register("/hello", self.handle_hello, methods="GET")

# 同时允许 GET 和 POST
root.register("/hello", self.handle_hello, methods=["GET", "POST"])
```

同一路径下，通配路由和方法路由**不能共存**，否则抛 `RouteConflictError`。

## 4. 处理函数的签名

所有注册的处理函数必须符合这个签名：

```python
def handler(ctx, query, body):
    """
    ctx   : ServerContext，含 ctx.api（ClassWidgets SDK 的 PluginAPI）、ctx.config 等
    query : URL 查询参数字典，如 ?name=x 时为 {"name": "x"}
    body  : POST 请求体解析后的字典；GET 请求时为 None
    """
```

三个参数的含义：

| 参数 | 类型 | 说明 |
|------|------|------|
| `ctx` | `ServerContext` | 通过 `ctx.api` 可以调用 SDK 的通知、课表、运行时等能力 |
| `query` | `dict` | URL 中 `?a=1&b=2` 解析成的 `{"a": "1", "b": "2"}` |
| `body` | `dict \| None` | POST 请求体 JSON 解析结果；GET 时为 `None` |

> [!WARNING]
> 处理函数在 HTTP API 插件的 **服务器线程** 里执行。如果函数里有耗时操作（如 `time.sleep(10)`、阻塞式网络请求），会卡住整个服务器。建议把耗时任务丢到 `threading.Thread` 里，立刻返回 `202`。

## 5. 返回值

处理函数可以返回三种形式，HTTP API 插件都会正确处理：

| 返回值 | 实际响应 |
|--------|----------|
| `None` | `200 {"code": 0, "message": "ok", "data": None}` |
| `(200, {...})` | 按指定的状态码和数据发送 |
| `{...}` | `200 那个字典` |

推荐始终返回 `(状态码, 数据)` 元组，契约清晰：

```python
def handle_hello(self, ctx, query, body):
    name = query.get("name", "World")
    return 200, {"code": 0, "data": {"message": f"Hello, {name}!"}}
```

出错时返回非 200 状态码：

```python
def handle_add(self, ctx, query, body):
    if not body:
        return 400, {"code": -1, "message": "缺少请求体"}
    return 200, {"code": 0, "data": {"result": body.get("a", 0) + body.get("b", 0)}}
```

> [!TIP]
> 处理函数抛出的任何异常，都会被 HTTP API 插件捕获并转换成 `500 {"code": 500, "message": "内部服务器错误"}`，不会拖垮服务器线程。但异常详情只会打印在日志里，外部调用者看不到，调试时请查看日志。

## 6. 卸载时清理

插件被禁用或卸载时，必须清理自己注册的路由，否则 HTTP API 插件的路由表里会留下指向已销毁对象的引用，外部访问会报错。

最省事的方式是一行 `destroy()`：

```python
def on_unload(self):
    if getattr(self, "root", None) is not None:
        self.root.destroy()
```

`destroy()` 会一次性移除该根路径下所有已注册路由，并把根路径本身也释放掉。

如果只想移除某个子路由、保留根路径，可以用 `unregister()`：

```python
def on_unload(self):
    if getattr(self, "root", None) is not None:
        self.root.unregister("/hello")
```

> [!WARNING]
> 如果 `http_api_mod` 在你插件之前卸载（即 HTTP API 插件被禁用），`root` 对象实际上已经失效。此时再调用 `destroy()` 不会报错（内部是 `pop(path, None)`），但也没有意义。用 `getattr(self, "root", None)` 判断存在性即可，不需要额外处理。

## 7. 完整示例

一个完整的、可以直接复制修改的插件示例：

```python
"""
Test
A Class Widgets plugin.
"""

import sys
from ClassWidgets.SDK import CW2Plugin, PluginAPI, NotificationLevel
from loguru import logger


class Plugin(CW2Plugin):
    pid = "test.a"
    name = "Test"

    def __init__(self, api: PluginAPI):
        super().__init__(api)
        self.api = api
        self.notification_provider = None
        self.root = None

    def on_load(self):
        super().on_load()

        # 1. 通知：失败不影响路由注册
        try:
            self.notification_provider = self.api.notification.get_provider(
                provider_id=f"{self.pid}.notification",
                name=self.name,
                icon=None
            )
            logger.info("通知提供者获取成功")
        except Exception as e:
            logger.error(f"获取通知提供者失败，通知功能不可用: {e}")

        # 2. HTTP 路由
        http = sys.modules.get("http_api_mod")
        if http is None:
            logger.warning("HTTP API 插件未加载，跳过路由注册")
            return

        try:
            self.root = http.add_root("/test")
            self.root.register("/hello", self.handle_hello)
            self.root.register("/notify", self.handle_notify)
            logger.success("Test 插件 HTTP 路由注册完成")
        except http.RootConflictError as e:
            logger.error(f"根路径 {e.root_path} 被占用，路由注册失败")
        except http.RegistryError as e:
            logger.error(f"路由注册失败: {e}")

    def handle_hello(self, ctx, query, body):
        """GET /test/hello?name=张三"""
        name = query.get("name") or "World"
        return 200, {"code": 0, "data": {"message": f"Hello, {name}!"}}

    def handle_notify(self, ctx, query, body):
        """POST /test/notify  {"title": "...", "message": "...", "level": "INFO"}"""
        if not self.notification_provider:
            return 503, {"code": -1, "message": "通知功能不可用"}

        data = body or {}
        title = data.get("title") or query.get("title") or "来自 Test 插件"
        message = data.get("message") or query.get("message") or "这是一条测试通知。"
        level_str = (data.get("level") or query.get("level") or "INFO").upper()

        level_map = {
            "INFO": NotificationLevel.INFO,
            "ANNOUNCEMENT": NotificationLevel.ANNOUNCEMENT,
            "WARNING": NotificationLevel.WARNING,
            "SYSTEM": NotificationLevel.SYSTEM,
        }
        level = level_map.get(level_str, NotificationLevel.INFO)

        try:
            self.notification_provider.push(
                level=level,
                title=title,
                message=message,
                duration=5000,
                closable=True,
            )
            return 200, {"code": 0, "data": {"sent": True}}
        except Exception as e:
            return 500, {"code": -1, "message": f"发送失败: {e}"}

    def on_unload(self):
        if self.root is not None:
            self.root.destroy()
            self.root = None
```

调用方式：

```bash
# GET
curl "http://127.0.0.1:8080/test/hello?name=张三"

# POST
curl "http://127.0.0.1:8080/test/notify" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"title":"114514","message":"1234567890","level":"WARNING"}'
```

## 8. 错误类型一览

所有异常继承自 `RegistryError`，可以精确捕获：

| 异常 | 含义 | 属性 |
|------|------|------|
| `RegistryError` | 所有注册表错误的基类 | — |
| `ReservedPrefixError` | 路径命中保留前缀（`/cwsdk`、`/system`、`/internal`、`/cw`、`/debug`、`/embedded`） | `.path`、`.prefix` |
| `RootConflictError` | 根路径已被占用 | `.root_path` |
| `RouteConflictError` | 完整路径已被占用 | `.full_path` |
| `InvalidPathError` | 路径格式不合法 | `.path`、`.reason` |

推荐捕获方式：

```python
try:
    self.root = http.add_root("/test")
    self.root.register("/hello", self.handle_hello)
except http.RootConflictError as e:
    logger.error(f"根路径 {e.root_path} 被占用")
except http.ReservedPrefixError as e:
    logger.error(f"不能用保留前缀 {e.prefix}")
except http.RegistryError as e:
    logger.error(f"注册失败: {e}")
```

## 9. 常见问题

**Q: 插件加载顺序怎么保证？**

A: 无法保证。必须假设 HTTP API 插件可能还没加载，用 `sys.modules.get` 判断 `None` 后跳过，或在 `QTimer` 里重试。

**Q: 处理函数能不能是 `async def`？**

A: 不支持。HTTP API 插件用的是同步的 `ThreadingHTTPServer`，`async def` 返回的是协程对象，不是结果。

**Q: 插件卸载了，但 HTTP API 插件还在跑，会怎样？**

A: 如果你在 `on_unload` 里调用了 `root.destroy()`，不会有残留。如果忘了调用，路由表里会留下指向已销毁对象的引用，外部访问时报 500。