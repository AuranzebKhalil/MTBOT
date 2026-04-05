from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import BotState
from app.telemetry.metrics import metrics
from pydantic import BaseModel
from typing import List

router = APIRouter()

class BotStatus(BaseModel):
    is_running: bool
    status_message: str
    current_action: str
    last_loop_at: str
    active_symbols: List[str]
    metrics: dict
    filter_status: dict
    active_cooldowns: list
    strategy_analytics: dict

@router.get("/status", response_model=BotStatus)
def get_bot_status(db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    if not state:
        return BotStatus(
            is_running=False, 
            status_message="", 
            current_action="", 
            last_loop_at="Never", 
            active_symbols=[], 
            metrics={}, 
            filter_status={}, 
            active_cooldowns=[], 
            strategy_analytics={}
        )
    
    # Merge telemetry metrics with DB-stored metrics
    app_metrics = dict(state.current_metrics or {})
    app_metrics.update(metrics.get_summary())
    
    return BotStatus(
        is_running=state.is_running,
        status_message=state.status_message,
        current_action=state.current_action,
        last_loop_at=state.last_loop_at.isoformat() if state.last_loop_at else "Never",
        active_symbols=state.active_symbols,
        metrics=app_metrics,
        filter_status=state.filter_status or {},
        active_cooldowns=state.active_cooldowns or [],
        strategy_analytics=state.strategy_analytics or {}
    )

@router.post("/start")
def start_bot(db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    if not state:
        state = BotState(is_running=True, active_symbols=["XAUUSD"])
        db.add(state)
    else:
        state.is_running = True
    db.commit()
    return {"message": "Bot engine engaged"}

@router.post("/stop")
def stop_bot(db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    if state:
        state.is_running = False
        db.commit()
    return {"message": "Bot engine halted"}
