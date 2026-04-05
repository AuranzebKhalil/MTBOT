from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.datatypes import OrderSide, TradeSignal
from app.core.annotations import AnnotationShape, AnnotationStyle


@dataclass
class SMCZone:
    id: str
    symbol: str
    timeframe: str
    concept_type: str  # e.g. ORDER_BLOCK, FVG
    direction: OrderSide
    time_start: int  # unix seconds
    time_end: int  # unix seconds (projection end)
    price_low: float
    price_high: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZoneRegistry:
    zones: Dict[str, SMCZone] = field(default_factory=dict)

    def add_zone(self, zone: SMCZone) -> None:
        self.zones[zone.id] = zone

    def get_zone(self, zone_id: str) -> Optional[SMCZone]:
        return self.zones.get(zone_id)

    def get_zones_for_symbol(self, symbol: str) -> List[SMCZone]:
        return [z for z in self.zones.values() if z.symbol == symbol]


@dataclass
class TradeAnnotationRecord:
    id: str
    symbol: str
    ticket_id: Optional[int]
    signal_id: Optional[str]
    concept_type: str
    shape: AnnotationShape
    style: AnnotationStyle
    time1: int
    price1: float
    time2: Optional[int] = None
    price2: Optional[float] = None
    text: Optional[str] = None
    layer_priority: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeSignalSnapshot:
    signal_id: str
    symbol: str
    timeframe: str
    side: OrderSide
    entry: float
    sl: float
    tp: float
    created_at: datetime
    context_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyOutput:
    signal: Optional[TradeSignal]
    involved_zone_ids: List[str] = field(default_factory=list)
    annotations: List[TradeAnnotationRecord] = field(default_factory=list)
    context_summary: Dict[str, Any] = field(default_factory=dict)

