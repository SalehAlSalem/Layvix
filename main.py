import sys
import ctypes
import keyboard
import time
import threading
import pystray
from plyer import notification
from PIL import Image, ImageDraw
import dictionary
import user_dictionary
import settings
import active_window
from mapper import convert_word
from layout_helper import get_current_language, switch_language
from PyQt6.QtWidgets import QApplication

# --- SINGLE INSTANCE LOCK ---
mutex_name = "Global\\Layvix_v1_Mutex"
kernel32 = ctypes.windll.kernel32
mutex = kernel32.CreateMutexW(None, False, mutex_name)
if kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, "Layvix - Dashboard")
    if hwnd:
        user32.ShowWindow(hwnd, 5) # SW_SHOW
        user32.SetForegroundWindow(hwnd)
    sys.exit(0)

# Global state
current_word = []
enabled = True
context_history = []
overlay_window = None
main_window = None
last_key_time = 0

undo_history = []

def is_mixed(w):
    has_alpha = any(c.isalpha() for c in w)
    has_punct = any(not c.isalpha() and not c.isspace() for c in w)
    return has_alpha and has_punct

def add_to_context(lang):
    global context_history
    context_history.append(lang)
    if len(context_history) > 5:
        context_history.pop(0)

def get_context_lang():
    if not context_history: return None
    return 'ar' if context_history.count('ar') > context_history.count('en') else 'en'

def correct_word(word_to_delete, target_word):
    threading.Thread(target=_correct_word_thread, args=(word_to_delete, target_word), daemon=True).start()

def _correct_word_thread(word_to_delete, target_word):
    global undo_history
    undo_history.append({'time': time.time(), 'wrong': word_to_delete, 'correct': target_word})
    if len(undo_history) > 20:
        undo_history.pop(0)
    
    for _ in range(len(word_to_delete) + 1):
        keyboard.send('backspace')
        time.sleep(0.01)
    
    switch_language()
    keyboard.write(target_word)
    keyboard.send('space')
    
    try:
        notification.notify(title="تم التصحيح!", message=f"تم تحويل '{word_to_delete}' إلى '{target_word}'", app_name="Layvix", timeout=1)
    except: pass

def trigger_undo():
    threading.Thread(target=_trigger_undo_thread, daemon=True).start()

def _trigger_undo_thread():
    global undo_history
    if not enabled or not undo_history: return
    
    # Force release modifiers via ctypes for robustness
    import ctypes
    user32 = ctypes.windll.user32
    for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]: # Shift, Ctrl, Alt, LWin, RWin
        user32.keybd_event(vk, 0, 2, 0)
    time.sleep(0.05)
    
    last = undo_history.pop()
    
    if time.time() - last['time'] < 30:
        for _ in range(len(last['correct']) + 1):
            keyboard.send('backspace')
            time.sleep(0.01)
            
        switch_language()
        keyboard.write(last['wrong'])
        keyboard.send('space')
        
        user_dictionary.add_correction(last['wrong'], last['wrong'])
        
        if main_window:
            from PyQt6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(main_window, "load_dictionary", Qt.ConnectionType.QueuedConnection)
            
        try:
            notification.notify(title="التراجع الذكي ↩️", message=f"تم إرجاع '{last['wrong']}' كاستثناء.", app_name="Layvix", timeout=2)
        except: pass

def manual_convert_selection():
    threading.Thread(target=_manual_convert_thread, daemon=True).start()

def _manual_convert_thread():
    try:
        import winsound
        try: winsound.MessageBeep()
        except: pass
        
        # Force release modifiers via ctypes to ensure OS knows they are up
        import ctypes
        user32 = ctypes.windll.user32
        for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]: # Shift, Ctrl, Alt, LWin, RWin
            user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.05)
        
        import pyperclip
        try: pyperclip.copy("") # Clear clipboard first
        except: pass
        time.sleep(0.05)
        
        # Simulating Ctrl+C via ctypes reliably
        user32.keybd_event(0x11, 0, 0, 0) # Ctrl down
        user32.keybd_event(0x43, 0, 0, 0) # C down
        time.sleep(0.02)
        user32.keybd_event(0x43, 0, 2, 0) # C up
        user32.keybd_event(0x11, 0, 2, 0) # Ctrl up
        
        time.sleep(0.2)
        
        text = ""
        for _ in range(5): # Retry reading clipboard
            try:
                text = pyperclip.paste().strip()
                if text: break
            except:
                time.sleep(0.1)
                
        if not text:
            # Fallback to Insert key copy if Ctrl+C failed
            user32.keybd_event(0x11, 0, 0, 0) # Ctrl down
            user32.keybd_event(0x2D, 0, 0, 0) # Insert down
            time.sleep(0.02)
            user32.keybd_event(0x2D, 0, 2, 0) # Insert up
            user32.keybd_event(0x11, 0, 2, 0) # Ctrl up
            time.sleep(0.2)
            try: text = pyperclip.paste().strip()
            except: pass
            
        if not text: return
        
        has_ar = any('\u0600' <= c <= '\u06FF' for c in text)
        if has_ar:
            converted = convert_word(text, "ar_to_en")
            target_layout = 'en'
        else:
            converted = convert_word(text, "en_to_ar")
            target_layout = 'ar'
            
        for _ in range(5):
            try:
                pyperclip.copy(converted)
                break
            except:
                time.sleep(0.1)
                
        time.sleep(0.1)
        # Simulating Ctrl+V via ctypes reliably
        user32.keybd_event(0x11, 0, 0, 0) # Ctrl down
        user32.keybd_event(0x56, 0, 0, 0) # V down
        time.sleep(0.02)
        user32.keybd_event(0x56, 0, 2, 0) # V up
        user32.keybd_event(0x11, 0, 2, 0) # Ctrl up
        
        # Automatically switch keyboard layout to match the converted text!
        lang_id = get_current_language()
        is_currently_ar = (lang_id == 1025)
        if target_layout == 'en' and is_currently_ar:
            switch_language()
        elif target_layout == 'ar' and not is_currently_ar:
            switch_language()
        
        try:
            notification.notify(title="التحويل اليدوي ✅", message=f"تم تحويل النص بنجاح.", app_name="Layvix", timeout=1)
        except: pass
    except Exception as e:
        print(f"Error in manual_convert: {e}")

