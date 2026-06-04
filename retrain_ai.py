"""
retrain_ai.py - Retrain Layvix AI with MORE data for better accuracy.

HOW TO USE:
  1. Add your own words to 'custom_words.txt' (one word per line, Arabic words)
  2. Run: python retrain_ai.py
  3. The model will be retrained with the new data + existing data
  
You can also adjust these settings:
  - MAX_AR_WORDS: increase for more Arabic training data
  - NGRAM_RANGE: try (2, 5) for longer patterns
  - MAX_FEATURES: increase for more detail
"""

import os
import sys
import pickle
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import cross_val_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapper import convert_word

# ============================================
# ⚙️ SETTINGS - Change these to improve accuracy
# ============================================
MAX_AR_WORDS = 50000        # Was 40,000 — now using ALL available Arabic words
MAX_EN_WORDS = 10000        # English words
NGRAM_RANGE = (2, 5)        # Was (2,4) — now captures longer patterns
MAX_FEATURES = 80000        # Was 50,000 — more features = more detail
MIN_WORD_LEN = 2            # Minimum word length to train on
# ============================================


def load_arabic_words(path, max_words):
    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            ar_word = parts[0]
            if len(ar_word) < MIN_WORD_LEN or len(ar_word) > 25:
                continue
            en_layout = convert_word(ar_word, 'ar_to_en')
            if en_layout and all(c.isascii() for c in en_layout):
                words.append(en_layout.lower())
            if len(words) >= max_words:
                break
    return words


def load_english_words(path, max_words):
    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().split()[0] if line.strip() else ''
            if len(word) < MIN_WORD_LEN or len(word) > 25:
                continue
            if word.isalpha():
                words.append(word.lower())
            if len(words) >= max_words:
                break
    return words


def load_custom_words(path):
    """Load custom Arabic words from user file."""
    if not os.path.exists(path):
        return []
    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            ar_word = line.strip()
            if not ar_word or len(ar_word) < MIN_WORD_LEN:
                continue
            en_layout = convert_word(ar_word, 'ar_to_en')
            if en_layout and all(c.isascii() for c in en_layout):
                words.append(en_layout.lower())
    return words


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ar_path = os.path.join(base_dir, 'ar_words.txt')
    en_path = os.path.join(base_dir, 'en_words.txt')
    custom_path = os.path.join(base_dir, 'custom_words.txt')

    print("=" * 60)
    print("  Layvix AI - Enhanced Retraining")
    print(f"  N-gram range: {NGRAM_RANGE}")
    print(f"  Max features: {MAX_FEATURES:,}")
    print("=" * 60)

    # Load data
    print("\n[1/4] Loading training data...")
    ar_on_en = load_arabic_words(ar_path, MAX_AR_WORDS)
    en_words = load_english_words(en_path, MAX_EN_WORDS)
    custom = load_custom_words(custom_path)

    print(f"  Arabic words (QWERTY mapped): {len(ar_on_en):,}")
    print(f"  English words:                {len(en_words):,}")
    print(f"  Custom user words:            {len(custom):,}")

    # Merge custom words (counted as Arabic, repeated for weight)
    if custom:
        ar_on_en.extend(custom * 50)  # Repeat custom words to boost importance
        print(f"  Custom words boosted: {len(custom)} × 50 = {len(custom) * 50}")

    # Build training set
    X = en_words + ar_on_en
    y = np.array([0] * len(en_words) + [1] * len(ar_on_en))

    # Shuffle
    idx = np.random.RandomState(42).permutation(len(X))
    X = [X[i] for i in idx]
    y = y[idx]

    # Extract features
    print(f"\n[2/4] Extracting character n-grams {NGRAM_RANGE}...")
    vectorizer = CountVectorizer(
        analyzer='char',
        ngram_range=NGRAM_RANGE,
        max_features=MAX_FEATURES,
        dtype=np.float32
    )
    X_features = vectorizer.fit_transform(X)
    print(f"  Feature matrix: {X_features.shape[0]:,} × {X_features.shape[1]:,}")
    print(f"  Memory: {X_features.data.nbytes / 1024:.0f} KB")

    # Train
    print("\n[3/4] Training classifier...")
    clf = SGDClassifier(
        loss='log_loss',
        alpha=1e-4,
        max_iter=200,      # More iterations for better convergence
        random_state=42,
        class_weight='balanced'
    )
    clf.fit(X_features, y)

    scores = cross_val_score(clf, X_features, y, cv=5, scoring='accuracy')
    print(f"  Accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")

    # Test problem cases
    print("\n[4/4] Testing known problem cases...")
    test_words = [
        ('gish', 'Should be Arabic: ليش/لهسا'),
        ('lvpfh', 'Arabic: مرحبا'),
        ('hello', 'English'),
        ('had', 'Ambiguous: could be English "had" or Arabic هاي'),
        (',hggi', 'Arabic: والله'),
        ('fix', 'English'),
        ('hgdvl,;', 'Arabic: اليرموك'),
        ('tab', 'English'),
        ('python', 'English'),
        ('fsl', 'Arabic: بسم'),
    ]

    for word, desc in test_words:
        vec = vectorizer.transform([word.lower()])
        pred = clf.predict(vec)[0]
        proba = clf.decision_function(vec)[0]
        confidence = 1 / (1 + np.exp(-abs(proba)))
        layout = 'AR' if pred == 1 else 'EN'
        status = '✅' if ('Arabic' in desc and layout == 'AR') or ('English' in desc and layout == 'EN') else '⚠️'
        print(f"  {status} '{word}' → {layout} ({confidence:.1%}) | {desc}")

    # Save
    model_path = os.path.join(base_dir, 'layvix_ai.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'classifier': clf,
            'version': '3.1',
            'n_training_samples': len(X),
            'n_features': X_features.shape[1]
        }, f, protocol=pickle.HIGHEST_PROTOCOL)

    size = os.path.getsize(model_path)
    print(f"\n{'=' * 60}")
    print(f"  ✅ Model saved: layvix_ai.pkl ({size / 1024:.0f} KB)")
    print(f"  Accuracy: {scores.mean():.2%}")
    print(f"{'=' * 60}")
    print(f"\n  To add custom words: edit 'custom_words.txt' and rerun this script.")


if __name__ == '__main__':
    main()
