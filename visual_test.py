import sys
import time
import subprocess
from pynput.keyboard import Controller, Key

sys.stdout.reconfigure(encoding='utf-8')
from pynput.keyboard import Controller, Key

def visual_test():
    print("=== بدء الاختبار البصري (Visual E2E Test) ===")
    print("الرجاء عدم لمس الكيبورد... سيتم فتح المفكرة الآن!")
    time.sleep(2)
    
    # Open Notepad
    print("Opening Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2.5) # Wait for Notepad to open and get focus
    
    keyboard = Controller()
    
    def type_slow(text):
        for char in text:
            if char.isupper():
                with keyboard.pressed(Key.shift):
                    keyboard.type(char.lower())
            else:
                keyboard.type(char)
            time.sleep(0.08) # Type like a human
            
    # Typing Test 1
    type_slow("Test 1 (Full Arabic): ")
    time.sleep(0.5)
    type_slow("lvpfh ;dt hgphg hkh hsld whgp , fpf hg`;hx hghw'khud []h ")
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(1.5)
    
    # Typing Test 2
    type_slow("Test 2 (Mixed Lang): ")
    time.sleep(0.5)
    type_slow("hi saleh this is my new app lvpfh jfhv; hggi ")
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(1.5)
    
    # Typing Test 3
    type_slow("Test 3 (Retroactive): ")
    time.sleep(0.5)
    type_slow("the thil ugd is very la ghki today ")
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    
    print("\n✅ تم الاختبار بنجاح! انظر إلى شاشتك.")

if __name__ == "__main__":
    visual_test()
