import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import Tuple, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

class MarketPredictor:
    def __init__(self, model_path="models/rf_model.pkl", scaler_path="models/scaler.pkl"):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                
                # Suppress sklearn feature name warnings for existing models
                if hasattr(self.model, "calibrated_classifiers_"):
                    for cal in self.model.calibrated_classifiers_:
                        if hasattr(cal, "base_estimator") and hasattr(cal.base_estimator, "feature_names_in_"):
                            cal.base_estimator.feature_names_in_ = None
                
                logger.info("AI model and scaler loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")

    @property
    def is_ready(self):
        return self.model is not None and self.scaler is not None

    def predict(self, df_m1: pd.DataFrame, confidence_threshold: float = 0.48) -> Tuple[bool, float, str]:
        if not self.is_ready:
            return True, 1.0, "AI model not loaded (Fallback to approval)"

        try:
            features_df = self._engineer_features(df_m1)
            if features_df.empty:
                return False, 0.0, "Insufficient data for features"

            feature_list = [
                'rsi', 'rel_activity', 'volatility',
                'is_sweep', 'is_bos', 'is_fvg', 'in_ob', 
                'in_sd_zone', 'is_2br', 'is_nsnd'
            ]
            
            X = features_df[feature_list].tail(1)
            scaler = self.scaler
            model = self.model
            
            if scaler is not None and model is not None:
                X_scaled = pd.DataFrame(scaler.transform(X), columns=feature_list)
                pred = model.predict(X_scaled)[0]
                probs = model.predict_proba(X_scaled)[0]
                conf = float(probs[int(pred)])
            else:
                return True, 1.0, "AI components missing (Fallback)"
            
            # 0: NONE, 1: BUY, 2: SELL
            if pred == 0:
                return False, conf, f"AI predicts No Trade (conf={conf:.2f}, thr={confidence_threshold:.2f})"
            
            # Confidence threshold (Floating point precision safety)
            if round(conf, 4) < round(confidence_threshold, 4):
                return False, conf, f"Low AI confidence (conf={conf:.2f}, thr={confidence_threshold:.2f})"
                
            return True, conf, f"AI confirms signal (pred={'BUY' if pred==1 else 'SELL'}, conf={conf:.2f}, thr={confidence_threshold:.2f})"

        except Exception as e:
            logger.error(f"AI prediction error: {e}")
            return True, 1.0, f"AI PATH ERROR: {e} (Fallback to approval)"

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # 1. Price Momentum
        df['change'] = df['close'].pct_change()
        df['rsi'] = self._calculate_rsi(df['close'])
        
        # 2. Relative Activity
        df['v_avg'] = df['tick_volume'].rolling(20).mean()
        df['rel_activity'] = df['tick_volume'] / df['v_avg']
        df['volatility'] = df['close'].rolling(window=20).std()
        
        # 3. SMC Flags (Encoded)
        from indicators import SMCIndicators
        df = SMCIndicators.detect_liquidity_sweeps(df)
        df = SMCIndicators.detect_bos_choch(df)
        df = SMCIndicators.detect_fvg(df)
        df = SMCIndicators.detect_order_blocks(df)
        df = SMCIndicators.detect_supply_demand(df)
        df = SMCIndicators.detect_vsa(df)
        
        # Binary flags for model
        df['is_sweep'] = np.where(df['sweep'] != 0, 1, 0) if 'sweep' in df.columns else 0
        df['is_bos'] = np.where(df['bos'] != 0, 1, 0) if 'bos' in df.columns else 0
        df['is_fvg'] = np.where(df['fvg_bullish'] | df['fvg_bearish'], 1, 0) if 'fvg_bullish' in df.columns and 'fvg_bearish' in df.columns else 0
        df['in_ob'] = np.where(df['order_block'] != 0, 1, 0) if 'order_block' in df.columns else 0
        
        # Ultra-defensive column safety for supply/demand zones
        sz = df['supply_zone'] if 'supply_zone' in df.columns else False
        dz = df['demand_zone'] if 'demand_zone' in df.columns else False
        
        # Calculate SD Zone presence without risking KeyError
        in_sd = (sz == True) | (dz == True) if (isinstance(sz, pd.Series) or isinstance(dz, pd.Series)) else (sz or dz)
        df['in_sd_zone'] = np.where(in_sd, 1, 0)
        
        # VSA patterns
        df['is_2br'] = np.where(df.get('vsa', "") == "TWO_BAR_REVERSAL", 1, 0) if 'vsa' in df.columns else 0
        df['is_nsnd'] = np.where((df.get('vsa', "") == "NO_SUPPLY") | (df.get('vsa', "") == "NO_DEMAND"), 1, 0) if 'vsa' in df.columns else 0
        
        return df.dropna()

    def train(self, historical_data: pd.DataFrame) -> bool:
        """Trains the model using historical data."""
        if historical_data is None or len(historical_data) < 500:
            logger.error("Insufficient data for training")
            return False
            
        try:
            df = self._engineer_features(historical_data)
            feature_list = [
                'rsi', 'rel_activity', 'volatility',
                'is_sweep', 'is_bos', 'is_fvg', 'in_ob', 
                'in_sd_zone', 'is_2br', 'is_nsnd'
            ]
            
            if len(df) < 100: return False

            X = df[feature_list]
            
            # Simple Labeling logic: +15 bars net change
            cost_pct = 0.0003
            y = np.zeros(len(df))
            for i in range(len(df) - 15):
                change = (df['close'].iloc[i+15] - df['close'].iloc[i]) / df['close'].iloc[i]
                if abs(change) > cost_pct * 3:
                    y[i] = 1 if change > 0 else 2
                else:
                    y[i] = 0
            
            X = X[:-15]
            y = y[:-15]
            
            from training_pipeline.trainer import ModelTrainer
            trainer = ModelTrainer(n_splits=5)
            
            scaler = self.scaler
            if scaler is not None:
                self.scaler = scaler
                scaler.fit(X)
                X_scaled = pd.DataFrame(scaler.transform(X), columns=feature_list)
            else:
                return False
            
            success = trainer.train_with_calibration(X_scaled, pd.Series(y), self.model_path)
            
            if success:
                self.model = joblib.load(self.model_path)
                joblib.dump(self.scaler, self.scaler_path)
                logger.info(f"Model successfully trained and saved to {self.model_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"AI training error: {e}", exc_info=True)
            return False

    def _calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
