import os
import sys
import json
import urllib.request
import threading
from urllib.error import URLError, HTTPError

from version import __version__
from utils.logger import app_logger

GITHUB_REPO = "SalehAlSalem/Layvix"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def check_for_updates():
    """
    Checks GitHub for the latest release.
    Returns a dict: {"update_available": bool, "latest_version": str, "current_version": str, "download_url": str}
    """
    try:
        req = urllib.request.Request(API_URL, headers={'User-Agent': 'Layvix-AutoUpdater'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
        latest_version = data.get("tag_name", "").lstrip("v")
        current_version = __version__.lstrip("v")
        
        # Simple semantic versioning comparison e.g. "4.1.0"
        latest_parts = [int(x) for x in latest_version.split('.') if x.isdigit()]
        current_parts = [int(x) for x in current_version.split('.') if x.isdigit()]
        
        update_available = False
        if latest_parts > current_parts:
            update_available = True
            
        download_url = None
        if update_available:
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break
                    
        return {
            "update_available": update_available,
            "latest_version": data.get("tag_name", latest_version),
            "current_version": __version__,
            "download_url": download_url
        }
    except Exception as e:
        app_logger.error(f"[UPDATER] Failed to check for updates: {e}")
        return {
            "update_available": False,
            "latest_version": __version__,
            "current_version": __version__,
            "download_url": None,
            "error": str(e)
        }

def install_update_async(download_url):
    """
    Spawns a background thread to download and install.
    """
    def _run():
        try:
            temp_dir = os.environ.get("TEMP", "C:\\Temp")
            exe_path = os.path.join(temp_dir, "Layvix_Update.exe")
            bat_path = os.path.join(temp_dir, "layvix_updater.bat")
            
            app_logger.info(f"[UPDATER] Downloading update from {download_url}...")
            
            # Download file
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Layvix-AutoUpdater'})
            with urllib.request.urlopen(req, timeout=60) as response, open(exe_path, 'wb') as out_file:
                out_file.write(response.read())
                
            app_logger.info(f"[UPDATER] Downloaded successfully to {exe_path}. Preparing updater script.")
            
            # Current executable path
            current_exe = sys.executable
            # If not frozen, we don't want to overwrite python.exe!
            if not getattr(sys, 'frozen', False):
                app_logger.warning("[UPDATER] Running in uncompiled mode. Will not overwrite python.exe.")
                return

            # Write batch file
            bat_content = f'''@echo off
echo Updating Layvix... Please wait.
timeout /t 3 /nobreak >nul
taskkill /f /im "{os.path.basename(current_exe)}" >nul 2>&1
move /y "{exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
'''
            with open(bat_path, "w") as f:
                f.write(bat_content)
                
            app_logger.info("[UPDATER] Executing batch script and exiting.")
            
            # Launch batch script
            import subprocess
            # Use CREATE_NO_WINDOW so it happens silently
            subprocess.Popen(
                bat_path, 
                shell=True, 
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # Exit application gracefully
            import api
            if hasattr(api, 'trigger_shutdown_callback') and api.trigger_shutdown_callback:
                api.trigger_shutdown_callback()
            else:
                os._exit(0)
            
        except Exception as e:
            app_logger.error(f"[UPDATER] Failed to install update: {e}")
            
    threading.Thread(target=_run, daemon=True).start()
