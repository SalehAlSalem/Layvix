import sys
import time
from collections import namedtuple

sys.stdout.reconfigure(encoding='utf-8')

import settings
settings.set_setting("min_word_length", 3)
settings.set_setting("retroactive_correction", True)
settings.set_setting("ai_confidence_threshold", 0.75)

import active_window
active_window.get_active_window_exe = lambda: "mock.exe"
import layout_helper
layout_helper.get_current_language = lambda: 0

import main
from mapper import convert_word

KeyEvent = namedtuple('KeyEvent', ['name', 'event_type'])

class MockWorker(main.CoreWorker):
    def __init__(self):
        super().__init__()
        self.final_text = []
        
    def do_correction(self, wrong_word, corrected_word, switch=True, predicted_layout=None, is_selection=False):
        # Simulate backspaces: remove the wrong words from our buffer
        words_to_delete = len(wrong_word.split())
        for _ in range(words_to_delete):
            if self.final_text:
                self.final_text.pop()
        
        # Add the corrected words
        self.final_text.extend(corrected_word.split())

    def on_key_event(self, event):
        if event.name == 'space' and event.event_type == 'down':
            word_str = "".join(self.current_word).strip()
            if word_str:
                self.final_text.append(word_str)
                # Run synchronously for accurate testing
                self._process_word(word_str)
                self.current_word.clear()
            return
        elif event.name == 'backspace' and event.event_type == 'down':
            if self.current_word:
                self.current_word.pop()
            else:
                self.pending_short_word = None
            return
        
        # For standard character typing
        if event.event_type == 'down' and len(event.name) == 1:
            self.current_word.append(event.name)


def text_to_keystrokes(text):
    result = []
    for word in text.split():
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in word)
        if is_arabic:
            result.append(convert_word(word, 'ar_to_en'))
        else:
            result.append(word)
    return " ".join(result) + " "

def simulate_fast_typing(worker, text):
    for char in text:
        if char == ' ':
            worker.on_key_event(KeyEvent('space', 'down'))
        elif char == '\b':
            worker.on_key_event(KeyEvent('backspace', 'down'))
        else:
            worker.on_key_event(KeyEvent(char, 'down'))

def run_accuracy_test(name, expected_text):
    worker = MockWorker()
    typed_text = text_to_keystrokes(expected_text)
    
    simulate_fast_typing(worker, typed_text)
    
    final_result = " ".join(worker.final_text)
    
    expected_words = expected_text.split()
    result_words = final_result.split()
    
    correct_count = 0
    total = len(expected_words)
    
    diffs = []
    for i in range(min(total, len(result_words))):
        if expected_words[i] == result_words[i]:
            correct_count += 1
        else:
            diffs.append((expected_words[i], result_words[i]))
            
    accuracy = (correct_count / total) * 100 if total > 0 else 0
    
    print(f"\n==========================================")
    print(f"{name}")
    print(f"==========================================")
    print(f"Accuracy: {accuracy:.2f}% ({correct_count}/{total} words)")
    if diffs:
        print("\n[False Positives / Misses]")
        for exp, res in diffs:
            print(f"  Expected: {exp:<15} | AI Output: {res}")
            
    if len(expected_words) != len(result_words):
        print(f"\n[Warning] Length mismatch! Expected: {len(expected_words)}, Got: {len(result_words)}")
        
    return accuracy

if __name__ == "__main__":
    ar_para = "تعتبر هندسة البرمجيات وإدارة الخوادم السحابية من أهم المجالات التقنية في عصرنا الحالي عندما تقوم بتصميم نظام ذكي يعتمد على الذكاء الاصطناعي يجب عليك مراعاة استهلاك الموارد مثل الذاكرة والمعالج لضمان استقرار الأداء لقد تم تطوير العديد من المنصات المخصصة للطلاب لتسهيل تبادل المواد الجامعية والملخصات الدراسية بكفاءة عالية إن بناء خوارزميات دقيقة تتطلب تفكيرا هندسيا في المنطق الرياضي والتجربة المستمرة للوصول إلى أفضل تجربة مستخدم ممكنة دون أي إزعاج أو تأخير في الاستجابة أو استهلاك عشوائي للموارد"
    en_para = "Building a persistent artificial intelligence system requires a solid understanding of machine learning algorithms and software architecture When optimizing a background process the core engine must efficiently handle character n-grams without overloading the system resources Implementing a continuous online learning loop allows the model to adapt dynamically to user preferences over time Setting up the infrastructure on cloud services with robust security groups and self hosted environments ensures that data privacy is maintained while delivering high performance"
    mixed_para = "اليوم شغالين على تطوير نظام AI جديد بيعتمد على تقنية وتدريب الموديل عشان يحسن دقة ال System بشكل مستمر المشكلة الأساسية كانت في استهلاك ال CPU لما يكون البرنامج شغال في ال Background طوال الوقت بس حليناها عن طريق بناء State Buffer ذكي بيعمل Delay بسيط قبل ما ياخذ القرار الحاسم لما تعمل Deploy للتطبيق الخاص فيك على سيرفرات سحابية أو حتى تستخدم Docker لازم تنتبه جدا لل Memory allocation عشان ما يصير عندك مشاكل في الأداء بصراحة فكرة ال Retroactive Correction خلت تجربة ال User خرافية وسحرية جدا"
    
    acc1 = run_accuracy_test("1. Pure Arabic Text", ar_para)
    acc2 = run_accuracy_test("2. Pure English Text", en_para)
    acc3 = run_accuracy_test("3. Mixed Text (Stress Test)", mixed_para)
    
    print(f"\n>>> OVERALL SYSTEM ACCURACY: {(acc1+acc2+acc3)/3:.2f}% <<<")
