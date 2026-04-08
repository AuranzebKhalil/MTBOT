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
        # Preprocess BB/RSI/ADX
        data["M1"] = self.logic_family.preprocess(data["M1"])
        
        # Only trade if ranging (lower ADX)
        regime = self.logic_family.detect_regime(data["M15"])
        if regime != "RANGING": return None
        
        signal = self.logic_family.check_mean_reversion(data, context.symbol)
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
        data["M1"] = self.logic_family.preprocess(data["M1"])
        signal = self.logic_family.check_support_resistance(data, context.symbol)
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
        data["M1"] = self.logic_family.preprocess(data["M1"])
        
        # Only trade if consolidation
        regime = self.logic_family.detect_regime(data["M15"])
        if regime != "CONSOLIDATION": return None
        
        signal = self.logic_family.check_breakout(data, context.symbol)
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
        data["M1"] = self.logic_family.preprocess(data["M1"])
        
        # Call the switcher's evaluation
        approved, _ = self.logic_family.evaluate(context.symbol, data)
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

class MadTrendLoopStrategy(BaseStrategy):
    def __init__(self, indicators: SMCIndicators):
        super().__init__(SetupFamily.HYBRID)
        self.strategy_id = "MAD_TREND_LOOP"
        self.indicators = indicators
        from app.strategy.custome_indicator import MeanDeviationLoopStrategy as IndicatorClass
        self.indicator_class = IndicatorClass

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        df = data["M1"].copy()
        df_ind = self.indicator_class.apply_indicator(df)
        if df_ind.empty: return None
        
        latest = df_ind.iloc[-1]
        
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
