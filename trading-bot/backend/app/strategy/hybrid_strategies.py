from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.strategy.base import BaseStrategy
from app.strategy.families.hybrid_logic import HybridLogicFamily
from app.core.datatypes import (
    RawSetup,
    SetupScore,
    SetupFamily,
    StrategyContext,
    InvalidationRule,
)
from indicators import SMCIndicators
from app.strategy.models import Signal

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

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.MEAN_REVERSION)
        self.strategy_id = "HYBRID_REVERSION"
        self.logic_family = HybridLogicFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        # Use local preprocessed copy to avoid contaminating shared context
        m1_local = self.logic_family.preprocess(data["M1"])
        local_data = {**data, "M1": m1_local}
        
        # Only trade if ranging (lower ADX)
        regime = self.logic_family.detect_regime(data["M15"])
        if regime != "RANGING": return None
        
        signal = self.logic_family.check_mean_reversion(local_data, context.symbol)
        return self._signal_to_setup(signal) if signal else None

    def _signal_to_setup(self, signal: Signal) -> RawSetup:
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
        return [] # Simplified

    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        return _default_invalidation(setup)

    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.entry_price

    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        return setup.stop_loss

    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        return setup.targets

class SupportResistanceStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.SUPPORT_RESISTANCE)
        self.strategy_id = "HYBRID_SR"
        self.logic_family = HybridLogicFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        m1_local = self.logic_family.preprocess(data["M1"])
        local_data = {**data, "M1": m1_local}
        signal = self.logic_family.check_support_resistance(local_data, context.symbol)
        return self._signal_to_setup(signal) if signal else None

    def _signal_to_setup(self, signal: Signal) -> RawSetup:
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

class BreakoutStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.BREAKOUT)
        self.strategy_id = "HYBRID_BREAKOUT"
        self.logic_family = HybridLogicFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        m1_local = self.logic_family.preprocess(data["M1"])
        local_data = {**data, "M1": m1_local}
        
        # Only trade if consolidation
        regime = self.logic_family.detect_regime(data["M15"])
        if regime != "CONSOLIDATION": return None
        
        signal = self.logic_family.check_breakout(local_data, context.symbol)
        return self._signal_to_setup(signal) if signal else None

    def _signal_to_setup(self, signal: Signal) -> RawSetup:
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

class HybridSwitcherStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.HYBRID)
        self.strategy_id = "HYBRID_MASTER"
        self.logic_family = HybridLogicFamily(indicators)

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        m1_local = self.logic_family.preprocess(data["M1"])
        local_data = {**data, "M1": m1_local}
        
        # Call the switcher's evaluation
        approved, _ = self.logic_family.evaluate(context.symbol, local_data)
        if approved:
            return self._signal_to_setup(approved[0])
        return None

    def _signal_to_setup(self, signal: Signal) -> RawSetup:
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
        m5 = data["M5"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        from app.core.enums import OrderSide
        
        # 1. M15 Trend Alignment
        if context.m15_bias != 0:
            if (context.m15_bias == 1 and setup.direction != OrderSide.BUY) or \
               (context.m15_bias == -1 and setup.direction != OrderSide.SELL):
                return False, "HTF_TREND_MISMATCH"

        # 2. M5 Confirmation
        m5_latest = m5.iloc[-1]
        m5_bullish = m5_latest['close'] > m5_latest['open']
        if setup.direction == OrderSide.BUY and not m5_bullish:
             if not self.logic_family._is_bullish_rejection(m5_latest):
                return False, "NO_M5_CONFIRMATION"
        if setup.direction == OrderSide.SELL and m5_bullish:
             if not self.logic_family._is_bearish_rejection(m5_latest):
                return False, "NO_M5_CONFIRMATION"

        # 3. Near Opposing Level
        support = m15[m15['swing_low'] == True]['low'].tail(3).max()
        resistance = m15[m15['swing_high'] == True]['high'].tail(3).min()
        if setup.direction == OrderSide.BUY and latest['close'] > resistance * 0.9995:
            return False, "NEAR_OPPOSING_LEVEL"
        if setup.direction == OrderSide.SELL and latest['close'] < support * 1.0005:
            return False, "NEAR_OPPOSING_LEVEL"

        # 4. Displacement / Pullback
        body = abs(latest['close'] - latest['open'])
        avg_body = abs(m1['close'] - m1['open']).tail(20).mean()
        if body > avg_body * 3.0:
            return False, "NO_VALID_PULLBACK"

        # 5. SMC Confirmation
        smc_confirmed = False
        m1_recent = m1.tail(5)
        for col in ['liquidity_sweep', 'bos', 'choch', 'order_block']:
            if col in m1.columns and (m1_recent[col] != 0).any():
                smc_confirmed = True
                break
        
        if not smc_confirmed:
            return False, "NO_LIQUIDITY_CONFIRMATION"

        return True, None

class MadTrendLoopStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.HYBRID)
        self.strategy_id = "MAD_TREND_LOOP"
        self.indicators = indicators
        from app.strategy.custome_indicator import MeanDeviationLoopStrategy as IndicatorClass
        self.indicator_class = IndicatorClass

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        df = data["M1"]
        # In backtest, signals are often pre-calculated in runner.py
        if 'buy_signal' in df.columns:
            latest = df.iloc[-1]
            df_ind = df # Use existing
        else:
            df_copy = df.copy()
            df_ind = self.indicator_class.apply_indicator(df_copy)
            latest = df_ind.iloc[-1]
        
        if df_ind.empty: return None
        
        from app.core.datatypes import OrderSide
        direction = None
        if latest.get('buy_signal', False):
            direction = OrderSide.BUY
        elif latest.get('sell_signal', False):
            direction = OrderSide.SELL
            
        if not direction:
            return None
            
        price = float(latest['close'])
        
        atr_val = self.indicators.calculate_atr(df)
        atr_latest = float(atr_val.iloc[-1]) if not atr_val.empty else 0.005
        sl_dist = atr_latest * 1.5
        tp_dist = atr_latest * 3.0
        
        sl = price - sl_dist if direction == OrderSide.BUY else price + sl_dist
        tp = price + tp_dist if direction == OrderSide.BUY else price - tp_dist
        
        signal = Signal(
            strategy=self.family,
            symbol=context.symbol,
            timeframe="M1",
            direction=direction,
            entry=price,
            sl=sl,
            tp=tp,
            score=85.0,
            reasons=["MAD trend loop score sequence matched"],
            metadata={"score": 85.0},
            timestamp=df.index[-1]
        )
        return self._signal_to_setup(signal)

    def _signal_to_setup(self, signal: Signal) -> RawSetup:
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
