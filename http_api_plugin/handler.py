import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from loguru import logger
from .routes import resolve, registry
from .response import success


class CustomHandler(BaseHTTPRequestHandler):
    timeout = 15

    def do_GET(self):
        logger.info("收到GET请求")
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}

            handler, is_external = self._resolve(path, "GET")
            if handler is None:
                self._send_json_error(404, "Not Found")
                return

            result = self._call_handler(handler, path, query, None, is_external)
            self._send_result(result)
            logger.success(f"GET {path} 请求成功")
        except ConnectionError as e:
            logger.debug(f"GET 请求连接中断: {e}")
        except Exception as e:
            logger.error(f"GET 请求失败: {e}")
            self._safe_send_json_error(500, "内部服务器错误")

    def do_POST(self):
        try:
            path = urlparse(self.path).path

            handler, is_external = self._resolve(path, "POST")
            if handler is None:
                self._send_json_error(404, "Not Found")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            # 空请求体是合法的：`POST /system/media/play` 这类无参数指令本来就
            # 不带 body。此时按 None 传给处理器，而不是把空串交给 json.loads
            # 报「无效的 JSON 格式」。
            if post_data.strip():
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = None

            result = self._call_handler(handler, path, {}, data, is_external)
            self._send_result(result)
            logger.success(f"POST {path} 请求成功")
        except json.JSONDecodeError:
            self._send_json_error(400, "无效的 JSON 格式")
        except ConnectionError as e:
            logger.debug(f"POST 请求连接中断: {e}")
        except Exception as e:
            logger.error(f"POST 请求失败: {e}")
            self._safe_send_json_error(500, "内部服务器错误")

    def _resolve(self, path, method):
        handler = resolve(path, method)
        if handler is not None:
            return handler, False
        return registry.get_handler(path, method), True

    def _call_handler(self, handler, path, query, body, is_external):
        try:
            return handler(self.server.ctx, query, body)
        except Exception as e:
            if is_external:
                logger.error(f"外部插件处理 {path} 失败: {e}")
            raise

    def _send_result(self, result):
        if result is None:
            self._send_json(200, {"code": 0, "message": "ok", "data": None})
        elif isinstance(result, tuple) and len(result) == 2:
            code, payload = result
            self._send_json(int(code), payload)
        else:
            self._send_json(200, result)

    def _send_json(self, code, payload):
        body = json.dumps(payload, indent=2, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_json_error(self, code, message):
        error_body = json.dumps({'code': code, 'message': message, 'data': None}, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(error_body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(error_body)

    def _safe_send_json_error(self, code, message):
        try:
            self._send_json_error(code, message)
        except ConnectionError:
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format % args}")
