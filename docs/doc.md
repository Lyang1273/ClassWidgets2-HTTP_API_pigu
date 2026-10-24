# HTTP API 参考文档

> [!NOTE]
> 适用版本 0.6.0 (Lake Tekapo)

通过 HTTP 请求使用 Class Widgets 2 的 SDK 能力。所有响应均为 JSON（`Content-Type: application/json; charset=utf-8`），并带 `Access-Control-Allow-Origin: *`（支持浏览器跨域调用）。

- **基础地址**：`http://<运行ClassWidgets的IP>:<端口>`，默认端口 `8080`
- **统一响应格式**：

  ```json
  { "code": 0, "message": "success", "data": { ... } }
  ```

  - `code`：业务状态码，`0` 表示成功；失败时为对应错误码
  - `message`：说明信息
  - `data`：业务数据（可能为 `null`）
- **状态码**：`200` 成功 / `400` JSON 格式错误或参数缺失 / `404` 路由不存在 / `500` 服务器内部错误
- **CORS**：`OPTIONS` 预检请求返回 `200`

## 配置

配置文件位于插件目录下 `config.json`，不存在时插件会自动创建默认配置。

```json
{
  "port": 8080
}
```

- `port`：HTTP 服务器监听端口

### 设置界面

插件在 Class Widgets 2 的「设置 → 插件」中提供图形化设置页面（`assets/settings.qml`），可查看服务器运行状态、修改监听端口并保存重启，以及一键在浏览器中打开面板。修改端口后插件会自动重启 HTTP 服务器；若端口非法或被占用会给出提示。

## `/cwsdk`

Class Widgets SDK 相关接口。

### GET `/cwsdk/runtime`

返回 ClassWidgets 的运行时数据。

字段说明（详细类型参考：https://github.com/RinLit-233-shiroko/Class-Widgets-2/blob/main/docs/dev/plugin/api_reference.md#4-runtimeapi---%E8%BF%90%E8%A1%8C%E6%97%B6%E4%BF%A1%E6%81%AF）：

| 字段 | 说明 |
| --- | --- |
| `current_time` | 当前时间 |
| `current_day_of_week` | 今天是星期几 |
| `current_week` | 当前周 |
| `current_week_of_cycle` | 当前大周 |
| `time_offset` | 时间偏移 |
| `schedule_meta` | 课程表元信息 |
| `current_day_entries` | 今天的课程条目列表 |
| `current_entry` | 当前课程条目 |
| `current_subject` | 当前学科 |
| `current_title` | 当前标题 |
| `next_entries` | 接下来课程条目列表 |
| `current_status` | 当前状态 |
| `progress` | 课程进度 |
| `remaining_time` | 剩余时间 |

示例响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "current_time": "2026-08-12 10:00:00",
    "current_day_of_week": 3,
    "current_week": 2,
    "current_week_of_cycle": 1,
    "time_offset": 0,
    "schedule_meta": { "name": "New Schedule 1" },
    "current_day_entries": [],
    "current_entry": null,
    "current_subject": null,
    "current_title": null,
    "next_entries": [],
    "current_status": "free",
    "progress": 0.0,
    "remaining_time": "00:00:00"
  }
}
```

### GET/POST `/cwsdk/notification`、`/cwsdk/notifi`

两个路径效果一致，`notifi` 为别名。发送 ClassWidgets 灵动通知。

**GET 查询参数 / POST JSON 字段：**

| 字段 | 说明 | 默认值 |
| --- | --- | --- |
| `level` | 通知级别：`INFO`、`ANNOUNCEMENT`、`WARNING`、`SYSTEM`（大小写不敏感，未知值回退为 `INFO`） | `INFO` |
| `title` | 通知标题 | `来自 HTTP API 的通知` |
| `message` | 通知内容（可选） | `""` |
| `duration` | 显示时长（毫秒），根据具体实现决定 `0`/`-1` 是否常驻 | `5000` |
| `closable` | 是否可关闭：GET 下字符串 `true`/`1`/`yes` 视为真；POST 下请传 JSON 布尔值（注意：POST 传字符串 `"false"` 会被视为真） | `true` |

**GET 示例：**

```
GET /cwsdk/notification?level=WARNING&title=测试&message=你好&duration=3000&closable=false
```

**POST 示例：**

```bash
curl -X POST http://localhost:8080/cwsdk/notification \
  -H "Content-Type: application/json" \
  -d '{"level":"WARNING","title":"测试","message":"你好","duration":3000,"closable":false}'
