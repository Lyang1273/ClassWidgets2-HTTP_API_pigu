# 路由注册表

ROUTES = {}


def register(path, method):
    def decorator(func):
        ROUTES[(path, method)] = func
        return func

    return decorator


def resolve(path, method):
    return ROUTES.get((path, method))


from . import notification, runtime, schedule, system, cw, app, theme, debug
