import sys
import os
import ctypes
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QFrame, QGraphicsDropShadowEffect,
    QScrollArea, QLineEdit, QListWidget, QSystemTrayIcon, QMenu, QGridLayout
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPoint, QSize, QPropertyAnimation, QEasingCurve, 
    QTimer, QRect, pyqtProperty
)
from PyQt6.QtGui import (
    QColor, QIcon, QFont, QFontDatabase, QPainter, QPainterPath, 
    QPen, QBrush, QAction, QPixmap
)

import settings
import user_dictionary
import learner
from i18n import t, set_language

VERSION = "1.0.0"

# --- Theme & Colors ---
class Theme:
    BG_BASE = "#0B1320"      # Dark navy blue background from logo
    BG_CARD = "#121C2F"      # Lighter navy for cards
    BG_CARD_HOVER = "#18253B" # Slightly lighter for hover
    
    PRIMARY = "#48C9B0"      # Bright Teal/Cyan from the octopus
    PRIMARY_HOVER = "#5BD6C0" # Lighter cyan for hover
    PRIMARY_GLOW = "rgba(72, 201, 176, 0.4)"
    
    ACCENT = "#2BDDBE"       # Vibrant cyan accent
    ACCENT_GLOW = "rgba(43, 221, 190, 0.4)"
    
    TEXT_MAIN = "#FFFFFF"
    TEXT_MUTED = "#87A0B3"   # Bluish gray for muted text
    
    DANGER = "#FF6B6B"
    SUCCESS = "#48C9B0"      # Matching primary for success

    BORDER = "#1E2C42"       # Navy border
    
    FONT_FAMILY = "Segoe UI"

# --- Custom Widgets ---

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {Theme.BG_BASE};")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(0)
        
        # Logo / Title
        self.title_label = QLabel(t("title"))
        self.title_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; font-size: 14px; font-family: {Theme.FONT_FAMILY};")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Window Controls
        self.min_btn = self._create_btn("—", self.window().showMinimized)
        self.max_btn = self._create_btn("□", self.toggle_maximize)
        self.close_btn = self._create_btn("✕", self.window().hide, hover_color=Theme.DANGER)
        
        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(self.close_btn)
        
        # Dragging mechanics
        self.start_pos = None

    def toggle_maximize(self):
        from PyQt6.QtWidgets import QApplication
        if not hasattr(self, 'normal_geometry'):
            self.normal_geometry = self.window().geometry()
            
        current_geo = self.window().geometry()
        max_geo = QApplication.primaryScreen().availableGeometry()
        
        if current_geo == max_geo:
            self.window().setGeometry(self.normal_geometry)
        else:
            self.normal_geometry = self.window().geometry()
            self.window().setGeometry(max_geo)

    def _create_btn(self, text, callback, hover_color="#333340"):
        btn = QPushButton(text)
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {hover_color};
                color: {Theme.TEXT_MAIN};
            }}
        """)
        return btn

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.window().move(self.window().pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None


class ToggleSwitch(QWidget):
    toggled_signal = pyqtSignal(bool)
    
    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 24)
        self.checked = checked
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._thumb_pos = 24 if self.checked else 2
        
        self.anim = QPropertyAnimation(self, b"thumb_pos")
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.setDuration(150)
        
    @pyqtProperty(int)
    def thumb_pos(self):
        return self._thumb_pos
        
    @thumb_pos.setter
    def thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()
        
    def set_on(self, val):
        self.checked = val
        self.anim.setEndValue(24 if self.checked else 2)
        self.anim.start()
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.checked = not self.checked
            self.anim.setEndValue(24 if self.checked else 2)
            self.anim.start()
            self.toggled_signal.emit(self.checked)
            
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Track
        track_rect = self.rect()
        if self.checked:
            p.setBrush(QColor(Theme.PRIMARY))
        else:
            p.setBrush(QColor(Theme.BORDER))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(track_rect, 12, 12)
        
        # Thumb
        thumb_rect = QRect(self._thumb_pos, 2, 20, 20)
        p.setBrush(QColor(Theme.TEXT_MAIN))
        # Draw shadow
        p.setPen(QColor(0, 0, 0, 50))
        p.drawRoundedRect(thumb_rect.translated(0, 1), 10, 10)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(thumb_rect, 10, 10)


class SidebarBtn(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 15, 0)
        
        self.indicator = QWidget()
        self.indicator.setFixedSize(4, 24)
        self.indicator.setStyleSheet("background: transparent; border-radius: 2px;")
        self.layout.addWidget(self.indicator)
        
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setStyleSheet(f"font-size: 18px; color: {Theme.TEXT_MUTED}; background: transparent;")
        self.layout.addWidget(self.icon_lbl)
        
        self.text_lbl = QLabel(text)
        self.text_lbl.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 14px; font-weight: bold; color: {Theme.TEXT_MUTED}; background: transparent;")
        self.layout.addWidget(self.text_lbl)
        
        self.layout.addStretch()
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_CARD_HOVER};
            }}
        """)
        
    def setChecked(self, val):
        super().setChecked(val)
        if val:
            self.indicator.setStyleSheet(f"background: {Theme.PRIMARY}; border-radius: 2px;")
            self.icon_lbl.setStyleSheet(f"font-size: 18px; color: {Theme.PRIMARY}; background: transparent;")
            self.text_lbl.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 14px; font-weight: bold; color: {Theme.TEXT_MAIN}; background: transparent;")
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.BG_CARD};
                    border: none;
                    border-radius: 8px;
                }}
            """)
        else:
            self.indicator.setStyleSheet("background: transparent; border-radius: 2px;")
            self.icon_lbl.setStyleSheet(f"font-size: 18px; color: {Theme.TEXT_MUTED}; background: transparent;")
            self.text_lbl.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 14px; font-weight: bold; color: {Theme.TEXT_MUTED}; background: transparent;")
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background: {Theme.BG_CARD_HOVER};
                }}
            """)

