# Layvix AI 🐙 (BETA - Under Testing)

Layvix is an advanced, AI-powered background application designed to fix keyboard layout typing mistakes seamlessly and automatically. Have you ever typed a long sentence only to realize your keyboard was on the wrong language layout (e.g., typing Arabic on an English layout or vice versa)? Layvix fixes this in real-time.

**Current Version:** 3.3.0 (Under Testing)

## Features ✨

- **100% Pure AI Engine**: Layvix uses a Machine Learning `SGDClassifier` trained on character N-grams. It does not use static dictionaries. It understands the underlying typing patterns of your language!
- **Real-Time Auto-Correction**: It monitors your keystrokes globally. If it detects you are typing on the wrong layout, it instantly replaces the gibberish word with the correctly typed word and switches your Windows keyboard language automatically!
- **Continuous Learning (Online Learning)**: Layvix learns from your typing habits. If it makes a mistake and you undo it, it learns. If you manually correct a word, it learns. Over time, it perfectly adapts to your specific slang and vocabulary.
- **Smart Selection Correction**: Highlight an entire sentence with your mouse and hit the manual correction hotkey. Layvix will instantly fix the whole sentence in-place without ruining your clipboard!
- **Persistent AI Stats**: The dashboard saves your statistics permanently. See exactly how many words Layvix has fixed for you over its lifetime!
- **Premium GUI**: A gorgeous, dark-themed, glassmorphic UI that allows you to control the background worker, view real-time AI statistics, and see exactly what the AI is learning.
- **Built-in GitHub Updater**: Keep your app up to date directly from the UI without needing to visit the repository.

## How It Works 🧠

Layvix runs quietly in your system tray. 
- Type normally in any application (Browser, Word, Discord, etc.).
- When you press `Space`, Layvix captures the word.
- The AI Engine evaluates the layout probability (e.g., `99.9% this is Arabic typed on an English layout`).
- Layvix deletes the wrong word, types the correct one, and switches your layout so you can continue typing seamlessly.

### Hotkeys ⌨️

You can customize these inside the app's Settings page by pressing your desired key combination directly:

- `Ctrl+Alt+Shift+Z` (Default): **Undo**. If Layvix auto-corrects a word that you actually wanted to keep (e.g., a strange password), press this shortcut. Layvix will immediately undo the correction AND learn that this specific word should not be corrected again.
- `Ctrl+Alt+Shift+S` (Default): **Manual Correct**. If Layvix misses a word (or if you have Auto-Correction turned off), press this combination. Layvix will instantly correct the last typed word AND learn from it. **You can also highlight a full sentence with your mouse and press this shortcut to fix it all at once!**

## Installation 🚀

1. Ensure you have **Python 3.10+** installed.
2. Clone this repository:
   ```bash
   git clone https://github.com/salehalsalem/layvix.git
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Requirements 📦
- `PyQt6` (For the modern UI)
- `scikit-learn` (For the AI Engine)
- `keyboard` (For low-level global hotkeys)
- `pyperclip` (For smart selection correction)
- `numpy`

## Architecture 🏗️
- `main.py`: Orchestrator and global key listener thread.
- `ai_engine.py`: Uses `CountVectorizer` and `SGDClassifier` to predict layout intent.
- `learner.py`: Uses `partial_fit` to incrementally update the model in real-time based on your feedback.
- `gui.py`: The beautiful frontend.
- `game_detector.py`: Detects fullscreen DirectX/Vulkan games and pauses Layvix automatically so it doesn't interfere with your gaming.

## License 📜
MIT License. Feel free to fork and improve!
