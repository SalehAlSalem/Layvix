import sys
import os
import ctypes
import pynput.keyboard
import mouse
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

import settings
import user_dictionary
import game_detector
import active_window
from mapper import convert_word
from layout_helper import get_current_language, switch_language
import ai_engine
import learner
from logger import get_logger

import gui
from gui import MainWindow
from plyer import notification

logger = get_logger()

# Global stats
_stats = settings.get_setting("stats")

def save_stats():
    settings.set_setting("stats", _stats)

class CoreWorker(QThread):
    def __init__(self):
        super().__init__()
        self.enabled = True
        self.running = True
        self.is_correcting = False
        self.current_word = []
        self.last_key_time = 0
        self.undo_history = []
        self.shift_pressed = False
        self.listener = None
        self.auto_mode = True  # True = auto correct, False = manual only
        self.last_typed_word = ""
        self.last_manual_word = None
        
    def run(self):
        import keyboard
        self.setup_hotkeys()
        
        while self.running:
            time.sleep(0.1)
            
        try:
            keyboard.unhook(self.on_key_event)
        except:
            pass
        
    def stop(self):
        self.running = False
        self.wait()

    def set_enabled(self, val):
        self.enabled = val

    def setup_hotkeys(self):
        import keyboard
        try:
            keyboard.unhook_all()
        except:
            pass
        
        undo_hk = settings.get_setting("undo_hotkey") or "pause"
        try: 
            keyboard.add_hotkey(undo_hk, self.trigger_undo)
            logger.info(f"[HOTKEYS] Registered undo hotkey: {undo_hk}")
        except Exception as e: 
            logger.error(f"[HOTKEYS] Failed to register undo hotkey '{undo_hk}': {e}")
            
        manual_hk = settings.get_setting("manual_hotkey") or "shift+pause"
        try: 
            keyboard.add_hotkey(manual_hk, self.trigger_manual)
            logger.info(f"[HOTKEYS] Registered manual hotkey: {manual_hk}")
        except Exception as e: 
            logger.error(f"[HOTKEYS] Failed to register manual hotkey '{manual_hk}': {e}")
        
        # Re-hook our main listener after unhook_all
        try: keyboard.hook(self.on_key_event)
        except: pass
            
    def trigger_manual(self):
        logger.info(f"[DEBUG] trigger_manual called! enabled={self.enabled}, is_correcting={self.is_correcting}")
        if not self.enabled or self.is_correcting:
            return
            
        import pyperclip
        import keyboard
        import time
        
        # 1. Check if text is currently highlighted by simulating Ctrl+C
        old_clipboard = pyperclip.paste()
        pyperclip.copy('')  # Clear it temporarily
        
        # Release modifiers just in case before sending Ctrl+C
        for mod in ['ctrl', 'alt', 'shift', 'windows', 'right ctrl', 'right alt', 'right shift', 'left ctrl', 'left alt', 'left shift']:
            if keyboard.is_pressed(mod):
                keyboard.release(mod)
        time.sleep(0.05)
        
        keyboard.send('ctrl+c')
        time.sleep(0.1) # Wait for OS to copy
        
        selected_text = pyperclip.paste()
        is_selection = bool(selected_text.strip())
        
        if is_selection:
            word_str = selected_text
            pyperclip.copy(old_clipboard) # Restore old clipboard
        else:
            pyperclip.copy(old_clipboard) # Restore if empty
            # 2. Fallback to typed word logic
            word_str = "".join(self.current_word).strip()
            if not word_str:
                word_str = self.last_typed_word
                
            if not word_str:
                return
                
            self.current_word.clear()
            
        lang_id = get_current_language()
        current_layout = 'ar' if lang_id == 1 else 'en'
        
        # Determine actual typed layout by character content
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in word_str)
        
        if not is_arabic:  # Typed in English chars, user wants Arabic
            corrected = convert_word(word_str, 'en_to_ar')
            target_layout = 'ar'
        else:              # Typed in Arabic chars, user wants English
            corrected = convert_word(word_str, 'ar_to_en')
            target_layout = 'en'
            
        logger.info(f"[MANUAL] User forced correction for '{word_str}' \u2192 '{corrected}' (selection: {is_selection})")
        self.do_correction(word_str, corrected, switch=True, predicted_layout=target_layout, is_selection=is_selection)
        
        # LEARN: user manually corrected -> teach AI the correct layout
        learner.learn_from_manual(convert_word(word_str, 'ar_to_en') if is_arabic else word_str, 'ar' if is_arabic else 'en', target_layout)

    def on_key_event(self, event):
        if event.event_type == 'up':
            if event.name == 'shift':
                self.shift_pressed = False
            return
            
        if not self.enabled or self.is_correcting:
            return
            
        import keyboard
        # Ignore normal typing if major modifiers are pressed (e.g. during a hotkey)
        if keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt') or keyboard.is_pressed('windows'):
            return
            
        try:
            name = event.name
            if len(name) == 1:
                if time.time() - self.last_key_time > 2.0:
                    self.current_word.clear()
                self.current_word.append(name)
                self.last_key_time = time.time()
            elif name == 'space':
                word_str = "".join(self.current_word).strip()
                if word_str:
                    # Run process_word in a background thread so we don't block the hook
                    threading.Thread(target=self._process_word, args=(word_str,), daemon=True).start()
                self.current_word.clear()
            elif name == 'backspace':
                if self.current_word:
                    self.current_word.pop()
            elif name == 'enter':
                self.current_word.clear()
            elif name == 'shift':
                self.shift_pressed = True
        except:
            pass

    def trigger_undo(self):
        if not self.enabled or not self.undo_history or self.is_correcting:
            return
            
        self.is_correcting = True
        user32 = ctypes.windll.user32
        for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]:
            user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.05)
        KEYEVENTF_SCANCODE = 0x0008
        KEYEVENTF_KEYUP = 0x0002
        last = self.undo_history.pop()
        if time.time() - last['time'] < 30:
            for _ in range(len(last['correct']) + 1):
                user32.keybd_event(0, 0x0E, KEYEVENTF_SCANCODE, 0)
                user32.keybd_event(0, 0x0E, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)
            
            if last.get('switched', True):
                switch_language()
                time.sleep(0.05)
            
            import pyperclip
            old_cb = ""
            try:
                old_cb = pyperclip.paste()
            except:
                pass
                
            try:
                pyperclip.copy(last['wrong'] + ' ')
                time.sleep(0.05)
                user32.keybd_event(0x11, 0, 0, 0)
                user32.keybd_event(0x56, 0, 0, 0)
                time.sleep(0.02)
                user32.keybd_event(0x56, 0, 2, 0)
                user32.keybd_event(0x11, 0, 2, 0)
                time.sleep(0.1)
            finally:
                if old_cb:
                    try:
                        pyperclip.copy(old_cb)
                    except:
                        pass
            
            user_dictionary.add_correction(last['wrong'], last['wrong'])
            _stats["words_learned"] += 1
            save_stats()
            
            # LEARN: user undid -> AI was wrong
            predicted = last.get('predicted_layout', 'ar')
            learner.learn_from_undo(last['wrong'], predicted)
            
            try:
                notification.notify(title="التراجع الذكي ↩️", message=f"تم إرجاع '{last['wrong']}' كاستثناء.", app_name="Layvix", timeout=2)
            except:
                pass
            
            _stats["corrections_today"] -= 1
            _stats["total_corrections"] -= 1
            save_stats()
            
        self.is_correcting = False



    def _process_word(self, word_str):
        """Pure AI-based layout correction. No dictionaries."""
        active_exe = active_window.get_active_window_exe()
        if active_exe and active_exe in settings.get_setting("excluded_apps"):
            logger.info(f"[SKIP] excluded app: {active_exe}")
            return
            
        # Check user overrides first
        user_correction = user_dictionary.get_correction(word_str)
        if user_correction:
            if user_correction != word_str:
                self.do_correction(word_str, user_correction)
            return
        
        # Skip very short words (1-2 chars) — too ambiguous
        if len(word_str) < 3:
            logger.info(f"[SKIP] too short: '{word_str}'")
            return
            
        self.last_typed_word = word_str
        lang_id = get_current_language()
        current_layout = 'ar' if lang_id == 1 else 'en'
        
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in word_str)
        
        # AI only understands QWERTY English chars, so map Arabic typed chars to their English keys first
        test_word = word_str
        if is_arabic:
            test_word = convert_word(word_str, 'ar_to_en')
        
        # Ask the AI
        predicted_layout, confidence = ai_engine.predict_layout(test_word)
        logger.info(f"[AI] '{word_str}' (test='{test_word}') \u2192 predicted={predicted_layout} conf={confidence:.2%} current={current_layout}")
        
        # Only correct if AI is confident enough (> 75%)
        if confidence < 0.75 or predicted_layout == 'unknown':
            logger.info(f"[SKIP] low confidence or unknown")
            return
            
        # If AI says this word belongs to a different layout than current
        if predicted_layout != current_layout:
            if current_layout == 'en':
                corrected = convert_word(word_str, 'en_to_ar')
            else:
                corrected = convert_word(word_str, 'ar_to_en')
            
            if self.auto_mode:
                logger.info(f"[CORRECT] '{word_str}' → '{corrected}' (auto)")
                self.do_correction(word_str, corrected, switch=True, predicted_layout=predicted_layout)
            else:
                logger.info(f"[MANUAL MODE] would correct '{word_str}' → '{corrected}' but auto is off")
        else:
            logger.info(f"[OK] same layout, no correction needed")
            
    def do_correction(self, wrong, correct, switch=True, predicted_layout='ar', is_selection=False):
        self.is_correcting = True
        self.undo_history.append({'time': time.time(), 'wrong': wrong, 'correct': correct, 'switched': switch, 'predicted_layout': predicted_layout})
        if len(self.undo_history) > 50: self.undo_history.pop(0)
        
        user32 = ctypes.windll.user32
        import keyboard
        import pyperclip
        
        # Wait for user to physically release modifiers to avoid shortcut collision
        modifiers = ['ctrl', 'alt', 'shift', 'windows', 'right ctrl', 'right alt', 'right shift', 'left ctrl', 'left alt', 'left shift']
        timeout = time.time() + 2.0
        while time.time() < timeout:
            if not any(keyboard.is_pressed(m) for m in modifiers):
                break
            time.sleep(0.05)
            
        time.sleep(0.05)
        
        KEYEVENTF_SCANCODE = 0x0008
        KEYEVENTF_KEYUP = 0x0002
        
        if not is_selection:
            for _ in range(len(wrong) + 1):
                user32.keybd_event(0, 0x0E, KEYEVENTF_SCANCODE, 0)
                user32.keybd_event(0, 0x0E, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)
            
        if switch:
            switch_language()
            time.sleep(0.05)
        
        import pyperclip
        old_cb = ""
        try:
            old_cb = pyperclip.paste()
        except:
            pass
            
        try:
            pyperclip.copy(correct + ' ')
            time.sleep(0.05)
            user32.keybd_event(0x11, 0, 0, 0)
            user32.keybd_event(0x56, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(0x56, 0, 2, 0)
            user32.keybd_event(0x11, 0, 2, 0)
            time.sleep(0.1)
        finally:
            if old_cb:
                try:
                    pyperclip.copy(old_cb)
                except:
                    pass
        
        _stats["corrections_today"] += 1
        _stats["total_corrections"] += 1
        save_stats()
        self.is_correcting = False
        
        # LEARN: reinforce accepted correction after 5 seconds if not undone
        wrong_copy = wrong
        pred_copy = predicted_layout
        def delayed_learn():
            time.sleep(5)
            # If user didn't undo within 5 seconds, reinforce
            if self.undo_history and self.undo_history[-1]['wrong'] == wrong_copy:
                learner.learn_from_accepted(wrong_copy, pred_copy)
        threading.Thread(target=delayed_learn, daemon=True).start()

# Global access
_worker = None

def get_stats():
    return _stats

def stop_all():
    if _worker:
        _worker.stop()

def main():
    try:
        # Single instance lock
        mutex_name = "Global\\Layvix_v2_Mutex"
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == 183: # ERROR_ALREADY_EXISTS
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, f"Layvix v{gui.VERSION}")
            if hwnd:
                user32.ShowWindow(hwnd, 5)
                user32.SetForegroundWindow(hwnd)
            sys.exit(1)

        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        global _worker
        _worker = CoreWorker()
        window = gui.MainWindow()
        window.toggle_app_signal.connect(lambda: _worker.set_enabled(window.app_enabled))
        window.hotkeys_changed_signal.connect(_worker.setup_hotkeys)
        
        # Connect auto/manual mode toggle from GUI
        if hasattr(window, 'mode_changed_signal'):
            window.mode_changed_signal.connect(lambda auto: setattr(_worker, 'auto_mode', auto))
        
        window.show()
        
        _worker.start()
        
        # Game detector in background thread
        game_detector.start(on_change_callback=lambda is_fs: _worker.set_enabled(not is_fs and window.app_enabled))
        
        try:
            ret = app.exec()
            sys.exit(ret)
        except Exception as e:
            raise
    except Exception as e:
        import traceback
        with open("crash2.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise

if __name__ == "__main__":
    print("BEFORE MAIN", flush=True)
    main()
    print("AFTER MAIN", flush=True)
