from loguru import logger
import ctypes
import webbrowser
from . import register
import platform


def handle_system_name(ctx, query, body):
    logger.success("GET /system/system_name 请求成功")
    return 200, {'status': 'success', 'message': platform.system()}


def handle_system_version(ctx, query, body):
    logger.success("GET /system/system_version 请求成功")
    return 200, {'status': 'success', 'message': platform.version()}


def handle_system_release(ctx, query, body):
    logger.success("GET /system/system_release 请求成功")
    return 200, {'status': 'success', 'message': platform.release()}


def handle_is_admin(ctx, query, body):
    if ctypes.windll.shell32.IsUserAnAdmin():
        logger.success("GET /system/is_admin 请求成功")
        return 200, {'status': 'success', 'message': 'True'}
    else:
        logger.success("GET /system/is_admin 请求成功")
        return 200, {'status': 'success', 'message': 'False'}


def handle_window_title(ctx, query, body):
    user32 = ctypes.windll.user32
    title = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetWindowTextW(user32.GetForegroundWindow(), title, 256)
    title = title.value

    logger.success("GET /system/window_title 请求成功")
    return 200, {'status': 'success', 'message': title}


def handle_lock_screen(ctx, query, body):
    if ctypes.windll.user32.LockWorkStation():
        logger.success("GET /system/lock_screen 请求成功")
        return 200, {'status': 'success', 'message': "True"}
    else:
        logger.success("GET /system/lock_screen 请求成功")
        return 200, {'status': 'success', 'message': "False"}


"""
def handle_screenshot(ctx, query, body):
    screenshot = pyautogui.screenshot()

    buffer = BytesIO()
    screenshot.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    base64_str = base64.b64encode(image_bytes).decode('utf-8')
    return 200, {'status': 'success', 'message': base64_str}
"""


def handle_open_website(ctx, query, body):
    link = query.get('link', '')
    if not link:
        return 400, {'status': 'error', 'message': '缺少 link 参数'}

    webbrowser.open(link)
    logger.success(f"GET /system/open_website 请求成功: {link}")
    return 200, {'status': 'success', 'message': 'True'}
    


register("/system/is_admin", "GET")(handle_is_admin)
register("/system/window_title", "GET")(handle_window_title)
register("/system/lock_screen", "GET")(handle_lock_screen)
register("/system/open_website", "GET")(handle_open_website)
# register("/system/screenshot", "GET")(handle_screenshot)
