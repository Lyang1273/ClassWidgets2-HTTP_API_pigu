from loguru import logger
from ..response import success
from . import register
import json
import os


def handle_cw_ver(ctx, query, body):
    with open("./configs/configs.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return success(config["app"]["version"])

def handle_cw_exit(ctx, query, body):
    logger.warning("通过HTTP API插件退出cw")
    os._exit(0)


register("/cw/cw_ver", "GET")(handle_cw_ver)
register("/cw/exit", "GET")(handle_cw_exit)
