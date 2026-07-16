import json
import os
import sys
import copy
import threading
from utils.logger import get_logger, get_data_dir

logger = get_logger()

SETTINGS_FILE = os.path.join(get_data_dir(), "settings.json")

DEFAULT_CONFIG = {
    "overlay_hotkey": "ctrl+alt+shift+a",
    "undo_hotkey": "ctrl+alt+shift+z",
    "manual_hotkey": "ctrl+alt+shift+s",
    "app_enabled": True,
    "run_on_startup": False,
    "language": "ar",
    "excluded_apps": ["cmd.exe", "powershell.exe", "WindowsTerminal.exe", "conhost.exe"],
    "whitelisted_apps": [],
    "ai_confidence_threshold": 0.70,
    "min_word_length": 2,
    "retroactive_correction": True,
    "show_floating_bubble": True,
    "auto_switch_language": True,
    "blackbox_mode": False,
    "bubble_size": 70,
    "bubble_x": 100,
    "bubble_y": 100,
    "stats": {
        "corrections_today": 0,
        "total_corrections": 0,
        "corrections_undone": 0,
        "manual_corrections": 0,
        "words_learned": 0,
        "words_typed_today": 0,
        "total_words_typed": 0,
        "wpm_session_start": None,
        "hourly_activity": [0] * 24,
        "top_corrections": {}
    }
}

config = copy.deepcopy(DEFAULT_CONFIG)

_save_timer = None
_timer_lock = threading.Lock()

def load_settings():
    global config
    config = copy.deepcopy(DEFAULT_CONFIG)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    config[k] = v
            
            # User requirement: App should always start enabled, ignoring saved state
            config["app_enabled"] = True
            
            logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

def _actual_write_to_disk():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        apply_startup_setting()
        logger.debug("Settings saved successfully to disk")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")

def save_settings():
    """Debounces disk writes to prevent disk IO burn during rapid stats updates."""
    global _save_timer
    with _timer_lock:
        if _save_timer is not None:
            _save_timer.cancel()
        _save_timer = threading.Timer(10.0, _actual_write_to_disk)
        _save_timer.start()

def force_save_settings():
    """Forces an immediate, synchronous save. Used by Bridge during clean shutdown."""
    global _save_timer
    with _timer_lock:
        if _save_timer is not None:
            _save_timer.cancel()
            _save_timer = None
    _actual_write_to_disk()

def get_setting(key, default=None):
    val = config.get(key)
    if val is None:
        val = DEFAULT_CONFIG.get(key, default)
    if key == "excluded_apps" and not isinstance(val, list):
        return []
    if key == "whitelisted_apps" and not isinstance(val, list):
        return []
    return val

def get_stat(key, default=0):
    stats = config.get("stats", {})
    val = stats.get(key)
    if val is None:
        val = DEFAULT_CONFIG.get("stats", {}).get(key, default)
    return val

def increment_stat(key, amount=1):
    if "stats" not in config:
        config["stats"] = {}
        
    import datetime
    today_str = datetime.date.today().isoformat()
    
    last_date = config["stats"].get("last_date", "")
    if last_date != today_str:
        if last_date:
            history = config["stats"].get("daily_history", [])
            # Only save non-zero days or just save all days
            history.append({
                "date": last_date,
                "corrections": config["stats"].get("corrections_today", 0)
            })
            # Keep only last 7 days
            config["stats"]["daily_history"] = history[-7:]
        
        config["stats"]["last_date"] = today_str
        config["stats"]["corrections_today"] = 0
        
    current = config["stats"].get(key, 0)
    config["stats"][key] = current + amount
    
    # Force a save on stat updates for accuracy
    save_settings()

def update_average_latency(new_latency_ms):
    if "stats" not in config:
        config["stats"] = {}
    current_avg = config["stats"].get("average_latency", 0)
    
    if current_avg == 0:
        new_avg = new_latency_ms
    else:
        # Exponential Moving Average (EMA) to smooth out spikes
        new_avg = int((current_avg * 0.9) + (new_latency_ms * 0.1))
        
    config["stats"]["average_latency"] = new_avg
    save_settings()

def track_word_typed():
    """Called every time a word is committed (space/enter pressed). Tracks WPM and hourly activity."""
    import datetime
    if "stats" not in config:
        config["stats"] = {}
    
    now = datetime.datetime.now()
    hour = now.hour
    
    # Hourly activity tracking
    hourly = config["stats"].get("hourly_activity", [0] * 24)
    if len(hourly) != 24:
        hourly = [0] * 24
    hourly[hour] = hourly[hour] + 1
    config["stats"]["hourly_activity"] = hourly
    
    # Words typed count
    config["stats"]["words_typed_today"] = config["stats"].get("words_typed_today", 0) + 1
    config["stats"]["total_words_typed"] = config["stats"].get("total_words_typed", 0) + 1
    
    save_settings()

def track_correction_word(original, corrected):
    """Tracks which words are most frequently corrected for the Top Corrections leaderboard."""
    if "stats" not in config:
        config["stats"] = {}
    top = config["stats"].get("top_corrections", {})
    key = f"{original}→{corrected}"
    top[key] = top.get(key, 0) + 1
    # Keep only top 20
    if len(top) > 20:
        top = dict(sorted(top.items(), key=lambda x: x[1], reverse=True)[:20])
    config["stats"]["top_corrections"] = top
    save_settings()

def set_setting(key, value):
    config[key] = value
    force_save_settings()

def apply_startup_setting():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        app_name = "Layvix"
        if config.get("run_on_startup", False):
            exe_path = os.path.abspath(sys.argv[0])
            if exe_path.endswith(".py"):
                python_exe = sys.executable
                cmd = f'"{python_exe}" "{exe_path}" --startup'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}" --startup')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except OSError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        logger.error(f"Failed to set startup registry: {e}")

# Initialize
load_settings()

from utils.logger import configure_blackbox_mode
configure_blackbox_mode(config.get("blackbox_mode", False))
