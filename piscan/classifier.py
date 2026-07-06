"""Optional learned-detector layer.

Loads a model trained by scripts/train_classifier.py and predicts whether a
chatbot response represents a successful injection. Degrades gracefully: if no
model file or scikit-learn/joblib is present, it simply reports unavailable, so
the rest of PIScanner keeps working.
"""

import os
from typing import Optional

DEFAULT_MODEL_PATH = os.path.join("models", "classifier.joblib")


class LearnedDetector:
    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self._model = None
        self._loaded = False

    @property
    def available(self) -> bool:
        self._ensure()
        return self._model is not None

    def _ensure(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            if os.path.exists(self.model_path):
                import joblib
                self._model = joblib.load(self.model_path)
        except Exception:
            self._model = None

    def predict(self, response: str) -> Optional[dict]:
        """Return {'detected', 'score'} or None if unavailable."""
        self._ensure()
        if self._model is None:
            return None
        try:
            proba = float(self._model.predict_proba([response or ""])[0][1])
            return {"detected": proba >= 0.5, "score": round(proba, 3)}
        except Exception:
            return None
