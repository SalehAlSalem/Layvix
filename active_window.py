import ctypes
from ctypes import wintypes
import os

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

def get_active_window_exe():
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd: return ""
        
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h_process: return ""
        
        exe_path = ctypes.create_unicode_buffer(260)
        size = wintypes.DWORD(260)
        
        success = kernel32.QueryFullProcessImageNameW(h_process, 0, exe_path, ctypes.byref(size))
        kernel32.CloseHandle(h_process)
        
        if success:
            return os.path.basename(exe_path.value).lower()
    except Exception:
        pass
    return ""
