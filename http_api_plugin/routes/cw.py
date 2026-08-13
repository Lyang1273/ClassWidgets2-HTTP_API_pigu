from loguru import logger
from ..response import success
from . import register
import json


def handle_cw_ver(ctx, query, body):
    with open("./configs/configs.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return success(config["app"]["version"])


register("/cw/cw_ver", "GET")(handle_cw_ver)
