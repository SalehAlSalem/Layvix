import os
import logging
from logging.handlers import RotatingFileHandler
import sys

from utils.event_bus import event_bus

APP_NAME = "Layvix"

def _determine_data_dir():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exe_dir, "portable.txt")):
            return os.path.join(exe_dir, "data")
        return os.path.join(os.environ.get("APPDATA", "."), APP_NAME, "data")
    else:
        # In DEV mode, save to APPDATA/Layvix-Dev to prevent polluting 
        # the source directory and accidentally bundling personal data in PyInstaller
        return os.path.join(os.environ.get("APPDATA", "."), f"{APP_NAME}-Dev", "data")

LOG_DIR = _determine_data_dir()
LOG_FILE = os.path.join(LOG_DIR, "layvix.log")

os.makedirs(LOG_DIR, exist_ok=True)

_logger = logging.getLogger(APP_NAME)
_logger.setLevel(logging.DEBUG)

from logging.handlers import TimedRotatingFileHandler

_file_handler = TimedRotatingFileHandler(
    LOG_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
# Start with INFO level by default, it will be updated by settings
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

_logger.addHandler(_file_handler)
_logger.addHandler(_console_handler)

def configure_blackbox_mode(enabled: bool):
    """Dynamically change file logging level based on Black Box setting."""
    if enabled:
        _file_handler.setLevel(logging.DEBUG)
        _logger.info("[LOGGER] Black Box Mode ENABLED. File logging is set to DEBUG.")
    else:
        _logger.info("[LOGGER] Black Box Mode DISABLED. File logging is set to INFO/ERROR.")
        _file_handler.setLevel(logging.INFO)

_activity_log = []
MAX_ACTIVITY_LOG = 50

class ActivityLogHandler(logging.Handler):
    def emit(self, record):
        import time
        msg = record.getMessage()
        
        # Security Filtering: Do NOT pass sensitive logs to UI via memory/SSE
        if "[SECURITY]" in msg or "[PASSWORD]" in msg:
            return
            
        event_type = record.levelname
        if msg.startswith("[") and "]" in msg:
            event_type = msg[1:msg.index("]")]
            msg = msg[msg.index("]")+1:].strip()
            
        entry = {
            "time": time.strftime("%H:%M:%S", time.localtime(record.created)),
            "type": event_type,
            "message": msg
        }
        _activity_log.append(entry)
        if len(_activity_log) > MAX_ACTIVITY_LOG:
            _activity_log.pop(0)
            
        # Broadcast to any active SSE clients
        event_bus.publish({"type": "log", "data": entry})

_ui_handler = ActivityLogHandler()
_ui_handler.setLevel(logging.INFO)
_logger.addHandler(_ui_handler)

def get_logger():
    return _logger

def log_activity(event_type: str, message: str):
    import time
    
    # File logging still runs normally, but block from UI Activity Log
    if "[SECURITY]" in message or "[PASSWORD]" in message:
        _logger.info(f"[{event_type}] {message}")
        return
        
    entry = {
        "time": time.strftime("%H:%M:%S"),
        "type": event_type,
        "message": message
    }
    _activity_log.append(entry)
    if len(_activity_log) > MAX_ACTIVITY_LOG:
        _activity_log.pop(0)
        
    event_bus.publish({"type": "log", "data": entry})
    _logger.info(f"[{event_type}] {message}")

def get_activity_log():
    return list(_activity_log)

def get_data_dir():
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR

def get_raw_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Only return the last 1000 lines to prevent UI freezing
                if len(lines) > 1000:
                    lines = lines[-1000:]
                return "".join(lines)
        return ""
    except Exception as e:
        return f"[LOGGER ERROR] Failed to read logs: {str(e)}"

def clear_raw_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
        return True
    except Exception as e:
        _logger.error(f"Failed to clear logs: {e}")
        return False
