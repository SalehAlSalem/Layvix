import os
import json
import gzip
from logger import get_logger

logger = get_logger()

# Frequency dictionaries: word -> frequency (int)
_en_freq = {}
_ar_freq = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_dictionaries():
    """Load compressed frequency dictionaries from JSON.gz files."""
    global _en_freq, _ar_freq
    
    en_path = os.path.join(BASE_DIR, "en_freq.json.gz")
    ar_path = os.path.join(BASE_DIR, "ar_freq.json.gz")
    
    if os.path.exists(en_path):
        try:
            with gzip.open(en_path, "rt", encoding="utf-8") as f:
                _en_freq = json.load(f)
            logger.info(f"Loaded {len(_en_freq):,} English words with frequencies")
        except Exception as e:
            logger.error(f"Failed to load English dictionary: {e}")
    else:
        logger.warning(f"English dictionary not found: {en_path}")
    
    if os.path.exists(ar_path):
        try:
            with gzip.open(ar_path, "rt", encoding="utf-8") as f:
                _ar_freq = json.load(f)
            logger.info(f"Loaded {len(_ar_freq):,} Arabic words with frequencies")
        except Exception as e:
            logger.error(f"Failed to load Arabic dictionary: {e}")
    else:
        logger.warning(f"Arabic dictionary not found: {ar_path}")


def get_english_frequency(word: str) -> int:
    """Returns the frequency of an English word (0 = not found)."""
    return _en_freq.get(word.lower(), 0)


def get_arabic_frequency(word: str) -> int:
    """Returns the frequency of an Arabic word (0 = not found)."""
    return _ar_freq.get(word, 0)


def is_valid_english(word: str) -> bool:
    """Returns True if the word exists in the English dictionary."""
    return get_english_frequency(word) > 0


def is_valid_arabic(word: str) -> bool:
    """Returns True if the word exists in the Arabic dictionary."""
    return get_arabic_frequency(word) > 0


# Initialize on import
load_dictionaries()
