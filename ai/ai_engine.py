"""
ai_engine.py - Layvix Runtime AI Engine  (v4.0 - Radical Refactor)
===================================================================
ARCHITECTURAL CHANGES (ADR Decision):

1. SAFE LOADING:
   - Loads layvix_ai.pkl (HashingVectorizer + SGDClassifier).
   - Falls back to copying base model to create personal model on first run.

2. CLEAN PREDICTION (predict_proba ONLY):
   - Old code: tried predict_proba, then fell back to sigmoid(decision_function).
   - New code: uses ONLY predict_proba.  If it fails for any reason,
     returns confidence=0.0 immediately — no guessing allowed.
   - Rationale: sigmoid over decision_function produces UNCALIBRATED scores
     that look like probabilities but are not.  They can mislead the engine
     into making corrections with falsely high confidence.

3. INITIALISES NEW LEARNER:
   - Calls learner.init() which starts the background queue worker thread.
"""

import os
import sys
import pickle
import shutil

from utils.logger import get_logger, get_data_dir

logger = get_logger()

_model      = None
_vectorizer = None
_model_info = {"version": "Unknown", "features": "Unknown", "samples": "Unknown"}

def get_model_info():
    return _model_info

def _compute_sha256_of(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _validate_model_hash(personal_model_path: str, sig_path: str) -> bool:
    import json
    if not os.path.exists(sig_path):
        return True  # First run — no sig yet, accept
    try:
        with open(sig_path, 'r') as f:
            expected = json.load(f).get('sha256', '')
        actual = _compute_sha256_of(personal_model_path)
        return actual == expected
    except Exception:
        return False  # Fail closed → fallback to base model

def _fallback_to_base_model(base_path, personal_path):
    logger.warning("[AI] Model integrity check failed. Falling back to base model.")
    if os.path.exists(base_path):
        shutil.copy2(base_path, personal_path)
        sig_path = personal_path + ".sig"
        if os.path.exists(sig_path):
            try:
                os.remove(sig_path)
            except OSError:
                pass
    else:
        logger.error("[AI] Base model missing during fallback!")


def load_model() -> bool:
    """Load the AI model from disk.
    
    Strategy (Single Model):
    - Personal model path is the ONE source of truth.
    - On first run: seed it from the base model (copy once).
    - Always load from personal path after that.
    - All learning writes back to the same file.
    """
    global _model, _vectorizer

    # PyInstaller unpacks data to sys._MEIPASS
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        root_dir = sys._MEIPASS
    else:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    base_model_path     = os.path.join(root_dir, 'data', 'layvix_ai.pkl')
    personal_model_path = os.path.join(get_data_dir(), 'layvix_ai_personal.pkl')

    # First run: seed personal model from base (one-time copy)
    if not os.path.exists(personal_model_path):
        if os.path.exists(base_model_path):
            shutil.copy2(base_model_path, personal_model_path)
            logger.info("[AI] First run: seeded personal model from base.")
        else:
            logger.error("[AI] Base model not found — cannot initialize.")
            return False

    sig_path = personal_model_path + ".sig"

    # Integrity verification
    if os.path.exists(personal_model_path):
        if not _validate_model_hash(personal_model_path, sig_path):
            if os.path.exists(base_model_path):
                _fallback_to_base_model(base_model_path, personal_model_path)
            else:
                logger.error("[AI] Model corrupted and no base model found.")
                return False

    if not os.path.exists(personal_model_path):
        logger.error(f"[AI] Model not found: {personal_model_path}")
        return False

    try:
        with open(personal_model_path, 'rb') as f:
            data = pickle.load(f)

        _vectorizer = data['vectorizer']
        _model      = data['classifier']

        # Determine defaults for missing metadata
        manifest = data.get('manifest', {})
        version = manifest.get('version') or data.get('version', 'Unknown')
        features = manifest.get('n_features') or data.get('n_features', 'Unknown')
        samples = manifest.get('training_samples') or data.get('n_training_samples', 'Unknown')
        
        global _model_info
        _model_info = {
            "version": str(version),
            "features": str(features),
            "samples": str(samples)
        }

        logger.info(
            f"[AI] Core Engine loaded successfully (v{version} | {features} features)"
        )

        # Start the online learning engine
        try:
            from ai import learner
            learner.init(_vectorizer, _model)
        except Exception as e:
            logger.error(f"Failed to init learner: {e}")

        return True

    except Exception as e:
        logger.error(f"Failed to load AI model: {e}")
        return False


def predict_layout(word: str) -> tuple[str, float]:
    """
    Predict whether the typed word was intended for English or Arabic layout.

    Returns:
        (predicted_layout, confidence)
        predicted_layout : 'en' | 'ar' | 'unknown'
        confidence       : float in [0.0, 1.0]

    Confidence is drawn EXCLUSIVELY from predict_proba().
    If predict_proba is unavailable or throws, confidence = 0.0 (no fallback).
    """
    if _model is None or _vectorizer is None:
        return ('unknown', 0.0)

    try:
        from tools.mapper import convert_word
        import re
        
        # The model was trained EXCLUSIVELY on QWERTY (Latin) characters.
        # It expects either real English words ("hello") or Arabic words typed on QWERTY ("lv;fh").
        # If the user provides Arabic characters ("مرحبا"), we MUST map them to QWERTY ("lv;fh") 
        # before the vectorizer can extract meaningful features.
        if re.search(r'[\u0600-\u06FF]', word):
            qwerty_word = convert_word(word, 'ar_to_en')
        else:
            qwerty_word = word
            
        vec  = _vectorizer.transform([qwerty_word.lower()])
        pred = _model.predict(vec)[0]        # 0 = English, 1 = Arabic
        layout = 'ar' if pred == 1 else 'en'

        # ── CONFIDENCE: predict_proba only ────────────────────────────────────
        # SGDClassifier with loss='log_loss' supports predict_proba natively.
        # We do NOT fall back to sigmoid(decision_function) — uncalibrated scores
        # can appear high while being meaningless, leading to wrong corrections.
        confidence = 0.0
        if hasattr(_model, 'predict_proba'):
            try:
                proba   = _model.predict_proba(vec)[0]   # [p_class_0, p_class_1]
                classes = list(getattr(_model, 'classes_', [0, 1]))
                idx     = classes.index(pred)
                confidence = float(proba[idx])
            except Exception:
                # predict_proba failed → return 0.0 (caller will skip correction)
                confidence = 0.0

        # Clamp defensively
        confidence = max(0.0, min(1.0, confidence))
        return (layout, confidence)

    except Exception as e:
        logger.error(f"AI prediction error: {e}")
        return ('unknown', 0.0)
