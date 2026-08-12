from loguru import logger
from . import register


def handle_cw(ctx, query, body):
    logger.success("GET /cw 请求成功")
    config = open("/configs/configs.json", "r", encoding="utf-8")
    return 200, {'status': 'success', 'message': config}


register("/cw", "GET")(handle_cw)
