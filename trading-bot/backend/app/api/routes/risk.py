from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import User
from pydantic import BaseModel

router = APIRouter()

class RiskSettings(BaseModel):
    risk_per_trade: float
    max_trades: int
    daily_loss_limit: float
    preferred_session: str
    risk_reward_ratio: float
    partial_execution_enabled: bool
    partial_stage_1_trigger: float
    partial_stage_1_close_pct: float
    partial_stage_2_trigger: float
    partial_stage_2_close_pct: float

@router.get("/", response_model=RiskSettings)
def get_risk_settings(db: Session = Depends(get_db)):
    user = db.query(User).first() # Default user
    if not user:
        return RiskSettings(
            risk_per_trade=0.01, max_trades=2, daily_loss_limit=0.10, preferred_session="ALL", risk_reward_ratio=1.5,
            partial_execution_enabled=True, partial_stage_1_trigger=0.6, partial_stage_1_close_pct=0.5,
            partial_stage_2_trigger=0.8, partial_stage_2_close_pct=0.25
        )
    return RiskSettings(
        risk_per_trade=user.risk_per_trade,
        max_trades=user.max_trades,
        daily_loss_limit=user.daily_loss_limit,
        preferred_session=user.preferred_session or "ALL",
        risk_reward_ratio=getattr(user, "preferred_rr_ratio", 1.5),
        partial_execution_enabled=getattr(user, "partial_execution_enabled", True),
        partial_stage_1_trigger=getattr(user, "partial_stage_1_trigger", 0.6),
        partial_stage_1_close_pct=getattr(user, "partial_stage_1_close_pct", 0.5),
        partial_stage_2_trigger=getattr(user, "partial_stage_2_trigger", 0.8),
        partial_stage_2_close_pct=getattr(user, "partial_stage_2_close_pct", 0.25),
    )

@router.post("/")
def update_risk_settings(settings: RiskSettings, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        user = User(email="admin@alertli.com")
        db.add(user)
    
    user.risk_per_trade = settings.risk_per_trade
    user.max_trades = settings.max_trades
    user.daily_loss_limit = settings.daily_loss_limit
    user.preferred_session = settings.preferred_session
    user.preferred_rr_ratio = settings.risk_reward_ratio
    
    # Partial Execution Settings
    user.partial_execution_enabled = settings.partial_execution_enabled
    user.partial_stage_1_trigger = settings.partial_stage_1_trigger
    user.partial_stage_1_close_pct = settings.partial_stage_1_close_pct
    user.partial_stage_2_trigger = settings.partial_stage_2_trigger
    user.partial_stage_2_close_pct = settings.partial_stage_2_close_pct
    
    db.commit()
    return {"message": "Risk settings updated"}
