# AI Architecture & Learning Engine

Layvix v4.0.0 uses a 100% local, privacy-first Machine Learning architecture built with `scikit-learn`. It is designed to be extremely fast (sub-5ms inference) and highly memory-efficient.

## 1. The Core Model (`ai_engine.py`)

Layvix relies on an `SGDClassifier` (Stochastic Gradient Descent) trained with logarithmic loss (`loss='log_loss'`). This allows the model to output *probability arrays* (e.g., 99% confident this is Arabic, 1% English) rather than just hard classifications.

### Feature Extraction (`HashingVectorizer`)
In v4.0.0, we completely abandoned `CountVectorizer` and static dictionaries. We now use a `HashingVectorizer` with 1,048,576 features.

**Why Hashing?**
- **Zero Out-of-Vocabulary (OOV) Errors:** Because every possible character sequence is mathematically hashed into a fixed-size array, the model never crashes when encountering a word it has never seen before.
- **Fixed Memory Footprint:** The vectorizer uses no state and no RAM for dictionary lookups. The memory stays locked at ~60MB regardless of how many new words the user types.

### Inference Pipeline
When the user finishes a word, `ai_engine.py` runs `predict_proba`:
```python
def predict_layout(text: str):
    # 1. Convert text to lowercase
    text = text.lower()
    
    # 2. Hash text into a sparse array
    X = vectorizer.transform([text])
    
    # 3. Predict probability
    probs = model.predict_proba(X)[0]
    
    # 4. Compare against Settings threshold
    max_prob = np.max(probs)
    if max_prob >= settings.ai_confidence_threshold:
        return classes[np.argmax(probs)]
    return None
```

## 2. Continuous Online Learning (`learner.py`)

Traditional AI models require "Recompiling" to learn new data. Layvix uses `partial_fit`, a technique that allows the `SGDClassifier` to slightly shift its mathematical weights dynamically in real-time.

### The Feedback Loop
If Layvix corrects a word incorrectly, the user presses the `Undo Hotkey` (`Ctrl+Alt+Shift+Z`). This triggers the `learner.py` feedback loop.

```python
def learn_from_mistake(wrong_text: str, correct_layout: str):
    X = vectorizer.transform([wrong_text])
    y = np.array([correct_layout])
    
    # Aggressively fit the model multiple times to guarantee the shift
    for _ in range(20):
        model.partial_fit(X, y, classes=model.classes_)
        
    _save_model()
```

### The Personal Model
When the user first runs Layvix, it copies the base model (`layvix_ai_base.pkl`) to `%APPDATA%\Layvix\data\layvix_ai_personal.pkl`. All future `partial_fit` updates are saved to the *personal* model. This ensures the user's specific slang and abbreviations are never overwritten by a software update.
