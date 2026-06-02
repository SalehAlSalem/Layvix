import json
import os
import winreg

SETTINGS_FILE = "settings.json"

# Default settings
config = {
    "overlay_hotkey": "ctrl+alt+shift+a",
    "undo_hotkey": "ctrl+alt+shift+z",
    "manual_hotkey": "ctrl+alt+shift+s",
    "run_on_startup": False,
    "excluded_apps": ["cmd.exe", "powershell.exe", "WindowsTerminal.exe"]
}

def load_settings():
    global config
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge defaults
                for k, v in loaded.items():
                    config[k] = v
        except:
            pass

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        apply_startup_setting()
    except:
        pass

def get_setting(key):
    val = config.get(key)
    if key == "excluded_apps" and not isinstance(val, list):
        return []
    return val

def set_setting(key, value):
    config[key] = value
    save_settings()

def apply_startup_setting():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        app_name = "Layvix"
        if config.get("run_on_startup", False):
            # Try to find the executable path
            exe_path = os.path.abspath(sys.argv[0])
            if exe_path.endswith(".py"): 
                # If running from python, don't set registry to avoid weird behavior
                return
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except OSError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Failed to set startup registry: {e}")

# Initialize
import sys
load_settings()
