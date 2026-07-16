import threading
import ctypes
from dataclasses import dataclass
from typing import Optional
from ctypes import wintypes
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from core.keyboard_hook import KeyboardHookManager
from core.security_guard import is_secure_context
from core import os_interact
from ai import ai_engine
from utils.logger import get_logger
from utils import settings

logger = get_logger()
user32 = ctypes.windll.user32

# WinEvent Constants
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_FOCUS = 0x8005
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002

@dataclass
class CorrectionResult:
    original_word: str
    corrected_word: str
    word_length: int
    predicted_layout: str
    confidence: float
    correction_applied: bool
    latency_ms: int
    delimiter_vk: Optional[int]

class CoreEngine:
    def __init__(self):
        self.keyboard = KeyboardHookManager()
        self.keyboard.on_key_down = self._handle_key_down
        self.keyboard.on_mouse_click = self._handle_mouse_click
        self.current_buffer = []
        self.last_typed_word = ""
        self.last_typed_layout = ""
        self.last_delimiter = 0x20
        self.last_correction = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        self.is_secure = False
        self.lock = threading.RLock()
        
        # State
        self.app_enabled = settings.get_setting("app_enabled", True)
        self.threshold = settings.get_setting("ai_confidence_threshold", 0.85)
        self.last_correction: Optional[CorrectionResult] = None
        self.picker_mode_active = False
        self.picker_result = None
        self.picker_timer = None

        
        # Hotkeys
        self.hotkeys = {}
        self.update_hotkeys()
        
        # Dual Focus Detection Hooks
        self.win_event_hook_fg = None
        self.win_event_hook_focus = None
        self.win_event_thread_id = None
        
        self._WinEventProcType = ctypes.WINFUNCTYPE(
            None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND,
            wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD
        )
        self._fg_cb = self._WinEventProcType(self._on_foreground_change)
        self._focus_cb = self._WinEventProcType(self._on_focus_change)

    def start(self):
        self.keyboard.start()
        
        def _run_focus_hooks():
            import pythoncom
            pythoncom.CoInitialize()
            try:
                self.win_event_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
                
                self.win_event_hook_fg = user32.SetWinEventHook(
                    EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, 0,
                    self._fg_cb, 0, 0, WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS
                )
                
                self.win_event_hook_focus = user32.SetWinEventHook(
                    EVENT_OBJECT_FOCUS, EVENT_OBJECT_FOCUS, 0,
                    self._focus_cb, 0, 0, WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS
                )
                
                logger.info("[CORE] Dual Focus Detectors started")
                msg = wintypes.MSG()
                while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
            finally:
                pythoncom.CoUninitialize()
                
        threading.Thread(target=_run_focus_hooks, daemon=True, name="FocusHooksThread").start()
        self._recheck_security()

    def stop(self):
        self.keyboard.stop()
        if self.win_event_hook_fg:
            user32.UnhookWinEvent(self.win_event_hook_fg)
        if self.win_event_hook_focus:
            user32.UnhookWinEvent(self.win_event_hook_focus)
        if self.win_event_thread_id:
            user32.PostThreadMessageW(self.win_event_thread_id, 0x0012, 0, 0)
            
        self.executor.shutdown(wait=False)
        self._flush_buffer()

    def set_auto_mode(self, enabled: bool):
        with self.lock:
            self.app_enabled = enabled
            logger.info(f"[CORE] Auto mode set to {enabled}")
            if hasattr(self, 'on_status_change') and callable(self.on_status_change):
                self.on_status_change("active" if enabled else "paused")

    def update_hotkeys(self):
        with self.lock:
            self.hotkeys = {
                "undo": self._parse_hotkey(settings.get_setting("undo_hotkey", "ctrl+alt+shift+z")),
                "manual": self._parse_hotkey(settings.get_setting("manual_hotkey", "ctrl+alt+shift+s")),
                "overlay": self._parse_hotkey(settings.get_setting("overlay_hotkey", "ctrl+alt+shift+a"))
            }
            logger.info("[CORE] Hotkeys updated")

    def _parse_hotkey(self, hotkey_str):
        if not hotkey_str: return None
        parts = hotkey_str.lower().split('+')
        modifiers = {
            'ctrl': 0x11, 'alt': 0x12, 'shift': 0x10, 'win': 0x5B, 'windows': 0x5B
        }
        req_mods = [modifiers[p] for p in parts if p in modifiers]
        main_keys = [p for p in parts if p not in modifiers]
        
        if not main_keys: return None
        
        # Simple mapping for a-z, 0-9
        main_char = main_keys[-1]
        vk = 0
        if len(main_char) == 1 and 'a' <= main_char <= 'z':
            vk = ord(main_char.upper())
        elif len(main_char) == 1 and '0' <= main_char <= '9':
            vk = ord(main_char)
            
        if vk == 0: return None
        return {"vk": vk, "mods": req_mods}

    def _check_hotkey(self, vk, hotkey_dict):
        if not hotkey_dict: return False
        if vk != hotkey_dict["vk"]: return False
        
        # Check if all required modifiers are held
        for mod in hotkey_dict["mods"]:
            if not (ctypes.windll.user32.GetAsyncKeyState(mod) & 0x8000):
                return False
                
        # Check if any OTHER modifiers are held (strict matching)
        all_mods = [0x11, 0x12, 0x10, 0x5B]
        for mod in all_mods:
            if mod not in hotkey_dict["mods"]:
                if ctypes.windll.user32.GetAsyncKeyState(mod) & 0x8000:
                    return False
        return True

    def _recheck_security(self):
        with self.lock:
            self.is_secure = is_secure_context()
            if self.is_secure:
                logger.info("[SECURITY] Secure context detected (e.g. Password). Bypassing engine.")

    def _flush_buffer(self):
        with self.lock:
            self.current_buffer.clear()

    def start_picker_mode(self):
        with self.lock:
            if self.picker_mode_active:
                return
            self.picker_mode_active = True
            self.picker_result = None
            
            os_interact.set_global_cursor_crosshair()
            logger.info("[PICKER] Magic picker started.")
            
            # Start watchdog timer to auto-cancel after 15 seconds
            def _watchdog():
                import time
                time.sleep(15)
                with self.lock:
                    if self.picker_mode_active:
                        self.picker_mode_active = False
                        self.picker_result = "unknown"
                        os_interact.restore_global_cursor()
                        logger.info("[PICKER] Auto-cancelled due to timeout.")
            
            self.picker_timer = threading.Thread(target=_watchdog, daemon=True)
            self.picker_timer.start()

    def _on_foreground_change(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        # Removed _flush_buffer() due to race condition with fast typing after focus change
        self._recheck_security()

    def _on_focus_change(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        # Removed _flush_buffer() due to race condition with fast typing after focus change
        self._recheck_security()

    def _handle_mouse_click(self, x, y):
        with self.lock:
            if self.picker_mode_active:
                try:
                    # Capture the window under the mouse
                    pt = wintypes.POINT(x, y)
                    hwnd = user32.WindowFromPoint(pt)
                    
                    # Get thread process ID
                    from core.security_guard import get_process_name_from_hwnd
                    process_name = get_process_name_from_hwnd(hwnd)
                    
                    if process_name and process_name.lower() not in ["layvixproportable.exe", "layvix.exe", "explorer.exe", "applicationframehost.exe"]:
                        self.picker_result = process_name.lower()
                        
                        # Add to exclusions
                        excluded = settings.get_setting("excluded_apps", [])
                        if self.picker_result not in excluded:
                            excluded.append(self.picker_result)
                            settings.set_setting("excluded_apps", excluded)
                            logger.info(f"[PICKER] Added {self.picker_result} to exclusions")
                    else:
                        logger.info("[PICKER] Ignored click on system/internal app")
                        self.picker_result = process_name.lower() if process_name else "unknown"
                    
                except Exception as e:
                    logger.error(f"[PICKER] Failed: {e}")
                    self.picker_result = "unknown"
                finally:
                    self.picker_mode_active = False
                    os_interact.restore_global_cursor()
                    return True # Suppress the click so it doesn't affect the target app

        # Mouse click means cursor moved. Must clear buffer.
        self._flush_buffer()
        return False

    def _is_modifier_held(self):
        for vk in (0x11, 0x12, 0x5B, 0x5C):   # Ctrl, Alt, LWin, RWin
            if ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000:
                return True
        return False

    def _perform_undo(self):
        if not self.last_correction:
            return
            
        orig = self.last_correction.original_word
        corr = self.last_correction.corrected_word
        delimiter_vk = self.last_correction.delimiter_vk
        
        logger.info(f"[CORE] Undo triggered: reverting word_length={len(corr)}")
        
        # Wait for the user to lift their fingers off Ctrl+Alt+Shift
        os_interact.wait_for_modifiers()
        
        # Erase the corrected word (plus the trailing space/delimiter if auto-corrected)
        num_backspaces = len(corr)
        if delimiter_vk:
            num_backspaces += 1
            
        os_interact.send_backspaces(num_backspaces)
        
        # Inject the original word
        os_interact.send_unicode_string(orig)
        
        # Restore the trailing space/delimiter if there was one
        if delimiter_vk:
            os_interact.send_virtual_key(delimiter_vk)
        
        # Send to Learner to learn from mistake
        from ai import learner
        learner.learn_from_undo(orig, self.last_correction.predicted_layout) 
        
        self.last_correction = None
        self.current_buffer.clear()
        
        from utils import settings
        settings.increment_stat("corrections_undone")

    def _perform_manual_correct(self):
        logger.info("[CORE] Manual correct triggered")
        # Wait for the user to lift their fingers off Ctrl+Alt+Shift
        os_interact.wait_for_modifiers()
        
        is_selected = False
        
        # 1. Try to read selected text
        selected_text = os_interact.get_selected_text()
        if selected_text and len(selected_text.strip()) > 0:
            word = selected_text
            is_selected = True
            is_active_word = True # No trailing space needed
        # 2. Fallback to current buffer
        elif self.current_buffer:
            word = "".join(self.current_buffer)
            self.current_buffer.clear()
            is_active_word = True
        # 3. Fallback to last typed word
        elif self.last_typed_word:
            word = self.last_typed_word
            is_active_word = False
        else:
            logger.info("[MANUAL] No word available to correct.")
            return
            
        # Determine the alphabet of the word to know the correct mapping direction
        import re
        if re.search(r'[a-zA-Z]', word):
            typed_layout = 'en'
            target_layout = 'ar'
            correction_direction = 'en_to_ar'
        elif re.search(r'[\u0600-\u06FF]', word):
            typed_layout = 'ar'
            target_layout = 'en'
            correction_direction = 'ar_to_en'
        else:
            logger.info(f"[MANUAL] Word '{word}' contains no identifiable alphabet.")
            return

        from tools.mapper import convert_word
        corrected = convert_word(word, correction_direction)

        if corrected and corrected != word:
            logger.info(f"[MANUAL] Correcting word_length={len(word)} target={target_layout} selected={is_selected}")
            
            if is_selected:
                # If text is already selected, injecting characters will naturally overwrite it.
                # No backspaces needed.
                os_interact.wait_for_modifiers()
                os_interact.send_unicode_string(corrected)
            else:
                # Send backspaces to delete the uncorrected word. 
                # If they had hit space (is_active_word = False), we must also delete that space/enter.
                num_backspaces = len(word)
                if not is_active_word:
                    num_backspaces += 1
                    
                logger.info(f"[MANUAL] Correcting '{word}' to '{corrected}'")
                os_interact.wait_for_modifiers()
                os_interact.send_backspaces(num_backspaces)
                import time
                time.sleep(0.02)
                os_interact.send_unicode_string(corrected)
                
                # Re-send the delimiter ONLY if they had already hit space/enter
                if not is_active_word:
                    os_interact.send_virtual_key(self.last_delimiter)
                
            self.last_typed_word = corrected
            self.last_typed_layout = target_layout
            
            from utils import settings
            if settings.get_setting("auto_switch_language", True):
                os_interact.switch_keyboard_layout(target_layout)
                
            self.last_correction = CorrectionResult(
                original_word=word,
                corrected_word=corrected,
                word_length=len(word),
                predicted_layout=target_layout,
                confidence=1.0,
                correction_applied=True,
                latency_ms=0,
                delimiter_vk=None
            )
            settings.increment_stat("manual_corrections")
            
            # Send to Learner to learn this manual correction
            from ai import learner
            learner.learn_from_manual(word, typed_layout, target_layout)
        else:
            logger.info(f"[MANUAL] Could not convert '{word}'")

    def _show_overlay(self):
        logger.info("[CORE] Overlay hotkey triggered")
        import api
        if api.app_window:
            api.app_window.restore()
            api.app_window.show()

    def _handle_key_down(self, vk, scan, char_str):
        with self.lock:
            
            # ── 0. Hotkey Checking ────────────────────────────────────────────
            if self._check_hotkey(vk, self.hotkeys.get("undo")):
                threading.Thread(target=self._perform_undo, daemon=True).start()
                return True # Suppress the hotkey
                
            if self._check_hotkey(vk, self.hotkeys.get("manual")):
                threading.Thread(target=self._perform_manual_correct, daemon=True).start()
                return True
                
            if self._check_hotkey(vk, self.hotkeys.get("overlay")):
                threading.Thread(target=self._show_overlay, daemon=True).start()
                return True

            # ── 1. App Disabled / Secure context → full pass-through ──────────
            if not self.app_enabled or self.is_secure:
                return False

            # ── 2. Navigation Keys → Clear buffer ─────────────────────────────
            # Esc also cancels picker mode
            if vk == 0x1B and self.picker_mode_active:
                self.picker_mode_active = False
                self.picker_result = "unknown"
                os_interact.restore_global_cursor()
                logger.info("[PICKER] Cancelled by Esc key.")
                return True # suppress Esc

            # Left, Up, Right, Down, Esc, Del, Home, End, PgUp, PgDn, Tab
            if vk in (0x25, 0x26, 0x27, 0x28, 0x1B, 0x2E, 0x24, 0x23, 0x21, 0x22, 0x09):
                self._flush_buffer()
                return False

            # ── 3. Shortcut combos (Ctrl/Alt/Win held) → pass-through ─────────
            if self._is_modifier_held():
                if self.current_buffer:
                    self._flush_buffer()
                return False

            # ── 4. Backspace → pop buffer ─────────────────────────────────────
            if vk == 0x08:
                if self.current_buffer:
                    self.current_buffer.pop()
                else:
                    self.last_typed_word = ""
                    self.last_typed_layout = ""
                return False

            # ── 5. Word-commit trigger: Space or Enter ─────────────────────────
            if vk in (0x20, 0x0D):
                if not self.current_buffer:
                    return False

                word = "".join(self.current_buffer)
                self.current_buffer.clear()
                
                # Check min word length for auto-correction
                if len(word) < settings.get_setting("min_word_length", 2):
                    self.last_typed_word = word
                    self.last_delimiter = vk
                    logger.info(f"[PASS] skipped word_length={len(word)} (below min_word_length)")
                    return False

                self.last_typed_word = word
                self.last_delimiter = vk

                # Basic heuristic: Ignore extreme repetitive gibberish like 'hhhhh', 'loooool'
                import re
                is_gibberish = bool(re.search(r'(.)\1{4,}', word.lower()))
                
                if is_gibberish:
                    logger.info(f"[PASS] skipped word_length={len(word)} (repetitive gibberish)")
                    return False

                # Count valid words only (not gibberish) for analytics
                settings.track_word_typed()

                # Latin word → ask AI if it was meant as Arabic, or vice-versa
                import time
                start_t = time.perf_counter()
                
                try:
                    future = self.executor.submit(ai_engine.predict_layout, word)
                    predicted_layout, confidence = future.result(timeout=0.030)
                except FuturesTimeoutError:
                    logger.warning(f"[TIMEOUT] Prediction for word_length={len(word)} took > 30ms. Aborting to save Hook.")
                    return False
                except Exception as e:
                    logger.error(f"[ERROR] Prediction failed: {e}")
                    return False

                end_t = time.perf_counter()
                latency_ms = int((end_t - start_t) * 1000)
                self.last_typed_layout = predicted_layout
                
                # Check dictionary first
                from utils import user_dictionary
                if word in user_dictionary.user_dict:
                    corrected = user_dictionary.user_dict[word]
                    self._apply_correction(word, corrected, 1.0, "dict", latency_ms=latency_ms)
                    # Guard: small delay ensures unicode string is fully sent before space arrives
                    threading.Thread(target=lambda: (__import__('time').sleep(0.05), os_interact.send_virtual_key(vk))).start()
                    return True # Suppress the original space/enter

                if confidence >= self.threshold:
                    from tools.mapper import convert_word
                    corrected = None
                    if predicted_layout == 'ar':
                        corrected = convert_word(word, 'en_to_ar')
                    elif predicted_layout == 'en':
                        corrected = convert_word(word, 'ar_to_en')
                        
                    if corrected and corrected != word:
                        self._apply_correction(word, corrected, confidence, predicted_layout, delimiter_vk=vk, latency_ms=latency_ms)
                        # Guard: small delay ensures unicode string is fully sent before space arrives
                        threading.Thread(target=lambda: (__import__('time').sleep(0.05), os_interact.send_virtual_key(vk))).start()
                        return True # Suppress the original space/enter
                    else:
                        logger.info(f"[PASS] kept word_length={len(word)} layout={predicted_layout} conf={confidence:.0%}")
                else:
                    logger.info(f"[PASS] kept word_length={len(word)} layout={predicted_layout} conf={confidence:.0%}")

                return False

            # ── 6. Regular printable char → echo immediately, buffer for later ──
            if char_str:
                # Fix Ligature Desync (e.g. 'b' -> 'لا' which is 2 chars)
                self.current_buffer.extend(list(char_str))
                return False

        return False

    def _apply_correction(self, word, corrected, confidence, predicted_layout, delimiter_vk=None, latency_ms=0):
        logger.info(f"[CORRECT] word_length={len(word)} layout={predicted_layout} conf={confidence:.0%} latency={latency_ms}ms")
        self.last_correction = CorrectionResult(
            original_word=word,
            corrected_word=corrected,
            word_length=len(word),
            predicted_layout=predicted_layout,
            confidence=confidence,
            correction_applied=True,
            latency_ms=latency_ms,
            delimiter_vk=delimiter_vk
        )
        
        # In echo-then-correct, we backspace the original word
        os_interact.wait_for_modifiers()
        os_interact.send_backspaces(len(word))
        import time
        time.sleep(0.02) # Ensure backspaces are processed before new text
        os_interact.send_unicode_string(corrected)
        
        if settings.get_setting("auto_switch_language", True) and predicted_layout in ('en', 'ar'):
            os_interact.switch_keyboard_layout(predicted_layout)
        
        # Track this correction for analytics leaderboard
        settings.track_correction_word(word, corrected)
        
        # Background learning
        if predicted_layout in ('en', 'ar'):
            from ai import learner
            learner.learn_from_accepted(word, predicted_layout)
            
        settings.increment_stat("total_corrections")
        settings.increment_stat("corrections_today")
        settings.update_average_latency(latency_ms)
