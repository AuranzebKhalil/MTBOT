from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import numpy as np
import pandas as pd

from app.strategy.base import BaseStrategy
from app.strategy.families.smc import SMCStrategyFamily
from app.core.datatypes import (
    RawSetup,
    SetupScore,
    SetupFamily,
    StrategyContext,
    InvalidationRule,
    SignalStatus
)
from indicators import SMCIndicators
from app.core.config import settings
from app.core.enums import OrderSide


def score_smc_setup(setup: RawSetup, context: StrategyContext, data: Optional[Dict[str, Any]] = None) -> SetupScore:
    # Start with a base score of 50.0
    score = 50.0
    weight_breakdown = {}
    factors = {}
    
    # 1. HTF Bias Alignment (max +10)
    bias_aligned = (setup.direction == OrderSide.BUY and context.m15_bias == 1) or \
                   (setup.direction == OrderSide.SELL and context.m15_bias == -1)
    if bias_aligned:
        score += 10.0
        weight_breakdown["htf_bias_alignment"] = 10.0
    else:
        weight_breakdown["htf_bias_alignment"] = 0.0
        
    # 2. Liquidity Sweep (max +10)
    has_sweep = False
    if data and "M1" in data:
        m1 = data["M1"]
        if "sweep" in m1.columns:
            has_sweep = (m1["sweep"].tail(10) != 0).any()
    if not has_sweep:
        has_sweep = bool(setup.metadata.get("liquidity_sweep") or setup.metadata.get("sweep_present", False))
    if has_sweep:
        score += 10.0
        weight_breakdown["liquidity_sweep"] = 10.0
    else:
        weight_breakdown["liquidity_sweep"] = 0.0
        
    # 3. FVG Confirmation (max +8)
    has_fvg = False
    if data and "M1" in data:
        m1 = data["M1"]
        fvg_bull = "fvg_bullish" in m1.columns and m1["fvg_bullish"].tail(10).any()
        fvg_bear = "fvg_bearish" in m1.columns and m1["fvg_bearish"].tail(10).any()
        has_fvg = (setup.direction == OrderSide.BUY and fvg_bull) or (setup.direction == OrderSide.SELL and fvg_bear)
    if not has_fvg:
        has_fvg = bool(setup.metadata.get("fvg_present") or setup.metadata.get("has_fvg", False))
    if has_fvg:
        score += 8.0
        weight_breakdown["fvg_confirmation"] = 8.0
    else:
        weight_breakdown["fvg_confirmation"] = 0.0
        
    # 4. Premium / Discount Alignment (max +8)
    pd_aligned = False
    if data and "M15" in data:
        m15 = data["M15"]
        if len(m15) >= 20:
            swing_high = float(m15["high"].tail(50).max())
            swing_low = float(m15["low"].tail(50).min())
            eq = (swing_high + swing_low) / 2.0
            if setup.direction == OrderSide.BUY and setup.entry_price < eq:
                pd_aligned = True
            elif setup.direction == OrderSide.SELL and setup.entry_price > eq:
                pd_aligned = True
    if not pd_aligned:
        pd_zone = setup.metadata.get("premium_discount_zone", {}).get("aligned_with_side")
        if pd_zone is None:
            pd_zone = setup.metadata.get("pd_aligned", False)
        pd_aligned = bool(pd_zone)
    if pd_aligned:
        score += 8.0
        weight_breakdown["premium_discount_alignment"] = 8.0
    else:
        weight_breakdown["premium_discount_alignment"] = 0.0
        
    # 5. Volume Expansion (max +6)
    vol_ratio = 1.0
    if data and "M1" in data:
        m1 = data["M1"]
        v_col = 'tick_volume' if 'tick_volume' in m1.columns else 'real_volume'
        if v_col in m1.columns and len(m1) >= 20:
            v_avg = m1[v_col].tail(20).mean()
            v_curr = float(m1[v_col].iloc[-1])
            vol_ratio = v_curr / v_avg if v_avg > 0 else 1.0
    else:
        vol_ratio = float(setup.metadata.get("volume_ratio", setup.metadata.get("rv_ratio", 1.0)))
    if vol_ratio > 1.25:
        score += 6.0
        weight_breakdown["volume_expansion"] = 6.0
    else:
        weight_breakdown["volume_expansion"] = 0.0
        
    # 6. Session Quality (max +4)
    s = (context.session or "").upper()
    is_prime_session = "LONDON" in s or "NY" in s or "NEW YORK" in s or "OVERLAP" in s
    if is_prime_session:
        score += 4.0
        weight_breakdown["session_quality"] = 4.0
    else:
        weight_breakdown["session_quality"] = 0.0
        
    # 7. Displacement Quality (max +4)
    disp_factor = 1.0
    if data and "M1" in data:
        m1 = data["M1"]
        if len(m1) >= 20:
            bodies = (m1["close"] - m1["open"]).abs()
            avg_body = bodies.tail(20).mean()
            curr_body = bodies.iloc[-1]
            disp_factor = curr_body / avg_body if avg_body > 0 else 1.0
    else:
        disp_factor = float(setup.metadata.get("displacement_factor", 1.0))
    if disp_factor > 1.5:
        score += 4.0
        weight_breakdown["displacement_quality"] = 4.0
    else:
        weight_breakdown["displacement_quality"] = 0.0
        
    # 8. Market Regime Quality (max +4)
    regime = context.regime_details
    regime_quality = (regime.get("is_trending", False) or regime.get("is_expansion", False)) and not regime.get("choppiness", False)
    if regime_quality:
        score += 4.0
        weight_breakdown["market_regime_quality"] = 4.0
    else:
        weight_breakdown["market_regime_quality"] = 0.0
        
    # --- PENALTIES ---
    penalties = 0.0
    # Choppy conditions (-15)
    if regime.get("choppiness", False):
        score -= 15.0
        penalties += 15.0
        factors["choppy_penalty"] = True
        
    # Near-equilibrium entries (-10)
    is_near_eq = False
    if data and "M15" in data:
        m15 = data["M15"]
        if len(m15) >= 20:
            swing_high = float(m15["high"].tail(50).max())
            swing_low = float(m15["low"].tail(50).min())
            eq = (swing_high + swing_low) / 2.0
            price_range = swing_high - swing_low
            if price_range > 0 and abs(setup.entry_price - eq) / price_range < 0.1:
                is_near_eq = True
    if is_near_eq:
        score -= 10.0
        penalties += 10.0
        factors["near_equilibrium_penalty"] = True
        
    # Low volatility (-10)
    if regime.get("is_low_volatility", False):
        score -= 10.0
        penalties += 10.0
        factors["low_volatility_penalty"] = True
        
    # Weak displacement (-10)
    if disp_factor < 0.8:
        score -= 10.0
        penalties += 10.0
        factors["weak_displacement_penalty"] = True
        
    # Late entry after overextended move (-10)
    is_overextended = False
    if data and "M1" in data:
        m1 = data["M1"]
        if not m1.empty:
            rsi = float(m1.iloc[-1].get("rsi", 50.0))
            if (setup.direction == OrderSide.BUY and rsi > 72.0) or (setup.direction == OrderSide.SELL and rsi < 28.0):
                is_overextended = True
    if is_overextended:
        score -= 10.0
        penalties += 10.0
        factors["overextended_penalty"] = True
        
    score = max(0.0, min(100.0, score))
    
    factors.update({
        "htf_bias_aligned": bias_aligned,
        "has_sweep": has_sweep,
        "has_fvg": has_fvg,
        "pd_aligned": pd_aligned,
        "vol_ratio": vol_ratio,
        "is_prime_session": is_prime_session,
        "disp_factor": disp_factor,
        "regime_quality": regime_quality,
        "penalties_applied": penalties
    })
    
    return SetupScore(
        total_score=score,
        is_qualified=True,
        weight_breakdown=weight_breakdown,
        factors=factors
    )