def on_key(event):
    global current_word, enabled, last_key_time
    if not enabled: return

    try:
        if time.time() - last_key_time > 1.5:
            current_word.clear()
        last_key_time = time.time()

        if event.name in ['left', 'right', 'up', 'down', 'home', 'end', 'page up', 'page down']:
            current_word.clear()
            return

        if event.event_type == keyboard.KEY_DOWN:
            if event.name in ['space', 'enter']:
                word_str = "".join(current_word)
                if len(word_str) > 0:
                    active_exe = active_window.get_active_window_exe()
                    if active_exe and active_exe in settings.get_setting("excluded_apps"):
                        current_word.clear()
                        return

                    # 1. User Dictionary has TOP priority (Force Conversion or Ignore)
                    user_correction = user_dictionary.get_correction(word_str)
                    if user_correction:
                        if user_correction != word_str:
                            correct_word(word_str, user_correction)
                        current_word.clear()
                        return

                    # 2. Check if valid in current layout
                    lang_id = get_current_language()
                    current_layout = 'ar' if lang_id == 1025 else 'en'
                    
                    is_valid_now = False
                    if current_layout == 'en' and dictionary.is_valid_english(word_str):
                        is_valid_now = True
                        add_to_context('en')
                    elif current_layout == 'ar' and dictionary.is_valid_arabic(word_str):
                        is_valid_now = True
                        add_to_context('ar')
                    
                    # 3. Auto-correct logic
                    if not is_valid_now:
                        score_en = 0
                        score_ar = 0
                        en_word = convert_word(word_str, "ar_to_en")
                        ar_word = convert_word(word_str, "en_to_ar")
                        
                        if dictionary.is_valid_arabic(ar_word): score_ar += 5
                        if get_context_lang() == 'ar': score_ar += 2
                        
                        if dictionary.is_valid_english(en_word): score_en += 5
                        if get_context_lang() == 'en': score_en += 2
                        
                        threshold = 5 if len(word_str) <= 3 else 4
                        
                        if current_layout == 'en' and score_ar >= threshold and score_ar > score_en:
                            correct_word(word_str, ar_word)
                            add_to_context('ar')
                        elif current_layout == 'ar' and score_en >= threshold and score_en > score_ar:
                            correct_word(word_str, en_word)
                            add_to_context('en')
                
                current_word.clear()
            elif event.name == 'backspace':
                if len(current_word) > 0:
                    current_word.pop()
            elif len(event.name) == 1:
                current_word.append(event.name)
    except Exception as exc:
        print(f"Error in on_key: {exc}")

def trigger_overlay():
    if not enabled: return
    if overlay_window:
        overlay_window.trigger_show.emit("")

hotkey_callbacks = []

def setup_hotkeys():
    global hotkey_callbacks
    for cb in hotkey_callbacks:
        try: keyboard.remove_hotkey(cb)
        except: pass
    hotkey_callbacks.clear()
    
    # Add safe fallbacks if empty
    over_hk = settings.get_setting("overlay_hotkey") or "ctrl+f12"
    undo_hk = settings.get_setting("undo_hotkey") or "pause"
    manual_hk = settings.get_setting("manual_hotkey") or "shift+pause"
    
    try:
        cb1 = keyboard.add_hotkey(over_hk, trigger_overlay)
        if cb1: hotkey_callbacks.append(cb1)
    except: pass
    
    try:
        cb2 = keyboard.add_hotkey(undo_hk, trigger_undo)
        if cb2: hotkey_callbacks.append(cb2)
    except: pass
    
    try:
        cb3 = keyboard.add_hotkey(manual_hk, manual_convert_selection)
        if cb3: hotkey_callbacks.append(cb3)
    except: pass

# --- Tray Icon ---
def create_image():
    image = Image.new('RGB', (64, 64), color=(40, 40, 40))
    dc = ImageDraw.Draw(image)
    dc.text((12, 10), "ALF", fill=(255, 255, 255))
    return image

def on_tray_click(icon, item):
    if main_window: main_window.show_dashboard_signal.emit()

def on_quit(icon, item):
    icon.stop()
    import os
    os._exit(0)

def setup_tray():
    menu = pystray.Menu(pystray.MenuItem('لوحة التحكم (Dashboard)', on_tray_click, default=True), pystray.MenuItem('إغلاق', on_quit))
    icon = pystray.Icon("Layvix", create_image(), "Auto Layout Fixer", menu)
    icon.run()

def on_ui_toggle():
    global enabled
    enabled = not enabled
    if main_window: main_window.update_toggle_button(enabled)

def main():
    from ui_overlay import OverlayWindow
    from ui_main import MainWindow

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    global overlay_window, main_window
    overlay_window = OverlayWindow()
    main_window = MainWindow()
    
    main_window.toggle_app_signal.connect(on_ui_toggle)
    main_window.hotkeys_changed_signal.connect(setup_hotkeys)
    
    main_window.show()

    setup_hotkeys()
    keyboard.hook(on_key)
    
    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
