# Architectural Decision Record (ADR)

**Project:** Layvix AI Pro (v4.0.0)

This document records the foundational engineering decisions made to build a secure, fast, and privacy-respecting enterprise desktop application.

## 1. HashingVectorizer vs CountVectorizer (The 1M Feature Decision)
**The Problem:** Traditional ML pipelines use a dictionary (`CountVectorizer`) built during training. If a user types a word the model hasn't seen (Out-Of-Vocabulary), the matrix shapes mismatch, and the prediction engine crashes or returns junk. Keeping a massive dictionary in RAM is also highly inefficient.

**The Decision:**
In v4.0.0, we migrated to a `HashingVectorizer` with 1,048,576 features. 
- Characters are converted to n-grams, mathematically hashed, and mapped directly into a fixed-size sparse array.
- OOV errors are mathematically impossible.
- Memory consumption remains fixed at ~60MB regardless of how much the user types.

## 2. Memory Isolation & Data Privacy
**The Problem:** Storing the Personal AI model and user dictionary inside the installation directory causes Permission Errors on Windows if installed in `C:\Program Files`, and ruins privacy if the directory is zipped and shared.

**The Decision:**
- Implemented a "Single Source of Truth" path using `%APPDATA%\Layvix\data`.
- The executable remains 100% read-only and static. All logs, settings, and the `layvix_ai_personal.pkl` file are written to `AppData`. This ensures user privacy is maintained across updates.

## 3. Diagnostic Logging (The Black Box Decision)
**The Problem:** Layvix fires thousands of low-level hooks per second. Writing these logs to disk will degrade the user's SSD lifespan and cause massive I/O bottlenecks.

**The Decision:**
- By default, Python's `logging` is set to `INFO`. All `DEBUG` logs (probability arrays, latency scores, individual character hooks) are instantly discarded from RAM.
- We built a **Hot-Swap Black Box Mode**. When enabled from the UI, `configure_blackbox_mode(True)` dynamically shifts the root logger to `DEBUG`.
- A `TimedRotatingFileHandler` is used to limit logs to exactly 7 days, automatically deleting older files to prevent disk bloating.

## 4. UI/UX: The "Power User" Glassmorphic Terminal
**The Problem:** Traditional auto-correct apps hide everything. Developers and fast typists want to *see* what the AI is doing, how much memory it is using, and why it made a decision.

**The Decision:**
- Abandoned minimalist UI for a dense, single-screen **Power User Dashboard**.
- Used React, Vite, and Tailwind CSS injected into a `pywebview` Chromium instance.
- Built a Live Developer Console that streams events via `Server-Sent Events` without database persistence, preventing SSD wear.

## 5. Security Guard (Zero Interference Guarantee)
**The Problem:** If Layvix intercepts a password, it might accidentally "correct" it. If Layvix runs during a competitive game (Valorant, CS:GO), the Windows hooking mechanism adds latency.

**The Decision:**
- `GetGUIThreadInfo` polls the foreground window. If `ES_PASSWORD` is flagged, Layvix hard-flushes its buffer.
- `game_detector.py` hooks into `SetWinEventHook` to detect `EVENT_SYSTEM_FOREGROUND`. If a window enters Exclusive Fullscreen DirectX/Vulkan mode, the `CoreEngine` immediately unhooks itself to guarantee 0.00ms latency impact.
