from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from app.core.datatypes import (
    RawSetup, SetupScore, SetupFamily, 
    StrategyContext, InvalidationRule
)

class BaseStrategy(ABC):
    def __init__(self, family: SetupFamily):
        self.family = family

    @abstractmethod
    def detect_setup(self, data: Dict[str, Any], context: StrategyContext) -> Optional[RawSetup]:
        """
        Scans data (M1, M5, M15) for a candidate setup.
        Returns RawSetup if found, else None.
        """
        pass

    @abstractmethod
    def score_setup(self, setup: RawSetup, context: StrategyContext) -> SetupScore:
        """
        Applies weighted scoring to a detected setup.
        """
        pass

    @abstractmethod
    def build_annotations(self, setup: RawSetup) -> List[Dict[str, Any]]:
        """
        Generates geometric chart data for frontend rendering.
        """
        pass

    @abstractmethod
    def get_invalidation_rules(self, setup: RawSetup) -> InvalidationRule:
        """
        Defines when this setup becomes stale or invalid.
        """
        pass

    @abstractmethod
    def propose_entry(self, setup: RawSetup, context: StrategyContext) -> float:
        """Calculates precise entry point (Market vs Limit)."""
        pass

    @abstractmethod
    def propose_stop(self, setup: RawSetup, context: StrategyContext) -> float:
        """Calculates precise stop loss with volatility buffer."""
        pass

    @abstractmethod
    def propose_targets(self, setup: RawSetup, context: StrategyContext) -> List[float]:
        """Calculates TP1, TP2 based on structural RR."""
        pass
