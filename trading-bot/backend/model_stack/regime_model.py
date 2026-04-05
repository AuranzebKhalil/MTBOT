import joblib
import pandas as pd
import os

class RegimeModel:
    """
    Model A: Regime model.
    Predicts: trending, ranging, unstable/high-volatility, dead market.
    """
    def __init__(self, model_path="models/regime_model.pkl"):
        self.model_path = model_path
        self.model = self._load()

    def _load(self):
        try:
            if os.path.exists(self.model_path):
                return joblib.load(self.model_path)
        except Exception:
            return None
        return None

    def predict(self, feature_row: pd.DataFrame) -> str:
        """
        Returns the market regime: 'trending', 'ranging', 'unstable', or 'dead'.
        """
        # Placeholder logic: return 'trending' for now till training
        if self.model:
            return self.model.predict(feature_row)[0]
        return "trending" # Default to trending for initial operation

    def is_regime_allowed(self, regime: str) -> bool:
        """
        Strict Rule: If regime is 'unstable' or 'dead', do NOT trade.
        """
        return regime in ['trending', 'ranging']
