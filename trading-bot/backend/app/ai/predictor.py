import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import Tuple, Dict, Any, Optional
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

    def predict(
        self,
        df_m1: pd.DataFrame,
        confidence_threshold: float = 0.48,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        AI filter result (backward-compatible fields included):
          - pass / decision / confidence / reason
          - strong_factors / weak_factors
        """
        context = context or {}
        if not self.is_ready:
            return {
                "pass": True,
                "decision": "FALLBACK_APPROVE",
                "confidence": 1.0,
                "reason": "AI model not loaded (fallback approval)",
                "strong_factors": ["model_fallback"],
                "weak_factors": [],
                # legacy compatibility keys
                "ai_pass": True,
                "ai_confidence": 1.0,
                "ai_reason": "AI model not loaded (fallback approval)",
            }

        try:
            features_df = self._engineer_features(df_m1)
            if features_df.empty:
                return {
                    "pass": False,
                    "decision": "REJECT",
                    "confidence": 0.0,
                    "reason": "Insufficient data for features",
                    "strong_factors": [],
                    "weak_factors": ["insufficient_features"],
                    "ai_pass": False,
                    "ai_confidence": 0.0,
                    "ai_reason": "Insufficient data for features",
                }

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
                return {
                    "pass": True,
                    "decision": "FALLBACK_APPROVE",
                    "confidence": 1.0,
                    "reason": "AI components missing (fallback approval)",
                    "strong_factors": ["model_fallback"],
                    "weak_factors": [],
                    "ai_pass": True,
                    "ai_confidence": 1.0,
                    "ai_reason": "AI components missing (fallback approval)",
                }
            
            strong_factors, weak_factors = self._summarize_context_factors(context)
            
            # 0: NONE, 1: BUY, 2: SELL
            if pred == 0:
                msg = f"AI predicts No Trade (conf={conf:.2f}, thr={confidence_threshold:.2f})"
                return {
                    "pass": False,
                    "decision": "NO_TRADE",
                    "confidence": conf,
                    "reason": msg,
                    "strong_factors": strong_factors,
                    "weak_factors": weak_factors + ["model_no_trade"],
                    "ai_pass": False,
                    "ai_confidence": conf,
                    "ai_reason": msg,
                }
            
            # Confidence threshold (Floating point precision safety)
            if round(conf, 4) < round(confidence_threshold, 4):
                msg = f"Low AI confidence (conf={conf:.2f}, thr={confidence_threshold:.2f})"
                return {
                    "pass": False,
                    "decision": "REJECT",
                    "confidence": conf,
                    "reason": msg,
                    "strong_factors": strong_factors,
                    "weak_factors": weak_factors + ["low_confidence"],
                    "ai_pass": False,
                    "ai_confidence": conf,
                    "ai_reason": msg,
                }
                
            msg = f"AI confirms signal (pred={'BUY' if pred==1 else 'SELL'}, conf={conf:.2f}, thr={confidence_threshold:.2f})"
            logger.info(f"[{context.get('symbol', 'UNK')}] AI Result: {msg} | Strong={strong_factors} | Weak={weak_factors}")
            return {
                "pass": True,
                "decision": "APPROVE",
                "confidence": conf,
                "reason": msg,
                "strong_factors": strong_factors,
                "weak_factors": weak_factors,
                "ai_pass": True,
                "ai_confidence": conf,
                "ai_reason": msg,
            }

        except Exception as e:
            logger.error(f"AI prediction error: {e}")
            msg = f"AI PATH ERROR: {e} (fallback approval)"
            return {
                "pass": True,
                "decision": "FALLBACK_APPROVE",
                "confidence": 1.0,
                "reason": msg,
                "strong_factors": ["model_error_fallback"],
                "weak_factors": ["predict_exception"],
                "ai_pass": True,
                "ai_confidence": 1.0,
                "ai_reason": msg,
            }

    def _summarize_context_factors(self, context: Dict[str, Any]) -> Tuple[list, list]:
        """
        Create human-readable strong/weak factor tags from strategy context.
        """
        strong = []
        weak = []

        ms = context.get("market_structure") or {}
        ms_score = self._to_float(ms.get("final_score"), default=0.0)
        if ms_score >= 0.65:
            strong.append("market_structure_strong")
        elif ms_score < 0.45:
            weak.append("market_structure_weak")

        htf = str(context.get("htf_trend", "NEUTRAL")).upper()
        setup_side = str(context.get("setup_side", ""))
        if (setup_side == "BUY" and htf == "BULLISH") or (setup_side == "SELL" and htf == "BEARISH"):
            strong.append("htf_alignment")
        elif htf != "NEUTRAL":
            weak.append("htf_misalignment")

        rr_quality = self._to_float(context.get("rr_quality"), default=0.0)
        if rr_quality >= 1.5:
            strong.append("rr_quality_good")
        elif rr_quality > 0 and rr_quality < 1.0:
            weak.append("rr_quality_poor")

        spread_state = str(context.get("spread_condition", "UNKNOWN")).upper()
        if spread_state == "GOOD":
            strong.append("spread_ok")
        elif spread_state in {"ELEVATED", "HIGH"}:
            weak.append("spread_elevated")

        momentum = self._to_float(context.get("candle_momentum"), default=0.0)
        if momentum >= 1.2:
            strong.append("momentum_supportive")
        elif momentum <= 0.6:
            weak.append("momentum_weak")

        if (context.get("market_structure") or {}).get("failing_factors"):
            weak.append("structure_subfactors_failed")

        if not strong:
            strong.append("model_signal_only")
        return strong[:6], weak[:6]

    def _to_float(self, value: Any, default: float = 0.0) -> float:
        try:
            out = float(value)
            return out if np.isfinite(out) else default
        except Exception:
            return default

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Avoid copying the entire dataframe if we don't have to
        # But dropna() at the end creates a copy anyway.
        # We'll check for columns first.
        
        # Binary flags for model
        if 'is_sweep' not in df.columns:
            # 1. Price Momentum & Basic Indicators
            if 'rsi' not in df.columns:
                df['rsi'] = self._calculate_rsi(df['close'])
            
            if 'v_avg' not in df.columns:
                v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
                if v_col in df.columns:
                    df['v_avg'] = df[v_col].rolling(20).mean()
                    df['rel_activity'] = df[v_col] / df['v_avg']
                else:
                    df['v_avg'] = 1.0
                    df['rel_activity'] = 1.0
                
            if 'volatility' not in df.columns:
                df['volatility'] = df['close'].rolling(window=20).std()
            
            # 2. SMC Flags (Encoded)
            # Skip if already present (massive speedup in backtest)
            smc_cols = ['sweep', 'bos', 'fvg_bullish', 'order_block']
            if not all(col in df.columns for col in smc_cols):
                from indicators import SMCIndicators
                df = SMCIndicators.detect_liquidity_sweeps(df)
                df = SMCIndicators.detect_bos_choch(df)
                df = SMCIndicators.detect_fvg(df)
                df = SMCIndicators.detect_order_blocks(df)
                df = SMCIndicators.detect_supply_demand(df)
                df = SMCIndicators.detect_vsa(df)
            
            df['is_sweep'] = np.where(df['sweep'] != 0, 1, 0) if 'sweep' in df.columns else 0
            df['is_bos'] = np.where(df['bos'] != 0, 1, 0) if 'bos' in df.columns else 0
            df['is_fvg'] = np.where(df['fvg_bullish'] | df['fvg_bearish'], 1, 0) if 'fvg_bullish' in df.columns and 'fvg_bearish' in df.columns else 0
            df['in_ob'] = np.where(df['order_block'] != 0, 1, 0) if 'order_block' in df.columns else 0
            
            # Ultra-defensive column safety for supply/demand zones
            sz = df['supply_zone'] if 'supply_zone' in df.columns else False
            dz = df['demand_zone'] if 'demand_zone' in df.columns else False
            in_sd = (sz == True) | (dz == True) if (isinstance(sz, pd.Series) or isinstance(dz, pd.Series)) else (sz or dz)
            df['in_sd_zone'] = np.where(in_sd, 1, 0)
            
            # VSA patterns
            df['is_2br'] = np.where(df.get('vsa', "") == "TWO_BAR_REVERSAL", 1, 0) if 'vsa' in df.columns else 0
            df['is_nsnd'] = np.where((df.get('vsa', "") == "NO_SUPPLY") | (df.get('vsa', "") == "NO_DEMAND"), 1, 0) if 'vsa' in df.columns else 0
        
        # 3. Handle Missing Values Safely
        # Use forward fill then backward fill for historical context
        df = df.ffill().bfill()
        
        # Count missing before zero-filling
        missing_counts = df.isnull().sum()
        total_missing = int(missing_counts.sum())
        
        # Final safety fill with zeros for numeric model inputs
        df = df.fillna(0)
        
        logger.debug(f"AI Feature Engineering: {len(df)} rows, {total_missing} missing values fixed.")
        return df.iloc[-1:] # Return only the last row

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
