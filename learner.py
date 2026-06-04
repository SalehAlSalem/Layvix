"""
learner.py - Continuous Online Learning Engine for Layvix
Uses SGDClassifier.partial_fit() for real-time incremental learning.

The AI learns from:
  1. Words the user UNDOES (correction was wrong → learn to not correct next time)
  2. Words the user MANUALLY corrects (AI missed it → learn to catch it next time)
  3. General typing patterns over time
"""

import os
import pickle
import time
import threading
import numpy as np
from logger import get_logger

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEARNING_LOG_PATH = os.path.join(BASE_DIR, 'learning_log.json')
MODEL_PATH = os.path.join(BASE_DIR, 'layvix_ai.pkl')

_vectorizer = None
_classifier = None
_lock = threading.Lock()

# Learning stats
_learn_stats = {
    "total_learned": 0,
    "learned_today": 0,
    "last_learn_time": None,
    "corrections_accepted": 0,
    "corrections_undone": 0,
    "manual_corrections": 0,
}


def init(vectorizer, classifier):
    """Initialize with the loaded model components."""
    global _vectorizer, _classifier
    _vectorizer = vectorizer
    _classifier = classifier
    
    # CRITICAL FIX: Disable balanced class weights for online learning
    # If the model was trained with class_weight='balanced', partial_fit
    # with single-class batches will raise a ValueError.
    if hasattr(_classifier, 'class_weight'):
        _classifier.class_weight = None
        
    logger.info("[LEARNER] Online learning engine initialized")


def get_stats():
    return _learn_stats.copy()


def learn_from_undo(word_str, was_predicted_layout):
    """
    User undid a correction → the AI was WRONG.
    Teach the model that this word belongs to the OPPOSITE layout.
    """
    if _vectorizer is None or _classifier is None:
        return

    with _lock:
        try:
            # If AI predicted 'ar' and user undid, the correct label is 'en' (0)
            # If AI predicted 'en' and user undid, the correct label is 'ar' (1)
            correct_label = 0 if was_predicted_layout == 'ar' else 1

            vec = _vectorizer.transform([word_str.lower()])
            # Repeat the sample multiple times for stronger learning signal
            X_batch = vec
            y_batch = np.array([correct_label])
            _classifier.class_weight = None
            if hasattr(_classifier, '_expanded_class_weight'):
                delattr(_classifier, '_expanded_class_weight')
            
            for _ in range(20):  # Reinforce 20x
                _classifier.partial_fit(X_batch, y_batch)

            _learn_stats["total_learned"] += 1
            _learn_stats["learned_today"] += 1
            _learn_stats["corrections_undone"] += 1
            _learn_stats["last_learn_time"] = time.strftime("%H:%M:%S")

            layout_name = 'English' if correct_label == 0 else 'Arabic'
            logger.info(f"[LEARN] Undo → '{word_str}' is actually {layout_name} (reinforced 20x)")

            # Auto-save after learning
            _save_model()
        except Exception as e:
            logger.error(f"[LEARN] Error learning from undo: {e}")


def learn_from_manual(word_str, from_layout, to_layout):
    """
    User manually corrected a word → the AI MISSED this one.
    Teach the model the correct layout.
    """
    if _vectorizer is None or _classifier is None:
        return

    with _lock:
        try:
            # The word was in from_layout, user wanted to_layout
            # We need to teach that this word (as typed) belongs to to_layout
            correct_label = 1 if to_layout == 'ar' else 0

            vec = _vectorizer.transform([word_str.lower()])
            y_batch = np.array([correct_label])
            _classifier.class_weight = None
            if hasattr(_classifier, '_expanded_class_weight'):
                delattr(_classifier, '_expanded_class_weight')
            
            for _ in range(30):  # Stronger signal for manual corrections
                _classifier.partial_fit(vec, y_batch)

            _learn_stats["total_learned"] += 1
            _learn_stats["learned_today"] += 1
            _learn_stats["manual_corrections"] += 1
            _learn_stats["last_learn_time"] = time.strftime("%H:%M:%S")

            logger.info(f"[LEARN] Manual → '{word_str}' should be {to_layout} (reinforced 30x)")

            _save_model()
        except Exception as e:
            logger.error(f"[LEARN] Error learning from manual: {e}")


def learn_from_accepted(word_str, predicted_layout):
    """
    User accepted a correction (didn't undo) → reinforce the AI's decision.
    Called after a short delay if no undo happens.
    """
    if _vectorizer is None or _classifier is None:
        return

    with _lock:
        try:
            correct_label = 1 if predicted_layout == 'ar' else 0
            vec = _vectorizer.transform([word_str.lower()])
            y_batch = np.array([correct_label])
            _classifier.class_weight = None
            if hasattr(_classifier, '_expanded_class_weight'):
                delattr(_classifier, '_expanded_class_weight')
            
            for _ in range(5):  # Light reinforcement
                _classifier.partial_fit(vec, y_batch)

            _learn_stats["corrections_accepted"] += 1

            # Save periodically (every 10 accepted corrections)
            if _learn_stats["corrections_accepted"] % 10 == 0:
                _save_model()
        except Exception as e:
            logger.error(f"[LEARN] Error reinforcing: {e}")


def _save_model():
    """Save the updated model to disk."""
    try:
        import ai_engine
        data = {
            'vectorizer': _vectorizer,
            'classifier': _classifier,
            'version': '3.1-live',
            'n_training_samples': 'online',
            'n_features': _vectorizer.get_feature_names_out().shape[0] if hasattr(_vectorizer, 'get_feature_names_out') else '?',
        }
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        logger.error(f"[LEARN] Error saving model: {e}")