# --- Visualizers ---
class StatCard(QFrame):
    def __init__(self, title, value, icon, color, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {Theme.BG_CARD};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        self.setFixedHeight(100)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        left = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px;")
        left.addWidget(title_lbl)
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 24px; font-weight: bold; font-family: {Theme.FONT_FAMILY};")
        left.addWidget(self.val_lbl)
        layout.addLayout(left)
        layout.addStretch()
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 32px; color: {color};")
        layout.addWidget(icon_lbl)
        
    def set_value(self, val):
        self.val_lbl.setText(str(val))


class AIActivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)
        self.setStyleSheet(f"""
            QWidget#AIActivity {{
                background-color: #0a0a0f;
                border-radius: 8px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        self.setObjectName("AIActivity")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # System Status Panel
        status_panel = QFrame()
        status_panel.setFixedWidth(220)
        status_panel.setStyleSheet(f"background-color: {Theme.BG_BASE}; border-radius: 8px; padding: 15px; border: none;")
        s_layout = QVBoxLayout(status_panel)
        s_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel("📡 حالة النظام والمحرك")
        lbl.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; font-size: 14px; border: none;")
        s_layout.addWidget(lbl)
        
        self.sys_info = QLabel("جاري التحميل...")
        self.sys_info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; border: none; line-height: 1.8; margin-top: 10px;")
        self.sys_info.setWordWrap(True)
        s_layout.addWidget(self.sys_info)
        s_layout.addStretch()
        
        main_layout.addWidget(status_panel)
        
        # Log terminal
        from PyQt6.QtWidgets import QTextEdit
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: #00ffcc;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: none;
            }}
        """)
        main_layout.addWidget(self.console)
        
        from logger import get_data_dir
        self.log_path = os.path.join(get_data_dir(), "layvix.log")
        self.last_size = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_logs)
        self.timer.timeout.connect(self.update_sys_info)
        self.timer.start(500)
        
        self.console.append("Layvix Pro Engine [Live AI Monitor]")
        self.console.append("-" * 50)
        
        self.update_sys_info()

    def update_sys_info(self):
        try:
            import settings, os, subprocess
            
            # Throttle RAM check to avoid UI lag (update every 2 seconds instead of 500ms)
            if not hasattr(self, '_ram_tick'): self._ram_tick = 0
            if not hasattr(self, '_last_ram'): self._last_ram = 0.0
            
            self._ram_tick += 1
            if self._ram_tick >= 4:
                self._ram_tick = 0
                try:
                    # CREATE_NO_WINDOW = 0x08000000 to prevent flashing consoles
                    out = subprocess.check_output(f'tasklist /FI "PID eq {os.getpid()}" /NH /FO CSV', shell=True, creationflags=0x08000000).decode('utf-8', errors='ignore')
                    mem_str = out.strip().split(',')[-1].replace('"', '').replace('K', '').replace('k', '').replace(' ', '').replace(',', '').replace('.', '')
                    self._last_ram = float(mem_str) / 1024
                except:
                    pass
            mem_mb = self._last_ram
            
            model_type = "Layvix Pro (Personal)" if settings.get_setting("use_personal_model") else "Base AI Model"
            words_count = 0
            dict_path = os.path.join(settings.get_data_dir(), "user_dict.json")
            if os.path.exists(dict_path):
                import json
                with open(dict_path, 'r', encoding='utf-8') as f:
                    words_count = len(json.load(f))
                    
            # If not explicitly set to False, it is Active
            sys_mode = "🟢 يعمل الآن (Active)" if settings.get_setting("app_enabled") is not False else "💤 نائم (Paused)"
            
            status_text = (
                f"🧠 <b>المودل الحالي:</b><br>{model_type}<br><br>"
                f"📚 <b>حجم الدستور اللغوي:</b><br>{words_count} كلمة<br><br>"
                f"⚡ <b>الذاكرة المستهلكة (RAM):</b><br>{mem_mb:.1f} ميجابايت<br><br>"
                f"🚀 <b>حالة الخدمة:</b><br>{sys_mode}"
            )
            self.sys_info.setText(status_text)
        except:
            pass

    def read_logs(self):
        try:
            import os
            if not os.path.exists(self.log_path): return
            current_size = os.path.getsize(self.log_path)
            if current_size < self.last_size:
                self.last_size = 0
            if current_size > self.last_size:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    f.seek(self.last_size)
                    new_lines = f.readlines()
                    self.last_size = current_size
                    for line in new_lines:
                        if "[AI]" in line or "[LEARN]" in line or "[CORRECT]" in line or "[SKIP]" in line:
                            clean_line = line.split(" - ")[-1].strip() if " - " in line else line.strip()
                            self.console.append(clean_line)
                            
                    # Auto-scroll
                    from PyQt6.QtWidgets import QScrollBar
                    sb = self.console.verticalScrollBar()
                    sb.setValue(sb.maximum())
        except:
            pass

    def pulse(self, text):
        pass
        # We can add animation here later

