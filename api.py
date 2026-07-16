"""FastAPI Server for Layvix Pro Backend."""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
import asyncio
import os
import json
import re

from utils import settings, user_dictionary
from utils.logger import get_activity_log, get_logger
from utils.event_bus import event_bus

logger = get_logger()

# ---- Frontend Integration Instructions ----
# To connect to this API from React:
# 1. Read `port` and `token` from the URL query params (e.g. ?port=5000&token=abc)
# 2. Open an EventSource connection to `http://127.0.0.1:{port}/api/stream?token={token}`
# 3. Listen for messages and update React state accordingly.
# 4. For REST API calls, append `?token={token}` to the URL.
# --------------------------------------------

# Validation Helpers
_HOTKEY_RE = re.compile(r'^(ctrl|alt|shift|windows|win)(\+(ctrl|alt|shift|windows|win|\w))*([+]ctrl)?$', re.IGNORECASE)
_APP_NAME_RE = re.compile(r'^[A-Za-z0-9_\-]+\.exe$')

def _validate_hotkey(value):
    if not isinstance(value, str) or not value:
        return False
    if not _HOTKEY_RE.match(value):
        return False
    parts = value.lower().split('+')
    if not any(p in ('ctrl', 'alt', 'shift', 'windows', 'win') for p in parts):
        return False
    return True

def _validate_app_name(value):
    if not isinstance(value, str) or not value:
        return False
    return bool(_APP_NAME_RE.match(value))

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Injected by main.py
core_engine_instance = None
app_window = None

def verify_token(token: str):
    """Auth Middleware: Rejects unauthorized requests with 401."""
    secure_token = os.environ.get("LAYVIX_SECURITY_TOKEN")
    if not secure_token or token != secure_token:
        raise HTTPException(status_code=401, detail="Invalid Security Token")
    return token

@app.on_event("startup")
async def startup_event():
    """CRITICAL INITIALIZATION: Connect Event Bus to FastAPI Event Loop."""
    logger.info("[API] FastAPI starting up. Initializing Event Bus.")
    event_bus.init(asyncio.get_running_loop())

# ---- Push Mechanism (SSE) ----

@app.get("/api/stream")
async def stream_events(token: str = Depends(verify_token)):
    async def event_generator():
        queue = event_bus.subscribe()
        min_interval = 1.0 / 10  # max 10 events/sec
        last_sent = 0.0
        try:
            while True:
                data = await queue.get()
                now = asyncio.get_event_loop().time()
                if now - last_sent < min_interval:
                    await asyncio.sleep(min_interval - (now - last_sent))
                last_sent = asyncio.get_event_loop().time()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            event_bus.unsubscribe(queue)
            raise
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ---- Pull Mechanism (REST) ----

@app.get("/api/settings")
def get_all_settings(token: str = Depends(verify_token)):
    return dict(settings.config)

@app.post("/api/settings/update")
async def update_setting(request: Request, token: str = Depends(verify_token)):
    data = await request.json()
    key = data.get("key")
    value = data.get("value")
    
    if not isinstance(key, str) or not key:
        return dict(settings.config)

    # Re-implemented Regex Validation
    if key.endswith("_hotkey") and not _validate_hotkey(value):
        logger.warning(f"[API] Rejected invalid hotkey: {key}={value!r}")
        return dict(settings.config)

    settings.set_setting(key, value)
    
    if key == "app_enabled" and core_engine_instance:
        if hasattr(core_engine_instance, "set_auto_mode"):
            core_engine_instance.set_auto_mode(value)
    elif key.endswith("_hotkey") and core_engine_instance:
        if hasattr(core_engine_instance, "update_hotkeys"):
            core_engine_instance.update_hotkeys()
    elif key == "blackbox_mode":
        from utils.logger import configure_blackbox_mode
        configure_blackbox_mode(value)
            
    return dict(settings.config)

@app.get("/api/dictionary")
def get_dictionary(token: str = Depends(verify_token)):
    dict_path = os.path.join(settings.get_data_dir(), "user_dict.json")
    if not os.path.exists(dict_path):
        return []
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [{"gibberish": k, "correct": v, "freq": "Manual"} for k, v in data.items()]
    except Exception as e:
        logger.error(f"Failed to read user dict: {e}")
        return []

@app.post("/api/dictionary/add")
async def add_dictionary_word(request: Request, token: str = Depends(verify_token)):
    data = await request.json()
    gibberish = data.get("gibberish")
    correct = data.get("correct")
    if isinstance(gibberish, str) and isinstance(correct, str) and gibberish and correct:
        user_dictionary.add_correction(gibberish, correct)
    return get_dictionary(token=token)

@app.post("/api/dictionary/remove")
async def remove_dictionary_word(request: Request, token: str = Depends(verify_token)):
    data = await request.json()
    gibberish = data.get("gibberish")
    if isinstance(gibberish, str) and gibberish:
        if gibberish in user_dictionary.user_dict:
            del user_dictionary.user_dict[gibberish]
            user_dictionary.save_user_dict()
    return get_dictionary(token=token)

