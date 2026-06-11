import ctypes
import time

user32 = ctypes.windll.user32


def _get_primary_language_id(hkl):
    layout_id = int(ctypes.cast(hkl, ctypes.c_void_p).value or 0) & 0xFFFF
    return layout_id & 0x03FF

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


def switch_to_language(target_primary_lang_id):
    """Switch directly to a keyboard layout with the requested primary language id."""
    try:
        count = user32.GetKeyboardLayoutList(0, None)
        if count <= 0:
            return False

        layouts = (ctypes.c_void_p * count)()
        actual = user32.GetKeyboardLayoutList(count, layouts)
        if actual <= 0:
            return False

        target_hkl = None
        for hkl in layouts[:actual]:
            if _get_primary_language_id(hkl) == target_primary_lang_id:
                target_hkl = hkl
                break

        if target_hkl is None:
            return False

        hwnd = user32.GetForegroundWindow()
        user32.PostMessageW(hwnd, 0x0050, 0, target_hkl)
        user32.ActivateKeyboardLayout(target_hkl, 0)
        time.sleep(0.05)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    lang = get_current_language()
    print(f"Current primary language ID: {lang}")
    if lang == 9:
        print("This is English.")
    elif lang == 1:
        print("This is Arabic.")
    else:
        print("Unknown language.")
