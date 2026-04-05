from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class AnnotationShape(str, Enum):
    HORIZONTAL_LINE = "HORIZONTAL_LINE"
    VERTICAL_LINE = "VERTICAL_LINE"
    ZONE_RECTANGLE = "ZONE_RECTANGLE"
    MARKER_UP = "MARKER_UP"
    MARKER_DOWN = "MARKER_DOWN"
    MARKER_DOT = "MARKER_DOT"
    LABEL = "LABEL"

class AnnotationStyle(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    RISK_STOP = "RISK_STOP"
    TARGET_PROFIT = "TARGET_PROFIT"
    INFO = "INFO"

class ChartAnnotation(BaseModel):
    id: str = Field(description="Unique UUID for this specific drawing")
    concept_type: str = Field(description="e.g., 'ORDER_BLOCK', 'SWEEP_LEVEL', 'ENTRY'")
    shape: AnnotationShape
    style: AnnotationStyle
    
    # Coordinate Geometry
    time1: int = Field(description="Unix timestamp (seconds) of exactly where it starts")
    price1: float = Field(description="Exact price level")
    time2: Optional[int] = Field(None, description="End time for Zones or Trendlines")
    price2: Optional[float] = Field(None, description="End price for Zones (Top/Bottom boundary)")
    
    # UX Data
    text: Optional[str] = Field(None, description="Text label shown on the chart")
    layer_priority: int = Field(0, description="0 (Back/Zones) to 10 (Front/Markers)")
    is_active: bool = Field(True, description="False if OB is mitigated or trade closed")
    metadata_fields: Dict[str, Any] = Field(default_factory=dict, description="Values for the frontend Hover Tooltip")

class TradeChartPayload(BaseModel):
    ticket_id: int
    symbol: str
    timeframe: str
    bars_start_time: int
    bars_end_time: int
    annotations: List[ChartAnnotation]
