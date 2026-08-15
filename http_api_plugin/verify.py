import ctypes
import platform


def yn_ver(title="验证", message=""):
    if platform.system() != "Windows":
        return False
    flags = 4 | 0x40000 | 0x30 | 0x1000
    return ctypes.windll.user32.MessageBoxW(0, message, title, flags) == 6
