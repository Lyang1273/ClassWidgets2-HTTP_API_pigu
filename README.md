<div align="center">
 <img src="icon.png" alt="插件图标" width="18%">
 <h1>HTTP API</h1>
</div>

 ## 介绍

 通过HTTP请求获取西大不丢的运行时数据

 ## 开始使用

 1.安装插件

 2.浏览器访问 [你的ip地址]:8080（如192.168.1.5:8080）

 ## 设置
 插件配置文件位于插件目录中（config.json）
 ```
{
  "port": 8080,    # 端口
  # 以下字段请参阅 https://github.com/RinLit-233-shiroko/Class-Widgets-2/blob/main/docs/dev/plugin/api_reference.md#4-runtimeapi---%E8%BF%90%E8%A1%8C%E6%97%B6%E4%BF%A1%E6%81%AF
  # （其实是懒）
  "fields": {
    "current_time": false,
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

## 致谢

- https://github.com/rinlit-233-shiroko/class-widgets-2
- https://github.com/Class-Widgets/class-widgets-sdk
- https://github.com/Delgan/loguru

## 版权

本项目基于 MIT 协议开源，详情请参阅 LICENSE 文件。
The project is licensed under the MIT license. Please refer to the LICENSE file for details.



  Copyright © 2026 Lyang1273.
