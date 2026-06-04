import json
import os
from logger import get_logger

logger = get_logger()

# Default translations
TRANSLATIONS = {
    "ar": {
        "title": "🐙 Layvix AI",
        "dashboard": "لوحة التحكم",
        "learning_center": "مركز التعلم",
        "settings": "الإعدادات",
        "about": "تحديث وحول",
        "welcome": "مرحباً بك في Layvix 🐙",
        "welcome_sub": "محرك الذكاء الاصطناعي يعمل في الخلفية ويحلل نمط كتابتك.",
        "corrections_today": "⚡ تصحيحات اليوم",
        "total_corrections": "📊 إجمالي التصحيحات",
        "words_learned": "🧠 كلمات تعلمها",
        "auto_correction": "التصحيح التلقائي",
        "auto_desc_on": "نشط (تغيير اللغة فوراً عند الطباعة)",
        "auto_desc_off": "متوقف (تغيير اللغة يدوياً فقط بالاختصار)",
        "learning_title": "التعلم المستمر 🧠",
        "learning_sub": "يتعلم الذكاء الاصطناعي من تصحيحاتك اليدوية وتراجعاتك لتكوين نمط خاص بك.",
        "live_training": "تدريب مباشر",
        "undones": "تراجعات",
        "manual_corrections": "تصحيح يدوي",
        "engine_waiting": "نشاط المحرك: ينتظر إدخالك...",
        "reset_brain": "إعادة ضبط الدماغ (مسح الذاكرة)",
        "brain_reset_success": "✅ تم مسح الذاكرة بنجاح",
        "settings_title": "الإعدادات المتقدمة ⚙️",
        "hotkeys_section": "اختصارات لوحة المفاتيح",
        "undo_hotkey": "اختصار التراجع (Undo):",
        "manual_hotkey": "اختصار التصحيح اليدوي:",
        "press_shortcut": "اضغط على الاختصار الآن...",
        "ai_params": "معايير الذكاء الاصطناعي",
        "confidence": "دقة التدخل المطلوبة (الثقة):",
        "min_word_len": "الحد الأدنى لطول الكلمة:",
        "chars": "أحرف",
        "exclusions": "استثناء التطبيقات والألعاب",
        "exclusions_desc": "اكتب أسماء النوافذ المستثناة مفصولة بفاصلة (مثال: valorant, csgo)",
        "startup_section": "خيارات النظام",
        "run_on_startup": "تشغيل التطبيق تلقائياً مع بدء ويندوز",
        "language": "لغة الواجهة (Language):",
        "save_settings": "حفظ جميع الإعدادات",
        "settings_saved": "✅ تم الحفظ بنجاح!",
        "about_title": "حول Layvix ✨",
        "current_version": "الإصدار الحالي: {version}",
        "check_updates": "البحث عن تحديثات",
        "checking": "جاري البحث...",
        "update_available": "تحديث جديد متاح! الإصدار {version}",
        "download_update": "تنزيل التحديث الآن",
        "up_to_date": "أنت تستخدم أحدث إصدار.",
        "developer_info": "عن المطور",
        "made_with_love": "Made with love by Saleh ALSalem ❤️",
        "github_btn": "زيارة المشروع على GitHub",
        "show_window": "إظهار النافذة",
        "quit_app": "إغلاق نهائي",
        "lang_ar": "العربية",
        "lang_en": "English",
        "custom_words": "الكلمات المخصصة",
        "view_custom_words": "عرض كلمات القاموس",
        "no_words": "القاموس فارغ حالياً.",
        "use_personal_model": "استخدام الموديل الشخصي (يتعلم منك دائمًا)",
        "retroactive_correction": "التصحيح الرجعي للكلمات القصيرة (استشراف المستقبل)",
        "fine_tune_btn": "تدريب الموديل الآن (Fine-Tune)",
        "fine_tune_success": "✅ تم تدريب الموديل بنجاح!",
        "fine_tune_fail": "❌ فشل التدريب (القاموس فارغ؟)",
        "export_data_btn": "تصدير البيانات لمشاركتها مع المطور",
        "export_success": "✅ تم حفظ الملف على سطح المكتب"
    },
    "en": {
        "title": "🐙 Layvix AI",
        "dashboard": "Dashboard",
        "learning_center": "Learning Center",
        "settings": "Settings",
        "about": "About & Update",
        "welcome": "Welcome to Layvix 🐙",
        "welcome_sub": "The AI engine is running in the background, analyzing your typing patterns.",
        "corrections_today": "⚡ Today's Fixes",
        "total_corrections": "📊 Total Fixes",
        "words_learned": "🧠 Words Learned",
        "auto_correction": "Auto-Correction",
        "auto_desc_on": "Active (Fixes layouts instantly as you type)",
        "auto_desc_off": "Paused (Only fixes manually via hotkey)",
        "learning_title": "Continuous Learning 🧠",
        "learning_sub": "The AI learns from your manual corrections and undos to build your personal typing profile.",
        "live_training": "Live Training",
        "undones": "Undos",
        "manual_corrections": "Manual Fixes",
        "engine_waiting": "Engine Status: Waiting for input...",
        "reset_brain": "Reset Brain (Clear Memory)",
        "brain_reset_success": "✅ Memory cleared successfully",
        "settings_title": "Advanced Settings ⚙️",
        "hotkeys_section": "Keyboard Shortcuts",
        "undo_hotkey": "Undo Hotkey:",
        "manual_hotkey": "Manual Fix Hotkey:",
        "press_shortcut": "Press the shortcut now...",
        "ai_params": "AI Parameters",
        "confidence": "Required Confidence Threshold:",
        "min_word_len": "Minimum Word Length:",
        "chars": "chars",
        "exclusions": "Excluded Apps & Games",
        "exclusions_desc": "Type window names separated by commas (e.g. valorant, csgo)",
        "startup_section": "System Options",
        "run_on_startup": "Run automatically on Windows startup",
        "language": "Interface Language:",
        "save_settings": "Save All Settings",
        "settings_saved": "✅ Saved successfully!",
        "about_title": "About Layvix ✨",
        "current_version": "Current Version: {version}",
        "check_updates": "Check for Updates",
        "checking": "Checking...",
        "update_available": "New update available! Version {version}",
        "download_update": "Download Update Now",
        "up_to_date": "You are using the latest version.",
        "developer_info": "Developer Info",
        "made_with_love": "Made with love by Saleh ALSalem ❤️",
        "github_btn": "Visit Project on GitHub",
        "show_window": "Show Window",
        "quit_app": "Quit Application",
        "lang_ar": "العربية",
        "lang_en": "English",
        "custom_words": "Custom Words",
        "view_custom_words": "View Custom Dictionary",
        "no_words": "Dictionary is currently empty.",
        "use_personal_model": "Use Personal Model (Learns continuously)",
        "retroactive_correction": "Retroactive Correction for Short Words",
        "fine_tune_btn": "Fine-Tune Model Now",
        "fine_tune_success": "✅ Model Fine-Tuned Successfully!",
        "fine_tune_fail": "❌ Fine-Tuning Failed (Empty Dictionary?)",
        "export_data_btn": "Export Data to Share with Developer",
        "export_success": "✅ File saved to Desktop!"
    }
}

_current_lang = "ar"

def set_language(lang_code):
    global _current_lang
    if lang_code in TRANSLATIONS:
        _current_lang = lang_code
        logger.info(f"Language set to: {lang_code}")

def get_language():
    return _current_lang

def t(key, **kwargs):
    """
    Translate a key into the current language.
    Supports formatting with kwargs (e.g., t("current_version", version="3.4.0"))
    """
    text = TRANSLATIONS.get(_current_lang, TRANSLATIONS["ar"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
