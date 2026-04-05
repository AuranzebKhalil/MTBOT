from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import Trade, SignalLog, BotState
from typing import List, Dict

router = APIRouter()

@router.get("/recent")
def get_recent_trades(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Trade).order_by(Trade.time.desc()).limit(limit).all()

@router.get("/signals")
def get_recent_signals(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(SignalLog).order_by(SignalLog.timestamp.desc()).limit(limit).all()

@router.get("/performance")
def get_performance_stats(db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    return state.strategy_analytics if state else {}
