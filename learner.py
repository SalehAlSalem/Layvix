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
from logger import get_logger, get_data_dir
import settings

logger = get_logger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEARNING_LOG_PATH = os.path.join(get_data_dir(), 'learning_log.json')
LEARNING_STATS_PATH = os.path.join(get_data_dir(), 'learner_stats.json')
PERSONAL_MODEL_PATH = os.path.join(get_data_dir(), 'layvix_ai_personal.pkl')

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

def _load_stats():
    global _learn_stats
    import json
    if os.path.exists(LEARNING_STATS_PATH):
        try:
            with open(LEARNING_STATS_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    _learn_stats[k] = v
        except Exception as e:
            logger.error(f"Failed to load learner stats: {e}")

def _save_stats():
    import json
    try:
        with open(LEARNING_STATS_PATH, 'w', encoding='utf-8') as f:
            json.dump(_learn_stats, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save learner stats: {e}")

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
        
    _load_stats()
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
            _save_stats()

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
            _save_stats()

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
    """Save the updated personal model to disk."""
    if not settings.get_setting("use_personal_model"):
        return # Do not save if personal model is not enabled
        
    try:
        data = {
            'vectorizer': _vectorizer,
            'classifier': _classifier,
            'version': '3.4-personal',
            'n_training_samples': 'online',
            'n_features': _vectorizer.get_feature_names_out().shape[0] if hasattr(_vectorizer, 'get_feature_names_out') else '?',
        }
        with open(PERSONAL_MODEL_PATH, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        logger.error(f"[LEARN] Error saving model: {e}")

def fine_tune_with_dictionary():
    """Batch fine-tune the personal model using user_dict.json"""
    import user_dictionary
    if _vectorizer is None or _classifier is None:
        return False
        
    custom_words = user_dictionary.user_dict
    if not custom_words:
        return False
        
    with _lock:
        try:
            X_words = []
            y_labels = []
            
            for wrong, correct in custom_words.items():
                # We want the model to predict 'correct' layout for 'wrong' input
                # Normally, if correct layout is Arabic (ar), label is 1, else 0
                import re
                has_arabic = bool(re.search(r'[\u0600-\u06FF]', correct))
                label = 1 if has_arabic else 0
                
                X_words.append(wrong.lower())
                y_labels.append(label)
                
            if not X_words:
                return False
                
            vecs = _vectorizer.transform(X_words)
            y_batch = np.array(y_labels)
            
            _classifier.class_weight = None
            if hasattr(_classifier, '_expanded_class_weight'):
                delattr(_classifier, '_expanded_class_weight')
                
            # Strong reinforcement for explicit dictionary overrides
            for _ in range(50):
                _classifier.partial_fit(vecs, y_batch, classes=np.array([0, 1]))
                
            _learn_stats["total_learned"] += len(X_words)
            _learn_stats["last_learn_time"] = time.strftime("%H:%M:%S")
            _save_stats()
            
            _save_model()
            logger.info(f"[LEARN] Successfully fine-tuned on {len(X_words)} dictionary words.")
            return True
        except Exception as e:
            logger.error(f"[LEARN] Error in fine-tuning: {e}")
            return False
