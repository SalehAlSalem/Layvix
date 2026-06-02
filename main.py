import sys
import ctypes
import keyboard
import time
import threading
import pystray
from plyer import notification
from PIL import Image, ImageDraw
from logger import get_logger, log_activity
import dictionary
import user_dictionary
import settings
import active_window
import game_detector
from mapper import convert_word
from layout_helper import get_current_language, switch_language
from PyQt6.QtWidgets import QApplication

logger = get_logger()

# --- SINGLE INSTANCE LOCK ---
mutex_name = "Global\\Layvix_v1_Mutex"
kernel32 = ctypes.windll.kernel32
mutex = kernel32.CreateMutexW(None, False, mutex_name)
if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, "Layvix - Dashboard")
    if hwnd:
        user32.ShowWindow(hwnd, 5)
        user32.SetForegroundWindow(hwnd)
    sys.exit(0)

# --- Global State ---
current_word = []
enabled = True
context_history = []  # list of 'ar' or 'en' for last N valid words
overlay_window = None
main_window = None
last_key_time = 0
undo_history = []
shutdown_event = threading.Event()  # Clean shutdown signal
_stats = {"corrections_today": 0, "total_corrections": 0, "words_learned": 0}

UNDO_HISTORY_MAX = 50
CONTEXT_HISTORY_MAX = 5
import mouse


# --- Context Tracking ---
def add_to_context(lang):
    context_history.append(lang)
    if len(context_history) > CONTEXT_HISTORY_MAX:
        context_history.pop(0)


def get_context_lang():
    """Returns the dominant language in recent context, or None."""
    if not context_history:
        return None
    ar_count = context_history.count('ar')
    en_count = context_history.count('en')
    if ar_count > en_count:
        return 'ar'
    elif en_count > ar_count:
        return 'en'
    return None


def get_context_strength():
    """Returns how strong the context is (0.0 to 1.0).
    1.0 = all last N words are same language."""
    if len(context_history) < 3:
        return 0.0
    dominant = get_context_lang()
    if not dominant:
        return 0.0
    count = context_history[-3:].count(dominant)
    return count / 3.0


# --- Correction Engine ---
def correct_word(word_to_delete, target_word):
    if shutdown_event.is_set():
        return
    threading.Thread(target=_correct_word_thread, args=(word_to_delete, target_word), daemon=True).start()


def _correct_word_thread(word_to_delete, target_word):
    if shutdown_event.is_set():
        return
    
    undo_history.append({'time': time.time(), 'wrong': word_to_delete, 'correct': target_word})
    if len(undo_history) > UNDO_HISTORY_MAX:
        undo_history.pop(0)
    
    for _ in range(len(word_to_delete) + 1):
        if shutdown_event.is_set():
            return
        keyboard.send('backspace')
        time.sleep(0.01)
    
    switch_language()
    keyboard.write(target_word)
    keyboard.send('space')
    
    _stats["corrections_today"] += 1
    _stats["total_corrections"] += 1
    log_activity("تصحيح", f"'{word_to_delete}' → '{target_word}'")
    
    try:
        notification.notify(title="تم التصحيح!", message=f"'{word_to_delete}' → '{target_word}'", app_name="Layvix", timeout=1)
    except Exception as e:
        logger.warning(f"Notification failed: {e}")


# --- Undo System (Self-Learning via Undo) ---
def trigger_undo():
    if shutdown_event.is_set():
        return
    threading.Thread(target=_trigger_undo_thread, daemon=True).start()


def _trigger_undo_thread():
    if shutdown_event.is_set() or not enabled or not undo_history:
        return
    
    user32 = ctypes.windll.user32
    for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]:
        user32.keybd_event(vk, 0, 2, 0)
    time.sleep(0.05)
    
    last = undo_history.pop()
    
    if time.time() - last['time'] < 30:
        for _ in range(len(last['correct']) + 1):
            if shutdown_event.is_set():
                return
            keyboard.send('backspace')
            time.sleep(0.01)
        
        switch_language()
        keyboard.write(last['wrong'])
        keyboard.send('space')
        
        # Self-learning: add to ignore list via Undo
        user_dictionary.add_correction(last['wrong'], last['wrong'])
        _stats["words_learned"] += 1
        log_activity("تعلّم", f"تم حفظ '{last['wrong']}' كاستثناء عبر التراجع")
        
        if main_window:
            from PyQt6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(main_window, "load_dictionary", Qt.ConnectionType.QueuedConnection)
        
        try:
            notification.notify(title="التراجع الذكي ↩️", message=f"تم إرجاع '{last['wrong']}' كاستثناء.", app_name="Layvix", timeout=2)
        except Exception as e:
            logger.warning(f"Undo notification failed: {e}")


# --- Manual Convert ---
def manual_convert_selection():
    if shutdown_event.is_set():
        return
    threading.Thread(target=_manual_convert_thread, daemon=True).start()


