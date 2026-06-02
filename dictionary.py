import os
import urllib.request

EN_WORDS_FILE = "en_words.txt"
AR_WORDS_FILE = "ar_words.txt"

# Sets for O(1) lookup
en_dictionary = set()
ar_dictionary = set()

def download_file(url, filename):
    print(f"Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

def ensure_dictionaries():
    if not os.path.exists(EN_WORDS_FILE):
        # 10k english words
        download_file("https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt", EN_WORDS_FILE)
    
    if not os.path.exists(AR_WORDS_FILE):
        # A curated list of common Arabic words might be hard to find a direct URL for right now.
        # Let's create a minimal list if it doesn't exist, and we can expand it.
        # Using Hermit Dave's frequency words
        ar_url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ar/ar_50k.txt"
        download_file(ar_url, AR_WORDS_FILE)

def load_dictionaries():
    ensure_dictionaries()
    
    if os.path.exists(EN_WORDS_FILE):
        with open(EN_WORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                en_dictionary.add(line.strip().lower())
                
    if os.path.exists(AR_WORDS_FILE):
        with open(AR_WORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # The file is formatted as: word count
                parts = line.strip().split()
                if parts:
                    ar_dictionary.add(parts[0])

    # Add some hardcoded very common words just in case the downloads failed or were incomplete
    en_dictionary.update(['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me'])
    ar_dictionary.update(['في', 'من', 'على', 'إلى', 'الله', 'لا', 'أن', 'عن', 'ما', 'هذا', 'يا', 'كل', 'أو', 'إن', 'بها', 'كان', 'هو', 'ولا', 'قال', 'التي', 'كما', 'ذلك', 'بعد', 'إلا', 'وقد', 'أي', 'ولم', 'هذه', 'وهو', 'ثم', 'الذي', 'بين', 'فإن', 'ولكن', 'مع', 'حتى', 'إذا', 'مرحبا', 'السلام', 'عليكم', 'كيف', 'الحال', 'شكرا'])

def is_valid_english(word):
    return word.lower() in en_dictionary

def is_valid_arabic(word):
    return word in ar_dictionary

# Initialize on import
load_dictionaries()
print(f"Loaded {len(en_dictionary)} English words and {len(ar_dictionary)} Arabic words.")

if __name__ == "__main__":
    print("Testing English:", is_valid_english("hello"))
    print("Testing Arabic:", is_valid_arabic("مرحبا"))
    print("Testing invalid:", is_valid_english("lvpfh"))
