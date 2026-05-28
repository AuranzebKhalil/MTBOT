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
    min_setup_score: float
    min_ai_confidence: float
    max_spread_points: float
    enable_htf_filter: bool
    enable_volatility_filter: bool
    min_sl_atr_multiplier: float
    late_entry_threshold: float
    min_rr_filter: float
    enable_post_sl_cooldown: bool
    cooldown_bars_after_sl: int
    enable_same_zone_block: bool
    same_zone_distance_atr_multiplier: float
    enable_level_distance_filter: bool
    min_reward_to_nearest_level_rr: float

@router.get("/", response_model=RiskSettings)
def get_risk_settings(db: Session = Depends(get_db)):
    user = db.query(User).first() # Default user
    if not user:
        return RiskSettings(
            risk_per_trade=0.01, max_trades=2, daily_loss_limit=0.10, preferred_session="ALL", risk_reward_ratio=1.5,
            partial_execution_enabled=True, partial_stage_1_trigger=0.6, partial_stage_1_close_pct=0.5,
            partial_stage_2_trigger=0.8, partial_stage_2_close_pct=0.25,
            min_setup_score=70.0, min_ai_confidence=0.45, max_spread_points=50.0,
            enable_htf_filter=True, enable_volatility_filter=True, min_sl_atr_multiplier=0.5,
            late_entry_threshold=0.7, min_rr_filter=1.0,
            enable_post_sl_cooldown=True, cooldown_bars_after_sl=5,
            enable_same_zone_block=True, same_zone_distance_atr_multiplier=0.25,
            enable_level_distance_filter=True, min_reward_to_nearest_level_rr=1.2
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
        min_setup_score=getattr(user, "min_setup_score", 70.0),
        min_ai_confidence=getattr(user, "min_ai_confidence", 0.45),
        max_spread_points=getattr(user, "max_spread_points", 50.0),
        enable_htf_filter=getattr(user, "enable_htf_filter", True),
        enable_volatility_filter=getattr(user, "enable_volatility_filter", True),
        min_sl_atr_multiplier=getattr(user, "min_sl_atr_multiplier", 0.5),
        late_entry_threshold=getattr(user, "late_entry_threshold", 0.7),
        min_rr_filter=getattr(user, "min_rr_filter", 1.0),
        enable_post_sl_cooldown=getattr(user, "enable_post_sl_cooldown", True),
        cooldown_bars_after_sl=getattr(user, "cooldown_bars_after_sl", 5),
        enable_same_zone_block=getattr(user, "enable_same_zone_block", True),
        same_zone_distance_atr_multiplier=getattr(user, "same_zone_distance_atr_multiplier", 0.25),
        enable_level_distance_filter=getattr(user, "enable_level_distance_filter", True),
        min_reward_to_nearest_level_rr=getattr(user, "min_reward_to_nearest_level_rr", 1.2),
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
    
    user.min_setup_score = settings.min_setup_score
    user.min_ai_confidence = settings.min_ai_confidence
    user.max_spread_points = settings.max_spread_points
    user.enable_htf_filter = settings.enable_htf_filter
    user.enable_volatility_filter = settings.enable_volatility_filter
    user.min_sl_atr_multiplier = settings.min_sl_atr_multiplier
    user.late_entry_threshold = settings.late_entry_threshold
    user.min_rr_filter = settings.min_rr_filter
    user.enable_post_sl_cooldown = settings.enable_post_sl_cooldown
    user.cooldown_bars_after_sl = settings.cooldown_bars_after_sl
    user.enable_same_zone_block = settings.enable_same_zone_block
    user.same_zone_distance_atr_multiplier = settings.same_zone_distance_atr_multiplier
    user.enable_level_distance_filter = settings.enable_level_distance_filter
    user.min_reward_to_nearest_level_rr = settings.min_reward_to_nearest_level_rr
    
    db.commit()
    return {"message": "Risk settings updated"}
