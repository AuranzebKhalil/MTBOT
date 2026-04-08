from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    risk_per_trade = Column(Float, default=0.03)
    max_trades = Column(Integer, default=2)
    daily_loss_limit = Column(Float, default=3.0)
    preferred_symbol = Column(String, default="GOLD")
    active_symbols = Column(String, default="GOLD") # Comma-separated list for multi-chart support
    preferred_timeframe = Column(String, default="M1")
    preferred_session = Column(String, default="ALL") # ALL, LONDON, NEW YORK, ASIAN
    trading_mode = Column(String, default="DEMO") # DEMO or REAL
    
    trades = relationship("Trade", back_populates="owner")
    custom_strategies = relationship("CustomStrategy", back_populates="owner")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, unique=True, index=True)
    symbol = Column(String)
    type = Column(String) # BUY/SELL
    volume = Column(Float)
    entry_price = Column(Float)
    current_price = Column(Float, nullable=True)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    profit = Column(Float)
    time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="CLOSED") # OPEN/CLOSED
    rationale = Column(String, nullable=True) # Explanation for why the trade was taken
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="trades")

class CustomStrategy(Base):
    __tablename__ = "custom_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String, default="Manual")
    description = Column(String)
    logic = Column(String)
    color = Column(String, default="#00ffbd")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="custom_strategies")
