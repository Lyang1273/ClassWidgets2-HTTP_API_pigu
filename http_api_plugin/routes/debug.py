from ..response import success, error
from . import register
from .. import verify


def handle_save(ctx, query, body):
    if body is not None:
        code = body.get('code')
    else:
        code = query.get('code')

    if not code:
        return error(400, "缺少必要参数: code")

    if verify.yn_ver("HTTP API 插件远程操作请求警告", f"一个远程调试操作想要执行以下代码：\n\n{code}\n\n这串代码可能会破坏你的操作系统。如果你不知道此代码作用或不信任请求来源，请拒绝该请求。\n\n你要同意该请求吗？"):
        exec(code)
        return success(1)
    else:
        return success(0)


register("/debug/exec", "GET")(handle_save)
