from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QTabWidget, QCheckBox, 
                             QLineEdit, QListWidget, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QKeySequence
import user_dictionary
import settings

class HotkeyInput(QLineEdit):
    def __init__(self, default_text=""):
        super().__init__(default_text)
        self.setPlaceholderText("اضغط على الاختصار هنا...")

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            self.clear()
            return
            
        # Ignore if only modifier is pressed
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_unknown):
            return
            
        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier: parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier: parts.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier: parts.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier: parts.append("windows")
        
        key_map = {
            Qt.Key.Key_Pause: "pause",
            Qt.Key.Key_ScrollLock: "scroll lock",
            Qt.Key.Key_Print: "print screen",
            Qt.Key.Key_Insert: "insert",
            Qt.Key.Key_Home: "home",
            Qt.Key.Key_End: "end",
            Qt.Key.Key_PageUp: "page up",
            Qt.Key.Key_PageDown: "page down",
            Qt.Key.Key_Up: "up",
            Qt.Key.Key_Down: "down",
            Qt.Key.Key_Left: "left",
            Qt.Key.Key_Right: "right",
            Qt.Key.Key_Escape: "esc",
        }
        
        if key in key_map:
            key_name = key_map[key]
        else:
            key_name = QKeySequence(key).toString().lower()
            
        if key_name:
            parts.append(key_name)
            self.setText("+".join(parts))

