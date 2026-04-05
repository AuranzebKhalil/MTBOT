from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.storage.models import Base
import logging

logger = logging.getLogger(__name__)

# Use check_same_thread=False only for SQLite
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True
)

# Enable WAL mode for SQLite to improve concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Lightweight migration for new columns
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                # Add columns if they don't exist (ignores error if already present)
                from sqlalchemy.exc import OperationalError
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN status_message VARCHAR DEFAULT 'Bot is Idle'"))
                except OperationalError: pass 
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN current_action VARCHAR DEFAULT 'None'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN ai_confidence_threshold REAL DEFAULT 0.48"))
                except OperationalError: pass
                # Migration for RR Ratio in User table
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN preferred_rr_ratio FLOAT DEFAULT 1.5"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN symbol_settings JSON DEFAULT '{}'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN strategy_settings JSON DEFAULT '{}'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN strategy_settings JSON DEFAULT '{}'"))
                except OperationalError: pass
                # Migration for partial close support
                try:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN initial_volume FLOAT"))
                except OperationalError: pass
                # Tracking flags for staged execution
                try:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN stage1_executed BOOLEAN DEFAULT 0"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN stage2_executed BOOLEAN DEFAULT 0"))
                except OperationalError: pass
                
                # User config for partial execution
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN partial_execution_enabled BOOLEAN DEFAULT 1"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN partial_stage_1_trigger FLOAT DEFAULT 0.6"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN partial_stage_1_close_pct FLOAT DEFAULT 0.5"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN partial_stage_2_trigger FLOAT DEFAULT 0.8"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN partial_stage_2_close_pct FLOAT DEFAULT 0.25"))
                except OperationalError: pass

                # --- NEW RISK FILTERS & ANALYTICS ---
                # User Settings
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN strategy_session_mapping JSON DEFAULT '{}'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN enable_post_sl_cooldown BOOLEAN DEFAULT 1"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN cooldown_bars_after_sl INTEGER DEFAULT 5"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN enable_same_zone_block BOOLEAN DEFAULT 1"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN same_zone_distance_atr_multiplier FLOAT DEFAULT 0.25"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN same_zone_block_minutes INTEGER DEFAULT 120"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN enable_level_distance_filter BOOLEAN DEFAULT 1"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN min_reward_to_nearest_level_rr FLOAT DEFAULT 1.2"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN news_filter_enabled BOOLEAN DEFAULT 1"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN news_block_minutes_before INTEGER DEFAULT 20"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN news_block_minutes_after INTEGER DEFAULT 20"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN high_impact_only BOOLEAN DEFAULT 1"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN session_filter_enabled BOOLEAN DEFAULT 1"))
                except OperationalError: pass

                # Extra User Configs
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN same_zone_threshold_points INTEGER DEFAULT 100"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN min_reward_to_level_points INTEGER DEFAULT 50"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN late_entry_threshold FLOAT DEFAULT 0.7"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN min_rr_filter FLOAT DEFAULT 1.0"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN max_spread_points FLOAT DEFAULT 50.0"))
                except OperationalError: pass

                # Bot State
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN filter_status JSON DEFAULT '{}'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN active_cooldowns JSON DEFAULT '[]'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN active_blocked_zones JSON DEFAULT '[]'"))
                except OperationalError: pass
                try:
                    conn.execute(text("ALTER TABLE bot_state ADD COLUMN strategy_analytics JSON DEFAULT '{}'"))
                except OperationalError: pass
                
                conn.commit()
        except Exception as e:
            logger.debug(f"Migration skip: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For non-FastAPI contexts (like the worker)
class DatabaseContext:
    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()
