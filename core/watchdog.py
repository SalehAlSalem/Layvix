"""
watchdog.py — Hook Thread Health Monitor
Monitors the WH_KEYBOARD_LL hook thread via thread liveness probe.
If the thread is dead, it is automatically re-registered.
"""
import threading
import time
from utils.logger import get_logger

logger = get_logger()

class WatchdogThread:
    CHECK_INTERVAL = 5.0  # seconds between liveness polls
    INITIAL_GRACE  = 3.0  # seconds to wait before first check

    def __init__(self, keyboard_hook_manager):
        self._keyboard = keyboard_hook_manager
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="WatchdogThread"
        )

    def start(self):
        self._thread.start()
        logger.info("[WATCHDOG] Hook watchdog started (5s check interval)")

    def stop(self):
        self._stop.set()

    def _run(self):
        time.sleep(self.INITIAL_GRACE)  # Let the hook fully start first
        while not self._stop.is_set():
            kbd_thread = getattr(self._keyboard, '_hook_thread', None)
            is_alive = kbd_thread is not None and kbd_thread.is_alive()
            if not is_alive and not self._stop.is_set():
                logger.critical(
                    "[WATCHDOG] Hook thread dead! Attempting auto-revive..."
                )
                try:
                    self._keyboard.stop()
                    time.sleep(0.1)
                    self._keyboard.start()
                    logger.info("[WATCHDOG] Hook thread revived successfully.")
                except Exception as e:
                    logger.critical(f"[WATCHDOG] Auto-revive FAILED: {e}")
            self._stop.wait(timeout=self.CHECK_INTERVAL)
