import joblib
import pandas as pd
import os

class ExecutionRiskModel:
    """
    Model C: Execution-risk model.
    Checks live execution: spread, slippage risk, session liquidity.
    """
    def __init__(self, model_path="models/execution_risk_model.pkl"):
        self.model_path = model_path
        self.model = self._load()

    def _load(self):
        try:
            if os.path.exists(self.model_path):
                return joblib.load(self.model_path)
        except Exception:
            return None
        return None

    def predict_risk(self, execution_features: dict) -> str:
        """
        Returns execution risk level: 'LOW', 'MEDIUM', or 'HIGH'.
        Influenced by: spread wide, slippage history, weak sessions.
        """
        # Placeholder risk logic
        spread = execution_features.get('current_spread', 0)
        is_london = execution_features.get('is_london', 0)
        is_ny = execution_features.get('is_new_york', 0)
        
        # Rule-based fallback for initial stage
        if spread > 150: # Points
            return 'HIGH'
        if not (is_london or is_ny):
            return 'MEDIUM'
            
        if self.model:
            return self.model.predict(pd.DataFrame([execution_features]))[0]
            
        return 'LOW'

    def is_risk_acceptable(self, risk_level: str) -> bool:
        """
        Strict Rule: If risk level is HIGH, do NOT trade.
        """
        return risk_level != 'HIGH'
