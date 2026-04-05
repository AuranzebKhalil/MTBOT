from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def _now(): return datetime.now(timezone.utc)

class AuditEventBase(BaseModel):
    timestamp: datetime = Field(default_factory=_now)
    symbol: str
    strategy_name: Optional[str] = None
    fingerprint: Optional[str] = None
    environment: str = "LIVE" # LIVE, PAPER, SHADOW

class SetupDetectedEvent(AuditEventBase):
    event_type: str = "SETUP_DETECTED"
    score: float
    regime: str

class AIRejectedEvent(AuditEventBase):
    event_type: str = "AI_REJECTED"
    confidence: float
    threshold: float

class ValidationRejectedEvent(AuditEventBase):
    event_type: str = "VALIDATION_REJECTED"
    reasons: list[str]
    warnings: list[str]

class OrderSubmittedEvent(AuditEventBase):
    event_type: str = "ORDER_SUBMITTED"
    ticket_or_req_id: str
    lot_size: float
    expected_price: float

class OrderFilledEvent(AuditEventBase):
    event_type: str = "ORDER_FILLED"
    ticket: str
    fill_price: float
    slippage_points: float
    latency_ms: float

class ReconciliationIssueEvent(AuditEventBase):
    event_type: str = "RECONCILIATION_ISSUE"
    issue_type: str
    severity: str
    details: str
