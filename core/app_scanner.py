import os
import win32com.client
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import base64
from io import BytesIO
import threading

_cached_apps = None
_cache_lock = threading.Lock()

def get_start_menu_apps():
    """Returns a list of installed apps from the Start Menu."""
    shell = win32com.client.Dispatch("WScript.Shell")
    paths_to_scan = [
        shell.SpecialFolders("AllUsersPrograms"),
        shell.SpecialFolders("Programs")
    ]
    
    apps = []
    seen_exes = set()
    
    for folder in paths_to_scan:
        if not folder or not os.path.exists(folder):
            continue
            
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".lnk"):
                    lnk_path = os.path.join(root, file)
                    try:
                        shortcut = shell.CreateShortCut(lnk_path)
                        target = shortcut.Targetpath
                        if target and target.lower().endswith(".exe"):
                            app_name = os.path.splitext(file)[0]
                            exe_name = os.path.basename(target).lower()
                            
                            # Skip common uninstallers or system utilities if desired
                            if "uninstall" in exe_name or "unins" in exe_name:
                                continue
                                
                            if exe_name not in seen_exes:
                                seen_exes.add(exe_name)
                                apps.append({
                                    "name": app_name,
                                    "exe": exe_name,
                                    "path": target
                                })
                    except Exception:
                        pass
                        
    return sorted(apps, key=lambda x: x["name"].lower())

def extract_icon_as_base64(exe_path):
    """Extracts the embedded icon from an executable and returns it as a Base64 PNG data URI."""
    try:
        large, small = win32gui.ExtractIconEx(exe_path, 0)
        if not large:
            return None
            
        hicon = large[0]
        
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
        
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)
        
        # Draw icon
        hdc_mem.DrawIcon((0, 0), hicon)
        
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (ico_x, ico_x), bmpstr, 'raw', 'BGRA', 0, 1)
        
        # Cleanup
        win32gui.DestroyIcon(hicon)
        if small:
            win32gui.DestroyIcon(small[0])
            
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        return None

def get_installed_apps_with_icons(force_refresh=False):
    """Gets the list of apps with icons. Caches the result to avoid slow re-scans."""
    global _cached_apps
    
    with _cache_lock:
        if _cached_apps is not None and not force_refresh:
            return _cached_apps
            
        apps = get_start_menu_apps()
        
        results = []
        for app in apps:
            icon_b64 = extract_icon_as_base64(app["path"])
            if icon_b64:
                app["icon"] = icon_b64
                results.append(app)
            else:
                # Provide a generic fallback or skip
                pass
                
        _cached_apps = results
        return _cached_apps
