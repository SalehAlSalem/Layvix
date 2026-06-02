from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QTabWidget, QCheckBox,
                             QLineEdit, QListWidget, QInputDialog, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent, QKeySequence, QIcon
import user_dictionary
import settings
import active_window
import os


class HotkeyInput(QLineEdit):
    def __init__(self, default_text=""):
        super().__init__(default_text)
        self.setPlaceholderText("اضغط على الاختصار هنا...")

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            self.clear()
            return
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_unknown):
            return
        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier: parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier: parts.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier: parts.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier: parts.append("windows")
        key_map = {
            Qt.Key.Key_Pause: "pause", Qt.Key.Key_ScrollLock: "scroll lock",
            Qt.Key.Key_Print: "print screen", Qt.Key.Key_Insert: "insert",
            Qt.Key.Key_Home: "home", Qt.Key.Key_End: "end",
            Qt.Key.Key_PageUp: "page up", Qt.Key.Key_PageDown: "page down",
            Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down",
            Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
            Qt.Key.Key_Escape: "esc",
            Qt.Key.Key_F1: "f1", Qt.Key.Key_F2: "f2", Qt.Key.Key_F3: "f3",
            Qt.Key.Key_F4: "f4", Qt.Key.Key_F5: "f5", Qt.Key.Key_F6: "f6",
            Qt.Key.Key_F7: "f7", Qt.Key.Key_F8: "f8", Qt.Key.Key_F9: "f9",
            Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
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
    hotkeys_changed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.app_enabled = True
        self.initUI()
        self.show_dashboard_signal.connect(self.show_and_activate)
        
        # Auto-refresh activity log every 3 seconds
        self._log_timer = QTimer()
        self._log_timer.timeout.connect(self._refresh_activity_log)
        self._log_timer.start(3000)

    def initUI(self):
        self.setWindowTitle("Layvix - Dashboard")
        self.resize(650, 500)

        # Try to load icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layvix.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Dark Cyan Theme
        self.setStyleSheet("""
            QWidget {
                background-color: #121619;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #1e262c;
                border-radius: 4px;
                background: #181d22;
            }
            QTabBar::tab {
                background: #181d22;
                color: #8c9baf;
                padding: 10px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #252d35;
                color: #00d2ff;
                border-bottom: 2px solid #00d2ff;
            }
            QPushButton {
                background-color: #1e262c;
                color: #e0e0e0;
                border: 1px solid #2d3844;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d3844;
                color: #00d2ff;
            }
            QPushButton#primaryBtn {
                background-color: #007a82;
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background-color: #00b4bf;
            }
            QPushButton#dangerBtn {
                background-color: #5c2020;
                color: #ff6b6b;
                border: 1px solid #7a2d2d;
            }
            QPushButton#dangerBtn:hover {
                background-color: #7a2d2d;
            }
            QLineEdit, QTableWidget, QListWidget, QTextEdit {
                background-color: #1e262c;
                border: 1px solid #2d3844;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 1px solid #00d2ff;
            }
            QHeaderView::section {
                background-color: #121619;
                color: #00d2ff;
                padding: 4px;
                border: 1px solid #2d3844;
            }
            QLabel {
                font-size: 14px;
            }
            QCheckBox {
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.tabs = QTabWidget()

        # Tab 1: Dashboard
        self.tab_dashboard = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "📊 لوحة التحكم")

        # Tab 2: Dictionary
        self.tab_dict = QWidget()
        self.setup_dict_tab()
        self.tabs.addTab(self.tab_dict, "📖 القاموس")

        # Tab 3: Settings
        self.tab_settings = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.tab_settings, "⚙️ الإعدادات")

        # Tab 4: Activity Log
        self.tab_log = QWidget()
        self.setup_log_tab()
        self.tabs.addTab(self.tab_log, "📋 سجل الأحداث")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def setup_dashboard_tab(self):
        layout = QVBoxLayout()

        title = QLabel("Layvix v1.0.1")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00d2ff; margin-bottom: 5px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("مصحح اللغتين الذكي")
        subtitle.setStyleSheet("font-size: 16px; color: #8c9baf; margin-bottom: 15px;")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        self.toggle_btn = QPushButton("🟢  البرنامج: مُفعل (انقر للإيقاف)")
        self.toggle_btn.setObjectName("primaryBtn")
        self.toggle_btn.setMinimumHeight(55)
        self.toggle_btn.setStyleSheet("font-size: 16px; background-color: #007a82; color: white; border: none; border-radius: 8px; padding: 12px;")
        self.toggle_btn.clicked.connect(self.on_toggle_clicked)
        layout.addWidget(self.toggle_btn)

        layout.addSpacing(15)

        # Stats
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: #1e262c; border-radius: 8px; padding: 15px;")
        stats_layout = QHBoxLayout(stats_widget)

        self.stat_today = QLabel("0")
        self.stat_total = QLabel("0")
        self.stat_learned = QLabel("0")

        for label, title_text in [
            (self.stat_today, "تصحيحات اليوم"),
            (self.stat_total, "إجمالي التصحيحات"),
            (self.stat_learned, "كلمات مُتعلَّمة")
        ]:
            col = QVBoxLayout()
            label.setStyleSheet("font-size: 32px; font-weight: bold; color: #00d2ff;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t = QLabel(title_text)
            t.setStyleSheet("font-size: 12px; color: #8c9baf;")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(label)
            col.addWidget(t)
            stats_layout.addLayout(col)

        layout.addWidget(stats_widget)

        layout.addSpacing(10)

        # Quick Tips
        tips = QLabel(
            f"<b>💡 اختصارات سريعة:</b><br><br>"
            f"1. التحويل اليدوي: حدد النص واضغط <b style='color:#00d2ff'>{settings.get_setting('manual_hotkey')}</b><br>"
            f"2. التراجع الذكي: اضغط <b style='color:#00d2ff'>{settings.get_setting('undo_hotkey')}</b> بعد أي تصحيح خاطئ<br>"
            f"3. نافذة الإعدادات: <b style='color:#00d2ff'>{settings.get_setting('overlay_hotkey')}</b>"
        )
        tips.setStyleSheet("color: #8c9baf; background: #1e262c; padding: 12px; border-radius: 8px;")
        tips.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(tips)

        layout.addStretch()
        self.tab_dashboard.setLayout(layout)

    def setup_dict_tab(self):
        layout = QVBoxLayout()
        desc = QLabel("القاموس الشخصي — يتعلمه البرنامج تلقائياً عند استخدام التراجع الذكي.")
        desc.setStyleSheet("color: #8c9baf;")
        layout.addWidget(desc)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["الكلمة الأصلية", "الكلمة المقابلة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_dictionary)
        delete_btn = QPushButton("🗑️ حذف المحدد")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

        self.tab_dict.setLayout(layout)
        self.load_dictionary()

    def setup_settings_tab(self):
        layout = QVBoxLayout()

        self.startup_cb = QCheckBox("تشغيل البرنامج تلقائياً عند إقلاع ويندوز")
        self.startup_cb.setChecked(settings.get_setting("run_on_startup") or False)
        self.startup_cb.stateChanged.connect(self.save_settings)
        layout.addWidget(self.startup_cb)

        layout.addSpacing(15)
        layout.addWidget(QLabel("<b>⌨️ اختصارات لوحة المفاتيح:</b>"))
        hk_layout = QVBoxLayout()

        for label_text, attr_name, setting_key in [
            ("نافذة الإعدادات:", "overlay_hk_input", "overlay_hotkey"),
            ("التراجع الذكي (Undo):", "undo_hk_input", "undo_hotkey"),
            ("التحويل اليدوي:", "manual_hk_input", "manual_hotkey"),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            inp = HotkeyInput(settings.get_setting(setting_key) or "")
            setattr(self, attr_name, inp)
            row.addWidget(inp)
            hk_layout.addLayout(row)

        save_hk_btn = QPushButton("💾 حفظ وتحديث الاختصارات")
        save_hk_btn.setObjectName("primaryBtn")
        save_hk_btn.clicked.connect(self.save_settings)
        hk_layout.addWidget(save_hk_btn)
        layout.addLayout(hk_layout)

        layout.addSpacing(15)
        layout.addWidget(QLabel("<b>🚫 البرامج المستثناة (لن يعمل المصحح داخلها):</b>"))

        self.excluded_list = QListWidget()
        for app in (settings.get_setting("excluded_apps") or []):
            self.excluded_list.addItem(app)
        layout.addWidget(self.excluded_list)

        ex_btn_layout = QHBoxLayout()
        add_app_btn = QPushButton("➕ إضافة برنامج يدوياً")
        add_app_btn.clicked.connect(self.add_excluded_app)

        add_current_btn = QPushButton("🎯 إضافة التطبيق الحالي")
        add_current_btn.setObjectName("primaryBtn")
        add_current_btn.clicked.connect(self.add_current_app)

        del_app_btn = QPushButton("🗑️ حذف")
        del_app_btn.setObjectName("dangerBtn")
        del_app_btn.clicked.connect(self.del_excluded_app)

        ex_btn_layout.addWidget(add_current_btn)
        ex_btn_layout.addWidget(add_app_btn)
        ex_btn_layout.addWidget(del_app_btn)
        layout.addLayout(ex_btn_layout)

        self.tab_settings.setLayout(layout)

    def setup_log_tab(self):
        layout = QVBoxLayout()
        desc = QLabel("سجل آخر 50 حدث — التصحيحات، التراجعات، والأخطاء.")
        desc.setStyleSheet("color: #8c9baf;")
        layout.addWidget(desc)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; "
            "background-color: #0d1117; color: #c9d1d9; border: 1px solid #2d3844; border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(self.log_display)

        copy_btn = QPushButton("📋 نسخ السجل")
        copy_btn.clicked.connect(self._copy_log)
        layout.addWidget(copy_btn)

        self.tab_log.setLayout(layout)

    # --- Actions ---
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

        apps = [self.excluded_list.item(i).text() for i in range(self.excluded_list.count())]
        settings.set_setting("excluded_apps", apps)

        if old_overlay != new_overlay or old_undo != new_undo or old_manual != new_manual:
            self.hotkeys_changed_signal.emit()

        QMessageBox.information(self, "نجاح ✅", "تم حفظ الإعدادات بنجاح!")

    def add_excluded_app(self):
        text, ok = QInputDialog.getText(self, 'إضافة استثناء', 'اكتب اسم ملف البرنامج (مثال: chrome.exe):')
        if ok and text:
            text = text.strip().lower()
            if not text.endswith(".exe"):
                text += ".exe"
            self.excluded_list.addItem(text)
            self.save_settings()

    def add_current_app(self):
        """Detect the previously active window's exe and add it to exclusions."""
        try:
            exe = active_window.get_active_window_exe()
            if exe and exe.lower() not in ["layvix.exe", "python.exe", "pythonw.exe"]:
                # Check if already in list
                existing = [self.excluded_list.item(i).text() for i in range(self.excluded_list.count())]
                if exe.lower() not in [e.lower() for e in existing]:
                    self.excluded_list.addItem(exe.lower())
                    self.save_settings()
                    QMessageBox.information(self, "تم ✅", f"تم إضافة '{exe}' لقائمة الاستثناءات!")
                else:
                    QMessageBox.information(self, "موجود", f"'{exe}' موجود بالفعل في القائمة.")
            else:
                QMessageBox.warning(self, "تنبيه", "لم يتم العثور على تطبيق نشط مناسب.")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل اكتشاف التطبيق: {e}")

    def del_excluded_app(self):
        selected = self.excluded_list.selectedItems()
        if selected:
            self.excluded_list.takeItem(self.excluded_list.row(selected[0]))
            self.save_settings()

    def update_toggle_button(self, is_enabled):
        self.app_enabled = is_enabled
        if is_enabled:
            self.toggle_btn.setText("🟢  البرنامج: مُفعل (انقر للإيقاف)")
            self.toggle_btn.setStyleSheet("font-size: 16px; background-color: #007a82; color: white; border: none; border-radius: 8px; padding: 12px;")
        else:
            self.toggle_btn.setText("🔴  البرنامج: متوقف (انقر للتشغيل)")
            self.toggle_btn.setStyleSheet("font-size: 16px; background-color: #3a3a3a; color: #888; border: none; border-radius: 8px; padding: 12px;")

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
        if not selected_rows:
            return
        row = selected_rows[0].row()
        wrong_word = self.table.item(row, 0).text()
        if wrong_word in user_dictionary.user_dict:
            del user_dictionary.user_dict[wrong_word]
            user_dictionary.save_user_dict()
            self.load_dictionary()

    def _refresh_activity_log(self):
        from logger import get_activity_log
        entries = get_activity_log()
        if entries:
            text = "\n".join([f"[{e['time']}] {e['type']}: {e['message']}" for e in reversed(entries)])
            self.log_display.setPlainText(text)
        
        # Update stats
        try:
            import main
            stats = main.get_stats()
            self.stat_today.setText(str(stats.get("corrections_today", 0)))
            self.stat_total.setText(str(stats.get("total_corrections", 0)))
            self.stat_learned.setText(str(stats.get("words_learned", 0)))
        except Exception:
            pass

    def _copy_log(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_display.toPlainText())
        QMessageBox.information(self, "تم ✅", "تم نسخ السجل!")

    def show_and_activate(self):
        self.show()
        self.activateWindow()
        self.load_dictionary()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
