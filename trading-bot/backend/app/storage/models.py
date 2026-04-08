from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # "user", "admin", "superadmin"
    is_active = Column(Boolean, default=True)
    is_breached = Column(Boolean, default=False)
    
    total_profit = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    
    risk_per_trade = Column(Float, default=0.01)
    max_trades = Column(Integer, default=2)
    daily_loss_limit = Column(Float, default=0.10)
    preferred_symbol = Column(String, default="XAUUSD")
    active_symbols = Column(String, default="XAUUSD")
    preferred_timeframe = Column(String, default="M1")
    preferred_session = Column(String, default="ALL")
    preferred_rr_ratio = Column(Float, default=1.5)
    symbol_settings = Column(JSON, default={}) # Stores { "GOLD": {"manual_volume": 0.1}, ... }
    strategy_settings = Column(JSON, default={}) 
    strategy_session_mapping = Column(JSON, default={}) # Stores { "MSS": ["LONDON", "NEW YORK"], "EXHAUSTION": ["ASIAN"], ... }
    
    # Partial Execution Settings
    partial_execution_enabled = Column(Boolean, default=True)
    partial_stage_1_trigger = Column(Float, default=0.6) # 60% of way to TP
    partial_stage_1_close_pct = Column(Float, default=0.5) # Close 50% of position
    partial_stage_2_trigger = Column(Float, default=0.8) # 80% of way to TP
    partial_stage_2_close_pct = Column(Float, default=0.25) # Close 25% of original position
    
    # New Filter Settings
    enable_post_sl_cooldown = Column(Boolean, default=True)
    cooldown_bars_after_sl = Column(Integer, default=5) 
    
    enable_same_zone_block = Column(Boolean, default=True)
    same_zone_distance_atr_multiplier = Column(Float, default=0.25)
    same_zone_block_minutes = Column(Integer, default=120) 
    
    enable_level_distance_filter = Column(Boolean, default=True)
    min_reward_to_nearest_level_rr = Column(Float, default=1.2)
    
    same_zone_threshold_points = Column(Integer, default=100) 
    min_reward_to_level_points = Column(Integer, default=50) # 5 pips
    late_entry_threshold = Column(Float, default=0.7) # 70% of move gone = block
    min_rr_filter = Column(Float, default=1.0) # Risk/Reward filter
    max_spread_points = Column(Float, default=50.0)
    news_filter_enabled = Column(Boolean, default=True)
    news_block_minutes_before = Column(Integer, default=20)
    news_block_minutes_after = Column(Integer, default=20)
    high_impact_only = Column(Boolean, default=True)
    session_filter_enabled = Column(Boolean, default=True)
    
    trades = relationship("Trade", back_populates="owner")
    risk_events = relationship("RiskEvent", back_populates="owner")
    tickets = relationship("SupportTicket", back_populates="owner", foreign_keys="SupportTicket.user_id")
    assigned_tickets = relationship("SupportTicket", back_populates="assignee", foreign_keys="SupportTicket.assigned_to")
    messages = relationship("SupportMessage", back_populates="sender")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, unique=True, index=True)
    symbol = Column(String, index=True)
    type = Column(String) 
    volume = Column(Float) # Current volume
    initial_volume = Column(Float, nullable=True) # Volume at entry
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    tp1 = Column(Float, nullable=True)
    tp2 = Column(Float, nullable=True)
    profit = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    exit_time = Column(DateTime, nullable=True)
    status = Column(String, index=True) # OPEN, CLOSED
    strategy_name = Column(String, nullable=True)
    rationale = Column(Text, nullable=True)
    
    # Context & AI Performance Analytics
    ai_score = Column(Float, nullable=True)
    session = Column(String, nullable=True)
    market_regime = Column(String, nullable=True)
    exit_reason = Column(String, nullable=True) # Overall reason like "TP_HIT"
    final_exit_reason = Column(String, nullable=True) # Legacy support if needed
    
    # Execution Analytics
    bid_at_entry = Column(Float, nullable=True)
    ask_at_entry = Column(Float, nullable=True)
    spread_at_entry = Column(Float, nullable=True)
    slippage_points = Column(Float, nullable=True)
    
    # Tracking for Staged Partial Closes
    stage1_executed = Column(Boolean, default=False) # Maps to stage1_completed
    stage1_partial_done = Column(Boolean, default=False)
    stage1_sl_done = Column(Boolean, default=False)
    stage1_trigger_time = Column(DateTime, nullable=True)
    
    stage2_executed = Column(Boolean, default=False) # Maps to stage2_completed
    stage2_partial_done = Column(Boolean, default=False)
    stage2_sl_done = Column(Boolean, default=False)
    stage2_trigger_time = Column(DateTime, nullable=True)
    
    breakeven_done = Column(Boolean, default=False)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="trades")
    execution_logs = relationship("ExecutionLog", back_populates="trade")

