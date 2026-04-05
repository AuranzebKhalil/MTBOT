from sqlalchemy.orm import Session
from app.storage.models import Trade, SignalLog, BotState, User
from typing import List, Optional, Dict
from datetime import datetime

class TradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, limit: int = 100) -> List[Trade]:
        return self.db.query(Trade).order_by(Trade.time.desc()).limit(limit).all()

    def create_trade(self, trade_data: Dict) -> Trade:
        trade = Trade(**trade_data)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

class SignalRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_signal(self, signal_data: Dict) -> SignalLog:
        log = SignalLog(**signal_data)
        self.db.add(log)
        self.db.commit()
        return log

    def get_recent(self, limit: int = 50) -> List[SignalLog]:
        return self.db.query(SignalLog).order_by(SignalLog.timestamp.desc()).limit(limit).all()

class StateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_state(self) -> BotState:
        state = self.db.query(BotState).first()
        if not state:
            state = BotState(is_running=False, active_symbols=["GOLD"])
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
        return state

    def update_state(self, updates: Dict):
        state = self.get_state()
        for key, value in updates.items():
            setattr(state, key, value)
        self.db.commit()
        self.db.refresh(state)
