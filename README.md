<div align="center">
 <img src="icon.png" alt="HTTP API 插件徽标" width="18%">
 <h1>HTTP API</h1>
</div>

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Lyang1273/ClassWidgets2-HTTP_API_pigu)


## 介绍

通过 HTTP API 给你的西大不丢（Class Widgets 2）开放一个 API 接口。

详细接口说明请参阅 [docs/doc.md](docs/doc.md)。

## 开始使用

1. 安装插件（将插件目录放入 Class Widgets 2 的插件目录并启用）。
2. 确保手机/浏览器与运行 Class Widgets 的电脑处于同一局域网。
3. 浏览器访问 `http://<你的ip地址>:8080`（如 `http://192.168.1.5:8080`）。

## 设置

插件配置文件位于插件目录下（`config.json`），不存在时插件会自动创建默认配置。

```json
{
  "port": 8080
}
```

- `port`：HTTP 服务器监听端口（默认 `8080`）。

也可在 Class Widgets 2 的「设置 → 插件」中打开本插件的设置页面，直接修改端口并重启服务器，无需手动编辑 `config.json`。

## 致谢

- https://github.com/rinlit-233-shiroko/class-widgets-2
- https://github.com/Class-Widgets/class-widgets-sdk
- https://github.com/Delgan/loguru
- https://github.com/UniDesktop/SDK

## 版权

本项目基于 MIT 协议开源，详情请参阅 LICENSE 文件。
The project is licensed under the MIT license. Please refer to the LICENSE file for details.

Copyright © 2026 Lyang1273.
