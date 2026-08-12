import socketserver
import sys
import threading
import urllib.request

from loguru import logger


class CustomTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128

    def __init__(self, server_address, RequestHandlerClass, ctx):
        self.ctx = ctx
        super().__init__(server_address, RequestHandlerClass)

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionError, BlockingIOError)):
            logger.debug(f"客户端连接异常中断: {client_address} ({exc})")
        else:
            logger.exception(f"处理 HTTP 请求时发生异常: {client_address}")


class ServerLifecycle:
    """HTTP 服务器启动、线程管理与关闭"""

    def __init__(self, ctx, handler_class):
        self.ctx = ctx
        self.handler_class = handler_class
        self.httpd = None
        self._thread = None

    @staticmethod
    def _check_port_in_use(port):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            return s.connect_ex(("127.0.0.1", port)) == 0
        finally:
            s.close()

    def _self_test(self, port):
        def probe():
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/system/is_admin", timeout=3) as resp:
                    logger.success(f"HTTP 服务器自检通过，本机访问正常 (HTTP {resp.status})")
            except Exception as e:
                logger.error(f"HTTP 服务器自检失败：{e}。端口 {port} 可能被旧实例或其它程序占用")

        threading.Thread(target=probe, daemon=True, name="http-self-test").start()

    def start(self):
        port = self.ctx.config.port
        if self._check_port_in_use(port):
            logger.warning(f"端口 {port} 当前已有监听者（可能是旧实例或其它程序），请确认")
        try:
            self.httpd = CustomTCPServer(("", port), self.handler_class, self.ctx)
            self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True, name="http-serve")
            self._thread.start()
            logger.info(f"HTTP 服务器启动，端口号 {port}")
            self._self_test(port)
        except OSError as e:
            logger.error(f"端口号 {port} 被占用：{e}")
            self.httpd = None
        except Exception as e:
            logger.error(f"HTTP 服务器启动失败：{e}")
            self.httpd = None

    def stop(self):
        if not self.httpd:
            return
        logger.info("正在关闭 HTTP 服务器")
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=3.0)
                if self._thread.is_alive():
                    logger.warning("HTTP 服务器线程未能在超时内退出")
        except Exception as e:
            logger.error(f"关闭服务器失败: {e}")
        self.httpd = None
        self._thread = None