```

响应：

```json
{ "code": 0, "message": "通知已发送", "data": null }
```

若通知提供者未注册（`provider` 注册失败），返回 `500`：`{"code": 500, "message": "通知提供者未注册", "data": null}`。

### GET `/cwsdk/schedule/get`

获取课程表对象，序列化为 JSON。结构包含：`meta`（课程表元信息）、`subjects`（学科列表）、`days`（按天的课程时间线）、`overrides`（临时替换/调课记录）。枚举字段（如 `type`、`weeks`）会转换为字符串值，如 `"class"`、`"break"`、`"all"`；日期、时间等对象会转换为 ISO 格式字符串。

### GET `/cwsdk/schedule/reload`

重新加载课程表。响应：`{ "code": 0, "message": "课程表已重新加载", "data": null }`。

### 课程表管理 `/cwsdk/schedulemanage/*`

| 接口 | 方法 | 必要参数 | 说明 |
| --- | --- | --- | --- |
| `/cwsdk/schedulemanage/list` | GET | — | 列出全部课程表 |
| `/cwsdk/schedulemanage/switch` | GET/POST | `name` | 切换到指定名称的课程表 |
| `/cwsdk/schedulemanage/add` | GET/POST | `name` | 新建课程表 |
| `/cwsdk/schedulemanage/save` | GET/POST | `name` | 将当前课程表保存为指定名称 |

- GET 通过查询参数传参，POST 通过 JSON body 传参（如 `{"name": "新学期"}`）。
- 缺少 `name` 返回 `400`；操作失败返回 `500`。

### GET `/cwsdk/app/info`

获取应用信息，`data` 为应用信息对象。

### GET `/cwsdk/app/restart`

下发重启命令。响应：`{ "code": 0, "message": "已下发重启命令", "data": null }`。

### GET `/cwsdk/theme/current`

获取当前主题信息，`data` 为当前主题对象。

### GET/POST `/cwsdk/diagnostics`

读取主程序诊断日志，`data` 为日志列表，每项结构：

| 字段 | 说明 |
| --- | --- |
| `time` | 日志时间 |
| `level` | 日志级别 |
| `message` | 日志内容 |

**参数：**

| 字段 | 说明 | 默认值 |
| --- | --- | --- |
| `limit` | 读取的日志条数，必须为正整数 | `100` |

- GET 通过查询参数传参，POST 通过 JSON body 传参（如 `{"limit": 50}`）。
- `limit` 非正整数返回 `400`；读取失败返回 `500`。

示例响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    { "time": "2026-08-12 10:00:00", "level": "INFO", "message": "应用启动" }
  ]
}
```

### 全局 Action `/cwsdk/action/*`

与 Class Widgets 2 SDK 的 `ActionsAPI` 对接，用于查询、触发和注册全局 Action（Action 即带参数的 Qt Signal）。以下接口均支持 GET 与 POST。

| 接口 | 参数 | 说明 |
| --- | --- | --- |
| `/cwsdk/action/get` | `name` | 查询 Action 是否存在，返回 `{ "name": ..., "exists": true }`；未注册返回 `404` |
| `/cwsdk/action/emit` | `name`、`args` | 触发 Action，等价于 `ctx.api.actions.get(name).emit(*args)` |
| `/cwsdk/action/register` | `name`、`params` | 注册 Action，等价于 `ctx.api.actions.register(name, *parameter_types)` |

- `name` 必填，缺失返回 `400`；未找到 Action 返回 `404`；触发/注册失败返回 `500`。
- `args` 的**个数与类型**必须和注册时的参数一致（例如注册为 `str,int` 就必须传 2 个参数）。

**`args` 的写法（无需 URL 转义）：**

| 写法 | 结果 |
| --- | --- |
| `args=dashboard,0` | `emit("dashboard", 0)` |
| `args=hello` | `emit("hello")` |
| `args=true,3.14` | `emit(True, 3.14)` |
| `args=[1,2]` | `emit(1, 2)`（JSON 数组） |
| `args=["a,b"]` | `emit("a,b")`（字符串含逗号时用此形式） |

- 逗号分隔时会智能转换：`true`/`false` → 布尔值，纯整数 → `int`，纯小数 → `float`，其余为字符串；`null`/`none` → `None`。
- POST 也可直接传 JSON：`{"name": "...", "args": ["dashboard", 0]}`。

**`params` 的类型名**：`str`/`string`、`int`、`float`、`bool`、`list`、`dict`、`any`；多个类型用逗号分隔（如 `params=str,int`）。

示例：

```
GET /cwsdk/action/emit?name=com.example.open&args=dashboard,0
```

```bash
curl -X POST http://localhost:8080/cwsdk/action/emit \
  -H "Content-Type: application/json" \
  -d '{"name":"com.example.open","args":["dashboard",0]}'
```

## `/cw`

### GET `/cw/cw_ver`

读取 `./configs/configs.json`（相对 ClassWidgets 工作目录），返回应用版本号。

## `/system`

系统操作。`/system/is_admin`、`/system/window_title` 仅在 Windows 可用；`/system/lock_screen` 跨平台。

### GET `/system/system_name`

返回操作系统名称（同 Python `platform.system()`），如 `Windows`。

### GET `/system/system_version`

返回操作系统版本号（同 `platform.version()`）。

### GET `/system/system_release`

返回操作系统发行版本（同 `platform.release()`）。

### GET `/system/is_admin`

检测当前程序是否以管理员权限运行。

响应：`{ "code": 0, "message": "success", "data": "True" | "False" }`

### GET `/system/window_title`

获取当前前台窗口的标题。

响应：`{ "code": 0, "message": "success", "data": "<窗口标题>" }`

### GET `/system/lock_screen`

锁定当前会话（跨平台，底层使用 [UDA](https://github.com/UniDesktop/SDK)）。

- Windows：`LockWorkStation()`
- Linux：`org.freedesktop.ScreenSaver.Lock()`，失败时回退 `loginctl lock-session`

成功响应：`{ "code": 0, "message": "success", "data": "True" }`

动态库缺失、当前桌面环境不支持锁定或后端调用失败时返回 `500`，`message` 中给出具体原因，
例如 `{ "code": 500, "message": "锁屏失败: ...", "data": null }`。

依赖插件目录 `http_api_plugin/uda/` 下与当前平台、架构匹配的动态库：

| 平台 | 文件名 | 说明 |
| --- | --- | --- |
| Windows 10/11 | `uda_ffi.dll` | 自带，无额外运行时依赖 |
| Linux | `libuda_ffi.so` | x86-64；需要 glibc ≥ 2.39（Ubuntu 24.04+、Fedora 40+、Debian 13+），musl（如 Alpine）不可用 |

库版本与解释器架构不匹配时（例如 32 位 Python 加载 64 位库）会被跳过并回退为 `500`，
不会影响插件的其他接口。可用环境变量 `UDA_LIBRARY` 指定其他路径的动态库。

接口实现见 `http_api_plugin/uni_desktop.py`：所有 UDA 相关路由都通过它统一加载动态库并
处理错误，新增接口时只需一行，详见[为插件开发接口](#为插件开发接口)。

### GET `/system/open_website`

用默认浏览器打开链接。

| 参数 | 说明 |
| --- | --- |
| `link` | 要打开的 URL（必填） |

缺少 `link` 返回 `400`；成功响应 `{ "code": 0, "message": "success", "data": "True" }`。

## `/debug`

### GET `/debug/exec`

> [!WARNING]
> 危险接口！执行任意 Python 代码，可能破坏系统。

执行远端下发的 Python 代码。执行前会在运行 ClassWidgets 的电脑上弹出确认对话框，用户拒绝则返回 `0`，同意则执行并返回 `1`。

| 参数 | 说明 |
| --- | --- |
| `code` | 要执行的 Python 代码（必填） |

响应：`{ "code": 0, "message": "success", "data": 0 | 1 }`

## 插件集成接口 `http_api_mod`

> [!NOTE]
> 有关`http_api_mod`的使用教程，请参见[此处](/docs/使用插件集成api接口.md)

本插件在加载时会向 `sys.modules` 注入一个名为 `http_api_mod` 的虚拟模块，供**其他 Class Widgets 插件**在运行期注册自己的 HTTP 路由。其他插件通过 `import http_api_mod` 即可使用，无需依赖本插件的包路径。

> [!NOTE]
> 该模块仅在本插件启用期间存在；本插件卸载时会从 `sys.modules` 中移除，并清空全部外部注册的路由。

### `http_api_mod.add_root(root_path)`

注册一个根路径，返回一个 `RootRegistry` 对象用于管理其子路由。

| 参数 | 说明 |
| --- | --- |
| `root_path` | 根路径，如 `/myplugin`。会自动补全前导 `/` 并去掉结尾 `/` |

- 根路径不能为 `/`，否则抛出 `InvalidPathError`。
- 根路径命中保留前缀时抛出 `ReservedPrefixError`。
- 根路径已被占用时抛出 `RootConflictError`。

### `RootRegistry.register(sub_path, handler, methods=None)`

在根路径下注册子路由。

| 参数 | 说明 |
| --- | --- |
| `sub_path` | 子路径，如 `/status`；传 `/` 表示根路径本身 |
| `handler` | 处理函数，签名见下 |
| `methods` | 可选。`None`（默认）表示**不限定 HTTP 方法**；传字符串或字符串列表（如 `["GET", "POST"]`）则为每个方法分别注册同一个 handler |

- 完整路径与已有方法冲突时抛出 `RouteConflictError`。
- 完整路径命中保留前缀时抛出 `ReservedPrefixError`。
- 返回注册的完整路径字符串。

### `RootRegistry.unregister(sub_path, methods=None)`

取消注册。`methods` 为 `None` 时移除该路径下的全部方法（含通配）；否则仅移除指定方法。

### `RootRegistry.destroy()`

清空该根路径下注册的所有路由，并从根路径表中移除该根。

### 处理函数签名与返回值

```python
def handler(ctx, query, body):
    ...
```

| 参数 | 说明 |
| --- | --- |
| `ctx` | 运行期上下文对象，见下 |
| `query` | GET 请求的查询参数字典（POST 时为 `{}`） |
| `body` | POST 请求解析后的 JSON（GET 时为 `None`） |

返回值支持三种形式：

| 返回 | 效果 |
| --- | --- |
| `None` | 返回 `200`，`{ "code": 0, "message": "ok", "data": null }` |
| `(http_code, payload)` | 以 `http_code` 作为 HTTP 状态码，`payload` 作为 JSON 体 |
| 其他（如 `dict`） | 返回 `200`，直接把返回值作为 JSON 体 |

推荐使用 `http_api_mod.success(data, message)` 与 `http_api_mod.error(code, message)` 构造返回值（等价于 `response.py` 中的 `success`/`error`，均返回 `(http_code, payload)` 元组）。

### `ctx` 可用属性

| 属性 | 说明 |
| --- | --- |
| `ctx.plugin` | HTTP API 插件实例 |
| `ctx.api` | Class Widgets SDK 的 `PluginAPI` 对象 |
| `ctx.notification_provider` | 本插件注册的通知提供者，可能为 `None` |
| `ctx.config` | 本插件配置对象（`port`） |

### 保留前缀

其他插件不得注册以下前缀（及其子路径），否则抛出 `ReservedPrefixError`：

`/cwsdk`、`/system`、`/internal`、`/cw`、`/debug`、`/embedded`

### 异常类

`http_api_mod` 暴露以下异常类，均继承自 `RegistryError`：`RegistryError`、`ReservedPrefixError`、`RootConflictError`、`RouteConflictError`、`InvalidPathError`。

### 示例

```python
import http_api_mod

root = http_api_mod.add_root("/myplugin")


def hello(ctx, query, body):
    return http_api_mod.success({"hello": "world"})


root.register("/hello", hello, methods=["GET"])
```

注册后即可通过 `GET /myplugin/hello` 访问。

### 接口版本

虚拟模块暴露 `http_api_mod.__version__`（等于本插件版本号），可用于兼容性判断。

## 为插件开发接口

在本插件内新增使用 UDA（桌面能力）的接口时，不要自己加载动态库：`http_api_plugin/uni_desktop.py`
已经封装了选库、架构校验、单例加载与错误处理。路由里只需一行：

```python
from ..response import success
from ..uni_desktop import uda_call

def handle_theme(ctx, query, body):
    return uda_call(lambda u: u.theme, what="获取主题")

def handle_lock_screen(ctx, query, body):
    return uda_call(lambda u: u.session.lock(), what="锁屏")
```

`uda_call` 的行为：

- 成功：返回 `{ "code": 0, "message": "success", "data": <返回值> }`；回调没有返回值时 `data` 为 `"True"`。
- UDA 不可用（未找到匹配的库）：返回 `500`，`message` 说明缺少哪个文件。
- 回调抛异常：返回 `500`，`message` 形如 `锁屏失败: <原因>`。

其它可用的模块级函数：

| 函数 | 用途 |
| --- | --- |
| `available()` | UDA 是否可用 |
| `is_supported(action)` | 当前平台是否支持某个会话动作（`lock` / `suspend` / `reboot` 等），不会抛异常 |
| `get_uda()` | 直接取 `Uda` 实例，用于需要多次调用的场景 |
| `release()` | 插件卸载时释放常亮锁与托盘资源 |
| `unavailable_reason()` | 不可用的具体原因（用于日志或错误信息） |

> [!WARNING]
> 会话类动作中只有 `lock` 适合直接暴露为接口。`shutdown` / `reboot` / `suspend` / `hibernate` /
> `logout` 会中断用户会话或关机，若封装为接口必须默认关闭并显式要求确认参数。

### 直接使用 UDA SDK（官方写法）

插件加载时会自动完成两件事：把 `http_api_plugin/uda/` 加入 `sys.path`，并把匹配当前平台的
动态库写入环境变量 `UDA_LIBRARY`。因此可以**照抄 UDA 官方文档**，无需传 `library_path`：

```python
from uda import Uda

with Uda() as uda:
    print("主题:", uda.theme)
    uda.notify("你好，桌面", "这是通过 UDA 发出的第一条系统通知。")
```

> [!NOTE]
> 上述代码的前置条件是**插件已经加载**（`http_api_plugin` 被导入）。独立脚本中直接使用需自行
> 设置 `UDA_LIBRARY` 或把 `uda/` 加入 `sys.path`。

### 在 Windows 上发通知，请优先用 Class Widgets 的通知

实测：UDA 的 `notify()` 在**普通（非 MSIX 打包）Windows 进程**中会失败，报错
`UDA error -5: CreateToastNotifierWithId failed: 该进程没有程序包标识符 (0x80073D54)`。
这是 Windows toast 要求包标识（AUMID）所致，与插件集成无关——不经插件、单独调用也如此。

因此在 Class Widgets 内发通知，请用已有的 `/cwsdk/notification` 接口或
`ctx.notification_provider`，不要依赖 `uda.notify()`。UDA 的其余能力（如锁屏）不受影响。