def _default_score(setup: RawSetup) -> SetupScore:
    base_score = float(setup.metadata.get("score", 70.0))
    return SetupScore(
        total_score=base_score,
        is_qualified=True,
        weight_breakdown={"base": 1.0},
        factors=setup.metadata.get("factors", {}),
    )


def _default_invalidation(setup: RawSetup) -> InvalidationRule:
    return InvalidationRule(
        setup_id=f"{setup.symbol}_{setup.family.value}_{int(setup.setup_candle_timestamp.timestamp())}",
        expiry_bars=10,
        structure_anchor=setup.entry_price,
    )


class SMCSweepReclaimStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.SWEEP_RECLAIM)
        self.strategy_id = "SMC_SWEEP"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_sweep_reclaim(data, context.m15_bias, context.symbol)
        if not signal:
            return None
        return self._signal_to_setup(signal, context)

    def _signal_to_setup(self, signal, context: StrategyContext) -> RawSetup:
        anchors = signal.metadata.get("anchors", {})
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=anchors,
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return _default_score(setup)

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets


class SMCVsaShiftStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.VSA_SHIFT)
        self.strategy_id = "SMC_VSA"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_vsa_shift(data, context.m15_bias, context.symbol)
        return self._signal_to_setup(signal, context) if signal else None

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return _default_score(setup)

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

class SMCContinuationRetestStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.CONTINUATION)
        self.strategy_id = "SMC_TREND"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_continuation(data, context.m15_bias, context.symbol)
        if not signal:
            return None
        setup = self._signal_to_setup(signal, context)
        # Calculate institutional grade score
        score_res = score_smc_setup(setup, context, data)
        setup.metadata["score"] = score_res.total_score
        setup.metadata["factors"] = score_res.factors
        setup.metadata["weight_breakdown"] = score_res.weight_breakdown
        return setup

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return SetupScore(
            total_score=setup.metadata.get("score", 70.0),
            is_qualified=True,
            weight_breakdown=setup.metadata.get("weight_breakdown", {"base": 1.0}),
            factors=setup.metadata.get("factors", {})
        )

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

    def validate_setup(self, setup: RawSetup, data: Dict[str, Any], context: StrategyContext) -> tuple[bool, Optional[str]]:
        regime = context.regime_details
        
        # Enforce Trending or Expansion environments
        is_trending = regime.get("is_trending", False)
        is_expansion = regime.get("is_expansion", False)
        is_ranging = regime.get("is_ranging", False)
        choppiness = regime.get("choppiness", False)
        is_low_volatility = regime.get("is_low_volatility", False)
        
        if not (is_trending or is_expansion):
            return False, "NON_TRENDING_OR_EXPANSION_REGIME"
        if is_ranging:
            return False, "RANGING_REGIME_BLOCKED"
        if choppiness:
            return False, "CHOPPY_REGIME_BLOCKED"
        if is_low_volatility:
            return False, "LOW_VOLATILITY_BLOCKED"
            
        # Score check
        score = setup.metadata.get("score", 0.0)
        min_score = settings.MIN_SCORE_SMC_TREND
        if score < min_score:
            missing = []
            factors = setup.metadata.get("factors", {})
            if not factors.get("htf_bias_aligned", False): missing.append("HTF bias alignment")
            if not factors.get("has_sweep", False): missing.append("liquidity sweep")
            if not factors.get("has_fvg", False): missing.append("FVG")
            if not factors.get("pd_aligned", False): missing.append("premium/discount alignment")
            reason = f"score={score:.1f} | reason=missing {', '.join(missing) if missing else 'confluence'} | regime={context.regime}"
            return False, reason
            
        return True, None

class SMCFirstTouchMitigationStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.MITIGATION)
        self.strategy_id = "SMC_MITIGATION"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_mitigation(data, context.m15_bias, context.symbol)
        return self._signal_to_setup(signal, context) if signal else None

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return _default_score(setup)

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

class SMCExhaustionReversalStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.EXHAUSTION)
        self.strategy_id = "SMC_REVERSAL"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_exhaustion(data, context.m15_bias, context.symbol)
        return self._signal_to_setup(signal, context) if signal else None

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return _default_score(setup)

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

class SMCMSSStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.MSS)
        self.strategy_id = "SMC_MSS"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_mss(data, context.m15_bias, context.symbol)
        if not signal:
            return None
        setup = self._signal_to_setup(signal, context)
        # Calculate institutional grade score
        score_res = score_smc_setup(setup, context, data)
        setup.metadata["score"] = score_res.total_score
        setup.metadata["factors"] = score_res.factors
        setup.metadata["weight_breakdown"] = score_res.weight_breakdown
        return setup

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return SetupScore(
            total_score=setup.metadata.get("score", 70.0),
            is_qualified=True,
            weight_breakdown=setup.metadata.get("weight_breakdown", {"base": 1.0}),
            factors=setup.metadata.get("factors", {})
        )

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

    def validate_setup(self, setup: RawSetup, data: Dict[str, Any], context: StrategyContext) -> tuple[bool, Optional[str]]:
        m1 = data["M1"]
        regime = context.regime_details
        
        # Block random MSS inside noisy chop
        if regime.get("choppiness", False):
            return False, "CHOPPY_REGIME_BLOCKED"
            
        # Allow only after compression, liquidity sweep, or reversal-style conditions
        is_compression = regime.get("is_compression", False)
        
        # Check for recent liquidity sweep in M1 tail (last 10 candles)
        has_sweep = False
        if "sweep" in m1.columns:
            has_sweep = (m1["sweep"].tail(10) != 0).any()
            
        # Check for reversal-style conditions: RSI overbought/oversold
        latest = m1.iloc[-1]
        rsi = latest.get("rsi", 50.0)
        is_reversal_style = rsi > 70 or rsi < 30
        
        if not (is_compression or has_sweep or is_reversal_style):
            return False, "NO_COMPRESSION_SWEEP_OR_REVERSAL_CONTEXT"
            
        # Score check
        score = setup.metadata.get("score", 0.0)
        min_score = settings.MIN_SCORE_SMC_MSS
        if score < min_score:
            missing = []
            factors = setup.metadata.get("factors", {})
            if not factors.get("htf_bias_aligned", False): missing.append("HTF bias alignment")
            if not factors.get("has_sweep", False): missing.append("liquidity sweep")
            if not factors.get("has_fvg", False): missing.append("FVG")
            if not factors.get("pd_aligned", False): missing.append("premium/discount alignment")
            reason = f"score={score:.1f} | reason=missing {', '.join(missing) if missing else 'confluence'} | regime={context.regime}"
            return False, reason
            
        return True, None

class SMCBreakerStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.BREAKER)
        self.strategy_id = "SMC_BREAKER"
        self.logic_family = SMCStrategyFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_breaker_block(data, context.m15_bias, context.symbol)
        return self._signal_to_setup(signal, context) if signal else None

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return _default_score(setup)

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

class SMCVolumeFlowStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.VOLUME)
        self.strategy_id = "SMC_VOLUME"
        self.logic_family = SMCStrategyFamily(indicators)
        self.last_skip_reason = None

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        self.last_skip_reason = None
        # Use the logic family to check for setup
        # Note: check_volume_flow now performs volume strength filtering internally
        signal = self.logic_family.check_volume_flow(data, context.m15_bias, context.symbol)
        
        if not signal:
            # Check if it was a weak POC touch (we can verify this by running the proximity check again)
            # or we can modify check_volume_flow to return the reason.
            # For simplicity, we'll re-check proximity here if signal is None
            m1 = data["M1"]
            if "poc" in m1.columns and not m1.empty:
                latest = m1.iloc[-1]
                poc = latest['poc']
                if poc > 0:
                    dist = abs(latest['close'] - poc) / latest['close']
                    if dist < 0.0005:
                        self.last_skip_reason = "SMC_VOLUME_WEAK_POC_TOUCH"
            return None
            
        return self._signal_to_setup(signal, context)

    def _signal_to_setup(self, signal, context):
        return RawSetup(
            family=self.family,
            direction=signal.direction,
            symbol=signal.symbol,
            entry_price=signal.entry,
            stop_loss=signal.sl,
            targets=[signal.tp],
            setup_candle_timestamp=signal.timestamp,
            anchors=signal.metadata.get("anchors", {}),
            metadata=signal.metadata,
        )

    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        return _default_score(setup)

    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        return []

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

    def validate_setup(self, setup: RawSetup, data: Dict[str, Any], context: StrategyContext) -> tuple[bool, Optional[str]]:
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        
        # 1. Volume Spike + Candle Direction Confirmation
        v_col = 'tick_volume' if 'tick_volume' in m1.columns else 'real_volume'
        if v_col in m1.columns:
            v_avg = m1[v_col].tail(20).mean()
            current_v = float(latest[v_col])
            ratio = current_v / v_avg if v_avg > 0 else 0
            
            # Enrich setup metadata with volume details for diagnostics
            setup.metadata.update({
                "volume_current": round(current_v, 2),
                "volume_average": round(v_avg, 2),
                "volume_ratio": round(ratio, 2),
                "required_volume_ratio": 1.2,
                "current_value": round(ratio, 2),
                "required_value": 1.2
            })
            
            if ratio < 1.2:
                return False, "VOLUME_WITHOUT_STRENGTH"
            
        is_bullish = latest['close'] > latest['open']
        from app.core.enums import OrderSide
        if setup.direction == OrderSide.BUY and not is_bullish:
             return False, "VOLUME_WITHOUT_DIRECTION"
        if setup.direction == OrderSide.SELL and is_bullish:
             return False, "VOLUME_WITHOUT_DIRECTION"

        # 2. M15 Trend Alignment
        if context.m15_bias != 0:
            if (context.m15_bias == 1 and setup.direction != OrderSide.BUY) or \
               (context.m15_bias == -1 and setup.direction != OrderSide.SELL):
                return False, "HTF_TREND_MISMATCH"

        # 3. Exhaustion Candle Check (RSI)
        m1_rsi = latest.get('rsi', 50)
        if setup.direction == OrderSide.BUY and m1_rsi > 80: return False, "EXHAUSTION_CANDLE"
        if setup.direction == OrderSide.SELL and m1_rsi < 20: return False, "EXHAUSTION_CANDLE"

        # 4. Displacement / Pullback Check
        body = abs(latest['close'] - latest['open'])
        avg_body = abs(m1['close'] - m1['open']).tail(20).mean()
        if body > avg_body * 2.5: # Extreme displacement
            reason = f"NO_VALID_PULLBACK: Trigger candle body ({body:.5f}) is > 2.5x avg body ({avg_body:.5f}). Price chasing detected."
            return False, reason

        # 5. Near Opposing Level/Liquidity
        if setup.direction == OrderSide.BUY:
            opposing_high = m15['high'].tail(50).max()
            if latest['close'] > opposing_high * 0.9998:
                return False, "NEAR_OPPOSING_LEVEL"
        else:
            opposing_low = m15['low'].tail(50).min()
            if latest['close'] < opposing_low * 1.0002:
                return False, "NEAR_OPPOSING_LEVEL"

        return True, None


