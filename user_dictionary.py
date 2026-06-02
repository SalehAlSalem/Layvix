import json
import os

USER_DICT_FILE = "user_dict.json"

# In-memory store
user_dict = {}

def load_user_dict():
    global user_dict
    if os.path.exists(USER_DICT_FILE):
        try:
            with open(USER_DICT_FILE, 'r', encoding='utf-8') as f:
                user_dict = json.load(f)
        except Exception as e:
            print(f"Error loading user dictionary: {e}")
            user_dict = {}
    else:
        user_dict = {}

def save_user_dict():
    try:
        with open(USER_DICT_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving user dictionary: {e}")

def add_correction(wrong_word, correct_word):
    user_dict[wrong_word] = correct_word
    save_user_dict()

def get_correction(word):
    return user_dict.get(word)

# Initialize
load_user_dict()
