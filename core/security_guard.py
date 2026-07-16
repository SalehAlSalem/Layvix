import ctypes
from ctypes import wintypes
import uiautomation as auto
from utils.logger import get_logger

logger = get_logger()
user32 = ctypes.windll.user32

GWL_STYLE = -16
ES_PASSWORD = 0x0020

def get_process_name_from_hwnd(hwnd):
    try:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        
        hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if hProcess:
            buffer = ctypes.create_unicode_buffer(260)
            if psapi.GetModuleBaseNameW(hProcess, 0, buffer, 260) > 0:
                kernel32.CloseHandle(hProcess)
                return buffer.value.lower()
            kernel32.CloseHandle(hProcess)
        return None
    except Exception as e:
        logger.error(f"Failed to get process name: {e}")
        return None

def is_secure_context():
    """
    Checks if the currently focused element is a password field or in an excluded app.
    Returns True if it is secure (should bypass engine), False otherwise.
    """
    try:
        from utils import settings
        excluded_apps = settings.get_setting("excluded_apps", [])
        
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
            
        # 0. Check Excluded Apps First
        process_name = get_process_name_from_hwnd(hwnd)
        if process_name:
            excluded_lower = [app.lower() for app in excluded_apps]
            if process_name in excluded_lower:
                logger.info(f"[SECURITY] Excluded app detected: {process_name}. Bypassing engine.")
                return True
                
            whitelisted_apps = settings.get_setting("whitelisted_apps", [])
            whitelisted_lower = [app.lower() for app in whitelisted_apps]
            if process_name in whitelisted_lower:
                return False
            
        # 1. Native Win32 Check (Standard Password Fields)
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        if style & ES_PASSWORD:
            return True
            
        # 2. Modern Check (Browsers, Electron, UWP)
        # Using UIAutomation to inspect the focused control
        focused_element = auto.GetFocusedControl()
        if focused_element:
            # ValuePattern.IsPassword is typically True for <input type="password">
            if getattr(focused_element, 'IsPassword', False):
                return True
                
        return False
    except Exception as e:
        # Intermittent COM errors are common when querying UIAutomation.
        # Don't fail open (return True) on these exceptions, otherwise the 
        # engine randomly bypasses typing in normal windows.
        # logger.debug(f"UIAutomation check failed: {e}")
        return False
