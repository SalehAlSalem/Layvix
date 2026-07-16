import sys
import os
import ctypes

_mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, True, "Global\\LayvixHookMutex_Current")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    ctypes.windll.user32.MessageBoxW(0, "Layvix is already running.", "Layvix", 0)
    sys.exit(0)

if getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

import threading
import webview
import socket
import secrets
import uvicorn
import pystray
from PIL import Image

from core.core_engine import CoreEngine
from utils import settings, logger

shutdown_event = threading.Event()

app_logger = logger.get_logger()

def find_free_port():
    """Finds an OS-assigned free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def start_fastapi(port):
    """Starts the Uvicorn server programmatically in a background thread."""
    import api
    # Crucial Security: Strict bind to 127.0.0.1
    uvicorn.run(api.app, host="127.0.0.1", port=port, log_level="error")

class LayvixApp:
    def __init__(self):
        self.core = CoreEngine()
        self.window = None
        self.tray_icon = None
        self._webview_started = False
        self._open_settings_lock = threading.Lock()
        
        # Authentication & Port
        self.port = find_free_port()
        self.token = secrets.token_hex(16)
        
        # Store for API access
        os.environ["LAYVIX_SECURITY_TOKEN"] = self.token
        os.environ["LAYVIX_PORT"] = str(self.port)

    def _create_tray_image(self):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'data', 'tray_icon_16.png')
        if os.path.exists(icon_path):
            return Image.open(icon_path)
        return Image.new('RGB', (64, 64), color=(59, 130, 246))

    def _build_window(self, hidden=False):
        if self.window is not None:
            return self.window

        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base_dir, "frontend", "dist", "index.html")
        dist_dir = os.path.join(base_dir, "frontend", "dist")

        # The frontend is now served directly by our FastAPI backend (api.py).
        # This completely eliminates CORS issues and pywebview http_server bugs.
        url = f"http://127.0.0.1:{self.port}/?port={self.port}&token={self.token}"

        self.window = webview.create_window(
            'Layvix Pro Control Center',
            url=url,
            width=1100,
            height=750,
            frameless=True,
            easy_drag=True,
            background_color='#0a0a0a',
            hidden=hidden
        )

        def on_closing():
            if self.window:
                self.window.hide()
            return False # Cancel the close event

        self.window.events.closing += on_closing

        # Inject window reference into API for maximize/minimize REST calls
        import api
        api.app_window = self.window

        return self.window

    def _open_settings(self, icon=None, item=None):
        if self.window is not None:
            try:
                self.window.show()
                self.window.restore()
            except Exception as e:
                app_logger.error(f"Failed to show window: {e}")

    def _quit_app(self, icon=None, item=None):
        self._graceful_shutdown()

    def _graceful_shutdown(self):
        shutdown_event.set()
        
        if hasattr(self, '_watchdog') and self._watchdog:
            try:
                self._watchdog.stop()
            except Exception:
                pass
                
        self.core.stop()
        
        try:
            from ai import learner
            if hasattr(learner, '_save_model_with_manifest'):
                learner._save_model_with_manifest()
        except Exception as e:
            app_logger.error(f"Error saving model on shutdown: {e}")
            
        settings.force_save_settings()
        
        try:
            from utils.event_bus import event_bus
            if hasattr(event_bus, 'close'):
                event_bus.close()
        except Exception:
            pass
            
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
                
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        os._exit(0)

    def _register_power_hook(self):
        """
        Registers a hidden Win32 message window to listen for WM_POWERBROADCAST.
        Pauses the hook on system sleep, re-registers on wake with backoff.
        """
        import ctypes
        from ctypes import wintypes

        WM_POWERBROADCAST = 0x0218
        PBT_APMSUSPEND = 0x0004
        PBT_APMRESUMEAUTOMATIC = 0x0012
        HWND_MESSAGE = -3

        WndProcType = ctypes.WINFUNCTYPE(
            wintypes.LPARAM, wintypes.HWND, wintypes.UINT,
            wintypes.WPARAM, wintypes.LPARAM
        )

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style",         wintypes.UINT),
                ("lpfnWndProc",   WndProcType),
                ("cbClsExtra",    ctypes.c_int),
                ("cbWndExtra",    ctypes.c_int),
                ("hInstance",     wintypes.HINSTANCE),
                ("hIcon",         wintypes.HANDLE),
                ("hCursor",       wintypes.HANDLE),
                ("hbrBackground", wintypes.HANDLE),
                ("lpszMenuName",  wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_POWERBROADCAST:
                if wparam == PBT_APMSUSPEND:
                    app_logger.info("[POWER] System sleep detected — pausing hook.")
                    self.core.keyboard.stop()
                elif wparam == PBT_APMRESUMEAUTOMATIC:
                    app_logger.info("[POWER] System wake detected — resuming hook.")
                    backoff = 0.05
                    for attempt in range(3):
                        try:
                            import time
                            time.sleep(backoff)
                            self.core.keyboard.start()
                            break
                        except Exception as e:
                            app_logger.warning(f"[POWER] Wake re-hook attempt {attempt+1} failed: {e}")
                            backoff *= 2
            return ctypes.windll.user32.DefWindowProcW(
                wintypes.HWND(hwnd), 
                wintypes.UINT(msg), 
                wintypes.WPARAM(wparam), 
                wintypes.LPARAM(lparam)
            )

        # Keep a reference so it's not garbage collected
        self._power_proc = WndProcType(wnd_proc)
        
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._power_proc
        wc.lpszClassName = "LayvixPowerHookClass"
        wc.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
        
        ctypes.windll.user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        ctypes.windll.user32.DefWindowProcW.restype = wintypes.LPARAM
        
        ctypes.windll.user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        ctypes.windll.user32.RegisterClassW.restype = wintypes.ATOM
        
        ctypes.windll.user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
        ]
        ctypes.windll.user32.CreateWindowExW.restype = wintypes.HWND
        
        ctypes.windll.user32.RegisterClassW(ctypes.byref(wc))
        
        hwnd = ctypes.windll.user32.CreateWindowExW(
            0,
            wc.lpszClassName,
            "LayvixPowerHook",
            0, 0, 0, 0, 0,
            0, 0, wc.hInstance, None
        )
        
        if not hwnd:
            app_logger.error("[POWER] Failed to create power hook window.")
            return

        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

    def _prepare_icons(self):
        # Icons are now pre-generated by convert_icon.py and stored in data/
        pass

    def _get_icon_path(self, state, size):
        # We rely on the pre-generated 64px tray icons in data/
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "data", f"tray_icon_64_{state}.png")

    def _update_tray_icon(self, state):
        if not hasattr(self, 'tray_icon') or not self.tray_icon: 
            return
        try:
            png_path = self._get_icon_path(state, 64)
            if os.path.exists(png_path):
                img = Image.open(png_path)
                self.tray_icon.icon = img
                self.tray_icon.title = f"Layvix — {state.capitalize()}"
        except Exception as e:
            app_logger.error(f"Failed to update tray icon: {e}")

    def _toggle_active_app(self, icon, item):
        import ctypes
        from core.security_guard import get_process_name_from_hwnd
        from utils import settings
        
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return
            
        process_name = get_process_name_from_hwnd(hwnd)
        if not process_name:
            return
            
        excluded = settings.get_setting("excluded_apps", [])
        whitelisted = settings.get_setting("whitelisted_apps", [])
        
        # If it's excluded, remove from excluded and add to whitelisted (Force Enable)
        if process_name in excluded:
            excluded.remove(process_name)
            if process_name not in whitelisted:
                whitelisted.append(process_name)
            settings.set_setting("excluded_apps", excluded)
            settings.set_setting("whitelisted_apps", whitelisted)
            app_logger.info(f"Tray: Force Enabled (Whitelisted) {process_name}")
            return
            
        # If it's whitelisted, remove from whitelisted (Neutral)
        if process_name in whitelisted:
            whitelisted.remove(process_name)
            settings.set_setting("whitelisted_apps", whitelisted)
            app_logger.info(f"Tray: Removed {process_name} from whitelist")
            return
            
        # Otherwise, add to excluded (Force Disable)
        if process_name not in excluded:
            excluded.append(process_name)
            settings.set_setting("excluded_apps", excluded)
            app_logger.info(f"Tray: Force Disabled (Excluded) {process_name}")

    def _run_tray(self):
        self._prepare_icons()
        initial_state = 'active' if self.core.app_enabled else 'paused'
        png_path = self._get_icon_path(initial_state, 64)
        
        if os.path.exists(png_path):
            image = Image.open(png_path)
        else:
            image = self._create_tray_image()
            
        menu = pystray.Menu(
            pystray.MenuItem('Open Control Center', self._open_settings, default=True),
            pystray.MenuItem('Quit', self._quit_app)
        )
        self.tray_icon = pystray.Icon("Layvix", image, f"Layvix — {initial_state.capitalize()}", menu)
        
        # Hook up state changes
        self.core.on_status_change = self._update_tray_icon
        
        self.tray_icon.run()

    def run(self):
        # Boot Order Maintained:
        # 1. Load AI First
        from ai import ai_engine
        ai_engine.load_model()

        # 2. Start Core Engine
        self.core.start()
        
        try:
            from core.watchdog import WatchdogThread
            self._watchdog = WatchdogThread(self.core.keyboard)
            self._watchdog.start()
        except ImportError:
            pass  # Will be implemented in T005

        import api
        api.core_engine_instance = self.core
        api.trigger_shutdown_callback = self._graceful_shutdown

        # 3. Start FastAPI Thread
        api_thread = threading.Thread(target=start_fastapi, args=(self.port,), daemon=True, name="FastAPIThread")
        api_thread.start()

        # 4. Start Tray Icon & PyWebView
        threading.Thread(target=self._run_tray, daemon=True).start()

        # 5. Start Power Hook Thread
        threading.Thread(target=self._register_power_hook, daemon=True, name="PowerHookThread").start()
        
        try:
            import signal
            signal.signal(signal.SIGTERM, lambda *_: self._graceful_shutdown())
            signal.signal(signal.SIGINT, lambda *_: self._graceful_shutdown())
        except AttributeError:
            pass # Windows might not support all signals

        if "--startup" not in sys.argv and not settings.get_setting("start_minimized", False):
            self._build_window(hidden=False)
        else:
            self._build_window(hidden=True)

        try:
            webview.start(debug=False)
        except Exception as e:
            app_logger.error(f"Failed to start webview: {e}")

        # Webview loop exited, shutdown
        self._graceful_shutdown()
        return 0

if __name__ == '__main__':
    app = LayvixApp()
    sys.exit(app.run())

