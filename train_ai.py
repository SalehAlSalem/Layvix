"""
train_ai.py - Layvix AI Model Builder
Trains a Character-Level N-gram classifier to detect keyboard layout intent.

The key insight: we don't classify "language" — we classify "layout intent".
Given raw keystrokes typed on a QWERTY keyboard, was the user intending to
type English, or were they on the wrong layout and meant Arabic?

Training data:
  - English class: real English words (as typed on QWERTY = correct)
  - Arabic class:  Arabic words MAPPED to their QWERTY equivalents
                   (what they look like when typed on wrong layout)

The model learns character n-gram patterns that distinguish
"real English letter sequences" from "Arabic-on-English-keyboard sequences".

Output: layvix_ai.pkl (vectorizer + classifier)
"""

import os
import sys
import pickle
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import cross_val_score

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapper import convert_word, AR_TO_EN


def load_arabic_words(path, max_words=40000):
    """Load Arabic words and convert them to QWERTY layout equivalents."""
    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            ar_word = parts[0]
            # Skip very short words (1 char) and very long ones
            if len(ar_word) < 2 or len(ar_word) > 25:
                continue
            # Convert Arabic word to what it looks like on English keyboard
            en_layout = convert_word(ar_word, 'ar_to_en')
            # Only keep if the mapping produced Latin characters
            if en_layout and all(c.isascii() for c in en_layout):
                words.append(en_layout.lower())
            if len(words) >= max_words:
                break
    return words


def load_english_words(path, max_words=10000):
    """Load English words."""
    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().split()[0] if line.strip() else ''
            if len(word) < 2 or len(word) > 25:
                continue
            if word.isalpha():
                words.append(word.lower())
            if len(words) >= max_words:
                break
    return words


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ar_path = os.path.join(base_dir, 'ar_words.txt')
    en_path = os.path.join(base_dir, 'en_words.txt')

    print("=" * 60)
    print("  Layvix AI Model Builder")
    print("  Character N-gram Layout Classifier")
    print("=" * 60)

    # Load training data
    print("\n[1/4] Loading training data...")
    ar_on_en = load_arabic_words(ar_path)
    en_words = load_english_words(en_path)

    print(f"  Arabic words (mapped to QWERTY): {len(ar_on_en):,}")
    print(f"  English words:                    {len(en_words):,}")

    if len(ar_on_en) < 100 or len(en_words) < 100:
        print("ERROR: Not enough training data!")
        sys.exit(1)

    # Build training set
    # Label 0 = English (correct layout), Label 1 = Arabic (wrong layout)
    X = en_words + ar_on_en
    y = np.array([0] * len(en_words) + [1] * len(ar_on_en))

    # Shuffle
    idx = np.random.RandomState(42).permutation(len(X))
    X = [X[i] for i in idx]
    y = y[idx]

    # Extract character n-grams (2 to 4)
    print("\n[2/4] Extracting character n-grams (2-4)...")
    vectorizer = CountVectorizer(
        analyzer='char',
        ngram_range=(2, 4),
        max_features=50000,
        dtype=np.float32
    )
    X_features = vectorizer.fit_transform(X)
    print(f"  Feature matrix: {X_features.shape[0]:,} samples × {X_features.shape[1]:,} features")
    print(f"  Memory: {X_features.data.nbytes / 1024:.0f} KB")

    # Train classifier (SGD with log loss = logistic regression, very fast)
    print("\n[3/4] Training SGD classifier...")
    clf = SGDClassifier(
        loss='log_loss',
        alpha=1e-4,
        max_iter=100,
        random_state=42,
        class_weight='balanced'
    )
    clf.fit(X_features, y)

    # Cross-validation
    scores = cross_val_score(clf, X_features, y, cv=5, scoring='accuracy')
    print(f"  Cross-validation accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")

    # Test with some examples
    print("\n[4/4] Testing predictions...")
    test_words = [
        ('hello', 'English word'),
        ('world', 'English word'),
        ('python', 'English word'),
        ('the', 'English word'),
        ('hgrvg', 'Arabic: القبل'),
        ('lv;fh', 'Arabic: مكتبا'),
        ('shgl', 'Arabic: شسلم'),
        ('fvl[d', 'Arabic: بركجي'),
        ('hghk', 'Arabic: الان'),
    ]

    for word, desc in test_words:
        vec = vectorizer.transform([word.lower()])
        pred = clf.predict(vec)[0]
        proba = clf.decision_function(vec)[0]
        confidence = 1 / (1 + np.exp(-abs(proba)))  # sigmoid
        layout = 'Arabic layout' if pred == 1 else 'English layout'
        print(f"  '{word}' ({desc}) → {layout} (confidence: {confidence:.2%})")

    # Save model
    model_path = os.path.join(base_dir, 'layvix_ai.pkl')
    model_data = {
        'vectorizer': vectorizer,
        'classifier': clf,
        'version': '3.0',
        'n_training_samples': len(X),
        'n_features': X_features.shape[1]
    }
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    model_size = os.path.getsize(model_path)
    print(f"\n{'=' * 60}")
    print(f"  Model saved: layvix_ai.pkl ({model_size / 1024:.0f} KB)")
    print(f"  Total features: {X_features.shape[1]:,}")
    print(f"  Accuracy: {scores.mean():.2%}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
