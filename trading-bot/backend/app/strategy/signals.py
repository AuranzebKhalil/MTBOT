from datetime import datetime, timezone
from app.core.datatypes import TradeSignal, SignalStatus, InvalidationReason

class SignalExpiryManager:
    def check_signal(self, signal: TradeSignal, current_bars_passed: int, current_regime: str, current_spread: float) -> bool:
        """Returns True if valid, False if invalidated/expired. Safely updates status."""
        if signal.status not in [SignalStatus.APPROVED, SignalStatus.LOCKED]:
            return False

        now = datetime.now(timezone.utc)
        
        if signal.expires_at and now >= signal.expires_at:
            signal.status = SignalStatus.EXPIRED
            signal.invalidation_reasons.append(InvalidationReason.TIME_EXPIRED)
            return False
            
        if signal.expiry_by_bars and current_bars_passed >= signal.expiry_by_bars:
            signal.status = SignalStatus.EXPIRED
            signal.invalidation_reasons.append(InvalidationReason.CANDLE_LIMIT_REACHED)
            return False
            
        if current_spread > signal.volatility_buffer:
            signal.status = SignalStatus.INVALIDATED
            signal.invalidation_reasons.append(InvalidationReason.SPREAD_UNSAFE)
            return False
            
        if signal.regime.value != current_regime and current_regime != "HIGH_VOLATILITY":
             signal.status = SignalStatus.INVALIDATED
             signal.invalidation_reasons.append(InvalidationReason.REGIME_CHANGED)
             return False
             
        return True
