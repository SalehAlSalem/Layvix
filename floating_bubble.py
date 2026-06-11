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
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(base_dir, "icon.svg")
        if not os.path.exists(self.icon_path):
            self.icon_path = os.path.join(base_dir, "icon.ico")
            
        self._set_active_style()
        self.layout.addWidget(self.label)
        
        self._drag_pos = None
        self._start_pos = None
        self.is_paused = False
        
        saved_x = int(settings.get_setting("bubble_x") or 100)
        saved_y = int(settings.get_setting("bubble_y") or 100)
        self.move(saved_x, saved_y)
        
    def update_size(self, size):
        self.current_size = size
        self.setFixedSize(size, size)
        if self.is_paused:
            self._set_paused_style()
        else:
            self._set_active_style()
        
    def _set_active_style(self):
        sz = getattr(self, 'current_size', 70)
        rad = int(sz / 2)
        
        from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
        from PyQt6.QtCore import Qt
        
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            target = QPixmap(sz, sz)
            target.fill(Qt.GlobalColor.transparent)
            painter = QPainter(target)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            path = QPainterPath()
            path.addEllipse(0, 0, sz, sz)
            painter.setClipPath(path)
            scaled = pixmap.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = int((sz - scaled.width()) / 2)
            y = int((sz - scaled.height()) / 2)
            painter.drawPixmap(x, y, scaled)
            painter.end()
            self.label.setPixmap(target)
        else:
            self.label.setText("🐙")
            
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(11, 19, 32, 220);
                color: white;
                font-size: {int(sz * 0.5)}px;
                border-radius: {rad}px;
                border: 2px solid rgba(72, 201, 176, 200);
            }}
            QLabel:hover {{
                background-color: rgba(18, 28, 47, 255);
                border: 2px solid rgba(91, 214, 192, 255);
            }}
        """)
        self.setToolTip("Layvix is RUNNING. Click to pause.")

    def _set_paused_style(self):
        sz = getattr(self, 'current_size', 70)
        rad = int(sz / 2)
        
        from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
        from PyQt6.QtCore import Qt
        
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            target = QPixmap(sz, sz)
            target.fill(Qt.GlobalColor.transparent)
            painter = QPainter(target)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            path = QPainterPath()
            path.addEllipse(0, 0, sz, sz)
            painter.setClipPath(path)
            
            # Make it look "paused" by making it semi-transparent
            painter.setOpacity(0.4)
            scaled = pixmap.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = int((sz - scaled.width()) / 2)
            y = int((sz - scaled.height()) / 2)
            painter.drawPixmap(x, y, scaled)
            painter.end()
            self.label.setPixmap(target)
        else:
            self.label.setText("💤")
            
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(30, 10, 15, 220);
                color: white;
                font-size: {int(sz * 0.5)}px;
                border-radius: {rad}px;
                border: 2px solid rgba(255, 107, 107, 200);
            }}
            QLabel:hover {{
                background-color: rgba(45, 15, 20, 255);
                border: 2px solid rgba(255, 130, 130, 255);
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
            else:
                import settings
                settings.set_setting("bubble_x", self.x())
                settings.set_setting("bubble_y", self.y())
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
