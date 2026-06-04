import json
import os
from logger import get_logger, get_data_dir

logger = get_logger()

USER_DICT_FILE = os.path.join(get_data_dir(), "user_dict.json")
user_dict = {}


def load_user_dict():
    global user_dict
    if os.path.exists(USER_DICT_FILE):
        try:
            with open(USER_DICT_FILE, 'r', encoding='utf-8') as f:
                user_dict = json.load(f)
            logger.info(f"User dictionary loaded: {len(user_dict)} entries")
        except Exception as e:
            logger.error(f"Failed to load user dictionary: {e}")
            user_dict = {}
    else:
        user_dict = {}


def save_user_dict():
    try:
        with open(USER_DICT_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_dict, f, ensure_ascii=False, indent=4)
        logger.info(f"User dictionary saved: {len(user_dict)} entries")
    except Exception as e:
        logger.error(f"Failed to save user dictionary: {e}")


def add_correction(wrong, correct):
    user_dict[wrong] = correct
    save_user_dict()


def get_correction(word):
    return user_dict.get(word)

def get_custom_words():
    """Returns a list of strings representing the custom words and their corrections"""
    return [f"{k} ➔ {v}" for k, v in user_dict.items()]

# Initialize
load_user_dict()
