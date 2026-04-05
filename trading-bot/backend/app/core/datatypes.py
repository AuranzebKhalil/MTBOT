from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

from app.core.enums import (
    SetupFamily, OrderSide, SignalStatus, EntryMode, 
    TradingSession, MarketRegime
)

# --- DATACLASSES ---

@dataclass
class SetupScore:
    total_score: float
    is_qualified: bool
    weight_breakdown: Dict[str, float] = field(default_factory=dict)
    factors: Dict[str, Any] = field(default_factory=dict) 

# Legacy alias for strategy compatibility
@dataclass
class ConfluenceScore(SetupScore):
    pass

@dataclass
class RiskParams:
    structural_sl: float
    volatility_buffer: float
    targets: List[float]

@dataclass
class InvalidationRule:
    setup_id: str
    expiry_bars: int
    structure_anchor: float        # Price level that triggers invalidation
    cancel_on_session_change: bool = True
    cancel_on_regime_flip: bool = True

@dataclass
class RawSetup:
    family: SetupFamily
    direction: OrderSide
    symbol: str
    entry_price: float
    stop_loss: float
    targets: List[float]
    setup_candle_timestamp: datetime
    anchors: Dict[str, Any]        # {"sweep_high": 1.2, "ob_zone": [1.1, 1.3]}
    metadata: Dict[str, Any] = field(default_factory=dict)
    chart_annotations: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class StrategyContext:
    symbol: str
    timeframe: str
    m15_bias: int                 # 1 (Bull), -1 (Bear), 0 (Neutral)
    m5_alignment: int
    session: str
    regime: str
    is_tradable: bool
    spread_v_atr: float
    current_tick: Dict[str, Any]

@dataclass
class StrategyDecision:
    is_triggered: bool
    action: OrderSide
    best_setup: Optional[RawSetup] = None
    selection_reason: str = ""
    rejection_reason: str = ""
    all_candidates: List[RawSetup] = field(default_factory=list)

@dataclass
class TradeSignal:
    idempotency_key: str
    signal_fingerprint: str
    strategy_name: str
    symbol: str
    timeframe: str
    side: OrderSide
    regime: str
    session: str
    setup_score: SetupScore
    ai_confidence: float
    ai_threshold_used: float
    entry_mode: EntryMode
    entry_price: float
    structural_sl: float
    volatility_buffer: float
    targets: List[float]
    estimated_rr: float
    setup_candle_timestamp: datetime
    chart_annotations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: SignalStatus = SignalStatus.DETECTED

    @property
    def strategy(self) -> str:
        return self.strategy_name

@dataclass
class ChartAnnotation:
    id: str
    concept_type: str
    shape: str
    style: str
    time1: int
    price1: float
    time2: Optional[int] = None
    price2: Optional[float] = None
    text: Optional[str] = None
    color: Optional[str] = None
    layer_priority: int = 0
    metadata_fields: Dict[str, Any] = field(default_factory=dict)
