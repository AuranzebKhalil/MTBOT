from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict
from app.core.enums import OrderSide, StrategyFamily

class Signal(BaseModel):
    strategy: str
    symbol: str
    timeframe: str
    direction: OrderSide
    entry: float
    sl: float
    tp: float
    score: float
    reasons: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = {}

class StrategyResult(BaseModel):
    signal: Optional[Signal] = None
    pipeline_status: Dict = {}
    macro_bias: str = "NEUTRAL"
    m5_alignment: bool = False
