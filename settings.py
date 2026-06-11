import json
import os
import sys
import copy
from logger import get_logger, get_data_dir

logger = get_logger()

SETTINGS_FILE = os.path.join(get_data_dir(), "settings.json")

# Default settings
DEFAULT_CONFIG = {
    "overlay_hotkey": "ctrl+alt+shift+a",
    "undo_hotkey": "ctrl+alt+shift+z",
    "manual_hotkey": "ctrl+alt+shift+s",
    "app_enabled": True,
    "run_on_startup": False,
    "language": "ar",
    "excluded_apps": ["cmd.exe", "powershell.exe", "WindowsTerminal.exe"],
    "ai_confidence_threshold": 0.85,
    "min_word_length": 1,
    "retroactive_correction": True,
    "show_floating_bubble": True,
    "use_personal_model": True,
    "bubble_size": 70,
    "bubble_x": 100,
    "bubble_y": 100,
    "stats": {
        "corrections_today": 0,
        "total_corrections": 0,
        "words_learned": 0
    }
}

config = copy.deepcopy(DEFAULT_CONFIG)

def load_settings():
    global config
    config = copy.deepcopy(DEFAULT_CONFIG)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    config[k] = v
            logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")


def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        apply_startup_setting()
        logger.info("Settings saved successfully")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")


def get_setting(key):
    val = config.get(key)
    if val is None:
        val = DEFAULT_CONFIG.get(key)
    if key == "excluded_apps" and not isinstance(val, list):
        return []
    return val


def set_setting(key, value):
    config[key] = value
    save_settings()


def apply_startup_setting():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        app_name = "Layvix"
        if config.get("run_on_startup", False):
            exe_path = os.path.abspath(sys.argv[0])
            if exe_path.endswith(".py"):
                python_exe = sys.executable
                cmd = f'"{python_exe}" "{exe_path}"'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
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
