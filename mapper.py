# mapper.py

EN_TO_AR = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'د',
    'a': 'ش', 's': 'س', 'd': 'ي', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ك', "'": 'ط',
    'z': 'ئ', 'x': 'ء', 'c': 'ؤ', 'v': 'ر', 'b': 'لا', 'n': 'ى', 'm': 'ة', ',': 'و', '.': 'ز', '/': 'ظ', '`': 'ذ',
    'Q': 'َ', 'W': 'ً', 'E': 'ُ', 'R': 'ٌ', 'T': 'لإ', 'Y': 'إ', 'U': '`', 'I': '÷', 'O': '×', 'P': '؛',
    'A': 'ِ', 'S': 'ٍ', 'D': ']', 'F': '[', 'G': 'لأ', 'H': 'أ', 'J': 'ـ', 'K': '،', 'L': '/',
    'Z': '~', 'X': 'ْ', 'C': '{', 'V': '}', 'B': 'لآ', 'N': 'آ', 'M': '\'', '<': ',', '>': '.', '?': '؟'
}

# Invert the dictionary for AR to EN
AR_TO_EN = {}
for en_char, ar_char in EN_TO_AR.items():
    if len(ar_char) == 1:
        AR_TO_EN[ar_char] = en_char

# Special handling for "لا" and its variations since they map back to a single English character
AR_TO_EN['لا'] = 'b'
AR_TO_EN['لأ'] = 'G'
AR_TO_EN['لإ'] = 'T'
AR_TO_EN['لآ'] = 'B'

def convert_word(word, direction='en_to_ar'):
    """
    Converts a string of text from one layout to the other.
    direction can be 'en_to_ar' or 'ar_to_en'
    """
    result = ""
    i = 0
    while i < len(word):
        # Look ahead for 2-character sequences in Arabic to English mapping
        if direction == 'ar_to_en' and i + 1 < len(word):
            two_chars = word[i:i+2]
            if two_chars in AR_TO_EN:
                result += AR_TO_EN[two_chars]
                i += 2
                continue
        
        char = word[i]
        if direction == 'en_to_ar':
            result += EN_TO_AR.get(char, char)
        else:
            result += AR_TO_EN.get(char, char)
        i += 1
        
    return result

if __name__ == '__main__':
    # Tests
    print("EN -> AR:", convert_word("lvpfh", "en_to_ar")) # should be مرحبا
    print("AR -> EN:", convert_word("سشمثا", "ar_to_en")) # should be saleh