class BotState(Base):
    __tablename__ = "bot_state"
    
    id = Column(Integer, primary_key=True)
    is_running = Column(Boolean, default=False)
    status_message = Column(String, default="Bot is Idle")
    current_action = Column(String, default="None")
    last_loop_at = Column(DateTime)
    active_symbols = Column(JSON, default=["XAUUSD"]) 
    current_metrics = Column(JSON, default={}) 
    live_charts = Column(JSON, default={}) # Stores { "GOLD": [...] }
    live_logs = Column(JSON, default=[]) # Stores last 50 log strings
    recent_rejections = Column(JSON, default=[])
    ai_confidence_threshold = Column(Float, default=0.48)  # Operator-controlled 0.15–1.0
    strategy_settings = Column(JSON, default={}) # Synced from user for worker access
    filter_status = Column(JSON, default={}) # {cooldown: True, news: False, ...}
    active_cooldowns = Column(JSON, default=[]) # [{symbol, dir, expiry, ...}]
    active_blocked_zones = Column(JSON, default=[]) # [{symbol, dir, top, bottom, ...}]
    strategy_analytics = Column(JSON, default={}) # Cached stats for frontend
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SignalLog(Base):
    __tablename__ = "signal_logs"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    strategy = Column(String, index=True)
    direction = Column(String)
    entry = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    score = Column(Float)
    reasons = Column(JSON)
    status = Column(String) # APPROVED, REJECTED, IGNORED
    rejection_reason = Column(String, nullable=True)
    
    # Analytics
    ai_score = Column(Float, nullable=True)
    session = Column(String, nullable=True)
    market_regime = Column(String, nullable=True)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RiskEvent(Base):
    __tablename__ = "risk_events"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String) # DAILY_LOSS_LIMIT, MAX_TRADES, SPREAD_HIGH
    details = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="risk_events")

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    symbol = Column(String)
    requested_price = Column(Float)
    filled_price = Column(Float, nullable=True)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    deviation = Column(Integer)
    retcode = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    latency_ms = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    trade = relationship("Trade", back_populates="execution_logs")

class LatencyLog(Base):
    __tablename__ = "latency_logs"
    
    id = Column(Integer, primary_key=True)
    component = Column(String) # MT5_FETCH, AI_INFERENCE, DB_WRITE
    duration_ms = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TradeAnnotation(Base):
    """Stores the literal coordinates for the frontend to draw."""
    __tablename__ = "trade_annotations"
    
    id = Column(String, primary_key=True) # UUID
    ticket_id = Column(Integer, ForeignKey("trades.ticket_id"), index=True)
    symbol = Column(String)
    
    concept_type = Column(String)
    shape = Column(String)
    style = Column(String)
    
    time1 = Column(Integer)
    time2 = Column(Integer, nullable=True)
    price1 = Column(Float)
    price2 = Column(Float, nullable=True)
    
    text = Column(String, nullable=True)
    layer_priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, default={})
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Trades 1 <---> N TradeAnnotations
    trade = relationship("Trade", back_populates="annotations")

Trade.annotations = relationship("TradeAnnotation", back_populates="trade")

class TradeEvent(Base):
    """Stores the lifecycle transitions (Break-even, Trailing Stop updates)"""
    __tablename__ = "trade_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("trades.ticket_id"), index=True)
    event_type = Column(String) # "STOP_LOSS_MOVED_TO_BE", "PARTIAL_CLOSED"
    old_value = Column(Float, nullable=True)
    new_value = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    annotation_snapshot = Column(JSON, nullable=True) # Snapshot of new annotation pushed to chart

class NewsWindow(Base):
    __tablename__ = "news_windows"
    id = Column(Integer, primary_key=True)
    event_name = Column(String)
    currency = Column(String)
    impact = Column(String) # HIGH, MEDIUM, LOW
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=True)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String)
    status = Column(String, default="open") # "open", "pending", "resolved", "closed"
    priority = Column(String, default="normal")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    assignee = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_to])
    messages = relationship("SupportMessage", back_populates="ticket", cascade="all, delete-orphan")

class SupportMessage(Base):
    __tablename__ = "support_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    
    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User", back_populates="messages")

class BlockedZone(Base):
    __tablename__ = "blocked_zones"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    direction = Column(String) # BUY, SELL
    price_level = Column(Float)
    range_points = Column(Integer)
    expiry = Column(DateTime)
    reason = Column(String) # SL_HIT, MANUAL
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
