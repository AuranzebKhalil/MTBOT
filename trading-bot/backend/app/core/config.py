from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Alertli Trading Bot"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "institutional-secret-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # MT5 Credentials
    MT5_LOGIN: Optional[int] = None
    MT5_PASSWORD: Optional[str] = None
    MT5_SERVER: Optional[str] = None
    MT5_PATH: Optional[str] = None
    
    # Bot Settings
    DEFAULT_SYMBOL: str = "XAUUSD"
    ACTIVE_SYMBOLS: List[str] = ["EURUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "GBPUSD", "XAUUSD"]
    TIMEFRAME_M1: str = "M1"
    TIMEFRAME_M5: str = "M5"
    TIMEFRAME_M15: str = "M15"
    BOT_LOOP_INTERVAL: float = 2.0  # seconds

    # Safety / Simulation
    # When enabled, all MT5 order sending is blocked (backtest/replay safe mode).
    BACKTEST_MODE: bool = False
    
    # Risk Management
    RISK_PER_TRADE: float = 0.01  # 1%
    MAX_TRADES: int = 2
    MAX_DAILY_TRADES: int = 20
    DAILY_LOSS_LIMIT: float = 0.10  # 10%
    MAX_SPREAD_PIPS: float = 50.0
    
    # Strategy Filter Thresholds
    AI_THRESHOLDS: dict = {
        "HYBRID_MASTER": 0.56,
        "SMC_VOLUME": 0.56,
        "HYBRID_REVERSION": 0.58,
        "SMC_REVERSAL": 0.58,
        "HYBRID_SR": 0.58,
        "SMC_TREND": 0.56,
        "SMC_MITIGATION": 0.60,
        "SMC_MSS": 0.62,
        "DEFAULT": 0.52
    }
    
    STRUCTURE_THRESHOLDS: dict = {
        "HYBRID_MASTER": 0.65,
        "SMC_VOLUME": 0.55,
        "HYBRID_REVERSION": 0.68,
        "SMC_REVERSAL": 0.68,
        "HYBRID_SR": 0.62,
        "SMC_TREND": 0.60,
        "SMC_MITIGATION": 0.68,
        "SMC_MSS": 0.70,
        "DEFAULT": 0.45
    }

    # Quality Filters
    MAX_CANDLE_ATR_RATIO: float = 1.5
    MIN_SCORE_SMC_TREND: float = 70.0
    MIN_SCORE_SMC_MSS: float = 75.0
    
    # Cooldowns (minutes)
    COOLDOWN_AFTER_LOSS: int = 45
    COOLDOWN_SAME_SETUP: int = 60
    
    # Daily Protection
    MAX_TRADES_PER_DAY: int = 3
    MAX_CONSECUTIVE_LOSSES: int = 2
    DAILY_DRAWDOWN_LIMIT_PCT: float = 0.015  # 1.5%
    
    # Phase 2 Cooldown, Clustering, & Health Monitoring Settings
    COOLDOWN_AFTER_LOSSES: int = 2
    COOLDOWN_MINUTES: int = 60
    PER_STRATEGY_COOLDOWN: bool = True
    PER_SYMBOL_COOLDOWN: bool = True
    MIN_CANDLES_BETWEEN_SAME_STRATEGY_ENTRIES: int = 10
    MIN_PRICE_DISTANCE_ATR_MULTIPLIER: float = 0.5
    MIN_ROLLING_WIN_RATE: float = 40.0
    MIN_ROLLING_PROFIT_FACTOR: float = 1.0

    # Staged Management
    ENABLE_PARTIAL_TP: bool = True
    STAGE_1_TRIGGER_PCT: float = 0.6
    STAGE_1_CLOSE_PCT: float = 0.5
    STAGE_1_SL_OFFSET_PCT: float = 0.1
    STAGE_2_TRIGGER_PCT: float = 0.8
    STAGE_2_CLOSE_PCT: float = 0.25 # Percent of ORIGINAL volume
    
    # Database
    SQLITE_DB_PATH: str = "trading_bot.db"
    POSTGRES_URL: Optional[str] = None
    
    @property
    def DATABASE_URL(self) -> str:
        if self.POSTGRES_URL:
            return self.POSTGRES_URL
        return f"sqlite:///./{self.SQLITE_DB_PATH}"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )

settings = Settings()
