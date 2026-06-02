import os
import logging
from logging.handlers import RotatingFileHandler

APP_NAME = "Layvix"
LOG_DIR = os.path.join(os.environ.get("APPDATA", "."), APP_NAME)
LOG_FILE = os.path.join(LOG_DIR, "layvix.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Create logger
_logger = logging.getLogger(APP_NAME)
_logger.setLevel(logging.DEBUG)

# File handler: rotates at 5MB, keeps 3 backups
_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

# Console handler (for dev)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

_logger.addHandler(_file_handler)
_logger.addHandler(_console_handler)

# In-memory log buffer for UI Activity Log tab
_activity_log = []
MAX_ACTIVITY_LOG = 50


def get_logger():
    """Returns the main application logger."""
    return _logger


def log_activity(event_type: str, message: str):
    """Log an activity event for display in the UI Activity Log tab."""
    import time
    entry = {
        "time": time.strftime("%H:%M:%S"),
        "type": event_type,
        "message": message
    }
    _activity_log.append(entry)
    if len(_activity_log) > MAX_ACTIVITY_LOG:
        _activity_log.pop(0)
    _logger.info(f"[{event_type}] {message}")


def get_activity_log():
    """Returns the in-memory activity log list."""
    return list(_activity_log)


def get_data_dir():
    """Returns the %APPDATA%/Layvix directory path, creating it if needed."""
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR
