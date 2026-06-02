import ctypes
import time

user32 = ctypes.windll.user32

def get_current_language():
    """
    Returns the primary language ID of the active window.
    English is usually 0x09 (9)
    Arabic is usually 0x01 (1)
    """
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
    layout_id = user32.GetKeyboardLayout(thread_id)
    language_id = layout_id & 0xFFFF
    primary_language_id = language_id & 0x03FF
    return primary_language_id

def switch_language():
    """
    Switches to the next keyboard layout.
    """
    hwnd = user32.GetForegroundWindow()
    # WM_INPUTLANGCHANGEREQUEST = 0x0050
    # INPUTLANGCHANGE_FORWARD = 0x0002
    user32.PostMessageW(hwnd, 0x0050, 2, 0)
    time.sleep(0.05) # Give Windows a tiny moment to switch

if __name__ == "__main__":
    lang = get_current_language()
    print(f"Current primary language ID: {lang}")
    if lang == 9:
        print("This is English.")
    elif lang == 1:
        print("This is Arabic.")
    else:
        print("Unknown language.")
