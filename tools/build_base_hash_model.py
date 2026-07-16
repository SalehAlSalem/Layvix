import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

# Minimal training data to initialize the classes (0=English, 1=Arabic)
X = ["hello", "world", "this", "is", "english", "lvpfh", "hgrvg", "fsl", "ih"]
y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1])

vectorizer = HashingVectorizer(
    analyzer='char',
    ngram_range=(2, 5),
    n_features=1048576,
    alternate_sign=False,
    dtype=np.float32
)

X_features = vectorizer.fit_transform(X)

clf = SGDClassifier(
    loss='log_loss',
    alpha=1e-4,
    random_state=42
)
clf.fit(X_features, y)

model_path = os.path.join(data_dir, 'layvix_ai.pkl')
with open(model_path, 'wb') as f:
    pickle.dump({
        'vectorizer': vectorizer,
        'classifier': clf,
        'version': '4.0-hashing',
        'n_training_samples': len(X),
        'n_features': 1048576
    }, f, protocol=pickle.HIGHEST_PROTOCOL)

print(f"Successfully generated HashingVectorizer base model at {model_path}")
