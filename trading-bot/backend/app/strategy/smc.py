from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.strategy.base import BaseStrategy
from app.strategy.families.smc import SMCStrategyFamily
from app.core.datatypes import (
    RawSetup,
    SetupScore,
    SetupFamily,
    StrategyContext,
    InvalidationRule,
)
from indicators import SMCIndicators


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

    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        signal = self.logic_family.check_volume_flow(data, context.m15_bias, context.symbol)
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


