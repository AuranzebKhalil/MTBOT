import logging
import pandas as pd
from feature_engine.m15_features import M15Features
from feature_engine.m5_features import M5Features
from feature_engine.m1_features import M1Features
from feature_engine.execution_features import ExecutionFeatures
from model_stack.regime_model import RegimeModel
from model_stack.setup_quality_model import SetupQualityModel
from model_stack.execution_risk_model import ExecutionRiskModel
from risk_engine.risk_manager import RiskManager
from risk_engine.social_news_layer import SocialNewsLayer

logger = logging.getLogger(__name__)

class ExecutionFlow:
    """
    Main orchestrator for the 'Say No' trading philosophy.
    Enforces the strict order: Regime -> Setup -> Execution -> Risk.
    """
    def __init__(self):
        self.regime_model = RegimeModel()
        self.setup_model = SetupQualityModel()
        self.execution_model = ExecutionRiskModel()
        self.risk_manager = RiskManager()
        self.social_layer = SocialNewsLayer()

    def validate_and_execute(self, symbol, mtf_data, execution_data, open_positions, history_deals, balance):
        """
        Runs the full 5-gate validation sequence.
        Returns (result: bool, message: str, meta: dict)
        """
        # 1. Feature Extraction
        m15_feat = M15Features.extract_all(mtf_data['M15'])
        m5_feat = M5Features.extract_all(mtf_data['M5'])
        m1_feat = M1Features.extract_all(mtf_data['M1'])
        exec_feat = ExecutionFeatures.extract_all(execution_data)
        
        # Merge primary features into a single row for model prediction
        feature_row = pd.DataFrame([{**m15_feat, **m5_feat, **m1_feat}])
        
        # 2. SOCIAL/NEWS GATE
        if not self.social_layer.is_market_safe(symbol):
            return False, "BLOCKED: High-impact news or social sentiment shock", {}

        # 3. REGIME GATE
        regime = self.regime_model.predict(feature_row)
        if not self.regime_model.is_regime_allowed(regime):
            return False, f"BLOCKED: Unfavorable market regime ({regime})", {}

        # 4. SETUP QUALITY GATE
        # score calculation (probability setup is good)
        setup_score = self.setup_model.get_score(feature_row)
        if not self.setup_model.is_setup_approved(setup_score):
             return False, f"BLOCKED: Setup score below threshold ({setup_score:.2f})", {}

        # 5. EXECUTION RISK GATE
        exec_risk = self.execution_model.predict_risk(exec_feat)
        if not self.execution_model.is_risk_acceptable(exec_risk):
            return False, f"BLOCKED: High execution risk ({exec_risk}) - check spread/slippage", {}

        # 6. RISK ENGINE GATE (Strict sizing & exposure)
        is_safe, reason = self.risk_manager.is_risk_acceptable(
            open_positions, history_deals, balance, symbol, spread=execution_data.get('spread', 0)
        )
        if not is_safe:
            return False, f"BLOCKED: Risk constraint exceeded ({reason})", {}

        # FINAL APPROVAL
        return True, "QUALIFIED: All institutional gates passed.", {
            "regime": regime,
            "setup_score": setup_score,
            "exec_risk": exec_risk,
            "features": feature_row.to_dict(orient='records')[0]
        }
