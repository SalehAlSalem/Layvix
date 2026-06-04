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
    QTimer, QRect
)
from PyQt6.QtGui import (
    QColor, QIcon, QFont, QFontDatabase, QPainter, QPainterPath, 
    QPen, QBrush, QAction, QPixmap
)

import settings
import user_dictionary
import learner

VERSION = "3.2.0"

# --- Theme & Colors ---
class Theme:
    BG_BASE = "#0F0F13"
    BG_CARD = "#1C1C24"
    BG_CARD_HOVER = "#252530"
    
    PRIMARY = "#6C5CE7"
    PRIMARY_HOVER = "#8275E9"
    PRIMARY_GLOW = "rgba(108, 92, 231, 0.4)"
    
    ACCENT = "#00D2D3"
    ACCENT_GLOW = "rgba(0, 210, 211, 0.4)"
    
    TEXT_MAIN = "#FFFFFF"
    TEXT_MUTED = "#A0A0B0"
    
    DANGER = "#FF7675"
    SUCCESS = "#55EFC4"

    BORDER = "#2D2D3A"
    
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
        self.title_label = QLabel("🐙 Layvix AI")
        self.title_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; font-size: 14px; font-family: {Theme.FONT_FAMILY};")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Window Controls
        self.min_btn = self._create_btn("—", self.window().showMinimized)
        self.close_btn = self._create_btn("✕", self.window().hide, hover_color=Theme.DANGER)
        
        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)
        
        # Dragging mechanics
        self.start_pos = None

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
        
        self.anim = QPropertyAnimation(self, b"thumb_pos")
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.setDuration(250)
        
        self._thumb_pos = 24 if self.checked else 2
        
    @property
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
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_CARD};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        layout = QVBoxLayout(self)
        self.lbl = QLabel("نشاط المحرك: ينتظر إدخالك...")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 16px; font-family: {Theme.FONT_FAMILY};")
        layout.addWidget(self.lbl)
        
    def pulse(self, text):
        self.lbl.setText(text)
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
        self.setText("اضغط على الاختصار الآن...")
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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(900, 600)
        self.app_enabled = True
        
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
        self.root_layout.setContentsMargins(10, 10, 10, 10) # For shadow
        
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {Theme.BG_BASE};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(shadow)
        
        self.root_layout.addWidget(self.main_frame)
        
        self.frame_layout = QVBoxLayout(self.main_frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)
        
        # Title bar
        self.title_bar = CustomTitleBar(self)
        self.frame_layout.addWidget(self.title_bar)
        
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
            ("🏠", "لوحة التحكم", self._page_dashboard),
            ("🧠", "مركز التعلم", self._page_learning),
            ("⚙️", "الإعدادات", self._page_settings),
            ("✨", "تحديث و حول", self._page_about)
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
        
        header = QLabel("مرحباً بك في Layvix 🐙")
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 28px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)
        
        sub = QLabel("محرك الذكاء الاصطناعي يعمل في الخلفية ويحلل نمط كتابتك.")
        sub.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 15px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(sub)
        
        layout.addSpacing(10)
        
        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.stat_today = StatCard("⚡ تصحيحات اليوم", "0", "📈", Theme.ACCENT)
        self.stat_total = StatCard("📊 إجمالي التصحيحات", "0", "🚀", Theme.PRIMARY)
        self.stat_learned = StatCard("🧠 كلمات تعلمها", "0", "💡", Theme.SUCCESS)
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
        mc_title = QLabel("حالة المحرك")
        mc_title.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: bold;")
        mc_header.addWidget(mc_title)
        mc_header.addStretch()
        self.master_toggle = ToggleSwitch(self.app_enabled)
        self.master_toggle.toggled_signal.connect(self._on_master_toggle)
        mc_header.addWidget(self.master_toggle)
        mc_layout.addLayout(mc_header)
        
        self.master_desc = QLabel("نشط يعمل في الخلفية")
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
        cards_layout.addWidget(self.mode_card)
        
        layout.addLayout(cards_layout)
        
        layout.addStretch()
        
    def _on_master_toggle(self, checked):
        self.app_enabled = checked
        self.master_desc.setText("نشط يعمل في الخلفية" if checked else "متوقف مؤقتاً")
        self.master_desc.setStyleSheet(f"color: {Theme.PRIMARY if checked else Theme.TEXT_MUTED}; font-size: 13px;")
        self.toggle_app_signal.emit()
        
    def _on_mode_toggle(self, checked):
        self.mode_desc.setText("تصحيح وتغيير اللغة فوراً" if checked else "يعتمد على الاختصار اليدوي فقط")
        self.mode_changed_signal.emit(checked)
        
    # --- PAGE: LEARNING ---
    def _page_learning(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        header = QLabel("التعلم المستمر 🧠")
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 24px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)
        
        sub = QLabel("يتعلم الذكاء الاصطناعي من تصحيحاتك اليدوية وتراجعاتك لتكوين نمط خاص بك.")
        sub.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 14px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(sub)
        layout.addSpacing(20)
        
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.learn_total = StatCard("تدريب مباشر", "0", "🔄", Theme.PRIMARY)
        self.learn_undone = StatCard("تراجعات", "0", "↩️", Theme.DANGER)
        self.learn_manual = StatCard("تصحيح يدوي", "0", "✍️", Theme.ACCENT)
        
        stats_row.addWidget(self.learn_total)
        stats_row.addWidget(self.learn_undone)
        stats_row.addWidget(self.learn_manual)
        
        layout.addLayout(stats_row)
        
        layout.addSpacing(20)
        self.ai_visualizer = AIActivityWidget()
        layout.addWidget(self.ai_visualizer)
        
        layout.addSpacing(20)
        reset_btn = QPushButton("إعادة ضبط الدماغ (مسح الذاكرة)")
        reset_btn.setFixedHeight(40)
        reset_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {Theme.DANGER}; border: 1px solid {Theme.DANGER}; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.DANGER}; color: white; }}
        """)
        reset_btn.clicked.connect(self._reset_brain)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
    def _reset_brain(self):
        # We need a confirmation dialog later, for now just reset
        try:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(base_dir, 'learning_log.json')
            if os.path.exists(log_path):
                os.remove(log_path)
            # Re-train or reload model logic can be added here
            sender = self.sender()
            if sender:
                sender.setText("✅ تم مسح الذاكرة (أعد تشغيل التطبيق)")
                QTimer.singleShot(2000, lambda: sender.setText("إعادة ضبط الدماغ (مسح الذاكرة)"))
        except:
            pass
        
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
        
        header = QLabel("الإعدادات المتقدمة ⚙️")
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 24px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        c_layout.addWidget(header)
        
        # 1. Hotkeys Section
        hotkeys_card = self._create_card(c_layout, "اختصارات لوحة المفاتيح")
        hk_layout = QVBoxLayout(hotkeys_card)
        hk_layout.setContentsMargins(20, 20, 20, 20)
        hk_layout.setSpacing(15)
        
        # Undo Hotkey
        u_row = QHBoxLayout()
        u_lbl = QLabel("اختصار التراجع (Undo):")
        u_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        u_row.addWidget(u_lbl)
        u_row.addStretch()
        self.undo_hk_input = HotkeyInput(settings.get_setting("undo_hotkey") or "pause")
        self.undo_hk_input.setFixedWidth(200)
        u_row.addWidget(self.undo_hk_input)
        hk_layout.addLayout(u_row)
        
        # Manual Hotkey
        m_row = QHBoxLayout()
        m_lbl = QLabel("اختصار التصحيح اليدوي:")
        m_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        m_row.addWidget(m_lbl)
        m_row.addStretch()
        self.manual_hk_input = HotkeyInput(settings.get_setting("manual_hotkey") or "shift+pause")
        self.manual_hk_input.setFixedWidth(200)
        m_row.addWidget(self.manual_hk_input)
        hk_layout.addLayout(m_row)
        
        # 2. AI Parameters Section
        ai_card = self._create_card(c_layout, "معايير الذكاء الاصطناعي")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(20, 20, 20, 20)
        ai_layout.setSpacing(15)
        
        # Confidence Threshold (Slider)
        conf_row = QHBoxLayout()
        conf_lbl = QLabel("دقة التدخل المطلوبة (الثقة):")
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
        len_lbl = QLabel("الحد الأدنى لطول الكلمة:")
        len_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        len_row.addWidget(len_lbl)
        len_row.addStretch()
        
        self.len_slider = QSlider(Qt.Orientation.Horizontal)
        self.len_slider.setRange(2, 6)
        self.len_slider.setValue(int(settings.get_setting("min_word_length") or 2))
        self.len_slider.setFixedWidth(150)
        
        self.len_val_lbl = QLabel(f"{self.len_slider.value()} أحرف")
        self.len_val_lbl.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; width: 50px;")
        self.len_slider.valueChanged.connect(lambda v: self.len_val_lbl.setText(f"{v} أحرف"))
        
        len_row.addWidget(self.len_slider)
        len_row.addWidget(self.len_val_lbl)
        ai_layout.addLayout(len_row)
        
        # 3. Exclusions Section
        ex_card = self._create_card(c_layout, "استثناء التطبيقات والألعاب")
        ex_layout = QVBoxLayout(ex_card)
        ex_layout.setContentsMargins(20, 20, 20, 20)
        
        ex_desc = QLabel("اكتب أسماء النوافذ المستثناة مفصولة بفاصلة (مثال: valorant, csgo)")
        ex_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px; margin-bottom: 5px;")
        ex_layout.addWidget(ex_desc)
        
        self.ex_input = QLineEdit()
        saved_ex = settings.get_setting("excluded_apps")
        if not saved_ex: saved_ex = ["valorant", "csgo", "league of legends", "dota 2"]
        self.ex_input.setText(", ".join(saved_ex))
        self.ex_input.setStyleSheet(f"QLineEdit {{ background: {Theme.BG_BASE}; color: {Theme.TEXT_MAIN}; border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 8px; }}")
        ex_layout.addWidget(self.ex_input)
        
        # Save Button
        save_btn = QPushButton("حفظ جميع الإعدادات")
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

    def _save_all_settings(self):
        # Save Hotkeys
        settings.set_setting("undo_hotkey", self.undo_hk_input.current_hk)
        settings.set_setting("manual_hotkey", self.manual_hk_input.current_hk)
        
        # Save AI Parameters
        conf_val = self.conf_slider.value() / 100.0
        settings.set_setting("confidence_threshold", conf_val)
        settings.set_setting("min_word_length", self.len_slider.value())
        
        # Save Exclusions
        ex_str = self.ex_input.text()
        ex_list = [x.strip() for x in ex_str.split(",") if x.strip()]
        settings.set_setting("excluded_apps", ex_list)
        
        self.hotkeys_changed_signal.emit()
        
        # Flash save button
        sender = self.sender()
        if sender:
            sender.setText("✅ تم الحفظ بنجاح!")
            QTimer.singleShot(2000, lambda: sender.setText("حفظ جميع الإعدادات"))

    # --- PAGE: ABOUT ---
    def _page_about(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        header = QLabel("حول Layvix ✨")
        header.setStyleSheet(f"font-family: {Theme.FONT_FAMILY}; font-size: 24px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)
        
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {Theme.BG_CARD}; border-radius: 12px; border: 1px solid {Theme.BORDER}; }}")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(20, 20, 20, 20)
        
        version_lbl = QLabel(f"الإصدار الحالي: {VERSION}")
        version_lbl.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px;")
        c_layout.addWidget(version_lbl)
        
        self.update_status = QLabel("جاهز للبحث عن تحديثات...")
        self.update_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        c_layout.addWidget(self.update_status)
        
        self.update_btn = QPushButton("البحث عن تحديثات")
        self.update_btn.setFixedHeight(40)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.PRIMARY}; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY_HOVER}; }}
        """)
        self.update_btn.clicked.connect(self._check_updates)
        c_layout.addWidget(self.update_btn)
        
        layout.addWidget(card)
        layout.addStretch()
        
    def _check_updates(self):
        self.update_btn.setEnabled(False)
        self.update_status.setText("جاري البحث...")
        import updater
        self.updater = updater.Updater(VERSION)
        self.updater.update_available.connect(self._on_update_found)
        self.updater.check_finished.connect(self._on_check_finished)
        self.updater.check_for_updates()
        
    def _on_update_found(self, version, url, body):
        self.update_status.setText(f"تحديث جديد متاح! الإصدار {version}")
        self.update_status.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 14px; font-weight: bold;")
        self.update_btn.setText("تنزيل التحديث الآن")
        
        # Disconnect old, connect new
        self.update_btn.clicked.disconnect()
        self.update_btn.clicked.connect(lambda: self._open_url(url))
        self.update_btn.setEnabled(True)
        
    def _on_check_finished(self, found):
        if not found:
            self.update_status.setText("أنت تستخدم أحدث إصدار.")
            self.update_btn.setEnabled(True)
            self.update_btn.setText("البحث عن تحديثات")
            
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
        
        show_act = QAction("إظهار النافذة", self)
        show_act.triggered.connect(self.showNormal)
        menu.addAction(show_act)
        
        quit_act = QAction("إغلاق نهائي", self)
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
