# HTTP API 参考文档

> [!NOTE]
> 本文档由 AI 生成（生成日期：2026-10-17），内容基于源码整理，可能存在偏差，请以实际代码行为准。

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
  "port": 8080,
  "fields": {
    "current_time": true,
    "current_day_of_week": true,
    "current_week": true,
    "current_week_of_cycle": true,
    "time_offset": true,
    "schedule_meta": true,
    "current_day_entries": true,
    "current_entry": true,
    "current_subject": true,
    "current_title": true,
    "next_entries": true,
    "current_status": true,
    "progress": true,
    "remaining_time": true
  }
}
```

- `port`：HTTP 服务器监听端口
- `fields`：`/cwsdk/runtime` 返回字段的开关，`false` 表示不在响应中返回该字段

## `/cwsdk`

Class Widgets SDK 相关接口。

### GET `/cwsdk/runtime`

返回 ClassWidgets 的运行时数据，返回字段由 `config.json` 的 `fields` 控制。

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

## `/cw`

### GET `/cw/cw_ver`

读取 `./configs/configs.json`（相对 ClassWidgets 工作目录），返回应用版本号。

## `/system`

系统操作（仅 Windows，依赖 `ctypes`）。

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

锁定工作站屏幕。

响应：`{ "code": 0, "message": "success", "data": "True" | "False" }`

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
| `ctx.config` | 本插件配置对象（`port` / `fields`） |

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