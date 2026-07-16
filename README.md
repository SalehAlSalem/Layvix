<div align="center">
  <img src="assets/github/logo.png" alt="Layvix Logo" width="150" />
  <h1>Layvix Pro</h1>
  <p><b>An ultra-fast, AI-powered smart keyboard layout auto-corrector for Windows.</b></p>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/Windows-10%20%7C%2011-blue?logo=windows" />
  <img src="https://img.shields.io/badge/version-v4.1.0-success" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" />
</div>

<br />

<div align="center">
  <img src="assets/github/dashboard.png" alt="Layvix Dashboard" width="800" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</div>

## 💡 What is Layvix?

Have you ever typed a long Arabic sentence only to realize your keyboard was in English? Or vice-versa? **Layvix** is an intelligent, zero-lag background service that detects gibberish typing caused by incorrect keyboard layouts. It automatically corrects the text *and* switches your keyboard layout on the fly. 

Designed for speed and security, Layvix runs completely offline using a lightweight AI model, ensuring your keystrokes never leave your machine.

---

## ✨ Key Features

- **🚀 Sub-10ms Latency:** Engineered for gamers and rapid typists. Intercepts and corrects keystrokes without any noticeable delay.
- **🧠 Local AI Engine:** Utilizes an offline Scikit-Learn `PassiveAggressiveClassifier` that continuously learns from your personal dictionary and typing habits.
- **🔒 Security Context Awareness:** Automatically pauses itself when it detects secure inputs (e.g., password fields) or full-screen gaming to prevent interference.
- **⚡ Retroactive Correction:** Select gibberish text you already typed, press a hotkey, and Layvix will translate it to the correct layout instantly.
- **🔄 Auto-Updater:** Seamless GitHub integration. It checks for updates on startup, downloads them in the background, and seamlessly hot-swaps the executable.
- **🎨 Modern React Dashboard:** A beautiful, dark-themed control center built with React and Vite, communicating via a fast local API.

---

## 🏗️ Architecture & Tech Stack

Layvix is built as a hybrid application, combining the raw performance of Python's OS-level hooks with a modern web UI:

1. **Core Engine (Python):** Uses `pynput` and `ctypes` to hook into the Windows event loop, capturing raw `WM_KEYDOWN` events globally before they reach the OS.
2. **Prediction Model:** A highly optimized N-gram frequency model + Scikit-Learn classifier that determines the probability of text being Arabic vs. English gibberish.
3. **Local API (FastAPI/Uvicorn):** A lightweight asynchronous server that acts as a bridge between the core engine and the frontend.
4. **Frontend (React/Vite):** A stunning, responsive control center wrapped inside a PyWebView container for a native desktop feel.
5. **Compiler (PyInstaller):** Bundled into a single, portable `.exe` file requiring zero installation.

---

## 🚀 Installation & Usage

1. Go to the [Releases](../../releases) page.
2. Download the latest `LayvixProPortable.exe`.
3. Run the executable. It will silently appear in your System Tray.
4. Right-click the tray icon and select **Open Control Center** to configure your hotkeys, dictionary, and exclusions.

> **Note:** Layvix is a portable executable. No installation is required.

---

## 🛠️ Building from Source

If you want to compile Layvix yourself:

### 1. Clone the repository
```bash
git clone https://github.com/SalehAlSalem/Layvix.git
cd Layvix
```

### 2. Set up the Python Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Build the Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Compile the Executable
```bash
venv\Scripts\pyinstaller.exe LayvixProPortable.spec --clean
```
Your compiled app will be available in the `dist/` directory.

---

## 📝 License
This project is licensed under the MIT License.
