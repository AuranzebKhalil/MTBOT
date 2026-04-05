from pydantic import BaseModel
from typing import Optional

class RiskDecision(BaseModel):
    is_approved: bool
    reason: str
    lot_size: float = 0.0
    risk_pct: float = 0.0
    metadata: Optional[dict] = None
