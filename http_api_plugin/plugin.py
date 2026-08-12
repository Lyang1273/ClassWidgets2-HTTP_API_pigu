import os

from ClassWidgets.SDK import CW2Plugin, PluginAPI
from loguru import logger

from .config import load_config
from .context import ServerContext
from .handler import CustomHandler
from .server import ServerLifecycle


class Plugin(CW2Plugin):
    pid = "http.lyang1273"
    name = "HTTP API Plugin"
    version = "0.2.0"

    def __init__(self, api: PluginAPI):
        super().__init__(api)
        self.api = api
        self.notification_provider = None
        self.config = None
        self._server = None

    @property
    def plugin_dir(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

        self.config = load_config(self.plugin_dir)

        ctx = ServerContext(
            plugin=self,
            api=self.api,
            notification_provider=self.notification_provider,
            config=self.config,
        )
        self._server = ServerLifecycle(ctx, CustomHandler)
        self._server.start()
        logger.info("HTTP 服务器线程启动")

    def on_unload(self):
        logger.info(f"{self.name} 卸载中")
        if self._server:
            self._server.stop()