class MainWindow(QWidget):
    toggle_app_signal = pyqtSignal()
    show_dashboard_signal = pyqtSignal()
    hotkeys_changed_signal = pyqtSignal() # Emitted when hotkeys change
    
    def __init__(self):
        super().__init__()
        self.app_enabled = True
        self.initUI()
        self.show_dashboard_signal.connect(self.show_and_activate)
        
    def initUI(self):
        self.setWindowTitle("Layvix - Dashboard")
        self.resize(600, 450)
        
        # Dark Theme
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI', Arial; }
            QTabWidget::pane { border: 1px solid #444; border-radius: 4px; }
            QTabBar::tab { background: #2b2b2b; color: #ccc; padding: 10px 20px; border: 1px solid #444; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #3c3c3c; color: white; font-weight: bold; }
            QLabel { font-size: 14px; }
            QPushButton { background-color: #333333; border: 1px solid #555555; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #444444; }
            QPushButton#primaryBtn { background-color: #0078D7; font-weight: bold; }
            QPushButton#primaryBtn:hover { background-color: #1084ea; }
            QPushButton#dangerBtn { background-color: #a83232; }
            QPushButton#dangerBtn:hover { background-color: #c93b3b; }
            QLineEdit { background-color: #2b2b2b; border: 1px solid #555; padding: 5px; color: white; }
            QTableWidget, QListWidget { background-color: #2b2b2b; border: 1px solid #444; gridline-color: #444; }
            QHeaderView::section { background-color: #333; padding: 4px; border: 1px solid #444; }
            QCheckBox { font-size: 14px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Dashboard
        self.tab_dashboard = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "لوحة التحكم (Dashboard)")
        
        # Tab 2: Dictionary
        self.tab_dict = QWidget()
        self.setup_dict_tab()
        self.tabs.addTab(self.tab_dict, "القاموس (Dictionary)")
        
        # Tab 3: Settings
        self.tab_settings = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.tab_settings, "الإعدادات (Settings)")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def setup_dashboard_tab(self):
        layout = QVBoxLayout()
        
        title = QLabel("حالة المصحح التلقائي")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078D7; margin-bottom: 20px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.toggle_btn = QPushButton("البرنامج: مُفعل (انقر للإيقاف)")
        self.toggle_btn.setObjectName("primaryBtn")
        self.toggle_btn.setMinimumHeight(60)
        self.toggle_btn.setStyleSheet("font-size: 18px;")
        self.toggle_btn.clicked.connect(self.on_toggle_clicked)
        layout.addWidget(self.toggle_btn)
        
        layout.addSpacing(30)
        
        # Quick Tips
        tips = QLabel(
            "<b>💡 اختصارات سريعة (الافتراضية):</b><br><br>"
            f"1. تصحيح كلمة بالماوس: حدد الكلمة واضغط <b>{settings.get_setting('overlay_hotkey')}</b><br>"
            f"2. تراجع ذكي (Undo): اضغط <b>{settings.get_setting('undo_hotkey')}</b> فوراً بعد أي تصحيح خاطئ<br>"
        )
        tips.setStyleSheet("color: #aaaaaa; background: #222; padding: 15px; border-radius: 8px;")
        tips.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(tips)
        
        layout.addStretch()
        self.tab_dashboard.setLayout(layout)

    def setup_dict_tab(self):
        layout = QVBoxLayout()
        desc = QLabel("هذا هو قاموسك الشخصي الذي يتعلمه البرنامج.\nعندما تستخدم (التراجع الذكي)، سيتم حفظ الكلمة هنا لمنع تصحيحها مجدداً.")
        layout.addWidget(desc)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["الكلمة الخاطئة", "الكلمة الصحيحة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_dictionary)
        
        delete_btn = QPushButton("حذف المحدد")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self.delete_selected)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        
        self.tab_dict.setLayout(layout)
        self.load_dictionary()

    def setup_settings_tab(self):
        layout = QVBoxLayout()
        
        # Startup Option
        self.startup_cb = QCheckBox("تشغيل البرنامج تلقائياً عند إقلاع ويندوز")
        self.startup_cb.setChecked(settings.get_setting("run_on_startup"))
        self.startup_cb.stateChanged.connect(self.save_settings)
        layout.addWidget(self.startup_cb)
        
        layout.addSpacing(15)
        
        # Hotkeys
        layout.addWidget(QLabel("<b>اختصارات لوحة المفاتيح:</b>"))
        hk_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("استدعاء نافذة إضافة استثناء:"))
        self.overlay_hk_input = HotkeyInput(settings.get_setting("overlay_hotkey"))
        row1.addWidget(self.overlay_hk_input)
        hk_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("التراجع الذكي (Undo):"))
        self.undo_hk_input = HotkeyInput(settings.get_setting("undo_hotkey"))
        row2.addWidget(self.undo_hk_input)
        hk_layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("التحويل اليدوي للنص المحدد:"))
        self.manual_hk_input = HotkeyInput(settings.get_setting("manual_hotkey"))
        row3.addWidget(self.manual_hk_input)
        hk_layout.addLayout(row3)
        
        save_hk_btn = QPushButton("حفظ وتحديث الاختصارات")
        save_hk_btn.setObjectName("primaryBtn")
        save_hk_btn.clicked.connect(self.save_settings)
        hk_layout.addWidget(save_hk_btn)
        layout.addLayout(hk_layout)
        
        layout.addSpacing(15)
        
        # Excluded Apps
        layout.addWidget(QLabel("<b>البرامج المستثناة (لن يعمل المصحح داخلها):</b>"))
        self.excluded_list = QListWidget()
        for app in settings.get_setting("excluded_apps"):
            self.excluded_list.addItem(app)
        layout.addWidget(self.excluded_list)
        
        ex_btn_layout = QHBoxLayout()
        add_app_btn = QPushButton("إضافة برنامج (exe)")
        add_app_btn.clicked.connect(self.add_excluded_app)
        del_app_btn = QPushButton("حذف البرنامج المحدد")
        del_app_btn.setObjectName("dangerBtn")
        del_app_btn.clicked.connect(self.del_excluded_app)
        
        ex_btn_layout.addWidget(add_app_btn)
        ex_btn_layout.addWidget(del_app_btn)
        layout.addLayout(ex_btn_layout)
        
        self.tab_settings.setLayout(layout)

    def save_settings(self):
        settings.set_setting("run_on_startup", self.startup_cb.isChecked())
        
        old_overlay = settings.get_setting("overlay_hotkey")
        old_undo = settings.get_setting("undo_hotkey")
        old_manual = settings.get_setting("manual_hotkey")
        
        new_overlay = self.overlay_hk_input.text().strip().lower()
        new_undo = self.undo_hk_input.text().strip().lower()
        new_manual = self.manual_hk_input.text().strip().lower()
        
        settings.set_setting("overlay_hotkey", new_overlay)
        settings.set_setting("undo_hotkey", new_undo)
        settings.set_setting("manual_hotkey", new_manual)
        
        # Save excluded apps
        apps = [self.excluded_list.item(i).text() for i in range(self.excluded_list.count())]
        settings.set_setting("excluded_apps", apps)
        
        # Emit signal to rehook if hotkeys changed
        if old_overlay != new_overlay or old_undo != new_undo or old_manual != new_manual:
            self.hotkeys_changed_signal.emit()
            
        QMessageBox.information(self, "نجاح", "تم حفظ الإعدادات بنجاح!")

    def add_excluded_app(self):
        text, ok = QInputDialog.getText(self, 'إضافة استثناء', 'اكتب اسم ملف البرنامج (مثال: chrome.exe):')
        if ok and text:
            text = text.strip().lower()
            if not text.endswith(".exe"): text += ".exe"
            self.excluded_list.addItem(text)
            self.save_settings()

    def del_excluded_app(self):
        selected = self.excluded_list.selectedItems()
        if selected:
            self.excluded_list.takeItem(self.excluded_list.row(selected[0]))
            self.save_settings()

    def update_toggle_button(self, is_enabled):
        self.app_enabled = is_enabled
        if is_enabled:
            self.toggle_btn.setText("البرنامج: مُفعل (انقر للإيقاف)")
            self.toggle_btn.setStyleSheet("background-color: #0078D7; font-weight: bold; font-size: 18px; padding: 10px;")
        else:
            self.toggle_btn.setText("البرنامج: متوقف (انقر للتشغيل)")
            self.toggle_btn.setStyleSheet("background-color: #666666; font-weight: bold; font-size: 18px; padding: 10px;")

    def on_toggle_clicked(self):
        self.toggle_app_signal.emit()

    def load_dictionary(self):
        user_dictionary.load_user_dict()
        dict_data = user_dictionary.user_dict
        self.table.setRowCount(len(dict_data))
        for row, (wrong, correct) in enumerate(dict_data.items()):
            self.table.setItem(row, 0, QTableWidgetItem(wrong))
            self.table.setItem(row, 1, QTableWidgetItem(correct))

    def delete_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows: return
        row = selected_rows[0].row()
        wrong_word = self.table.item(row, 0).text()
        if wrong_word in user_dictionary.user_dict:
            del user_dictionary.user_dict[wrong_word]
            user_dictionary.save_user_dict()
            self.load_dictionary()

    def show_and_activate(self):
        self.show()
        self.activateWindow()
        self.load_dictionary()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
