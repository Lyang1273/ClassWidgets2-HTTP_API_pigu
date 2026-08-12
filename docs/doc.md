# HTTP API 参考文档

通过 HTTP 请求使用 Class Widgets SDK。所有响应均为 JSON（`Content-Type: application/json; charset=utf-8`），并带 `Access-Control-Allow-Origin: *`（支持浏览器跨域调用）。

- **基础地址**：`http://<运行ClassWidgets的IP>:<端口>`，默认端口 `8080`
- 错误响应统一格式：`{"error": "错误信息"}`
- 状态码：`200` 成功 / `400` JSON 格式错误 / `404` 路由不存在 / `500` 服务器内部错误

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

- `port`：HTTP 服务器端口
- `fields`：`/cwsdk/runtime` 返回字段的开关，`false` 表示不在响应中返回该字段

## `/cwsdk`

Class Widgets SDK

### `/cwsdk/runtime`

支持 `GET`

返回 ClassWidgets 的运行时数据。返回字段由 `config.json` 的 `fields` 控制。

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
```

### `/cwsdk/notification` 和 `/cwsdk/notifi`

支持 `GET` `POST`（两个路径效果一致，`notifi` 为别名）

发送 ClassWidgets 灵动通知。

**GET 查询参数 / POST JSON 字段：**

| 字段 | 说明 | 默认值 |
| --- | --- | --- |
| `level` | 通知级别：`INFO`(0)、`ANNOUNCEMENT`(1)、`WARNING`(2)、`SYSTEM`(3)，已支持数字传入 | `INFO` |
| `title` | 通知标题 | `来自 HTTP API 的通知` |
| `message` | 通知内容（可选） | `""` |
| `duration` | 显示时长（毫秒），`0` 或 `-1` 表示常驻 | `5000` |
| `closable` | 是否可关闭（字符串 `true`/`1`/`yes` 视为真） | `true` |

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
{ "status": "success", "message": "通知已发送" }
```

### `/cwsdk/schedule`

课程表数据

- `/cwsdk/schedule/get`（`GET`）
  - 获取课程表对象，序列化为 JSON
  - 结构：`meta`（课程表元信息）、`subjects`（学科列表）、`days`（按天的课程时间线）、`overrides`（临时替换/调课记录）
  - 枚举字段（如 `type`、`weeks`）会转换为字符串值，如 `"class"`、`"break"`、`"all"`
- `/cwsdk/schedule/reload`（`GET`）
  - 重新加载课程表
  - 响应：`{ "status": "success", "message": "课程表已重新加载" }`

## `/system`

系统操作（仅 Windows，依赖 `ctypes`）

### `/system/is_admin`

支持 `GET`

检测当前程序是否以管理员权限运行。

响应：`{ "status": "success", "message": "True" | "False" }`

### `/system/window_title`

支持 `GET`

获取当前前台窗口的标题。

响应：`{ "status": "success", "message": "<窗口标题>" }`

### `/system/lock_screen`

支持 `GET`

锁定工作站屏幕。

响应：`{ "status": "success", "message": "True" | "False" }`
