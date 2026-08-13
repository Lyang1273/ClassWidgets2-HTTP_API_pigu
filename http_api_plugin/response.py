def success(data=None, message="success"):
    return 200, {"code": 0, "message": message, "data": data}


def error(code=500, message="error", http_status=None):
    if http_status is None:
        http_status = code if 100 <= code <= 599 else 500
    return http_status, {"code": code, "message": message, "data": None}
