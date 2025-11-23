# ui/messages.py
import ctypes

# native message boxes
MB_OK = 0
MB_ICONINFO = 0x40
MB_ICONERROR = 0x10
MB_YESNO = 0x04
IDYES = 6

def msg_info(title, text):
    ctypes.windll.user32.MessageBoxW(None, str(text), str(title), MB_OK | MB_ICONINFO)

def msg_error(title, text):
    ctypes.windll.user32.MessageBoxW(None, str(text), str(title), MB_OK | MB_ICONERROR)

def ask_yes_no(title, text) -> bool:
    return ctypes.windll.user32.MessageBoxW(None, str(text), str(title), MB_YESNO | MB_ICONINFO) == IDYES
