import ctypes
import ctypes.wintypes
import threading
from logger import get_logger

logger = get_logger()

# Windows constants
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002

user32 = ctypes.windll.user32

# Callback type
WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,   # hWinEventHook
    ctypes.wintypes.DWORD,    # event
    ctypes.wintypes.HWND,     # hwnd
    ctypes.wintypes.LONG,     # idObject
    ctypes.wintypes.LONG,     # idChild
    ctypes.wintypes.DWORD,    # dwEventThread
    ctypes.wintypes.DWORD,    # dwmsEventTime
)

_is_fullscreen = False
_on_fullscreen_change = None  # callback: fn(is_fullscreen: bool)
_hook_handle = None


def _is_window_fullscreen(hwnd):
    """Check if a window covers the entire screen (fullscreen)."""
    try:
        if not hwnd or not user32.IsWindow(hwnd):
            return False
        
        # Get window rect
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        # Get monitor info for the monitor this window is on
        monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        
        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.wintypes.DWORD),
                ("rcMonitor", ctypes.wintypes.RECT),
                ("rcWork", ctypes.wintypes.RECT),
                ("dwFlags", ctypes.wintypes.DWORD),
            ]
        
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
        
        # Check if window covers the entire monitor
        screen = mi.rcMonitor
        return (
            rect.left <= screen.left and
            rect.top <= screen.top and
            rect.right >= screen.right and
            rect.bottom >= screen.bottom
        )
    except Exception as e:
        logger.error(f"Error checking fullscreen: {e}")
        return False


def _win_event_callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    """Called by Windows when the foreground window changes."""
    global _is_fullscreen
    try:
        new_state = _is_window_fullscreen(hwnd)
        if new_state != _is_fullscreen:
            _is_fullscreen = new_state
            logger.info(f"Fullscreen state changed: {_is_fullscreen}")
            if _on_fullscreen_change:
                _on_fullscreen_change(_is_fullscreen)
    except Exception as e:
        logger.error(f"Error in win_event_callback: {e}")


# Must keep a reference to prevent garbage collection
_callback_ref = WinEventProcType(_win_event_callback)


def is_fullscreen():
    """Returns True if the current foreground window is fullscreen."""
    return _is_fullscreen


def start(on_change_callback=None):
    """Start monitoring foreground window changes via SetWinEventHook.
    
    Args:
        on_change_callback: Optional function(is_fullscreen: bool) called on state change.
    """
    global _on_fullscreen_change, _hook_handle
    _on_fullscreen_change = on_change_callback
    
    def _run_hook():
        global _hook_handle
        _hook_handle = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            0,
            _callback_ref,
            0, 0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
        )
        if not _hook_handle:
            logger.error("Failed to set WinEventHook for game detection")
            return
        
        logger.info("Game detector started (SetWinEventHook)")
        
        # Message loop required for the hook to work
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    
    t = threading.Thread(target=_run_hook, daemon=True, name="GameDetector")
    t.start()


def stop():
    """Stop the event hook."""
    global _hook_handle
    if _hook_handle:
        user32.UnhookWinEvent(_hook_handle)
        _hook_handle = None
        logger.info("Game detector stopped")
