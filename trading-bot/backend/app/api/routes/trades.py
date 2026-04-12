from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import Trade, SignalLog, BotState
from typing import List, Dict

router = APIRouter()

@router.get("")
def get_trades(status: str = "OPEN", limit: int = 50, db: Session = Depends(get_db)):
    if status.upper() == "ALL":
        return db.query(Trade).order_by(Trade.time.desc()).limit(limit).all()
    return db.query(Trade).filter(Trade.status == status.upper()).order_by(Trade.time.desc()).limit(limit).all()

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

@router.post("/{ticket_id}/close")
def close_trade(ticket_id: int, db: Session = Depends(get_db)):
    """Executes a full market close for an active position."""
    from app.market_data.mt5_client import MT5Client
    from fastapi import HTTPException
    
    trade = db.query(Trade).filter(Trade.ticket_id == ticket_id, Trade.status == "OPEN").first()
    if not trade:
        raise HTTPException(status_code=404, detail="Active trade not found in database.")

    client = MT5Client()
    if client.connect():
        # Resolve the symbol to the broker-specific name for execution
        mt5_symbol = client.resolve_symbol(trade.symbol)
        if not mt5_symbol:
            raise HTTPException(status_code=400, detail=f"Could not resolve execution symbol for {trade.symbol}")
            
        res = client.partial_close(ticket_id, trade.volume, mt5_symbol)
        if res.get("status") in ["SUCCESS", "CLOSED_FULL"]:
            # Sync DB state
            trade.status = "CLOSED"
            from datetime import datetime, timezone
            trade.exit_time = datetime.now(timezone.utc)
            trade.exit_price = res.get("effective_price") # This comes from the result
            db.commit()
            return {"status": "SUCCESS", "message": f"Closed #{ticket_id} on terminal."}
        else:
            raise HTTPException(status_code=500, detail=f"Terminal Exit Failed: {res.get('reason')}")
    
    raise HTTPException(status_code=503, detail="MT5 Terminal Disconnected")
