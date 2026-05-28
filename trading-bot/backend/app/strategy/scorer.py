from typing import Dict, Any, List, Optional
from app.core.datatypes import RawSetup, SetupScore, StrategyContext, SetupFamily

class ConfluenceScorer:
    """Strategy-specific weighted scoring engine."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.weights = config or self._default_weights()

    def appraise(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        """Calculates 0-100 score for a setup based on weighted factors."""
        
        # 1. Bias Alignment Score (30%)
        bias_score = self._score_bias(setup, context)
        
        # 2. Setup Quality Score (30%)
        quality_score = self._score_setup_specific_quality(setup)
        
        # 3. Volume Intensity (20%)
        volume_score = self._score_vol_spike(setup, context)
        
        # 4. Session Boost (10%)
        session_score = self._score_session(context)
        
        # 5. Risk-Reward Efficiency (10%)
        rr_score = self._score_risk_reward(setup)
        
        weights = self.weights
        total = (
            bias_score * weights.get("bias", 0.3)
            + quality_score * weights.get("quality", 0.3)
            + volume_score * weights.get("volume", 0.2)
            + session_score * weights.get("session", 0.1)
            + rr_score * weights.get("rr", 0.1)
        )
                
        return SetupScore(
            total_score=total,
            is_qualified=(total >= 70.0),
            weight_breakdown={
                "bias": bias_score,
                "quality": quality_score,
                "volume": volume_score,
                "session": session_score,
                "rr": rr_score
            }
        )

    def _score_bias(self, setup: RawSetup, context: StrategyContext) -> float:
        """Alignment between M1 setup and M15 bias."""
        if setup.direction.value == "BUY" and context.m15_bias == 1: return 100
        if setup.direction.value == "SELL" and context.m15_bias == -1: return 100
        return 0

    def _score_setup_specific_quality(self, setup: RawSetup) -> float:
        """Stricter rule checks per family."""
        if setup.family == SetupFamily.SWEEP_RECLAIM:
             # Freshness and Displacement check
             return max(0.0, min(100.0, setup.metadata.get('displacement_factor', 0.5) * 100))
        return 80.0 # Standard quality

    def _score_vol_spike(self, setup: RawSetup, context: StrategyContext) -> float:
        """Relative Volume Z-Score logic."""
        return max(0.0, min(100.0, setup.metadata.get('rv_ratio', 1.0) * 50))

    def _score_session(self, context: StrategyContext) -> float:
        """Bonus for London/NY Killzones."""
        if context.session in ["LONDON", "NY"]: return 100
        return 20

    def _score_risk_reward(self, setup: RawSetup) -> float:
        """Reward:Risk must be viable (> 1:2)."""
        if not setup.targets:
            return 0.0
        risk = abs(setup.entry_price - setup.stop_loss)
        reward = abs(setup.targets[0] - setup.entry_price)
        if risk <= 0:
            return 0.0
        rr = reward / risk
        if rr > 3.0: return 100
        if rr > 2.0: return 80
        if rr > 1.2: return 50
        return 0

    def _default_weights(self) -> Dict[str, Any]:
        return {"bias": 0.3, "quality": 0.3, "volume": 0.2, "session": 0.1, "rr": 0.1}
