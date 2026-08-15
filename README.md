<div align="center">
 <img src="icon.png" alt="插件图标" width="18%">
 <h1>HTTP API</h1>
</div>

> [!NOTE]
> 本文档由 AI 生成（生成日期：2026-08-15），内容基于源码整理，可能存在偏差，请以实际代码行为为准。

## 介绍

通过 HTTP 请求获取西大不丢（Class Widgets 2）的运行时数据，并支持通知发送、课程表管理、系统操作等远程控制能力。所有接口返回 JSON。

详细接口说明请参阅 [docs/doc.md](docs/doc.md)。

## 开始使用

1. 安装插件（将插件目录放入 Class Widgets 2 的插件目录并启用）。
2. 确保手机/浏览器与运行 Class Widgets 的电脑处于同一局域网。
3. 浏览器访问 `http://<你的ip地址>:8080`（如 `http://192.168.1.5:8080`）。

## 设置

插件配置文件位于插件目录下（`config.json`），不存在时插件会自动创建默认配置。

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

- `port`：HTTP 服务器监听端口（默认 `8080`）。
- `fields`：`/cwsdk/runtime` 接口返回字段的开关，`false` 表示不在响应中返回该字段。

`fields` 各字段的详细类型与含义，请参阅 [Class Widgets 2 插件 API 参考](https://github.com/RinLit-233-shiroko/Class-Widgets-2/blob/main/docs/dev/plugin/api_reference.md#4-runtimeapi---%E8%BF%90%E8%A1%8C%E6%97%B6%E4%BF%A1%E6%81%AF)。

## 致谢

- https://github.com/rinlit-233-shiroko/class-widgets-2
- https://github.com/Class-Widgets/class-widgets-sdk
- https://github.com/Delgan/loguru

## 版权

本项目基于 MIT 协议开源，详情请参阅 LICENSE 文件。
The project is licensed under the MIT license. Please refer to the LICENSE file for details.

Copyright © 2026 Lyang1273.
