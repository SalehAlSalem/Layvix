import sys
import os
import urllib.request
import json
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class Updater(QObject):
    update_available = pyqtSignal(str, str, str) # version, url, body
    check_finished = pyqtSignal(bool) # True if update found, False otherwise
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.repo = "salehalsalem/layvix"
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        
    def check_for_updates(self):
        """Runs the check in a background thread"""
        threading.Thread(target=self._do_check, daemon=True).start()
        
    def _do_check(self):
        try:
            req = urllib.request.Request(self.api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get('tag_name', '').lstrip('v')
                    if latest_version and self._is_newer(latest_version, self.current_version):
                        url = data.get('html_url', '')
                        body = data.get('body', '')
                        self.update_available.emit(latest_version, url, body)
                        self.check_finished.emit(True)
                        return
        except Exception as e:
            pass
        self.check_finished.emit(False)
        
    def _is_newer(self, latest, current):
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            # Pad with 0s to make lengths equal
            while len(l_parts) < 3: l_parts.append(0)
            while len(c_parts) < 3: c_parts.append(0)
            
            for l, c in zip(l_parts, c_parts):
                if l > c: return True
                if l < c: return False
            return False
        except:
            return latest != current
