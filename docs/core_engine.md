# Core Engine Documentation (OS Level)

This document provides an in-depth technical explanation of Layvix's OS-level interaction layer. The Core Engine is responsible for capturing keystrokes globally, interacting with the Windows clipboard and synthetic input APIs, and orchestrating the AI's predictions into actual text modifications on the user's screen.

## 1. Keyboard Interception (`keyboard_hook.py`)

Layvix relies on low-level Win32 hooks to intercept keystrokes before they reach the active application.

### The Problem with Synthetic Loops
When Layvix corrects a word, it fires synthetic `Backspace` keys and types out the correct word. Without protection, the low-level keyboard hook would intercept these *synthetic* keys as well, feeding them back into the buffer and causing an infinite recursion loop (crashing the app).

### The Solution: Magic Signatures (`dwExtraInfo`)
We use `ctypes` to interface with `user32.dll`. We define a magic constant:
```python
LAYVIX_MAGIC_INFO = 0xABCD
```
Whenever Layvix sends a synthetic keystroke (e.g., a Backspace or a character), it attaches this `LAYVIX_MAGIC_INFO` to the `dwExtraInfo` field of the `KEYBDINPUT` structure.

Inside the `LowLevelKeyboardProc` callback:
```python
def low_level_keyboard_handler(nCode, wParam, lParam):
    kb = cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
    
    # 1. Ignore injected keys to prevent infinite loops!
    if kb.dwExtraInfo == LAYVIX_MAGIC_INFO:
        return CallNextHookEx(hook_id, nCode, wParam, lParam)
```
This guarantees that only true, physical hardware keystrokes are buffered by the engine.

## 2. Text Buffer and Correction Logic (`core_engine.py`)

`CoreEngine` acts as the orchestrator. It maintains a running buffer of characters typed by the user (`self.current_word`).

### Trigger Mechanisms
The engine evaluates the buffer when the user types a **delimiter** (Space, Enter, Punctuation).
```python
if char in [' ', '\n', '.', ',', '!', '?', '\t']:
    word_to_check = "".join(self.current_word)
    self.current_word.clear()
    
    # Validate the word length
    if len(word_to_check) >= settings.get_setting("min_word_length", 3):
        self._check_and_correct(word_to_check)
```

### The Correction Sequence (`_apply_correction`)
If the AI Engine (see `ai_model.md`) flags the word as gibberish (e.g., confidence > threshold), the Core Engine executes the following sequence:

1. **Backspace Deletion:** It calculates the length of the wrong word and sends that exact number of synthetic backspaces.
2. **Keyboard Layout Switch:** It hooks into `user32.PostMessageW` to swap the active window's keyboard layout to the target language (e.g., from EN to AR).
3. **Synthetic Typing:** It converts the corrected string into individual Unicode keystrokes and sends them sequentially with a micro-delay.
```python
# From os_interact.py -> send_unicode_string
for char in text:
    # Build INPUT array for KEYEVENTF_UNICODE
    # Apply LAYVIX_MAGIC_INFO to bypass the hook
    user32.SendInput(...)
    time.sleep(0.005) # Crucial to prevent buffer overflow in Chromium/VSCode
```

## 3. Security and Context Awareness (`security_guard.py`)

Layvix must never interfere with sensitive input or video games.

### Password Fields & Secure Contexts
The engine constantly polls the foreground window. Using `GetGUIThreadInfo`, it checks if the user's cursor is currently inside an input field marked with `ES_PASSWORD`. If `is_secure_context()` returns `True`, the `CoreEngine` immediately flushes the buffer and ignores all typing.

### Game Detection (Fullscreen Exclusive)
We maintain a list of `excluded_apps` (e.g., `valorant.exe`). Furthermore, `game_detector.py` uses `SetWinEventHook` to detect when a process enters DirectX/Vulkan Exclusive Fullscreen mode. If a game is detected, the AI prediction pipeline is completely bypassed to ensure 0.00ms latency impact on the user's gaming experience.
