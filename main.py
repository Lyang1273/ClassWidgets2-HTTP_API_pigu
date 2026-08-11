from ClassWidgets.SDK import CW2Plugin, PluginAPI, NotificationLevel
from loguru import logger
import http.server
import socketserver
import json
import threading
import os
from urllib.parse import urlparse, parse_qs


class CustomHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/runtime":
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                fields_config = self.server.plugin.config.get('fields', {})
                runtime = self.server.plugin_api.runtime

                response_data = {}
                field_map = {
                    'current_time': runtime.current_time,
                    'current_day_of_week': runtime.current_day_of_week,
                    'current_week': runtime.current_week,
                    'current_week_of_cycle': runtime.current_week_of_cycle,
                    'time_offset': runtime.time_offset,
                    'schedule_meta': runtime.schedule_meta,
                    'current_day_entries': runtime.current_day_entries,
                    'current_entry': runtime.current_entry,
                    'current_subject': runtime.current_subject,
                    'current_title': runtime.current_title,
                    'next_entries': runtime.next_entries,
                    'current_status': runtime.current_status,
                    'progress': runtime.progress,
                    'remaining_time': runtime.remaining_time,
                }
                for key, default in field_map.items():
                    if fields_config.get(key, True):   # 默认启用
                        response_data[key] = default

                response = json.dumps(response_data, indent=2, ensure_ascii=False, default=str).encode('utf-8')
                self.wfile.write(response)
                logger.success("GET /runtime 请求成功")
                return

            if path in ("/notification", "/notifi"):
                # 从查询参数获取数据（GET 兼容）
                query = dict(parse_qs(parsed.query))
                # 解析参数（注意 parse_qs 返回列表，取最后一个值）
                data = {
                    'level': query.get('level', ['INFO'])[-1],
                    'title': query.get('title', [''])[-1] or '来自 HTTP API 的通知',
                    'message': query.get('message', [''])[-1],
                    'duration': query.get('duration', ['5000'])[-1],
                    'closable': query.get('closable', ['true'])[-1].lower() in ('true', '1', 'yes')
                }
                # 调用统一发送函数
                self._send_notification(data)
                return

            self._send_json_error(404, "Not Found")

        except Exception as e:
            logger.error(f"GET 请求失败: {e}")
            self._send_json_error(500, "内部服务器错误")

    def do_POST(self):
        try:
            path = self.path
            if path not in ("/notification", "/notifi"):
                self._send_json_error(404, "Not Found")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            self._send_notification(data)

        except json.JSONDecodeError:
            self._send_json_error(400, "无效的 JSON 格式")
        except Exception as e:
            logger.error(f"POST 请求失败: {e}")
            self._send_json_error(500, "内部服务器错误")

    def _send_notification(self, data):
        """统一发送通知，data 可为字典（来自 GET 查询或 POST JSON）"""
        # 解析 level
        level_str = data.get('level', 'INFO').upper()
        level_map = {
            'INFO': NotificationLevel.INFO,
            'ANNOUNCEMENT': NotificationLevel.ANNOUNCEMENT,
            'WARNING': NotificationLevel.WARNING,
            'SYSTEM': NotificationLevel.SYSTEM,
        }
        level = level_map.get(level_str, NotificationLevel.INFO)

        title = data.get('title', '来自 HTTP API 的通知')
        message = data.get('message', '')
        # 确保类型正确
        try:
            duration = int(data.get('duration', 5000))
        except (ValueError, TypeError):
            duration = 5000
        closable = bool(data.get('closable', True))

        provider = self.server.plugin.notification_provider
        provider.push(
            level=level,
            title=title,
            message=message,
            duration=duration,
            closable=closable
        )

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        resp = json.dumps({'status': 'success', 'message': '通知已发送'}, ensure_ascii=False)
        self.wfile.write(resp.encode('utf-8'))
        logger.success(f"通知发送成功: {title} - {message}")

    def _send_json_error(self, code, message):
        """发送 JSON 格式错误响应"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_body = json.dumps({'error': message}, ensure_ascii=False)
        self.wfile.write(error_body.encode('utf-8'))

    def do_OPTIONS(self):
        """处理 OPTIONS 预检请求，允许跨域"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

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
    version = "0.1.1"

    def __init__(self, api: PluginAPI):
        super().__init__(api)
        self.api = api
        self.httpd = None
        self.server_thread = None
        self.config = {}
        self.notification_provider = None
        self._load_config()

    def on_load(self):
        super().on_load()
        logger.info(f"{self.name} v{self.version} 加载中")

        try:
            self.notification_provider = self.api.notification.get_provider(
                provider_id=f"{self.pid}.notification",
                name=self.name,
                icon=None
            )
            logger.info("通知提供者注册成功")
        except Exception as e:
            logger.error(f"注册通知提供者失败: {e}")
            self.notification_provider = None

        self._load_config()

        self.server_thread = threading.Thread(target=self.start_http_server, daemon=True)
        self.server_thread.start()
        logger.info("HTTP 服务器线程启动")

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
