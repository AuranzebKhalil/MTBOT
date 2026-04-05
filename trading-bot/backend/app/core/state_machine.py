from app.core.datatypes import SignalStatus

class SignalStateMachine:
    _valid_transitions = {
        SignalStatus.DETECTED: [SignalStatus.SCORED, SignalStatus.INVALIDATED],
        SignalStatus.SCORED: [SignalStatus.AI_REJECTED, SignalStatus.APPROVED, SignalStatus.INVALIDATED],
        SignalStatus.APPROVED: [SignalStatus.VALIDATION_REJECTED, SignalStatus.LOCKED, SignalStatus.EXPIRED, SignalStatus.INVALIDATED],
        SignalStatus.LOCKED: [SignalStatus.ORDER_SUBMITTING, SignalStatus.INVALIDATED],
        SignalStatus.ORDER_SUBMITTING: [SignalStatus.ORDER_SUBMITTED, SignalStatus.ORDER_REJECTED],
        SignalStatus.ORDER_SUBMITTED: [SignalStatus.ORDER_FILLED, SignalStatus.ORDER_PARTIALLY_FILLED, SignalStatus.ORDER_REJECTED],
        SignalStatus.ORDER_FILLED: [SignalStatus.TRADE_OPEN],
        SignalStatus.TRADE_OPEN: [SignalStatus.TRADE_CLOSED]
    }

    @classmethod
    def can_transition(cls, current: SignalStatus, target: SignalStatus) -> bool:
        allowed = cls._valid_transitions.get(current, [])
        return target in allowed
