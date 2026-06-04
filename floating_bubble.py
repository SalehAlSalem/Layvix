from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QPoint
import os

class FloatingBubble(QWidget):
    def __init__(self, core_loop):
        super().__init__()
        self.core_loop = core_loop
        # Window type keeps it persistent, WindowStaysOnTopHint keeps it on top
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        import settings
        self.current_size = int(settings.get_setting("bubble_size") or 70)
        self.setFixedSize(self.current_size, self.current_size)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel("🐙")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_active_style()
        self.layout.addWidget(self.label)
        
        self._drag_pos = None
        self._start_pos = None
        self.is_paused = False
        
        # Position top left initially to guarantee visibility on all monitor setups
        self.move(100, 100)
        
    def update_size(self, size):
        self.current_size = size
        self.setFixedSize(size, size)
        if self.is_paused:
            self._set_paused_style()
        else:
            self._set_active_style()
        
    def _set_active_style(self):
        sz = getattr(self, 'current_size', 70)
        font_sz = int(sz * 0.5)
        rad = int(sz / 2)
        
        self.label.setText("🐙")
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(20, 20, 30, 220);
                color: white;
                font-size: {font_sz}px;
                border-radius: {rad}px;
                border: 2px solid rgba(138, 43, 226, 200);
            }}
            QLabel:hover {{
                background-color: rgba(40, 40, 50, 255);
                border: 2px solid rgba(170, 80, 255, 255);
            }}
        """)
        self.setToolTip("Layvix is RUNNING. Click to pause.")

    def _set_paused_style(self):
        sz = getattr(self, 'current_size', 70)
        font_sz = int(sz * 0.5)
        rad = int(sz / 2)
        
        self.label.setText("💤")
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(40, 10, 10, 220);
                color: white;
                font-size: {font_sz}px;
                border-radius: {rad}px;
                border: 2px solid rgba(255, 50, 50, 200);
            }}
            QLabel:hover {{
                background-color: rgba(60, 20, 20, 255);
                border: 2px solid rgba(255, 80, 80, 255);
            }}
        """)
        self.setToolTip("Layvix is PAUSED. Click to resume.")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._start_pos:
            dist = (event.globalPosition().toPoint() - self._start_pos).manhattanLength()
            if dist < 5:  # It's a click, not a drag
                self.toggle_pause()
        self._drag_pos = None
        self._start_pos = None

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.core_loop:
            self.core_loop.enabled = not self.is_paused
            
        if self.is_paused:
            self._set_paused_style()
        else:
            self._set_active_style()
