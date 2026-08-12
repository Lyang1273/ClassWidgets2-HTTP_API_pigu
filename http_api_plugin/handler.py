import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from loguru import logger
from .routes import resolve


class CustomHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}

            handler = resolve(path, "GET")
            if handler is None:
                self._send_json_error(404, "Not Found")
                return

            code, payload = handler(self.server.ctx, query, None)
            self._send_json(code, payload)
            logger.success(f"GET {path} 请求成功")
        except Exception as e:
            logger.error(f"GET 请求失败: {e}")
            self._send_json_error(500, "内部服务器错误")

    def do_POST(self):
        try:
            path = urlparse(self.path).path

            handler = resolve(path, "POST")
            if handler is None:
                self._send_json_error(404, "Not Found")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            code, payload = handler(self.server.ctx, {}, data)
            self._send_json(code, payload)
            logger.success(f"POST {path} 请求成功")
        except json.JSONDecodeError:
            self._send_json_error(400, "无效的 JSON 格式")
        except Exception as e:
            logger.error(f"POST 请求失败: {e}")
            self._send_json_error(500, "内部服务器错误")

    def _send_json(self, code, payload):
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        body = json.dumps(payload, indent=2, ensure_ascii=False, default=str).encode('utf-8')
        self.wfile.write(body)

    def _send_json_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_body = json.dumps({'error': message}, ensure_ascii=False)
        self.wfile.write(error_body.encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format % args}")