@app.get("/api/stats")
def get_stats(token: str = Depends(verify_token)):
    import datetime
    
    # Calculate accuracy rate
    total = settings.get_stat("total_corrections", 0)
    undone = settings.get_stat("corrections_undone", 0)
    accuracy = round(((total - undone) / total * 100) if total > 0 else 100, 1)
    
    # Build top corrections list sorted by frequency
    top_raw = settings.get_stat("top_corrections", {})
    top_list = sorted(
        [{"pair": k, "count": v} for k, v in top_raw.items()],
        key=lambda x: x["count"], reverse=True
    )[:5]
    
    from ai import ai_engine
    return {
        "corrections_today": settings.get_stat("corrections_today", 0),
        "total_corrections": settings.get_stat("total_corrections", 0),
        "corrections_undone": settings.get_stat("corrections_undone", 0),
        "manual_corrections": settings.get_stat("manual_corrections", 0),
        "words_learned": settings.get_stat("words_learned", 0),
        "words_typed_today": settings.get_stat("words_typed_today", 0),
        "total_words_typed": settings.get_stat("total_words_typed", 0),
        "average_latency": settings.get_stat("average_latency", 0),
        "accuracy_rate": accuracy,
        "hourly_activity": settings.get_stat("hourly_activity", [0] * 24),
        "top_corrections": top_list,
        "daily_history": settings.get_stat("daily_history", []),
        "today": datetime.date.today().strftime("%A, %B %d"),
        "model_info": ai_engine.get_model_info()
    }

@app.get("/api/activity_log")
def get_activity_log_endpoint(token: str = Depends(verify_token)):
    return get_activity_log()

@app.get("/api/logs/raw")
def get_raw_logs_endpoint(token: str = Depends(verify_token)):
    from utils.logger import get_raw_logs
    return {"logs": get_raw_logs()}

@app.get("/api/logs/export")
def export_logs_endpoint(token: str = Depends(verify_token)):
    import shutil
    import tempfile
    import datetime
    from fastapi.background import BackgroundTasks
    from utils.logger import get_data_dir

    data_dir = get_data_dir()
    
    # Generate unique filename with date and time
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_filename = f"layvix_diagnostics_{timestamp}"
    
    # Create temp directory specifically for this export to avoid conflicts
    temp_export_dir = tempfile.mkdtemp()
    zip_path_base = os.path.join(temp_export_dir, base_filename)
    
    # Create the zip file
    zip_path = shutil.make_archive(zip_path_base, 'zip', data_dir)
    
    # Use BackgroundTasks to delete the temp directory and zip file after sending
    # Wait, FileResponse doesn't accept BackgroundTasks directly in its constructor easily without BackgroundTask object.
    # Actually, we can use fastapi.background.BackgroundTask
    from starlette.background import BackgroundTask
    
    def cleanup(temp_dir):
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

    return FileResponse(
        zip_path, 
        filename=f"{base_filename}.zip", 
        media_type="application/zip",
        background=BackgroundTask(cleanup, temp_export_dir)
    )

@app.delete("/api/logs")
def clear_raw_logs_endpoint(token: str = Depends(verify_token)):
    from utils.logger import clear_raw_logs
    success = clear_raw_logs()
    return {"status": "ok" if success else "error"}

@app.get("/api/hotkeys")
def get_hotkeys(token: str = Depends(verify_token)):
    return {
        "undo_hotkey": settings.get_setting("undo_hotkey", "ctrl+alt+shift+z"),
        "manual_hotkey": settings.get_setting("manual_hotkey", "ctrl+alt+shift+s"),
        "overlay_hotkey": settings.get_setting("overlay_hotkey", "ctrl+alt+shift+a"),
    }

@app.post("/api/hotkeys/update")
async def update_hotkey(request: Request, token: str = Depends(verify_token)):
    data = await request.json()
    key = data.get("key")
    value = data.get("value")
    if not isinstance(key, str) or not key:
        return get_hotkeys(token=token)
    if not _validate_hotkey(value):
        logger.warning(f"[API] Rejected invalid hotkey: {key}={value!r}")
        return get_hotkeys(token=token)
    settings.set_setting(key, value)
    if core_engine_instance and hasattr(core_engine_instance, "update_hotkeys"):
        try:
            core_engine_instance.update_hotkeys()
        except Exception as e:
            logger.error(f"Failed to update hotkeys: {e}")
    return get_hotkeys(token=token)

@app.get("/api/exclusions")
def get_exclusions(token: str = Depends(verify_token)):
    return settings.get_setting("excluded_apps", [])

@app.post("/api/exclusions/add")
async def add_exclusion(request: Request, token: str = Depends(verify_token)):
    data = await request.json()
    app_name = data.get("app_name")
    if not _validate_app_name(app_name):
        logger.warning(f"[API] Rejected invalid exclusion: {app_name!r}")
        return settings.get_setting("excluded_apps", [])
    excluded = settings.get_setting("excluded_apps", []) or []
    if app_name not in excluded:
        excluded.append(app_name)
        settings.set_setting("excluded_apps", excluded)
    return settings.get_setting("excluded_apps", [])

