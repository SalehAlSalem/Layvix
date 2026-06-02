import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
import user_dictionary

class OverlayWindow(QWidget):
    # Define a signal that can be emitted from another thread to show the window
    trigger_show = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.trigger_show.connect(self.display_window)

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Main container for styling
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #2b2b2b;
                border: 1px solid #4a4a4a;
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084ea;
            }
        """)

        container_layout = QVBoxLayout(container)
        
        # Title
        title = QLabel("AutoLayoutFixer - إضافة قاعدة جديدة")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        container_layout.addWidget(title)
        
        # Wrong Word
        self.wrong_input = QLineEdit()
        self.wrong_input.setPlaceholderText("الكلمة الخاطئة (مثال: ثءث)")
        container_layout.addWidget(QLabel("الكلمة الخاطئة:"))
        container_layout.addWidget(self.wrong_input)
        
        # Right Word
        self.correct_input = QLineEdit()
        self.correct_input.setPlaceholderText("الكلمة الصحيحة (مثال: exe)")
        container_layout.addWidget(QLabel("الكلمة الصحيحة:"))
        container_layout.addWidget(self.correct_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ القاعدة")
        save_btn.clicked.connect(self.save_rule)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet("background-color: #444444;")
        cancel_btn.clicked.connect(self.hide)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        container_layout.addLayout(btn_layout)

        layout.addWidget(container)
        self.setLayout(layout)
        self.resize(350, 250)

    def display_window(self, selected_text):
        self.wrong_input.setText(selected_text)
        self.correct_input.clear()
        
        # Move near mouse cursor
        from PyQt6.QtGui import QCursor
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 15, cursor_pos.y() + 15)
        
        self.show()
        self.activateWindow()
        self.correct_input.setFocus()

    def save_rule(self):
        wrong = self.wrong_input.text().strip()
        correct = self.correct_input.text().strip()
        if wrong and correct:
            user_dictionary.add_correction(wrong, correct)
            # Show a system notification
            from plyer import notification
            try:
                notification.notify(
                    title="تم حفظ القاعدة",
                    message=f"سيتم دائماً تحويل '{wrong}' إلى '{correct}'",
                    app_name="AutoLayoutFixer",
                    timeout=2
                )
            except:
                pass
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OverlayWindow()
    ex.display_window("ثءث")
    sys.exit(app.exec())
