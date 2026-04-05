from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExecutionResult(BaseModel):
    success: bool
    ticket: Optional[int] = None
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    order_type: Optional[str] = None # "BUY" or "SELL"
    retcode: int
    comment: str
    lot_size: Optional[float] = None
    latency_ms: float = 0.0
    timestamp: datetime = datetime.utcnow()
