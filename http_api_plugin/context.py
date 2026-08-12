class ServerContext:
    """服务器运行期共享上下文，注入给路由处理函数。"""

    def __init__(self, plugin, api, notification_provider, config):
        self.plugin = plugin
        self.api = api
        self.notification_provider = notification_provider
        self.config = config