class HotkeyInput(QPushButton):
    def __init__(self, current_hk, parent=None):
        super().__init__(current_hk, parent)
        self.current_hk = current_hk
        self.listening = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_BASE};
                color: {Theme.PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 5px;
                text-align: left;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                border: 1px solid {Theme.PRIMARY_GLOW};
            }}
        """)
        self.clicked.connect(self._start_listening)
        
    def _start_listening(self):
        self.listening = True
        self.setText(t("press_shortcut"))
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_BASE};
                color: {Theme.ACCENT};
                border: 1px solid {Theme.ACCENT};
                border-radius: 6px;
                padding: 5px;
                text-align: left;
                padding-left: 10px;
            }}
        """)
        
    def keyPressEvent(self, event):
        if not self.listening:
            super().keyPressEvent(event)
            return
            
        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return # Wait for actual key
            
        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier: parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier: parts.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier: parts.append("shift")
        
        # Mapping Qt keys to keyboard module strings
        key_name = ""
        if key == Qt.Key.Key_Pause: key_name = "pause"
        elif key == Qt.Key.Key_F1: key_name = "f1"
        elif key == Qt.Key.Key_F2: key_name = "f2"
        elif key == Qt.Key.Key_F3: key_name = "f3"
        elif key == Qt.Key.Key_F4: key_name = "f4"
        elif key == Qt.Key.Key_F5: key_name = "f5"
        elif key == Qt.Key.Key_F6: key_name = "f6"
        elif key == Qt.Key.Key_F7: key_name = "f7"
        elif key == Qt.Key.Key_F8: key_name = "f8"
        elif key == Qt.Key.Key_F9: key_name = "f9"
        elif key == Qt.Key.Key_F10: key_name = "f10"
        elif key == Qt.Key.Key_F11: key_name = "f11"
        elif key == Qt.Key.Key_F12: key_name = "f12"
        elif key == Qt.Key.Key_Insert: key_name = "insert"
        elif key == Qt.Key.Key_Home: key_name = "home"
        elif key == Qt.Key.Key_PageUp: key_name = "page up"
        elif key == Qt.Key.Key_PageDown: key_name = "page down"
        elif key == Qt.Key.Key_End: key_name = "end"
        else:
            text = event.text().lower()
            if text: key_name = text
            
        if not key_name:
            # Fallback
            key_name = event.text()
            
        if key_name:
            parts.append(key_name)
            
        final_hk = "+".join(parts)
        self.current_hk = final_hk
        self.setText(final_hk)
        self.listening = False
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_BASE};
                color: {Theme.PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 5px;
                text-align: left;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                border: 1px solid {Theme.PRIMARY_GLOW};
            }}
        """)

# --- Main Window ---

class MainWindow(QWidget):
    toggle_app_signal = pyqtSignal()
    hotkeys_changed_signal = pyqtSignal()
    mode_changed_signal = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layvix AI")
        
        # Native Dark Mode Title Bar
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(2)), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(ctypes.c_int(2)), 4)
        except:
            pass
            
        self.setStyleSheet(f"background-color: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN};")
        self.resize(1000, 700)
        self.app_enabled = True
        if settings.get_setting("language") == "ar" or not settings.get_setting("language"):
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        set_language(settings.get_setting("language") or "ar")
        self._build_ui()
        self._setup_tray()
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def _build_ui(self):
        # We need a timer for live stats
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(1000)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {Theme.BG_BASE};
                border: none;
            }}
        """)
        
        self.root_layout.addWidget(self.main_frame)
        
        self.frame_layout = QVBoxLayout(self.main_frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)
        
        # Body
        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        self.frame_layout.addWidget(self.body_widget)
        
        self._build_sidebar()
        
        # Content Stack
        self.stack = QStackedWidget()
        self.body_layout.addWidget(self.stack)
        
        # Pages
        self.pages = [
            ("🏠", t("dashboard"), self._page_dashboard),
            ("🧠", t("learning_center"), self._page_learning),
            ("⚙️", t("settings"), self._page_settings),
            ("✨", t("about"), self._page_about)
        ]
        
        for icon, title, builder in self.pages:
            self._add_sidebar_item(icon, title)
            page = QWidget()
            page.setStyleSheet("background: transparent;")
            builder(page)
            self.stack.addWidget(page)
            
        self._switch_page(0)
        
    def _update_stats(self):
        try:
            import sys
            core_loop = sys.modules.get('__main__')
            if not core_loop or not hasattr(core_loop, 'get_stats'):
                import main as core_loop
            stats = core_loop.get_stats()
            self.stat_today.set_value(stats.get("corrections_today", 0))
            self.stat_total.set_value(stats.get("total_corrections", 0))
            self.stat_learned.set_value(stats.get("words_learned", 0))
        except Exception as e:
            pass
        try:
            ls = learner.get_stats()
            self.learn_total.set_value(ls.get("total_learned", 0))
            self.learn_undone.set_value(ls.get("corrections_undone", 0))
            self.learn_manual.set_value(ls.get("manual_corrections", 0))
        except:
            pass

    def _build_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_BASE};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)
        self.sb_layout = QVBoxLayout(self.sidebar)
        self.sb_layout.setContentsMargins(10, 20, 10, 20)
        self.sb_layout.setSpacing(10)
        
        self.nav_btns = []
        self.body_layout.addWidget(self.sidebar)
        
    def _add_sidebar_item(self, icon, title):
        idx = len(self.nav_btns)
        btn = SidebarBtn(icon, title)
        btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
        self.sb_layout.addWidget(btn)
        self.nav_btns.append(btn)
        
    def _switch_page(self, index):
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        
    # --- PAGE: DASHBOARD ---
    def _page_dashboard(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Hero Section
        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero.setStyleSheet(f"""
            QFrame#HeroCard {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Theme.PRIMARY}, stop:1 #8a2be2);
                border-radius: 16px;
            }}
        """)
        h_layout = QVBoxLayout(hero)
        h_layout.setContentsMargins(30, 30, 30, 30)
        
        h_title = QLabel("🤖 محرك ذكاء اصطناعي يعمل في الخلفية")
        h_title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        h_layout.addWidget(h_title)
        
        h_desc = QLabel("تطبيق Layvix يقرأ الآن نمط طباعتك ويحلل كل كلمة تكتبها عبر نموذج (Machine Learning) متقدم.<br>لا تقلق أبداً بشأن نسيان تبديل اللغة، اكتب بحرية ودع الذكاء الاصطناعي يقوم بالسحر ويصحح أخطاءك فوراً!")
        h_desc.setWordWrap(True)
        h_desc.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 15px; margin-top: 10px; line-height: 1.5;")
        h_layout.addWidget(h_desc)
        
        layout.addWidget(hero)
        layout.addSpacing(10)
        
        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.stat_today = StatCard(t("corrections_today"), "0", "📈", Theme.ACCENT)
        self.stat_total = StatCard(t("total_corrections"), "0", "🚀", Theme.PRIMARY)
        self.stat_learned = StatCard(t("words_learned"), "0", "💡", Theme.SUCCESS)
        stats_row.addWidget(self.stat_today)
        stats_row.addWidget(self.stat_total)
        stats_row.addWidget(self.stat_learned)
        layout.addLayout(stats_row)
        
        layout.addSpacing(20)
        
        # Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Main Toggle Card
        self.master_card = QFrame()
        self.master_card.setObjectName("Card")
        self.master_card.setStyleSheet(f"QFrame#Card {{ background-color: {Theme.BG_CARD}; border-radius: 12px; border: 1px solid {Theme.BORDER}; }}")
        mc_layout = QVBoxLayout(self.master_card)
        mc_layout.setContentsMargins(20, 20, 20, 20)
        
        mc_header = QHBoxLayout()
        mc_title = QLabel(t("auto_correction"))
        mc_title.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: bold;")
        mc_header.addWidget(mc_title)
        mc_header.addStretch()
        self.master_toggle = ToggleSwitch(self.app_enabled)
        self.master_toggle.toggled_signal.connect(self._on_master_toggle)
        mc_header.addWidget(self.master_toggle)
        mc_layout.addLayout(mc_header)
        
        self.master_desc = QLabel(t("auto_desc_on"))
        self.master_desc.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 13px;")
        mc_layout.addWidget(self.master_desc)
        cards_layout.addWidget(self.master_card)
        
        # Mode Card
        self.mode_card = QFrame()
        self.mode_card.setObjectName("Card")
        self.mode_card.setStyleSheet(f"QFrame#Card {{ background-color: {Theme.BG_CARD}; border-radius: 12px; border: 1px solid {Theme.BORDER}; }}")
        md_layout = QVBoxLayout(self.mode_card)
        md_layout.setContentsMargins(20, 20, 20, 20)
        
        md_header = QHBoxLayout()
        md_title = QLabel("التصحيح التلقائي")
        md_title.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: bold;")
        md_header.addWidget(md_title)
        md_header.addStretch()
        self.mode_toggle = ToggleSwitch(True)
        self.mode_toggle.toggled_signal.connect(self._on_mode_toggle)
        md_header.addWidget(self.mode_toggle)
        md_layout.addLayout(md_header)
        
        self.mode_desc = QLabel("تصحيح وتغيير اللغة فوراً")
        self.mode_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px;")
        md_layout.addWidget(self.mode_desc)
        # cards_layout.addWidget(self.mode_card)
        
        layout.addLayout(cards_layout)
        
        layout.addStretch()
        
    def _on_master_toggle(self, checked):
        self.app_enabled = checked
        self.master_desc.setText(t("auto_desc_on") if checked else t("auto_desc_off"))
        self.master_desc.setStyleSheet(f"color: {Theme.PRIMARY if checked else Theme.TEXT_MUTED}; font-size: 13px;")
        self.toggle_app_signal.emit()
        
    def _on_mode_toggle(self, checked):
        self.mode_desc.setText("تصحيح وتغيير اللغة فوراً" if checked else "يعتمد على الاختصار اليدوي فقط")
        self.mode_changed_signal.emit(checked)
        
    # --- PAGE: LEARNING ---
    def _page_learning(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        header = QLabel(t("learning_title"))
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 24px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)
        
        sub = QLabel(t("learning_sub"))
        sub.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 14px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(sub)
        layout.addSpacing(20)
        
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.learn_total = StatCard(t("live_training"), "0", "🔄", Theme.PRIMARY)
        self.learn_undone = StatCard(t("undones"), "0", "↩️", Theme.DANGER)
        self.learn_manual = StatCard(t("manual_corrections"), "0", "✍️", Theme.ACCENT)
        
        stats_row.addWidget(self.learn_total)
        stats_row.addWidget(self.learn_undone)
        stats_row.addWidget(self.learn_manual)
        
        layout.addLayout(stats_row)
        
        layout.addSpacing(20)
        self.ai_visualizer = AIActivityWidget()
        layout.addWidget(self.ai_visualizer)
        
        layout.addSpacing(20)
        
        actions_row = QHBoxLayout()
        actions_row.setSpacing(15)
        
        view_words_btn = QPushButton(t("view_custom_words"))
        view_words_btn.setFixedHeight(40)
        view_words_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.BG_CARD_HOVER}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY}; border: 1px solid {Theme.PRIMARY_GLOW}; }}
        """)
        view_words_btn.clicked.connect(self._view_custom_words)
        actions_row.addWidget(view_words_btn)
        
        fine_tune_btn = QPushButton(t("fine_tune_btn"))
        fine_tune_btn.setFixedHeight(40)
        fine_tune_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.ACCENT_GLOW}; }}
        """)
        fine_tune_btn.clicked.connect(self._fine_tune_model)
        actions_row.addWidget(fine_tune_btn)
        
        reset_btn = QPushButton(t("reset_brain"))
        reset_btn.setFixedHeight(40)
        reset_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {Theme.DANGER}; border: 1px solid {Theme.DANGER}; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.DANGER}; color: white; }}
        """)
        reset_btn.clicked.connect(self._reset_brain)
        actions_row.addWidget(reset_btn)
        
        layout.addLayout(actions_row)
        
        self.words_display = QListWidget()
        self.words_display.setStyleSheet(f"""
            QListWidget {{ background: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 8px; padding: 10px; font-size: 14px; }}
        """)
        self.words_display.hide()
        layout.addWidget(self.words_display)
        
        layout.addStretch()
        
    def _reset_brain(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'تأكيد مسح الذاكرة', 
                                     'هل أنت متأكد من مسح جميع تدريبات الموديل والقاموس المخصص؟\nلا يمكن التراجع عن هذا الإجراء.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import os
                import learner
                import user_dictionary
                
                # Clear learning log
                base_dir = os.path.dirname(os.path.abspath(__file__))
                log_path = os.path.join(base_dir, 'learning_log.json')
                if os.path.exists(log_path):
                    os.remove(log_path)
                    
                # Clear personal model
                model_path = os.path.join(base_dir, 'personal_model.pkl')
                if os.path.exists(model_path):
                    os.remove(model_path)
                    
                # Clear stats
                learner._stats = {"total_learned": 0, "corrections_undone": 0, "manual_corrections": 0}
                learner._save_stats()
                
                import sys
                core_loop = sys.modules.get('__main__')
                if core_loop and hasattr(core_loop, '_stats'):
                    core_loop._stats = {"corrections_today": 0, "total_corrections": 0, "words_learned": 0, "last_date": ""}
                    if hasattr(core_loop, 'save_stats'):
                        core_loop.save_stats()
                    
                # Clear dictionary
                user_dictionary.user_dict.clear()
                user_dictionary.save_user_dict()
                
                # Re-init learner
                learner.init_engine()
                self._update_stats()
                
                sender = self.sender()
                if sender:
                    sender.setText(t("brain_reset_success"))
                    QTimer.singleShot(2000, lambda: sender.setText(t("reset_brain")))
            except Exception as e:
                pass

    def _view_custom_words(self, *args):
        from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout
        from PyQt6.QtCore import Qt
        dialog = QDialog(self)
        dialog.setWindowTitle(t("custom_words"))
        dialog.setFixedSize(450, 500)
        dialog.setStyleSheet(f"QDialog {{ background-color: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; }}")
        
        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel(t("custom_words"))
        lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.PRIMARY};")
        d_layout.addWidget(lbl)
        
        list_widget = QListWidget()
        list_widget.setStyleSheet(f"""
            QListWidget {{ background: {Theme.BG_CARD}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 8px; padding: 10px; font-size: 14px; }}
            QListWidget::item:selected {{ background: {Theme.PRIMARY_HOVER}; border-radius: 4px; }}
        """)
        
        def refresh_list():
            list_widget.clear()
            custom_words = user_dictionary.get_custom_words()
            if not custom_words:
                list_widget.addItem(t("no_words"))
            else:
                for wrong, right in user_dictionary.user_dict.items():
                    item = QListWidgetItem(f"{wrong} ➔ {right}")
                    item.setData(Qt.ItemDataRole.UserRole, wrong)
                    list_widget.addItem(item)
                    
        refresh_list()
        d_layout.addWidget(list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        del_btn = QPushButton("حذف المحدد")
        del_btn.setFixedHeight(40)
        del_btn.setStyleSheet(f"QPushButton {{ background: {Theme.DANGER}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background: #ff4444; }}")
        
        def delete_selected():
            selected = list_widget.selectedItems()
            if not selected: return
            item = selected[0]
            wrong = item.data(Qt.ItemDataRole.UserRole)
            if wrong and wrong in user_dictionary.user_dict:
                del user_dictionary.user_dict[wrong]
                user_dictionary.save_user_dict()
                refresh_list()
                
        del_btn.clicked.connect(delete_selected)

        edit_btn = QPushButton("تعديل المحدد")
        edit_btn.setFixedHeight(40)
        edit_btn.setStyleSheet(f"QPushButton {{ background: {Theme.ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background: {Theme.PRIMARY}; }}")

        def edit_selected():
            selected = list_widget.selectedItems()
            if not selected: return
            item = selected[0]
            wrong = item.data(Qt.ItemDataRole.UserRole)
            if not wrong or wrong not in user_dictionary.user_dict:
                return

            current_right = user_dictionary.user_dict[wrong]

            edit_dialog = QDialog(dialog)
            edit_dialog.setWindowTitle("تعديل الكلمة")
            edit_dialog.setFixedSize(400, 200)
            edit_dialog.setStyleSheet(f"QDialog {{ background-color: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; }}")
            el = QVBoxLayout(edit_dialog)
            el.setContentsMargins(20, 20, 20, 20)
            el.setSpacing(12)

            lbl_wrong = QLabel(f"الكلمة الخاطئة: {wrong}")
            lbl_wrong.setStyleSheet(f"color: {Theme.DANGER}; font-size: 14px; font-weight: bold;")
            el.addWidget(lbl_wrong)

            right_input = QLineEdit(current_right)
            right_input.setPlaceholderText("الكلمة الصحيحة...")
            right_input.setStyleSheet(f"QLineEdit {{ background: {Theme.BG_CARD}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 8px; padding: 8px; font-size: 14px; }}")
            right_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            el.addWidget(right_input)

            btn_row = QHBoxLayout()
            save_e = QPushButton("حفظ")
            save_e.setFixedHeight(36)
            save_e.setStyleSheet(f"QPushButton {{ background: {Theme.PRIMARY}; color: white; border-radius: 6px; font-weight: bold; }}")
            cancel_e = QPushButton("إلغاء")
            cancel_e.setFixedHeight(36)
            cancel_e.setStyleSheet(f"QPushButton {{ background: {Theme.BG_CARD}; color: {Theme.TEXT_MUTED}; border-radius: 6px; font-weight: bold; }}")
            btn_row.addWidget(save_e)
            btn_row.addWidget(cancel_e)
            el.addLayout(btn_row)

            def do_save():
                new_right = right_input.text().strip()
                if new_right:
                    user_dictionary.user_dict[wrong] = new_right
                    user_dictionary.save_user_dict()
                    refresh_list()
                edit_dialog.accept()

            save_e.clicked.connect(do_save)
            cancel_e.clicked.connect(edit_dialog.reject)
            edit_dialog.exec()

        edit_btn.clicked.connect(edit_selected)
        
        close_btn = QPushButton("إغلاق")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(f"QPushButton {{ background: {Theme.PRIMARY}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background: {Theme.PRIMARY_HOVER}; }}")
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(close_btn)
        
        d_layout.addLayout(btn_layout)
        dialog.exec()

    def _fine_tune_model(self):
        import learner
        sender = self.sender()
        if not sender: return
        
        sender.setText("...")
        sender.setEnabled(False)
        QApplication.processEvents()
        
        success = learner.fine_tune_with_dictionary()
        
        if success:
            sender.setText(t("fine_tune_success"))
            sender.setStyleSheet(f"""
                QPushButton {{ background-color: {Theme.SUCCESS}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            """)
        else:
            sender.setText(t("fine_tune_fail"))
            sender.setStyleSheet(f"""
                QPushButton {{ background-color: {Theme.DANGER}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            """)
            
        QTimer.singleShot(3000, lambda: self._reset_fine_tune_btn(sender))

    def _reset_fine_tune_btn(self, btn):
        btn.setText(t("fine_tune_btn"))
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.ACCENT_GLOW}; }}
        """)
        btn.setEnabled(True)

        
    # --- PAGE: SETTINGS ---
    def _page_settings(self, page):
        # We use a scroll area to make it fit nicely
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_w = QWidget()
        c_layout = QVBoxLayout(content_w)
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(20)
        
        header = QLabel(t("settings_title"))
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 24px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        c_layout.addWidget(header)
        
        # 1. Hotkeys Section
        hotkeys_card = self._create_card(c_layout, t("hotkeys_section"))
        hk_layout = QVBoxLayout(hotkeys_card)
        hk_layout.setContentsMargins(20, 20, 20, 20)
        hk_layout.setSpacing(15)
        
        # Undo Hotkey
        u_row = QHBoxLayout()
        u_lbl = QLabel(t("undo_hotkey"))
        u_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        u_row.addWidget(u_lbl)
        u_row.addStretch()
        self.undo_hk_input = HotkeyInput(settings.get_setting("undo_hotkey") or "pause")
        self.undo_hk_input.setFixedWidth(200)
        u_row.addWidget(self.undo_hk_input)
        hk_layout.addLayout(u_row)
        
        # Manual Hotkey
        m_row = QHBoxLayout()
        m_lbl = QLabel(t("manual_hotkey"))
        m_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        m_row.addWidget(m_lbl)
        m_row.addStretch()
        self.manual_hk_input = HotkeyInput(settings.get_setting("manual_hotkey") or "shift+pause")
        self.manual_hk_input.setFixedWidth(200)
        m_row.addWidget(self.manual_hk_input)
        hk_layout.addLayout(m_row)
        
        # 2. AI Parameters Section
        ai_card = self._create_card(c_layout, t("ai_params"))
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(20, 20, 20, 20)
        ai_layout.setSpacing(15)
        
        # Confidence Threshold (Slider)
        conf_row = QHBoxLayout()
        conf_lbl = QLabel(t("confidence"))
        conf_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        conf_row.addWidget(conf_lbl)
        conf_row.addStretch()
        
        from PyQt6.QtWidgets import QSlider
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(70, 99)
        self.conf_slider.setValue(int(float(settings.get_setting("confidence_threshold") or 0.85) * 100))
        self.conf_slider.setFixedWidth(150)
        
        self.conf_val_lbl = QLabel(f"{self.conf_slider.value()}%")
        self.conf_val_lbl.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; width: 40px;")
        self.conf_slider.valueChanged.connect(lambda v: self.conf_val_lbl.setText(f"{v}%"))
        
        conf_row.addWidget(self.conf_slider)
        conf_row.addWidget(self.conf_val_lbl)
        ai_layout.addLayout(conf_row)
        
        # Min Word Length
        len_row = QHBoxLayout()
        len_lbl = QLabel(t("min_word_len"))
        len_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        len_row.addWidget(len_lbl)
        len_row.addStretch()
        
        self.len_slider = QSlider(Qt.Orientation.Horizontal)
        self.len_slider.setRange(2, 6)
        self.len_slider.setValue(int(settings.get_setting("min_word_length") or 2))
        self.len_slider.setFixedWidth(150)
        
        self.len_val_lbl = QLabel(f"{self.len_slider.value()}  " + t("chars") + "")
        self.len_val_lbl.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; width: 50px;")
        self.len_slider.valueChanged.connect(lambda v: self.len_val_lbl.setText(f"{v}  " + t("chars") + ""))
        
        len_row.addWidget(self.len_slider)
        len_row.addWidget(self.len_val_lbl)
        ai_layout.addLayout(len_row)
        
        # 3. System Options Section
        sys_card = self._create_card(c_layout, t("startup_section"))
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(15)
        
        # Language Dropdown
        lang_row = QHBoxLayout()
        lang_lbl = QLabel(t("language"))
        lang_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        lang_row.addWidget(lang_lbl)
        lang_row.addStretch()
        
        from PyQt6.QtWidgets import QComboBox
        self.lang_cb = QComboBox()
        self.lang_cb.addItem(t("lang_ar"), "ar")
        self.lang_cb.addItem(t("lang_en"), "en")
        current_lang = settings.get_setting("language") or "ar"
        idx = self.lang_cb.findData(current_lang)
        if idx >= 0:
            self.lang_cb.setCurrentIndex(idx)
        self.lang_cb.setFixedWidth(150)
        self.lang_cb.setStyleSheet(f"QComboBox {{ background: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 5px; }}")
        lang_row.addWidget(self.lang_cb)
        sys_layout.addLayout(lang_row)
        
        # Run on Startup
        startup_row = QHBoxLayout()
        startup_lbl = QLabel(t("run_on_startup"))
        startup_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 14px;")
        startup_row.addWidget(startup_lbl)
        startup_row.addStretch()
        self.startup_toggle = ToggleSwitch(settings.get_setting("run_on_startup") or False)
        startup_row.addWidget(self.startup_toggle)
        sys_layout.addLayout(startup_row)
        
        # Model Selection (Dropdown)
        model_row = QHBoxLayout()
        model_lbl = QLabel("إصدار الذكاء الاصطناعي (Model):")
        model_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 14px;")
        model_row.addWidget(model_lbl)
        model_row.addStretch()
        
        self.model_cb = QComboBox()
        self.model_cb.addItem("Layvix Pro (Personal Learning)", "personal")
        self.model_cb.addItem("Layvix Fast (Base Model)", "base")
        self.model_cb.setFixedWidth(220)
        self.model_cb.setStyleSheet(f"QComboBox {{ background: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 5px; }}")
        
        val = settings.get_setting("use_personal_model")
        if val is False:
            self.model_cb.setCurrentIndex(1)
        else:
            self.model_cb.setCurrentIndex(0)
            
        model_row.addWidget(self.model_cb)
        sys_layout.addLayout(model_row)
        
        # Retroactive Correction
        retro_row = QHBoxLayout()
        retro_lbl = QLabel(t("retroactive_correction"))
        retro_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 14px;")
        retro_row.addWidget(retro_lbl)
        retro_row.addStretch()
        r_val = settings.get_setting("retroactive_correction")
        if r_val is None: r_val = True
        self.retro_toggle = ToggleSwitch(r_val)
        retro_row.addWidget(self.retro_toggle)
        sys_layout.addLayout(retro_row)
        
        # Floating Bubble Toggle
        bubble_row = QHBoxLayout()
        bubble_lbl = QLabel("تشغيل الفقاعة العائمة (Floating Bubble)")
        bubble_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 14px;")
        bubble_row.addWidget(bubble_lbl)
        bubble_row.addStretch()
        b_val = settings.get_setting("show_floating_bubble")
        if b_val is None: b_val = True
        self.bubble_toggle = ToggleSwitch(b_val)
        bubble_row.addWidget(self.bubble_toggle)
        sys_layout.addLayout(bubble_row)
        
        # Floating Bubble Size
        bsize_row = QHBoxLayout()
        bsize_lbl = QLabel("حجم الفقاعة العائمة")
        bsize_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        bsize_row.addWidget(bsize_lbl)
        bsize_row.addStretch()
        
        self.bsize_slider = QSlider(Qt.Orientation.Horizontal)
        self.bsize_slider.setRange(30, 70)
        self.bsize_slider.setValue(int(settings.get_setting("bubble_size") or 70))
        self.bsize_slider.setFixedWidth(150)
        
        self.bsize_val_lbl = QLabel(f"{self.bsize_slider.value()} px")
        self.bsize_val_lbl.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; width: 50px;")
        self.bsize_slider.valueChanged.connect(lambda v: self.bsize_val_lbl.setText(f"{v} px"))
        
        bsize_row.addWidget(self.bsize_slider)
        bsize_row.addWidget(self.bsize_val_lbl)
        sys_layout.addLayout(bsize_row)
        
        # 4. Exclusions Section
        ex_card = self._create_card(c_layout, t("exclusions"))
        ex_layout = QVBoxLayout(ex_card)
        ex_layout.setContentsMargins(20, 20, 20, 20)
        
        ex_desc = QLabel(t("exclusions_desc"))
        ex_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px; margin-bottom: 5px;")
        ex_layout.addWidget(ex_desc)
        
        self.ex_input = QLineEdit()
        saved_ex = settings.get_setting("excluded_apps")
        if not saved_ex: saved_ex = ["valorant", "csgo", "league of legends", "dota 2"]
        self.ex_input.setText(", ".join(saved_ex))
        self.ex_input.setStyleSheet(f"QLineEdit {{ background: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 8px; }}")
        ex_layout.addWidget(self.ex_input)
        
        # 5. Backup & Restore Section
        export_card = self._create_card(c_layout, "النسخ الاحتياطي (Backup)")
        export_layout = QVBoxLayout(export_card)
        export_layout.setContentsMargins(20, 20, 20, 20)
        
        btn_row = QHBoxLayout()
        export_btn = QPushButton("تصدير (Export)")
        export_btn.setFixedHeight(40)
        export_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.PRIMARY}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY_HOVER}; }}
        """)
        export_btn.clicked.connect(self._export_backup)
        
        import_btn = QPushButton("استيراد (Import)")
        import_btn.setFixedHeight(40)
        import_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.BG_CARD_HOVER}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY}; border: 1px solid {Theme.PRIMARY_GLOW}; }}
        """)
        import_btn.clicked.connect(self._import_backup)
        
        btn_row.addWidget(import_btn)
        btn_row.addWidget(export_btn)
        export_layout.addLayout(btn_row)
        
        # Save Button
        save_btn = QPushButton(t("save_settings"))
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.PRIMARY}; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; margin-top: 10px; }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY_HOVER}; }}
        """)
        save_btn.clicked.connect(self._save_all_settings)
        c_layout.addWidget(save_btn)
        
        c_layout.addStretch()
        scroll.setWidget(content_w)
        layout.addWidget(scroll)

    def _create_card(self, parent_layout, title):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_CARD}; border-radius: 12px; border: 1px solid {Theme.BORDER}; }}")
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: bold; padding: 15px 15px 0px 15px;")
        lbl.setParent(card) # Visual trick, but better to use layouts
        parent_layout.addWidget(lbl) # Add title outside the card for clean look
        parent_layout.addWidget(card)
        return card

    def _export_backup(self):
        import os
        import zipfile
        from PyQt6.QtWidgets import QFileDialog
        from logger import get_data_dir
        
        data_dir = get_data_dir()
        
        export_path, _ = QFileDialog.getSaveFileName(self, "حفظ النسخة الاحتياطية", "Layvix_Backup.layvix", "Layvix Backup (*.layvix)")
        if not export_path:
            return
        
        try:
            files_to_backup = ['user_dict.json', 'learning_log.json', 'settings.json', 'layvix_ai_personal.pkl', 'learner_stats.json']
            count = 0
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files_to_backup:
                    f_path = os.path.join(data_dir, f)
                    if os.path.exists(f_path):
                        zf.write(f_path, f)
                        count += 1
                        
            sender = self.sender()
            if sender:
                sender.setText(f"✅ تم تصدير {count} ملفات بنجاح!")
                QTimer.singleShot(3000, lambda: sender.setText("تصدير (Export)"))
        except Exception as e:
            from logger import get_logger
            get_logger().error(f"Failed to export backup: {e}")

    def _import_backup(self):
        import os
        import zipfile
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from PyQt6.QtCore import QProcess
        from logger import get_data_dir
        import sys
        
        data_dir = get_data_dir()
        
        import_path, _ = QFileDialog.getOpenFileName(self, "استيراد نسخة احتياطية", "", "Layvix Backup (*.layvix)")
        if not import_path:
            return
            
        reply = QMessageBox.question(self, 'تأكيد الاستيراد', 
                                     'هل أنت متأكد من استيراد هذه النسخة؟\nسيتم محو الدماغ والقاموس الحالي واستبداله بالنسخة المستوردة.\nسيتم إعادة تشغيل البرنامج.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with zipfile.ZipFile(import_path, 'r') as zf:
                    zf.extractall(data_dir)
                    
                # Restart to apply imported model and dictionary
                if getattr(sys, 'frozen', False):
                    QProcess.startDetached(sys.executable, sys.argv[1:])
                else:
                    QProcess.startDetached(sys.executable, sys.argv)
                QApplication.quit()
            except Exception as e:
                from logger import get_logger
                get_logger().error(f"Failed to import backup: {e}")

    def _save_all_settings(self):
        old_lang = settings.get_setting("language")
        
        # Save Hotkeys
        settings.set_setting("undo_hotkey", self.undo_hk_input.current_hk)
        settings.set_setting("manual_hotkey", self.manual_hk_input.current_hk)
        
        # Save AI Parameters
        conf_val = self.conf_slider.value() / 100.0
        settings.set_setting("confidence_threshold", conf_val)
        settings.set_setting("min_word_length", self.len_slider.value())
        
        # Save System Settings
        new_lang = self.lang_cb.currentData()
        settings.set_setting("language", new_lang)
        settings.set_setting("run_on_startup", self.startup_toggle.checked)
        settings.set_setting("use_personal_model", self.model_cb.currentData() == "personal")
        settings.set_setting("retroactive_correction", self.retro_toggle.checked)
        settings.set_setting("show_floating_bubble", self.bubble_toggle.checked)
        settings.set_setting("bubble_size", self.bsize_slider.value())
        
        # Apply bubble visibility and size instantly
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if hasattr(app, 'bubble'):
            app.bubble.update_size(self.bsize_slider.value())
            if self.bubble_toggle.checked:
                app.bubble.show()
            else:
                app.bubble.hide()
        
        # Save Exclusions
        ex_str = self.ex_input.text()
        ex_list = [x.strip() for x in ex_str.split(",") if x.strip()]
        settings.set_setting("excluded_apps", ex_list)
        
        self.hotkeys_changed_signal.emit()
        
        if old_lang and old_lang != new_lang:
            from PyQt6.QtCore import QProcess
            import sys
            # Restart application to apply language
            if getattr(sys, 'frozen', False):
                # Compiled executable
                QProcess.startDetached(sys.executable, sys.argv[1:])
            else:
                # Python script (Development version)
                QProcess.startDetached(sys.executable, sys.argv)
            QApplication.quit()
            return
            
        # Flash save button
        sender = self.sender()
        if sender:
            sender.setText(t("settings_saved"))
            QTimer.singleShot(2000, lambda: sender.setText(t("save_settings")))

    # --- PAGE: ABOUT ---
    def _page_about(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        header = QLabel(t("about_title"))
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 28px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)
        
        # App Info Card
        info_card = QFrame()
        info_card.setObjectName("InfoCard")
        info_card.setStyleSheet(f"QFrame#InfoCard {{ background-color: {Theme.BG_CARD}; border-radius: 12px; border: 1px solid {Theme.BORDER}; }}")
        i_layout = QVBoxLayout(info_card)
        i_layout.setContentsMargins(25, 25, 25, 25)
        
        i_title = QLabel("ما هو Layvix Pro؟ 🧠")
        i_title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 20px; font-weight: bold;")
        i_layout.addWidget(i_title)
        
        i_desc = QLabel("هو أول لوحة مفاتيح ذكية للكمبيوتر تعتمد على الذكاء الاصطناعي وتعلم الآلة (SGD Classifier).<br>يتعلم التطبيق من أخطائك، يحلل لغتك، ويتدرب محلياً على جهازك لضمان خصوصيتك 100% بدون أي اتصال بالإنترنت أو إرسال بيانات خارجية.")
        i_desc.setWordWrap(True)
        i_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 15px; margin-top: 10px; line-height: 1.6;")
        i_layout.addWidget(i_desc)
        
        # Features Grid
        f_layout = QHBoxLayout()
        f_layout.setContentsMargins(0, 20, 0, 0)
        f_layout.setSpacing(15)
        
        def _feat(icon, title, desc):
            w = QFrame()
            w.setObjectName("FeatCard")
            w.setStyleSheet(f"QFrame#FeatCard {{ background-color: {Theme.BG_BASE}; border-radius: 8px; padding: 10px; }}")
            wl = QVBoxLayout(w)
            wl.setContentsMargins(10, 10, 10, 10)
            l1 = QLabel(f"{icon} {title}")
            l1.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 15px; font-weight: bold;")
            l2 = QLabel(desc)
            l2.setWordWrap(True)
            l2.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; margin-top: 5px;")
            wl.addWidget(l1)
            wl.addWidget(l2)
            wl.addStretch()
            return w
            
        f_layout.addWidget(_feat("🔒", "خصوصية تامة", "بياناتك ودستورك اللغوي لا تغادر جهازك أبداً ولا تحتاج لإنترنت."))
        f_layout.addWidget(_feat("⚡", "سرعة خارقة", "خوارزميات مكتوبة باحترافية لتستجيب في أجزاء من الثانية."))
        f_layout.addWidget(_feat("🧠", "تعلم مستمر", "المحرك يتطور ويصبح أذكى ويتأقلم مع مصطلحاتك بشكل دائم."))
        i_layout.addLayout(f_layout)
        
        layout.addWidget(info_card)
        
        # Updates Card
        card = QFrame()
        card.setObjectName("UpdateCard")
        card.setStyleSheet(f"QFrame#UpdateCard {{ background-color: {Theme.BG_CARD}; border-radius: 12px; border: 1px solid {Theme.BORDER}; margin-top: 10px; }}")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(25, 25, 25, 25)
        
        version_lbl = QLabel(t("current_version", version=VERSION))
        version_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px;")
        c_layout.addWidget(version_lbl)
        
        self.update_status = QLabel("جاهز للبحث عن تحديثات...")
        self.update_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        c_layout.addWidget(self.update_status)
        
        self.update_btn = QPushButton(t("check_updates"))
        self.update_btn.setFixedHeight(45)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.PRIMARY}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; margin-top: 10px; }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY_HOVER}; }}
        """)
        self.update_btn.clicked.connect(self._check_updates)
        c_layout.addWidget(self.update_btn)
        
        layout.addWidget(card)
        
        # Developer Card
        dev_card = QFrame()
        dev_card.setObjectName("DevCard")
        dev_card.setStyleSheet(f"QFrame#DevCard {{ background-color: {Theme.BG_BASE}; border-radius: 12px; border: 1px solid {Theme.PRIMARY_GLOW}; margin-top: 20px; }}")
        dev_layout = QVBoxLayout(dev_card)
        dev_layout.setContentsMargins(20, 20, 20, 20)
        
        dev_title = QLabel(t("developer_info"))
        dev_title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 16px; font-weight: bold;")
        dev_layout.addWidget(dev_title)
        
        dev_love = QLabel(t("made_with_love"))
        dev_love.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 18px; font-family: {Theme.FONT_FAMILY};")
        dev_layout.addWidget(dev_love)
        
        gh_btn = QPushButton(t("github_btn"))
        gh_btn.setFixedHeight(35)
        gh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {Theme.TEXT_MUTED}; border: 1px solid {Theme.BORDER}; border-radius: 8px; font-weight: bold; margin-top: 10px; }}
            QPushButton:hover {{ background-color: {Theme.BG_CARD_HOVER}; color: {Theme.TEXT_MAIN}; }}
        """)
        gh_btn.clicked.connect(lambda: self._open_url("https://github.com/SalehAlSalem/Layvix"))
        dev_layout.addWidget(gh_btn)
        
        layout.addWidget(dev_card)
        
        layout.addStretch()
        
    def _check_updates(self):
        self.update_btn.setEnabled(False)
        self.update_status.setText(t("checking"))
        import updater
        self.updater = updater.Updater(VERSION)
        self.updater.update_available.connect(self._on_update_found)
        self.updater.check_finished.connect(self._on_check_finished)
        self.updater.check_for_updates()
        
    def _on_update_found(self, version, url, body):
        self.update_status.setText(t("update_available", version=version))
        self.update_status.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 14px; font-weight: bold;")
        self.update_btn.setText(t("download_update"))
        
        # Disconnect old, connect new
        self.update_btn.clicked.disconnect()
        self.update_btn.clicked.connect(lambda: self._open_url(url))
        self.update_btn.setEnabled(True)
        
    def _on_check_finished(self, found):
        if not found:
            self.update_status.setText(t("up_to_date"))
            self.update_btn.setEnabled(True)
            self.update_btn.setText(t("check_updates"))
            
    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    # --- System Tray ---
    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        # Using a default icon for now, since we don't have an asset loaded yet
        # We will set a custom drawn icon if needed
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(Theme.PRIMARY))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, 28, 28)
        p.end()
        self.tray.setIcon(QIcon(pixmap))
        
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 5px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.PRIMARY};
            }}
        """)
        
        show_act = QAction(t("show_window"), self)
        show_act.triggered.connect(self.showNormal)
        menu.addAction(show_act)
        
        quit_act = QAction(t("quit_app"), self)
        quit_act.triggered.connect(self._quit_app)
        menu.addAction(quit_act)
        
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def _quit_app(self):
        try:
            import main
            main.stop_all()
        except:
            pass
        QApplication.quit()
        sys.exit(0)
