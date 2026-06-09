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

KeyEvent = namedtuple('KeyEvent', ['name', 'event_type'])

class MockWorker(main.CoreWorker):
    def __init__(self):
        super().__init__()
        self.corrections_made = []
        
    def do_correction(self, wrong_word, corrected_word, switch=True, predicted_layout=None, is_selection=False):
        self.corrections_made.append((wrong_word, corrected_word))
        self.current_word.clear()

def simulate_paragraph(worker, paragraph):
    print(f"\n[TYPING] {paragraph}")
    for char in paragraph:
        if char == ' ':
            worker.on_key_event(KeyEvent('space', 'down'))
            worker.on_key_event(KeyEvent('space', 'up'))
        elif char == '\b':
            worker.on_key_event(KeyEvent('backspace', 'down'))
            worker.on_key_event(KeyEvent('backspace', 'up'))
        else:
            worker.on_key_event(KeyEvent(char, 'down'))
            worker.on_key_event(KeyEvent(char, 'up'))
        time.sleep(0.005) # Fast typing simulation (200 chars/second)
    
    # Wait for the background _process_word threads to complete
    time.sleep(0.8)

def run_paragraph_tests():
    print("\n" + "="*50)
    print("=== بدء اختبارات الفقرات الطويلة (Long Paragraph Tests) ===")
    print("="*50)
    
    # Test 7: Long Arabic Sentence Typed in English
    # "مرحبا كيف الحال انا اسمي صالح و بحب الذكاء الاصطناعي جدا"
    worker = MockWorker()
    paragraph1 = "lvpfh ;dt hgphg hkh hsld whgp , fpf hg`;hx hghw'khud []h "
    simulate_paragraph(worker, paragraph1)
    print(">> Corrections Log:")
    for wrong, right in worker.corrections_made:
        print(f"   [+] {wrong}  ➔  {right}")
    
    # Test 8: Mixed Language Paragraph (English context + Arabic switch)
    # "hi saleh this is my new app lvpfh jfhv; hggi "
    worker = MockWorker()
    paragraph2 = "hi saleh this is my new app lvpfh jfhv; hggi "
    simulate_paragraph(worker, paragraph2)
    print(">> Corrections Log:")
    for wrong, right in worker.corrections_made:
        print(f"   [+] {wrong}  ➔  {right}")
        
    # Test 9: Real-time Rapid Typos with Retroactive Short Word Fix
    # "the thil ugd is very la ghki today" 
    # (thil ugd = فاهم علي) (la ghki = مش لانه)
    worker = MockWorker()
    paragraph3 = "the thil ugd is very la ghki today "
    simulate_paragraph(worker, paragraph3)
    print(">> Corrections Log:")
    for wrong, right in worker.corrections_made:
        print(f"   [+] {wrong}  ➔  {right}")

if __name__ == "__main__":
    run_paragraph_tests()
