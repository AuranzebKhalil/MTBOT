import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
import joblib
import logging

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Implements: TimeSeriesSplit, Walk-Forward Validation, and Probability Calibration.
    Ensures no future data leak.
    """
    def __init__(self, n_splits=5):
        self.n_splits = n_splits
        self.tscv = TimeSeriesSplit(n_splits=self.n_splits)

    def train_with_calibration(self, X, y, model_path):
        """
        Trains and calibrates a classifier using walk-forward splits.
        """
        if len(X) < 10 or len(X) != len(y):
            logger.error("Insufficient data for training/calibration.")
            return False

        # 1. Standard RF model
        base_clf = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # 2. Probability Calibration using TimeSeries CV
        # CalibratedClassifierCV allows us to refine probabilities 
        calibrated_clf = CalibratedClassifierCV(base_clf, method='sigmoid', cv=self.tscv)
        
        try:
            # Convert to numpy to avoid feature name warnings with CalibratedClassifierCV
            X_numpy = X.values if hasattr(X, 'values') else X
            calibrated_clf.fit(X_numpy, y)
            joblib.dump(calibrated_clf, model_path)
            logger.info(f"Model trained and calibrated: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False

    def walk_forward_validate(self, X, y, model_func):
        """
        Simulates walk-forward evaluation.
        Train on one period, test on the next unseen period.
        """
        scores = []
        for train_index, test_index in self.tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            model = model_func().fit(X_train, y_train)
            score = model.score(X_test, y_test)
            scores.append(score)
            
        return np.mean(scores)