@app.post("/api/exclusions/remove")
async def remove_exclusion(request: Request, token: str = Depends(verify_token)):
    data = await request.json()
    app_name = data.get("app_name")
    if not isinstance(app_name, str):
        return settings.get_setting("excluded_apps", [])
    excluded = settings.get_setting("excluded_apps", []) or []
    if app_name in excluded:
        excluded.remove(app_name)
        settings.set_setting("excluded_apps", excluded)
    return settings.get_setting("excluded_apps", [])

# ---- Target Picker State ----
@app.post("/api/exclusions/picker/start")
def start_picker(token: str = Depends(verify_token)):
    if core_engine_instance and hasattr(core_engine_instance, 'start_picker_mode'):
        core_engine_instance.start_picker_mode()
    return {"status": "started"}

@app.get("/api/exclusions/picker/status")
def get_picker_status(token: str = Depends(verify_token)):
    active = False
    result = None
    if core_engine_instance and hasattr(core_engine_instance, 'picker_mode_active'):
        active = core_engine_instance.picker_mode_active
        result = core_engine_instance.picker_result
    return {"active": active, "result": result}

@app.get("/api/active_windows")
def get_active_windows(token: str = Depends(verify_token)):
    import ctypes
    from ctypes import wintypes
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    
    active_apps = set()
    
    def foreach_window(hwnd, lParam):
        if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            
            hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
            if hProcess:
                buffer = ctypes.create_unicode_buffer(260)
                if psapi.GetModuleBaseNameW(hProcess, 0, buffer, 260) > 0:
                    exe_name = buffer.value.lower()
                    if exe_name not in ["layvixproportable.exe", "layvix.exe", "explorer.exe", "applicationframehost.exe"]:
                        active_apps.add(exe_name)
                kernel32.CloseHandle(hProcess)
        return True
        
    user32.EnumWindows(EnumWindowsProc(foreach_window), 0)
    return {"windows": sorted(list(active_apps))}

@app.get("/api/installed_apps")
def get_installed_apps(token: str = Depends(verify_token)):
    from core.app_scanner import get_installed_apps_with_icons
    # We run this in a thread pool to not block the main asyncio loop
    # actually, fastapi will automatically run it in a threadpool since it's a 'def' not 'async def'
    apps = get_installed_apps_with_icons()
    return {"apps": apps}

# ---- Window Controls ----

@app.post("/api/window/minimize")
def minimize_window(token: str = Depends(verify_token)):
    if app_window:
        try:
            app_window.minimize()
        except Exception as e:
            logger.error(f"minimize failed: {e}")
    return {"status": "ok"}

@app.post("/api/window/hide")
def hide_window(token: str = Depends(verify_token)):
    if app_window:
        try:
            app_window.hide()
        except Exception as e:
            logger.error(f"hide failed: {e}")
    return {"status": "ok"}

@app.post("/api/window/toggle_maximize")
def toggle_maximize(token: str = Depends(verify_token)):
    if app_window:
        try:
            app_window.toggle_fullscreen()
        except Exception as e:
            logger.error(f"toggle_maximize failed: {e}")
    return {"status": "ok"}

trigger_shutdown_callback = None

@app.post("/api/quit")
def quit_engine(token: str = Depends(verify_token)):
    logger.info("[API] Received quit command. Shutting down.")
    
    if trigger_shutdown_callback:
        # Trigger the graceful shutdown in a background thread so the API can return
        import threading
        threading.Thread(target=trigger_shutdown_callback, daemon=True).start()
    else:
        # Fallback
        if core_engine_instance:
            try:
                core_engine_instance.stop()
            except Exception as e:
                logger.error(f"Failed to stop core: {e}")
        settings.force_save_settings()
        def _exit_later():
            import time, os
            time.sleep(0.5)
            os._exit(0)
        import threading
        threading.Thread(target=_exit_later).start()
        
    return {"status": "shutting down"}

# ---- Updater Endpoints ----

@app.get("/api/update/check")
def check_update_endpoint(token: str = Depends(verify_token)):
    from core.updater import check_for_updates
    # Run synchronously, check_for_updates blocks but has a 5s timeout
    return check_for_updates()

@app.post("/api/update/install")
async def install_update_endpoint(request: Request, token: str = Depends(verify_token)):
    from core.updater import install_update_async
    data = await request.json()
    download_url = data.get("download_url")
    if download_url:
        install_update_async(download_url)
        return {"status": "started"}
    return {"status": "error", "message": "No download URL provided"}

# ---- Frontend Static Files Serving ----
import sys
base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
dist_dir = os.path.join(base_dir, "frontend", "dist")

if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Serve actual files if they exist (e.g. favicon.ico, images)
        if full_path:
            file_path = os.path.join(dist_dir, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
        
        # Fallback to index.html for React Router
        return FileResponse(os.path.join(dist_dir, "index.html"))
