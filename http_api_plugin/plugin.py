import os
import sys
import webbrowser
from types import ModuleType

from ClassWidgets.SDK import CW2Plugin, PluginAPI
from loguru import logger
from PySide6.QtCore import Signal, Slot

from .config import DEFAULT_PORT, load_config, save_config
from .context import ServerContext
from .handler import CustomHandler
from .response import success as response_success, error as response_error
from .server import ServerLifecycle
from .routes import registry as _registry
from . import __version__


class Plugin(CW2Plugin):
    pid = "http.lyang1273"
    name = "HTTP API Plugin"

    serverStateChanged = Signal()

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

        self._register_settings_page()

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

    def _register_settings_page(self):
        try:
            self.api.ui.register_settings_page(
                qml_path="assets/settings.qml",
                title="HTTP API",
                icon="ic_fluent_server_20_regular",
            )
            logger.info("设置页面注册成功")
        except Exception as e:
            logger.error(f"注册设置页面失败: {e}")

    @Slot(result=int)
    def getPort(self):
        return self.config.port if self.config else DEFAULT_PORT

    @Slot(result=bool)
    def isServerRunning(self):
        return bool(self._server and self._server.httpd)

    @Slot(result=str)
    def getBaseUrl(self):
        return f"http://127.0.0.1:{self.getPort()}/"

    @Slot()
    def openInBrowser(self):
        webbrowser.open(self.getBaseUrl())

    @Slot(int, result=str)
    def applyPort(self, port):
        try:
            port = int(port)
        except (TypeError, ValueError):
            return "端口必须是整数"
        if not 1 <= port <= 65535:
            return "端口范围应为 1 - 65535"
        if self.config is None:
            return "配置尚未加载"

        if port == self.config.port and self.isServerRunning():
            return ""

        self.config.port = port
        try:
            save_config(self.config, os.path.join(self.plugin_dir, "config.json"))
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return f"保存配置失败: {e}"

        if self._server is not None:
            try:
                self._server.stop()
                self._server.start()
            except Exception as e:
                logger.error(f"重启服务器失败: {e}")
                return f"重启服务器失败: {e}"
            if not self._server.httpd:
                return f"端口 {port} 启动失败（可能被占用）"

        self.serverStateChanged.emit()
        logger.info(f"端口已切换为 {port}")
        return ""

    def on_unload(self):
        logger.info(f"{self.name} 卸载")

        sys.modules.pop("http_api_mod", None)
        _registry.clear_all()

        if self._server:
            self._server.stop()