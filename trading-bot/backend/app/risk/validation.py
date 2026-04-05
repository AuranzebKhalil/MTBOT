from dataclasses import dataclass, field
from typing import List, Optional, Dict
from app.core.datatypes import TradeSignal, SignalStatus, RejectionReason

@dataclass
class ValidationResult:
    approved: bool
    rejection_reasons: List[RejectionReason] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    calculated_lot_size: Optional[float] = None
    risk_amount: Optional[float] = None
    details: Dict[str, float] = field(default_factory=dict)

class ValidationPipeline:
    def __init__(self, portfolio_state, lock_store, rules_engine, system_health):
        self.portfolio = portfolio_state
        self.locks = lock_store
        self.rules = rules_engine
        self.health = system_health

    def validate(self, signal: TradeSignal, current_spread: float) -> ValidationResult:
        result = ValidationResult(approved=True)

        if not self._validate_system_health():
            result.rejection_reasons.append(RejectionReason.SYSTEM_HEALTH_UNSAFE)
            
        if not self._validate_duplicate_lock(signal):
            result.rejection_reasons.append(RejectionReason.DUPLICATE_TRADE_LOCK)
            
        if not self._validate_spread(signal, current_spread):
            result.rejection_reasons.append(RejectionReason.SPREAD_TOO_HIGH)
            
        if signal.estimated_rr < self.rules.get_min_rr(signal.strategy_name):
            result.rejection_reasons.append(RejectionReason.RISK_REWARD_TOO_LOW)

        # Dynamic Sizing Check
        lot_size, risk_dollar = self._calculate_and_validate_lot(signal)
        if lot_size is None or lot_size <= 0:
            result.rejection_reasons.append(RejectionReason.INVALID_LOT_SIZE)
        else:
            result.calculated_lot_size = lot_size
            result.risk_amount = risk_dollar

        if len(result.rejection_reasons) > 0:
            result.approved = False
            signal.status = SignalStatus.VALIDATION_REJECTED
            signal.rejection_reasons = result.rejection_reasons
        
        return result

    def _validate_system_health(self) -> bool: return self.health.is_safe()
    def _validate_duplicate_lock(self, signal: TradeSignal) -> bool:
        return not self.locks.exists(signal.idempotency_key)
    def _validate_spread(self, signal, spread) -> bool: return spread <= 2.5 # Configure later
    def _calculate_and_validate_lot(self, signal) -> tuple: return (1.5, 150.0) # Placeholder Math
