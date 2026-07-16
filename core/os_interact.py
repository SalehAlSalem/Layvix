import ctypes
from ctypes import wintypes
import time
from utils.logger import get_logger

logger = get_logger()

# ── Cursor Management ──
SPI_SETCURSORS = 0x0057
IDC_CROSS = 32515
IDC_ARROW = 32512

def set_global_cursor_crosshair():
    try:
        hCross = ctypes.windll.user32.LoadCursorW(None, IDC_CROSS)
        hCopy = ctypes.windll.user32.CopyIcon(hCross)
        ctypes.windll.user32.SetSystemCursor(hCopy, IDC_ARROW)
    except Exception as e:
        logger.error(f"Failed to set crosshair cursor: {e}")

def restore_global_cursor():
    try:
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)
    except Exception as e:
        logger.error(f"Failed to restore cursor: {e}")

# Win32 INPUT Structures
user32 = ctypes.windll.user32

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t))

class INPUT_I(ctypes.Union):
    _fields_ = (("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT),
                ("hi", HARDWAREINPUT))

class INPUT(ctypes.Structure):
    _fields_ = (("type", wintypes.DWORD),
                ("ii", INPUT_I))

INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

# Magic info to tag our own synthetic inputs
LAYVIX_MAGIC_INFO = 0xABCD

def send_unicode_string(text):
    """
    Sends a string character by character via SendInput, with a micro-delay.
    This prevents input buffer overflow in legacy Win32 apps (e.g. Notepad).
    Constructs 2 INPUT events per character (KeyDown + KeyUp).
    """
    if not text:
        return

    # Tag these events so keyboard_hook.py can ignore them
    extra = ctypes.c_ulong(LAYVIX_MAGIC_INFO)
    p_extra = ctypes.pointer(extra)

    for char in text:
        inputs = (INPUT * 2)()
        
        # Key Down
        inputs[0].type = INPUT_KEYBOARD
        inputs[0].ii.ki.wVk = 0
        inputs[0].ii.ki.wScan = ord(char)
        inputs[0].ii.ki.dwFlags = KEYEVENTF_UNICODE
        inputs[0].ii.ki.time = 0
        inputs[0].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
        
        # Key Up
        inputs[1].type = INPUT_KEYBOARD
        inputs[1].ii.ki.wVk = 0
        inputs[1].ii.ki.wScan = ord(char)
        inputs[1].ii.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        inputs[1].ii.ki.time = 0
        inputs[1].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

        # Dispatch single character
        user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        
        # 5ms delay to pace injection
        time.sleep(0.005)


def send_backspaces(count: int):
    """
    Sends `count` Backspace key events one by one via SendInput, with a micro-delay.
    Used by the echo-then-correct pattern to erase the echoed word
    before injecting the corrected version.
    Tagged with LAYVIX_MAGIC_INFO so the hook ignores them.
    """
    if count <= 0:
        return

    VK_BACK = 0x08
    extra   = ctypes.c_ulong(LAYVIX_MAGIC_INFO)
    p_extra = ctypes.pointer(extra)

    for i in range(count):
        inputs  = (INPUT * 2)()
        # Key Down
        inputs[0].type         = INPUT_KEYBOARD
        inputs[0].ii.ki.wVk   = VK_BACK
        inputs[0].ii.ki.wScan  = 0
        inputs[0].ii.ki.dwFlags = 0
        inputs[0].ii.ki.time   = 0
        inputs[0].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
        # Key Up
        inputs[1].type         = INPUT_KEYBOARD
        inputs[1].ii.ki.wVk   = VK_BACK
        inputs[1].ii.ki.wScan  = 0
        inputs[1].ii.ki.dwFlags = KEYEVENTF_KEYUP
        inputs[1].ii.ki.time   = 0
        inputs[1].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

        user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        time.sleep(0.015)

def wait_for_modifiers():
    """
    Waits until all modifier keys (Ctrl, Alt, Shift, Win) are released.
    This prevents 'modifier bleed' where synthetic keystrokes (like Backspace)
    get accidentally combined with a physically held modifier (e.g. Ctrl+Backspace
    which deletes whole words instead of single characters).
    """
    modifiers = [0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]
    timeout = 1.0 # Max wait 1 second
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        all_released = True
        for vk in modifiers:
            # GetAsyncKeyState returns short. Most significant bit is set if key is down.
            if user32.GetAsyncKeyState(vk) & 0x8000:
                all_released = False
                break
        
        if all_released:
            return
        time.sleep(0.01) # Check every 10ms

def send_virtual_key(vk_code):
    """
    Sends a single virtual key (like Space or Enter) atomically.
    Tagged with LAYVIX_MAGIC_INFO so the hook ignores it.
    """
    extra   = ctypes.c_ulong(LAYVIX_MAGIC_INFO)
    p_extra = ctypes.pointer(extra)
    inputs  = (INPUT * 2)()

    # Key Down
    inputs[0].type         = INPUT_KEYBOARD
    inputs[0].ii.ki.wVk    = vk_code
    inputs[0].ii.ki.wScan  = 0
    inputs[0].ii.ki.dwFlags = 0
    inputs[0].ii.ki.time   = 0
    inputs[0].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
    
    # Key Up
    inputs[1].type         = INPUT_KEYBOARD
    inputs[1].ii.ki.wVk    = vk_code
    inputs[1].ii.ki.wScan  = 0
    inputs[1].ii.ki.dwFlags = KEYEVENTF_KEYUP
    inputs[1].ii.ki.time   = 0
    inputs[1].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    del inputs

def get_clipboard_text():
    try:
        if not user32.OpenClipboard(0):
            return ""
        kernel32 = ctypes.windll.kernel32
        
        # Explicitly define types to prevent OverflowError on 64-bit systems
        user32.GetClipboardData.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        
        handle = user32.GetClipboardData(13) # CF_UNICODETEXT
        if not handle:
            user32.CloseClipboard()
            return ""
            
        pcontents = kernel32.GlobalLock(handle)
        text = ctypes.c_wchar_p(pcontents).value if pcontents else ""
        kernel32.GlobalUnlock(handle)
        user32.CloseClipboard()
        return text or ""
    except Exception as e:
        logger.error(f"Clipboard read failed: {e}")
        return ""

def clear_clipboard():
    try:
        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.CloseClipboard()
    except Exception as e:
        logger.error(f"Failed to clear clipboard: {e}")

def set_clipboard_text(text):
    try:
        if not user32.OpenClipboard(0):
            return
        user32.EmptyClipboard()
        kernel32 = ctypes.windll.kernel32
        
        # GMEM_MOVEABLE = 0x0002
        byte_len = (len(text) + 1) * 2
        handle = kernel32.GlobalAlloc(0x0002, byte_len)
        if handle:
            pcontents = kernel32.GlobalLock(handle)
            ctypes.memmove(pcontents, text.encode('utf-16le'), byte_len)
            kernel32.GlobalUnlock(handle)
            user32.SetClipboardData(13, handle) # CF_UNICODETEXT = 13
        user32.CloseClipboard()
    except Exception as e:
        logger.error(f"Failed to set clipboard: {e}")

def get_selected_text():
    """
    Sends Ctrl+C atomically, waits briefly, and returns the clipboard contents.
    Returns the original clipboard contents back after reading if possible.
    """
    VK_CONTROL = 0x11
    VK_C = 0x43
    extra = ctypes.c_ulong(LAYVIX_MAGIC_INFO)
    p_extra = ctypes.pointer(extra)
    inputs = (INPUT * 4)()

    # Save old clipboard
    old_clip = get_clipboard_text()
    clear_clipboard()

    # Ctrl Down
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].ii.ki.wVk = VK_CONTROL
    inputs[0].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
    
    # C Down
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].ii.ki.wVk = VK_C
    inputs[1].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
    
    # C Up
    inputs[2].type = INPUT_KEYBOARD
    inputs[2].ii.ki.wVk = VK_C
    inputs[2].ii.ki.dwFlags = KEYEVENTF_KEYUP
    inputs[2].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
    
    # Ctrl Up
    inputs[3].type = INPUT_KEYBOARD
    inputs[3].ii.ki.wVk = VK_CONTROL
    inputs[3].ii.ki.dwFlags = KEYEVENTF_KEYUP
    inputs[3].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    # Send Ctrl+C
    user32.SendInput(4, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    del inputs

    # Give OS time to process copy command and update clipboard
    time.sleep(0.1)
    
    selected_text = get_clipboard_text()
    
    # Restore old clipboard
    if old_clip:
        set_clipboard_text(old_clip)
    else:
        clear_clipboard()
        
    return selected_text

def select_previous_word():
    """
    Sends Ctrl+Shift+Left to select the previous word.
    """
    VK_CONTROL = 0x11
    VK_SHIFT = 0x10
    VK_LEFT = 0x25
    extra = ctypes.c_ulong(LAYVIX_MAGIC_INFO)
    p_extra = ctypes.pointer(extra)
    inputs = (INPUT * 6)()

    # Ctrl Down
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].ii.ki.wVk = VK_CONTROL
    inputs[0].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO
    
    # Shift Down
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].ii.ki.wVk = VK_SHIFT
    inputs[1].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    # Left Down
    inputs[2].type = INPUT_KEYBOARD
    inputs[2].ii.ki.wVk = VK_LEFT
    inputs[2].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    # Left Up
    inputs[3].type = INPUT_KEYBOARD
    inputs[3].ii.ki.wVk = VK_LEFT
    inputs[3].ii.ki.dwFlags = KEYEVENTF_KEYUP
    inputs[3].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    # Shift Up
    inputs[4].type = INPUT_KEYBOARD
    inputs[4].ii.ki.wVk = VK_SHIFT
    inputs[4].ii.ki.dwFlags = KEYEVENTF_KEYUP
    inputs[4].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    # Ctrl Up
    inputs[5].type = INPUT_KEYBOARD
    inputs[5].ii.ki.wVk = VK_CONTROL
    inputs[5].ii.ki.dwFlags = KEYEVENTF_KEYUP
    inputs[5].ii.ki.dwExtraInfo = LAYVIX_MAGIC_INFO

    user32.SendInput(6, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    del inputs
    time.sleep(0.02) # Give UI time to update selection

def switch_keyboard_layout(lang_code):
    """
    Switches the Windows keyboard layout for the current foreground window
    without installing new ghost keyboards into the taskbar.
    lang_code: 'ar' or 'en'
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return
        
    WM_INPUTLANGCHANGEREQUEST = 0x0050
    
    # Primary Language IDs
    LANG_ARABIC = 0x01
    LANG_ENGLISH = 0x09
    
    target_primary_lang = LANG_ARABIC if lang_code == 'ar' else LANG_ENGLISH
    
    # Get number of loaded layouts
    count = user32.GetKeyboardLayoutList(0, None)
    if count == 0:
        return
        
    # Get the actual loaded HKLs
    hkl_list = (wintypes.HKL * count)()
    user32.GetKeyboardLayoutList(count, hkl_list)
    
    target_hkl = None
    for hkl in hkl_list:
        hkl_val = ctypes.cast(hkl, ctypes.c_void_p).value
        if not hkl_val:
            continue
        lang_id = hkl_val & 0xFFFF
        primary_lang_id = lang_id & 0x03FF
        
        if primary_lang_id == target_primary_lang:
            target_hkl = hkl
            break
            
    if target_hkl:
        user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, target_hkl)
        logger.info(f"Switched keyboard layout to {lang_code.upper()} using existing HKL")
    else:
        # Fallback ONLY if the user doesn't have the language installed
        if lang_code == 'ar':
            fallback_hkl = user32.LoadKeyboardLayoutW("00000401", 1)
        else:
            fallback_hkl = user32.LoadKeyboardLayoutW("00000409", 1)
        user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, fallback_hkl)
        logger.warning(f"Forced load keyboard layout {lang_code.upper()}")
