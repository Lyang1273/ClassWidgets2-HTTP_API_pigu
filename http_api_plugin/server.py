import socketserver
import threading

from loguru import logger


class CustomTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, ctx):
        self.ctx = ctx
        super().__init__(server_address, RequestHandlerClass)


class ServerLifecycle:
    """HTTP 服务器启动、线程管理与关闭"""

    def __init__(self, ctx, handler_class):
        self.ctx = ctx
        self.handler_class = handler_class
        self.httpd = None
        self._thread = None

    def start(self):
        port = self.ctx.config.port
        try:
            self.httpd = CustomTCPServer(("", port), self.handler_class, self.ctx)
            logger.info(f"HTTP 服务器启动，端口号 {port}")
            self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self._thread.start()
        except OSError as e:
            logger.error(f"端口号 {port} 被占用：{e}")
        except Exception as e:
            logger.error(f"HTTP 服务器启动失败：{e}")

    def stop(self):
        if not self.httpd:
            return
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
