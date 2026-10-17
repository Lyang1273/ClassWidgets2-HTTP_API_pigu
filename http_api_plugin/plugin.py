import os
import sys
from types import ModuleType

from ClassWidgets.SDK import CW2Plugin, PluginAPI
from loguru import logger

from .config import load_config
from .context import ServerContext
from .handler import CustomHandler
from .response import success as response_success, error as response_error
from .server import ServerLifecycle
from .routes import registry as _registry
from . import __version__


class Plugin(CW2Plugin):
    pid = "http.lyang1273"
    name = "HTTP API Plugin"

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
        logger.info(f"工作目录：{os.getcwd()}")
        logger.info(f"{self.name}加载")

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

        virtual = ModuleType("http_api_mod")
        virtual.__version__ = __version__
        virtual.add_root = _registry.add_root
        virtual.get_handler = _registry.get_handler
        virtual.success = response_success
        virtual.error = response_error
        virtual.RegistryError = _registry.RegistryError
        virtual.ReservedPrefixError = _registry.ReservedPrefixError
        virtual.RootConflictError = _registry.RootConflictError
        virtual.RouteConflictError = _registry.RouteConflictError
        virtual.InvalidPathError = _registry.InvalidPathError
        sys.modules["http_api_mod"] = virtual
        
        logger.info("虚拟模块 http_api_mod 已注入")

    def on_unload(self):
        logger.info(f"{self.name} 卸载")

        sys.modules.pop("http_api_mod", None)
        _registry.clear_all()

        if self._server:
            self._server.stop()