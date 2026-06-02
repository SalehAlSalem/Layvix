<p align="center">
  <img src="layvix.ico" alt="Layvix Logo" width="120"/>
</p>

<h1 align="center">Layvix</h1>
<p align="center"><strong>المصحح الذكي للغتين | Smart Bilingual Auto-Corrector</strong></p>
<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-green?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" />
</p>

---

## 🧠 What is Layvix?

**Layvix** is an intelligent desktop application for Windows that automatically detects and corrects text typed in the wrong keyboard layout (Arabic ↔ English). It runs silently in the background and fixes mistakes in real-time — so you never have to delete and retype again.

## ✨ Features

| Feature | Description |
|---|---|
| 🔄 **Auto-Correction** | Detects wrong-layout words and fixes them instantly when you press Space |
| ✋ **Manual Convert** | Select any text and press a hotkey to flip it to the other language |
| ↩️ **Smart Undo** | Undo corrections with a hotkey — the app learns and won't repeat the mistake |
| 📖 **Force Dictionary** | Add custom word mappings to force specific conversions |
| 🖱️ **Ghost-Type Prevention** | Mouse clicks, arrow keys, and timeouts clear the typing buffer |
| ⌨️ **Auto Layout Switch** | After manual conversion, the keyboard layout switches to match the new language |
| 🧵 **Multi-Threaded Engine** | All corrections run in background threads to prevent Windows from killing the keyboard hook |
| 🎨 **Premium Dark UI** | Sleek dark theme with cyan/teal accents powered by Qt6 |
| 📦 **Windows Installer** | Professional Setup.exe with desktop shortcut, Start Menu entry, and auto-start option |

## 🚀 Installation

### Option 1: Download the Installer
Download `Layvix_Setup.exe` from the [Releases](../../releases) page and run it.

### Option 2: Run from Source
```bash
git clone https://github.com/SalehAlSalem/Layvix.git
cd Layvix
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## ⌨️ Default Hotkeys

| Action | Shortcut |
|---|---|
| Manual Convert (selected text) | `Ctrl + Alt + Shift + S` |
| Undo Last Correction | `Ctrl + Alt + Shift + Z` |
| Open Settings / Dictionary | `Ctrl + Alt + Shift + A` |

> All hotkeys are fully customizable from the Settings panel (just click and press your desired key combo).

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **UI Framework:** PyQt6
- **Keyboard Hooks:** `keyboard` library
- **Mouse Detection:** `mouse` library
- **System Tray:** `pystray` + `Pillow`
- **Installer:** Inno Setup
- **Packaging:** PyInstaller

## 📁 Project Structure

```
Layvix/
├── main.py              # Core engine (keyboard hooks, correction logic, hotkeys)
├── ui_main.py           # Settings panel UI (PyQt6)
├── ui_overlay.py        # Floating overlay window
├── dictionary.py        # Arabic & English dictionary validation
├── user_dictionary.py   # User's custom force-conversion dictionary
├── mapper.py            # Character mapping (AR ↔ EN)
├── layout_helper.py     # Keyboard layout detection & switching
├── active_window.py     # Active window detection (exclude apps)
├── settings.py          # Settings management (JSON)
├── ar_words.txt         # Arabic word list
├── en_words.txt         # English word list
├── layvix.ico           # Application icon
├── LayvixSetup.iss      # Inno Setup installer script
└── requirements.txt     # Python dependencies
```

## 📜 License

This project is licensed under the MIT License.

---

<p align="center">Made with ❤️ by <strong>Saleh AlSalem</strong></p>
