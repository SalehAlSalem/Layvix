"""
ai_engine.py - Layvix Runtime AI Engine
Loads the trained character n-gram model and predicts keyboard layout intent.
100% AI-based, no dictionaries, no word lists.
Integrates with learner.py for continuous online learning.
"""

import os
import pickle
import numpy as np
from logger import get_logger

logger = get_logger()

_model = None
_vectorizer = None


def load_model():
    """Load the trained AI model from disk."""
    global _model, _vectorizer

    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, 'layvix_ai.pkl')

    if not os.path.exists(model_path):
        logger.error(f"AI model not found: {model_path}. Run train_ai.py first!")
        return False

    try:
        with open(model_path, 'rb') as f:
            data = pickle.load(f)

        _vectorizer = data['vectorizer']
        _model = data['classifier']

        logger.info(
            f"AI model loaded: v{data.get('version', '?')}, "
            f"{data.get('n_features', '?')} features, "
            f"{data.get('n_training_samples', '?')} training samples"
        )
        
        # Initialize online learner
        try:
            import learner
            learner.init(_vectorizer, _model)
        except Exception as e:
            logger.error(f"Failed to init learner: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to load AI model: {e}")
        return False


def predict_layout(word: str) -> tuple:
    """
    Predict whether the typed word was intended for English or Arabic layout.
    
    Returns:
        (predicted_layout, confidence)
        predicted_layout: 'en' or 'ar'
        confidence: float 0.0 to 1.0
    """
    if _model is None or _vectorizer is None:
        return ('unknown', 0.0)

    try:
        vec = _vectorizer.transform([word.lower()])
        pred = _model.predict(vec)[0]
        decision = _model.decision_function(vec)[0]
        confidence = 1 / (1 + np.exp(-abs(decision)))

        layout = 'ar' if pred == 1 else 'en'
        return (layout, float(confidence))
    except Exception as e:
        logger.error(f"AI prediction error: {e}")
        return ('unknown', 0.0)


# Load model on import
load_model()

