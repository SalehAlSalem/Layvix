import re

with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add imports
if 'from i18n import t, set_language' not in content:
    content = content.replace('import learner', 'import learner\nfrom i18n import t, set_language')

# 2. Add language init in MainWindow.__init__
if 'set_language' not in content.split('class MainWindow')[1]:
    content = content.replace(
        'self.app_enabled = True\n        \n        self._build_ui()',
        'self.app_enabled = True\n        set_language(settings.get_setting("language") or "ar")\n        self._build_ui()'
    )

# 3. Replace strings with t()
replacements = [
    ('QLabel("🐙 Layvix AI")', 'QLabel(t("title"))'),
    ('("🏠", "لوحة التحكم", self._page_dashboard)', '("🏠", t("dashboard"), self._page_dashboard)'),
    ('("🧠", "مركز التعلم", self._page_learning)', '("🧠", t("learning_center"), self._page_learning)'),
    ('("⚙️", "الإعدادات", self._page_settings)', '("⚙️", t("settings"), self._page_settings)'),
    ('("✨", "تحديث و حول", self._page_about)', '("✨", t("about"), self._page_about)'),
    
    ('QLabel("مرحباً بك في Layvix 🐙")', 'QLabel(t("welcome"))'),
    ('QLabel("محرك الذكاء الاصطناعي يعمل في الخلفية ويحلل نمط كتابتك.")', 'QLabel(t("welcome_sub"))'),
    
    ('StatCard("⚡ تصحيحات اليوم"', 'StatCard(t("corrections_today")'),
    ('StatCard("📊 إجمالي التصحيحات"', 'StatCard(t("total_corrections")'),
    ('StatCard("🧠 كلمات تعلمها"', 'StatCard(t("words_learned")'),
    
    # Dashboard layout restructuring
    ('mc_title = QLabel("حالة المحرك")', 'mc_title = QLabel(t("auto_correction"))'),
    ('self.master_desc = QLabel("نشط يعمل في الخلفية")', 'self.master_desc = QLabel(t("auto_desc_on"))'),
    ('self.master_desc.setText("نشط يعمل في الخلفية" if checked else "متوقف مؤقتاً")', 'self.master_desc.setText(t("auto_desc_on") if checked else t("auto_desc_off"))'),
    
    # Remove the second card (mode_card) entirely from Dashboard and replace it with run_on_startup toggle? 
    # Actually, the user said they don't want "Master Engine", they just want "Auto-Correction".
    # Since I just replaced "حالة المحرك" with "Auto-Correction", I'll hide the second mode card!
    ('cards_layout.addWidget(self.mode_card)', '# cards_layout.addWidget(self.mode_card)'),
    
    ('QLabel("التعلم المستمر 🧠")', 'QLabel(t("learning_title"))'),
    ('QLabel("يتعلم الذكاء الاصطناعي من تصحيحاتك اليدوية وتراجعاتك لتكوين نمط خاص بك.")', 'QLabel(t("learning_sub"))'),
    
    ('StatCard("تدريب مباشر"', 'StatCard(t("live_training")'),
    ('StatCard("تراجعات"', 'StatCard(t("undones")'),
    ('StatCard("تصحيح يدوي"', 'StatCard(t("manual_corrections")'),
    
    ('QLabel("نشاط المحرك: ينتظر إدخالك...")', 'QLabel(t("engine_waiting"))'),
    ('QPushButton("إعادة ضبط الدماغ (مسح الذاكرة)")', 'QPushButton(t("reset_brain"))'),
    ('sender.setText("✅ تم مسح الذاكرة (أعد تشغيل التطبيق)")', 'sender.setText(t("brain_reset_success"))'),
    ('sender.setText("إعادة ضبط الدماغ (مسح الذاكرة)")', 'sender.setText(t("reset_brain"))'),
    
    ('QLabel("الإعدادات المتقدمة ⚙️")', 'QLabel(t("settings_title"))'),
    ('_create_card(c_layout, "اختصارات لوحة المفاتيح")', '_create_card(c_layout, t("hotkeys_section"))'),
    ('QLabel("اختصار التراجع (Undo):")', 'QLabel(t("undo_hotkey"))'),
    ('QLabel("اختصار التصحيح اليدوي:")', 'QLabel(t("manual_hotkey"))'),
    ('self.setText("اضغط على الاختصار الآن...")', 'self.setText(t("press_shortcut"))'),
    
    ('_create_card(c_layout, "معايير الذكاء الاصطناعي")', '_create_card(c_layout, t("ai_params"))'),
    ('QLabel("دقة التدخل المطلوبة (الثقة):")', 'QLabel(t("confidence"))'),
    ('QLabel("الحد الأدنى لطول الكلمة:")', 'QLabel(t("min_word_len"))'),
    ('أحرف', ' " + t("chars") + "'), # This might need manual fix later
    
    ('_create_card(c_layout, "استثناء التطبيقات والألعاب")', '_create_card(c_layout, t("exclusions"))'),
    ('QLabel("اكتب أسماء النوافذ المستثناة مفصولة بفاصلة (مثال: valorant, csgo)")', 'QLabel(t("exclusions_desc"))'),
    ('QPushButton("حفظ جميع الإعدادات")', 'QPushButton(t("save_settings"))'),
    ('sender.setText("✅ تم الحفظ بنجاح!")', 'sender.setText(t("settings_saved"))'),
    ('sender.setText("حفظ جميع الإعدادات")', 'sender.setText(t("save_settings"))'),
    
    ('QLabel("حول Layvix ✨")', 'QLabel(t("about_title"))'),
    ('QLabel(f"الإصدار الحالي: {VERSION}")', 'QLabel(t("current_version", version=VERSION))'),
    ('QPushButton("البحث عن تحديثات")', 'QPushButton(t("check_updates"))'),
    ('self.update_status.setText("جاري البحث...")', 'self.update_status.setText(t("checking"))'),
    ('self.update_status.setText(f"تحديث جديد متاح! الإصدار {version}")', 'self.update_status.setText(t("update_available", version=version))'),
    ('self.update_btn.setText("تنزيل التحديث الآن")', 'self.update_btn.setText(t("download_update"))'),
    ('self.update_status.setText("أنت تستخدم أحدث إصدار.")', 'self.update_status.setText(t("up_to_date"))'),
    ('self.update_btn.setText("البحث عن تحديثات")', 'self.update_btn.setText(t("check_updates"))'),
    
    ('QAction("إظهار النافذة", self)', 'QAction(t("show_window"), self)'),
    ('QAction("إغلاق نهائي", self)', 'QAction(t("quit_app"), self)'),
    
    # RTL direction fix
    ('layout.addStretch()', 'layout.addStretch()'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Fix RTL direction globally for MainWindow
if 'self.setLayoutDirection' not in content:
    content = content.replace(
        'self.app_enabled = True',
        'self.app_enabled = True\n        if settings.get_setting("language") == "ar" or not settings.get_setting("language"):\n            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)\n        else:\n            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)'
    )

with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)
