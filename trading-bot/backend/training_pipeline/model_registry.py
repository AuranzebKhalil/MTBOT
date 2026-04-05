import joblib
import pandas as pd
import os
import shutil
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Handles Model Promotion: Champion vs. Challenger.
    Only promotes a new model if it outperforms the active one on OOS metrics.
    """
    def __init__(self, registry_dir="models/registry"):
        self.registry_dir = registry_dir
        self.champion_path = "models/active_model.pkl"
        os.makedirs(self.registry_dir, exist_ok=True)

    def promote_challenger(self, challenger_path, oos_metrics: dict):
        """
        Comparison engine: Expectancy / PF / Drawdown.
        """
        # 1. Compare against current Champion
        champion_metrics = self._get_champion_metrics()
        
        # Simple promotion rule: Challenger must have higher Expectancy AND lower Drawdown
        if oos_metrics.get('expectancy', -999) > champion_metrics.get('expectancy', -999):
            if oos_metrics.get('drawdown', 100) < champion_metrics.get('drawdown', 100):
                # PROMOTION
                logger.info(f"PROMOTING CHALLENGER: {oos_metrics}")
                shutil.copy(challenger_path, self.champion_path)
                return True
        
        logger.info("Challenger failed to beat Champion on institutional criteria.")
        return False

    def _get_champion_metrics(self):
        # Placeholder for real metrics store
        try:
            if os.path.exists("models/active_metrics.json"):
                # Load JSON
                return pd.read_json("models/active_metrics.json", typ='series').to_dict()
        except Exception:
            pass
        return {"expectancy": -1.0, "drawdown": 100.0}
