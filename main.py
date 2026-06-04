import sys
import os
import ctypes
import pynput.keyboard
import mouse
import numpy as np
import sklearn # Explicit import required for PyInstaller to pack it
import pickle
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon

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
_stats = settings.get_setting("stats") or {"corrections_today": 0, "total_corrections": 0, "words_learned": 0}

# Ensure all keys exist
for key in ["corrections_today", "total_corrections", "words_learned"]:
    if key not in _stats:
        _stats[key] = 0

# Daily reset: if today's date is different from last saved date, reset today's counter
import datetime
_today = datetime.date.today().isoformat()
_last_date = settings.get_setting("stats_date")
if _last_date != _today:
    _stats["corrections_today"] = 0
    settings.set_setting("stats_date", _today)

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
        
        # Monitor mouse clicks to clear buffers (preventing blind backspaces)
        import mouse
        try:
            mouse.hook(self.on_mouse_event)
        except Exception as e:
            logger.error(f"Failed to hook mouse: {e}")
        self.last_manual_word = None
        self.pending_short_word = None
        self.pending_short_time = 0
        
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
        
        # Wait for user to physically release modifiers to avoid shortcut collision
        modifiers = ['ctrl', 'alt', 'shift', 'windows', 'right ctrl', 'right alt', 'right shift', 'left ctrl', 'left alt', 'left shift']
        timeout = time.time() + 2.0
        while time.time() < timeout:
            if not any(keyboard.is_pressed(m) for m in modifiers):
                break
            time.sleep(0.05)
            
        import ctypes
        user32 = ctypes.windll.user32
        
        # Force software release of modifiers
        for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]: # Shift, Ctrl, Alt, LWin, RWin
            user32.keybd_event(vk, 0, 2, 0) # 2 is KEYUP
        time.sleep(0.05)
        
        # Send clean Ctrl+C via user32
        user32.keybd_event(0x11, 0, 0, 0) # Ctrl down
        user32.keybd_event(0x43, 0, 0, 0) # C down
        time.sleep(0.02)
        user32.keybd_event(0x43, 0, 2, 0) # C up
        user32.keybd_event(0x11, 0, 2, 0) # Ctrl up
        
        time.sleep(0.2) # Wait longer for OS to copy to clipboard
        
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
                try:
                    from plyer import notification
                    notification.notify(title="تنبيه ⚠️", message="يرجى تحديد (تظليل) الكلمة التي تريد تصحيحها أولاً.", app_name="Layvix", timeout=3)
                except:
                    pass
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
        
        # SMART LEARNING: Split sentence into words and learn them individually
        original_words = word_str.split()
        corrected_words = corrected.split()
        
        for w_wrong, w_right in zip(original_words, corrected_words):
            # Learn in AI model
            w_is_arabic = any('\u0600' <= c <= '\u06FF' for c in w_wrong)
            learner.learn_from_manual(convert_word(w_wrong, 'ar_to_en') if w_is_arabic else w_wrong, 'ar' if w_is_arabic else 'en', target_layout)
            
            # Add to explicit User Dictionary to enforce it immediately
            user_dictionary.add_correction(w_wrong, w_right)

    def on_mouse_event(self, event):
        # If the user clicks the mouse, they moved the cursor.
        # We must clear the typing buffers so we don't blindly send backspaces to the wrong place.
        import mouse
        if isinstance(event, mouse.ButtonEvent) and event.event_type == 'down':
            self.current_word.clear()
            self.last_typed_word = ""
            self.pending_short_word = None

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
                else:
                    self.pending_short_word = None
            elif name == 'enter':
                self.current_word.clear()
                self.pending_short_word = None
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
            
        lang_id = get_current_language()
        current_layout = 'ar' if lang_id == 1 else 'en'
        self.last_typed_word = word_str
            
        # Check user overrides first
        user_correction = user_dictionary.get_correction(word_str)
        if user_correction:
            if user_correction != word_str:
                self.do_correction(word_str, user_correction)
            return
        
        # Skip very short words based on setting (Save for retroactive)
        min_len = int(settings.get_setting("min_word_length") or 2)
        if len(word_str) < min_len:
            logger.info(f"[SKIP] too short: '{word_str}' (Saved for retroactive analysis)")
            self.pending_short_word = word_str
            self.pending_short_layout = current_layout
            self.pending_short_time = time.time()
            return
            
        # Clear pending short word if it's older than 2.5 seconds
        if self.pending_short_word and (time.time() - self.pending_short_time > 2.5):
            self.pending_short_word = None
        
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in word_str)
        
        # AI only understands QWERTY English chars, so map Arabic typed chars to their English keys first
        test_word = word_str
        if is_arabic:
            test_word = convert_word(word_str, 'ar_to_en')
        
        # Ask the AI
        predicted_layout, confidence = ai_engine.predict_layout(test_word)
        logger.info(f"[AI] '{word_str}' (test='{test_word}') \u2192 predicted={predicted_layout} conf={confidence:.2%} current={current_layout}")
        
        # Only correct if AI is confident enough
        threshold = float(settings.get_setting("ai_confidence_threshold") or settings.get_setting("confidence_threshold") or 0.85)
        if confidence < threshold or predicted_layout == 'unknown':
            logger.info(f"[SKIP] low confidence or unknown (Saved for retroactive analysis)")
            self.pending_short_word = word_str
            self.pending_short_layout = current_layout
            self.pending_short_time = time.time()
            return
            
        # If AI says this word belongs to a different layout than current
        if predicted_layout != current_layout:
            if current_layout == 'en':
                corrected = convert_word(word_str, 'en_to_ar')
            else:
                corrected = convert_word(word_str, 'ar_to_en')
                
            # --- RETROACTIVE CORRECTION TRIGGER ---
            retro_enabled = settings.get_setting("retroactive_correction")
            if retro_enabled is None: retro_enabled = True
            
            if self.pending_short_word and retro_enabled:
                prev_word = self.pending_short_word
                if current_layout == 'en':
                    prev_corrected = convert_word(prev_word, 'en_to_ar')
                else:
                    prev_corrected = convert_word(prev_word, 'ar_to_en')
                    
                combined_wrong = prev_word + " " + word_str
                combined_correct = prev_corrected + " " + corrected
                
                logger.info(f"[RETROACTIVE] Correcting past short word: '{combined_wrong}' -> '{combined_correct}'")
                self.pending_short_word = None
                
                if self.auto_mode:
                    self.do_correction(combined_wrong, combined_correct, switch=True, predicted_layout=predicted_layout)
                return
            # ----------------------------------------
            
            self.pending_short_word = None
            if self.auto_mode:
                logger.info(f"[CORRECT] '{word_str}' → '{corrected}' (auto)")
                self.do_correction(word_str, corrected, switch=True, predicted_layout=predicted_layout)
            else:
                logger.info(f"[MANUAL MODE] would correct '{word_str}' → '{corrected}' but auto is off")
        else:
            retro_enabled = settings.get_setting("retroactive_correction")
            if retro_enabled is None: retro_enabled = True
            
            if self.pending_short_word and retro_enabled and hasattr(self, 'pending_short_layout') and self.pending_short_layout != current_layout:
                prev_word = self.pending_short_word
                if self.pending_short_layout == 'en':
                    prev_corrected = convert_word(prev_word, 'en_to_ar')
                else:
                    prev_corrected = convert_word(prev_word, 'ar_to_en')
                    
                prev_test_word = convert_word(prev_word, 'ar_to_en') if any('\u0600' <= c <= '\u06FF' for c in prev_word) else prev_word
                prev_pred, prev_conf = ai_engine.predict_layout(prev_test_word)
                
                if prev_pred == current_layout and prev_conf >= threshold:
                    combined_wrong = prev_word + " " + word_str
                    combined_correct = prev_corrected + " " + word_str
                    logger.info(f"[RETROACTIVE] Manual Switch detected! Correcting past short word: '{combined_wrong}' -> '{combined_correct}'")
                    self.pending_short_word = None
                    if self.auto_mode:
                        self.do_correction(combined_wrong, combined_correct, switch=False, predicted_layout=predicted_layout)
                    return
                    
            self.pending_short_word = None
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
            
        # Force software release of modifiers
        for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]:
            user32.keybd_event(vk, 0, 2, 0)
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
        
        # Set Official App Icon (Octopus)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        global _worker
        _worker = CoreWorker()
        window = gui.MainWindow()
        window.toggle_app_signal.connect(lambda: _worker.set_enabled(window.app_enabled))
        window.hotkeys_changed_signal.connect(_worker.setup_hotkeys)
        
        # Connect auto/manual mode toggle from GUI
        if hasattr(window, 'mode_changed_signal'):
            window.mode_changed_signal.connect(lambda auto: setattr(_worker, 'auto_mode', auto))
            
        # Initialize Floating Bubble
        from floating_bubble import FloatingBubble
        bubble = FloatingBubble(_worker)
        if settings.get_setting("show_floating_bubble"):
            bubble.show()
        
        # We need to keep a reference to the bubble so it isn't garbage collected
        app.bubble = bubble
        
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
