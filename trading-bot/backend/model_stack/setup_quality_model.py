import joblib
import pandas as pd
import os

class SetupQualityModel:
    """
    Model B: Setup-quality model.
    Scores the probability that a given SMC/Price Action setup is 'high quality'.
    """
    def __init__(self, model_path="models/setup_quality_model.pkl"):
        self.model_path = model_path
        self.model = self._load()

    def _load(self):
        try:
            if os.path.exists(self.model_path):
                return joblib.load(self.model_path)
        except Exception:
            return None
        return None

    def get_score(self, feature_row: pd.DataFrame) -> float:
        """
        Returns a probability score (0.0 to 1.0) for the setup quality.
        """
        if self.model:
            # probability of class 1 | 2 (high quality)
            probs = self.model.predict_proba(feature_row)[0]
            # Assumes 0 is No Trade, 1 | 2 is Buy | Sell
            return float(max(probs[1:])) if len(probs) > 1 else 0.5
            
        return 0.5 # Default probability if no model trained

    def is_setup_approved(self, score: float, threshold: float = 0.6) -> bool:
        """
        Threshold check: Only approved if score exceeds the calibrated threshold.
        """
        return score >= threshold
