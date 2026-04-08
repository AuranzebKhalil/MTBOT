from enum import Enum

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

class MarketSession(str, Enum):
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    ASIAN = "ASIAN"
    IDLE = "IDLE"

class TradingSession(str, Enum):
    ASIA = "ASIA"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OVERLAP = "OVERLAP"
    DEAD_ZONE = "DEAD_ZONE"

class StrategyFamily(str, Enum):
    """Legacy and Display Names."""
    SWEEP_RECLAIM = "Sweep Reclaim Reversal"       
    VSA_SHIFT = "VSA Institutional Shift"
    CONTINUATION = "Continuation Retest"
    MITIGATION = "First Touch Mitigation"
    EXHAUSTION = "Exhaustion Reversal"
    MSS = "Market Structure Shift"
    BREAKER = "Breaker Block Retest"
    VOLUME = "Volume Profile POC"
    MEAN_REVERSION = "Mean Reversion (BB/RSI)"
    SUPPORT_RESISTANCE = "Support & Resistance"
    BREAKOUT = "Breakout Momentum"
    HYBRID = "Hybrid Dynamic Switcher"

class SetupFamily(str, Enum):
    """Core logic family identifiers."""
    SWEEP_RECLAIM = "SWEEP_RECLAIM"
    VSA_SHIFT = "VSA_SHIFT"
    CONTINUATION = "CONTINUATION"
    MITIGATION = "MITIGATION"
    EXHAUSTION = "EXHAUSTION"
    MSS = "MSS"
    BREAKER = "BREAKER"
    VOLUME = "VOLUME"
    MEAN_REVERSION = "MEAN_REVERSION"
    SUPPORT_RESISTANCE = "SUPPORT_RESISTANCE"
    BREAKOUT = "BREAKOUT"
    HYBRID = "HYBRID"

class SignalStatus(str, Enum):
    DETECTED = "DETECTED"
    SCORED = "SCORED"
    APPROVED = "APPROVED"
    AI_REJECTED = "AI_REJECTED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
    TRADE_OPEN = "TRADE_OPEN"
    TRADE_CLOSED = "TRADE_CLOSED"

class EntryMode(str, Enum):
    MARKET_IMMEDIATE = "MARKET_IMMEDIATE"
    LIMIT_ORDER = "LIMIT_ORDER"
    STOP_ORDER = "STOP_ORDER"

class MarketRegime(str, Enum):
    TRENDING_BULLISH = "TRENDING_BULLISH"
    TRENDING_BEARISH = "TRENDING_BEARISH"
    RANGING_EXPANDED = "RANGING_EXPANDED"
    RANGING_COMPRESSED = "RANGING_COMPRESSED"
    RANGING_HIGH_VOL = "RANGING_HIGH_VOL"
    RANGING_LOW_VOL = "RANGING_LOW_VOL"

class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
