from ClassWidgets.SDK import CW2Plugin, PluginAPI
from loguru import logger
import http.server
import socketserver
import json
import threading
import os


class CustomHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            fields_config = self.server.plugin.config.get('fields', {})
            runtime = self.server.plugin_api.runtime

            response_data = {}

            if fields_config.get('current_time', True):
                response_data['current_time'] = runtime.current_time
            if fields_config.get('current_day_of_week', True):
                response_data['current_day_of_week'] = runtime.current_day_of_week
            if fields_config.get('current_week', True):
                response_data['current_week'] = runtime.current_week
            if fields_config.get('current_week_of_cycle', True):
                response_data['current_week_of_cycle'] = runtime.current_week_of_cycle
            if fields_config.get('time_offset', True):
                response_data['time_offset'] = runtime.time_offset
            if fields_config.get('schedule_meta', True):
                response_data['schedule_meta'] = runtime.schedule_meta
            if fields_config.get('current_day_entries', True):
                response_data['current_day_entries'] = runtime.current_day_entries
            if fields_config.get('current_entry', True):
                response_data['current_entry'] = runtime.current_entry
            if fields_config.get('current_subject', True):
                response_data['current_subject'] = runtime.current_subject
            if fields_config.get('current_title', True):
                response_data['current_title'] = runtime.current_title
            if fields_config.get('next_entries', True):
                response_data['next_entries'] = runtime.next_entries
            if fields_config.get('current_status', True):
                response_data['current_status'] = runtime.current_status
            if fields_config.get('progress', True):
                response_data['progress'] = runtime.progress
            if fields_config.get('remaining_time', True):
                response_data['remaining_time'] = runtime.remaining_time

            response = json.dumps(response_data, indent=2, ensure_ascii=False, default=str).encode('utf-8')
            self.wfile.write(response)
            logger.success(f"Get请求成功")

        except Exception as e:
            logger.error(f"请求失败：{e}")
            self.send_error(500, f"网络服务器错误：{e}")

    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format % args}")


class CustomTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, plugin, plugin_api):
        self.plugin = plugin
        self.plugin_api = plugin_api
        super().__init__(server_address, RequestHandlerClass)


class Plugin(CW2Plugin):
    pid = "http.lyang1273"
    name = "HTTP API Plugin"
    version = "1.0.0"

    def __init__(self, api: PluginAPI):
        super().__init__(api)
        self.api = api
        self.httpd = None
        self.server_thread = None
        self.config = {}
        self._load_config()

    def _load_config(self):
        try:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(plugin_dir, "config.json")

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"配置已加载：{config_path}")
            else:
                logger.warning(f"找不到配置文件，创建一个默认配置")
                self.config = {
                    "port": 8080,
                    "fields": {
                        "current_time": True,
                        "current_day_of_week": True,
                        "current_week": True,
                        "current_week_of_cycle": True,
                        "time_offset": True,
                        "schedule_meta": True,
                        "current_day_entries": True,
                        "current_entry": True,
                        "current_subject": True,
                        "current_title": True,
                        "next_entries": True,
                        "current_status": True,
                        "progress": True,
                        "remaining_time": True
                    }
                }
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                logger.info(f"默认配置已创建：{config_path}")

        except Exception as e:
            logger.error(f"配置加载失败：{e}")
            self.config = {"port": 8080, "fields": {}}

    def start_http_server(self):
        port = self.config.get('port', 8080)

        try:
            self.httpd = CustomTCPServer(("", port), CustomHandler, self, self.api)
            logger.info(f"HTTP 服务器启动，端口号 {port}")
            self.httpd.serve_forever()

        except OSError as e:
            logger.error(f"端口号 {port} 被占用：{e}")
        except Exception as e:
            logger.error(f"HTTP 服务器启动失败：{e}")

    def on_load(self):
        super().on_load()
        logger.info(f"{self.name} v{self.version} 请稍后")
        self._load_config()

        self.server_thread = threading.Thread(target=self.start_http_server, daemon=True)
        self.server_thread.start()
        logger.info("HTTP 服务器线程启动")

    def on_unload(self):
        logger.info(f"{self.name} 卸载中")
        if self.httpd:
            logger.info("正在关闭 HTTP 服务器")
            try:
                def shutdown_server():
                    try:
                        self.httpd.shutdown()
                        self.httpd.server_close()
                    except Exception as e:
                        logger.error(f"关闭服务器异常: {e}")

                t = threading.Thread(target=shutdown_server, daemon=True)
                t.start()
                t.join(timeout=2.0)
                logger.info("HTTP 服务器已关闭")
            except Exception as e:
                logger.error(f"关闭服务器失败: {e}")