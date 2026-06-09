import sys
import time
from collections import namedtuple

sys.stdout.reconfigure(encoding='utf-8')

# Ensure settings are mocked before anything else imports them
import settings
settings.set_setting("min_word_length", 3)
settings.set_setting("retroactive_correction", True)
settings.set_setting("ai_confidence_threshold", 0.75)

# Mock active window to not skip processing
import active_window
active_window.get_active_window_exe = lambda: "mock.exe"

import layout_helper
layout_helper.get_current_language = lambda: 0 # Simulate English keyboard layout

import main
import ai_engine

# Force synchronous loading of the AI model
print("AI Model is automatically loaded upon import!")
print("AI Model Loaded!")

KeyEvent = namedtuple('KeyEvent', ['name', 'event_type'])

class MockWorker(main.CoreWorker):
    def __init__(self):
        super().__init__()
        self.corrections_made = []
        
    def do_correction(self, wrong_word, corrected_word, switch=True, predicted_layout=None, is_selection=False):
        self.corrections_made.append((wrong_word, corrected_word))
        self.current_word.clear()

def simulate_typing(worker, text):
    for char in text:
        if char == ' ':
            worker.on_key_event(KeyEvent('space', 'down'))
            worker.on_key_event(KeyEvent('space', 'up'))
        elif char == '\b':
            worker.on_key_event(KeyEvent('backspace', 'down'))
            worker.on_key_event(KeyEvent('backspace', 'up'))
        else:
            worker.on_key_event(KeyEvent(char, 'down'))
            worker.on_key_event(KeyEvent(char, 'up'))
        time.sleep(0.01)
    
    # Wait for the background _process_word threads to complete
    time.sleep(0.5)

def run_tests():
    print("\n=== بدء اختبارات التصحيح الآلي (Automated Tests) ===")
    
    # Test 1: Normal English
    worker = MockWorker()
    simulate_typing(worker, "hello ")
    if len(worker.corrections_made) == 0:
        print("[PASS] ✅ Test 1: Normal English word ignored.")
    else:
        print("[FAIL] ❌ Test 1: Expected 0 corrections, got:", worker.corrections_made)
        
    # Test 2: Normal Arabic
    worker = MockWorker()
    simulate_typing(worker, "lvpfh ") # مرحبا
    if len(worker.corrections_made) == 1 and worker.corrections_made[0][1] == "مرحبا":
        print("[PASS] ✅ Test 2: Normal Arabic word corrected.")
    else:
        print("[FAIL] ❌ Test 2: Expected 'مرحبا', got:", worker.corrections_made)
        
    # Test 3: Short Word Ignored
    worker = MockWorker()
    simulate_typing(worker, "la ") # مش
    if len(worker.corrections_made) == 0:
        print("[PASS] ✅ Test 3: Short Arabic word ignored temporarily.")
    else:
        print("[FAIL] ❌ Test 3: Expected 0 corrections, got:", worker.corrections_made)
        
    # Test 4: Retroactive Correction
    worker = MockWorker()
    simulate_typing(worker, "la ghki ") # مش لانه
    if len(worker.corrections_made) == 1 and worker.corrections_made[0][1] == "مش لانه":
        print("[PASS] ✅ Test 4: Retroactive correction works perfectly!")
    else:
        print("[FAIL] ❌ Test 4: Expected retroactive correction, got:", worker.corrections_made)
        
    # Test 5: Backspace Memory Wipe
    worker = MockWorker()
    simulate_typing(worker, "la")
    # Simulate manual backspaces
    simulate_typing(worker, "\b\b")
    # Simulate new word
    simulate_typing(worker, "ghki ")
    if len(worker.corrections_made) == 1 and worker.corrections_made[0][1] == "لانه":
        print("[PASS] ✅ Test 5: Backspace correctly cleared the memory buffer.")
    else:
        print("[FAIL] ❌ Test 5: Expected single correction, got:", worker.corrections_made)
        
    # Test 6: Low Confidence Retroactive Correction
    worker = MockWorker()
    simulate_typing(worker, "thil ugd ") # فاهم علي (thil has 71% confidence so it gets skipped)
    if len(worker.corrections_made) == 1 and worker.corrections_made[0][1] == "فاهم علي":
        print("[PASS] ✅ Test 6: Low confidence word (thil) corrected retroactively!")
    else:
        print("[FAIL] ❌ Test 6: Expected retroactive correction for 'thil', got:", worker.corrections_made)
        
    # Test 7: User's specific issue ("is Clean" typed in Arabic layout)
    worker = MockWorker()
    main.get_current_language = lambda: 1 # ARABIC
    simulate_typing(worker, "هس {مثشى ")
    
    if len(worker.corrections_made) == 1 and worker.corrections_made[0][1] == "is Clean":
        print("[PASS] ✅ Test 7: 'is Clean' typed in Arabic layout was retroactively corrected perfectly!")
    else:
        print("[FAIL] ❌ Test 7: Expected 'is Clean', got:", worker.corrections_made)
        
    main.get_current_language = lambda: 0 # Reset to English

if __name__ == "__main__":
    run_tests()