def _manual_convert_thread():
    if shutdown_event.is_set():
        return
    try:
        import winsound
        try:
            winsound.MessageBeep()
        except Exception:
            pass
        
        user32 = ctypes.windll.user32
        for vk in [0x10, 0x11, 0x12, 0x5B, 0x5C]:
            user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.05)
        
        import pyperclip
        try:
            pyperclip.copy("")
        except Exception:
            pass
        time.sleep(0.05)
        
        user32.keybd_event(0x11, 0, 0, 0)
        user32.keybd_event(0x43, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(0x43, 0, 2, 0)
        user32.keybd_event(0x11, 0, 2, 0)
        time.sleep(0.2)
        
        text = ""
        for _ in range(5):
            try:
                text = pyperclip.paste().strip()
                if text:
                    break
            except Exception:
                time.sleep(0.1)
        
        if not text:
            user32.keybd_event(0x11, 0, 0, 0)
            user32.keybd_event(0x2D, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(0x2D, 0, 2, 0)
            user32.keybd_event(0x11, 0, 2, 0)
            time.sleep(0.2)
            try:
                text = pyperclip.paste().strip()
            except Exception:
                pass
        
        if not text:
            logger.warning("Manual convert: clipboard empty after copy attempts")
            return
        
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
            except Exception:
                time.sleep(0.1)
        
        time.sleep(0.1)
        user32.keybd_event(0x11, 0, 0, 0)
        user32.keybd_event(0x56, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(0x56, 0, 2, 0)
        user32.keybd_event(0x11, 0, 2, 0)
        
        lang_id = get_current_language()
        is_currently_ar = (lang_id == 1025)
        if target_layout == 'en' and is_currently_ar:
            switch_language()
        elif target_layout == 'ar' and not is_currently_ar:
            switch_language()
        
        log_activity("تحويل يدوي", f"'{text[:20]}...' → '{converted[:20]}...'")
        
        try:
            notification.notify(title="التحويل اليدوي ✅", message="تم تحويل النص بنجاح.", app_name="Layvix", timeout=1)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error in manual_convert: {e}")


# --- Keyboard Hook (Context Tracker as Tie-Breaker) ---
def on_key(event):
    global current_word, enabled, last_key_time
    if not enabled:
        return
    
    # Skip if fullscreen game is active
    if game_detector.is_fullscreen():
        return
    
    try:
        # Timeout: clear buffer if user paused typing
        if time.time() - last_key_time > 1.5:
            current_word.clear()
        last_key_time = time.time()
        
        # Arrow keys / navigation = clear buffer
        if event.name in ['left', 'right', 'up', 'down', 'home', 'end', 'page up', 'page down']:
            current_word.clear()
            return
        
        if event.event_type == keyboard.KEY_DOWN:
            if event.name in ['space', 'enter']:
                word_str = "".join(current_word)
                if len(word_str) > 0:
                    _process_word(word_str)
                current_word.clear()
            elif event.name == 'backspace':
                if len(current_word) > 0:
                    current_word.pop()
            elif len(event.name) == 1:
                current_word.append(event.name)
    except Exception as exc:
        logger.error(f"Error in on_key: {exc}")


def _process_word(word_str):
    """Core correction logic with Context as Tie-Breaker."""
    # Check excluded apps
    active_exe = active_window.get_active_window_exe()
    if active_exe and active_exe in settings.get_setting("excluded_apps"):
        return
    
    # 1. User Dictionary has TOP priority
    user_correction = user_dictionary.get_correction(word_str)
    if user_correction:
        if user_correction != word_str:
            correct_word(word_str, user_correction)
        return
    
    # 2. Detect current layout
    lang_id = get_current_language()
    current_layout = 'ar' if lang_id == 1025 else 'en'
    
    # 3. Check if valid in current layout
    if current_layout == 'en' and dictionary.is_valid_english(word_str):
        add_to_context('en')
        return  # Valid in current layout, don't touch it!
    elif current_layout == 'ar' and dictionary.is_valid_arabic(word_str):
        add_to_context('ar')
        return  # Valid in current layout, don't touch it!
    
    # 4. Word is NOT valid in current layout. Try converting.
    en_word = convert_word(word_str, "ar_to_en")
    ar_word = convert_word(word_str, "en_to_ar")
    
    en_freq = dictionary.get_english_frequency(en_word)
    ar_freq = dictionary.get_arabic_frequency(ar_word)
    
    en_valid = en_freq > 0
    ar_valid = ar_freq > 0
    
    # --- GOLDEN RULE: Dictionary Validity beats Context ---
    
    # Case A: Valid in exactly ONE language → correct immediately
    if current_layout == 'en' and ar_valid and not en_valid:
        correct_word(word_str, ar_word)
        add_to_context('ar')
        return
    
    if current_layout == 'ar' and en_valid and not ar_valid:
        correct_word(word_str, en_word)
        add_to_context('en')
        return
    
    # Case B: Valid in BOTH languages → Context is the tie-breaker
    if ar_valid and en_valid:
        ctx = get_context_lang()
        ctx_strength = get_context_strength()
        
        if current_layout == 'en':
            # Currently English, both are valid
            if ctx == 'ar' and ctx_strength >= 0.66:
                # Strong Arabic context → switch to Arabic
                correct_word(word_str, ar_word)
                add_to_context('ar')
            else:
                # Default: use frequency as final tie-breaker
                if ar_freq > en_freq * 2:  # Arabic must be significantly more frequent
                    correct_word(word_str, ar_word)
                    add_to_context('ar')
                # else: leave it alone
        
        elif current_layout == 'ar':
            if ctx == 'en' and ctx_strength >= 0.66:
                correct_word(word_str, en_word)
                add_to_context('en')
            else:
                if en_freq > ar_freq * 2:
                    correct_word(word_str, en_word)
                    add_to_context('en')
    
    # Case C: Valid in NEITHER language → don't touch it


# --- Overlay ---
def trigger_overlay():
    if not enabled:
        return
    if overlay_window:
        overlay_window.trigger_show.emit("")


# --- Hotkeys ---
hotkey_callbacks = []


def setup_hotkeys():
    global hotkey_callbacks
    for cb in hotkey_callbacks:
        try:
            keyboard.remove_hotkey(cb)
        except Exception:
            pass
    hotkey_callbacks.clear()
    
    over_hk = settings.get_setting("overlay_hotkey") or "ctrl+f12"
    undo_hk = settings.get_setting("undo_hotkey") or "pause"
    manual_hk = settings.get_setting("manual_hotkey") or "shift+pause"
    
    try:
        cb1 = keyboard.add_hotkey(over_hk, trigger_overlay)
        if cb1:
            hotkey_callbacks.append(cb1)
    except Exception as e:
        logger.error(f"Failed to register overlay hotkey '{over_hk}': {e}")
    
    try:
        cb2 = keyboard.add_hotkey(undo_hk, trigger_undo)
        if cb2:
            hotkey_callbacks.append(cb2)
    except Exception as e:
        logger.error(f"Failed to register undo hotkey '{undo_hk}': {e}")
    
    try:
        cb3 = keyboard.add_hotkey(manual_hk, manual_convert_selection)
        if cb3:
            hotkey_callbacks.append(cb3)
    except Exception as e:
        logger.error(f"Failed to register manual hotkey '{manual_hk}': {e}")
    
    logger.info(f"Hotkeys registered: overlay={over_hk}, undo={undo_hk}, manual={manual_hk}")


# --- Tray Icon ---
def create_image():
    image = Image.new('RGB', (64, 64), color=(18, 22, 25))
    dc = ImageDraw.Draw(image)
    dc.text((6, 18), "LVX", fill=(0, 210, 255))
    return image


def on_tray_click(icon, item):
    if main_window:
        main_window.show_dashboard_signal.emit()


def on_quit(icon, item):
    logger.info("Shutting down Layvix...")
    
    # 1. Unhook keyboard FIRST
    try:
        keyboard.unhook_all()
    except Exception as e:
        logger.error(f"Error unhooking keyboard: {e}")
    
    # 2. Signal all threads to stop
    shutdown_event.set()
    
    # 3. Stop game detector
    try:
        game_detector.stop()
    except Exception:
        pass
    
    # 4. Stop tray icon
    try:
        icon.stop()
    except Exception:
        pass
    
    # 5. Quit Qt app
    try:
        app = QApplication.instance()
        if app:
            app.quit()
    except Exception:
        pass
    
    logger.info("Layvix shutdown complete")


def setup_tray():
    menu = pystray.Menu(
        pystray.MenuItem('لوحة التحكم (Dashboard)', on_tray_click, default=True),
        pystray.MenuItem('إغلاق', on_quit)
    )
    icon = pystray.Icon("Layvix", create_image(), "Layvix - Smart Layout Fixer", menu)
    icon.run()


def on_ui_toggle():
    global enabled
    enabled = not enabled
    state = "enabled" if enabled else "disabled"
    log_activity("تبديل", f"البرنامج الآن: {'مُفعل' if enabled else 'متوقف'}")
    if main_window:
        main_window.update_toggle_button(enabled)


def get_stats():
    return _stats.copy()


# --- Fullscreen callback ---
def on_fullscreen_change(is_fs):
    if is_fs:
        log_activity("وضع اللعبة", "تم تعطيل المصحح (ملء الشاشة)")
    else:
        log_activity("وضع اللعبة", "تم تفعيل المصحح (خروج من ملء الشاشة)")


# --- Main ---
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
    
    # Mouse click clears typing buffer
    try:
        mouse.on_click(lambda: current_word.clear())
    except Exception as e:
        logger.warning(f"Failed to hook mouse: {e}")
    
    # Start game detector (event-driven, zero CPU)
    game_detector.start(on_change_callback=on_fullscreen_change)
    
    # Start tray icon
    tray_thread = threading.Thread(target=setup_tray, daemon=True, name="TrayIcon")
    tray_thread.start()
    
    logger.info("Layvix v1.0.1 started successfully")
    log_activity("بدء", "تم تشغيل Layvix v1.0.1")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
