from enum import Enum
from dataclasses import dataclass
from typing import List

class ReconciliationIssueType(str, Enum):
    BROKER_POSITION_MISSING_LOCALLY = "BROKER_POSITION_MISSING_LOCALLY" # Orphan
    LOCAL_POSITION_MISSING_AT_BROKER = "LOCAL_POSITION_MISSING_AT_BROKER" # Ghost
    MISMATCHED_LOT_SIZE = "MISMATCHED_LOT_SIZE" # Partial close occurred
    MISMATCHED_SL = "MISMATCHED_SL" # Slippage or manual intervention
    MISMATCHED_TP = "MISMATCHED_TP"
    MISMATCHED_DIRECTION = "MISMATCHED_DIRECTION" # Critical hedge failure
    STALE_LOCAL_STATUS = "STALE_LOCAL_STATUS"

@dataclass
class ReconciliationItem:
    issue_type: ReconciliationIssueType
    ticket: int
    symbol: str
    severity: str # "CRITICAL", "WARNING", "INFO"
    details: str
    recommended_action: str

class ReconciliationEngine:
    def reconcile(self, local_open_trades: dict, broker_positions: dict) -> List[ReconciliationItem]:
        issues = []
        
        for ticket, local_trade in local_open_trades.items():
            if ticket not in broker_positions:
                issues.append(ReconciliationItem(
                    issue_type=ReconciliationIssueType.LOCAL_POSITION_MISSING_AT_BROKER,
                    ticket=ticket, symbol=local_trade.symbol, severity="WARNING",
                    details="Trade exists locally as OPEN but missing on broker.",
                    recommended_action="MARK_LOCAL_CLOSED_SYNC_HISTORY"
                ))
            else:
                broker_pos = broker_positions[ticket]
                if abs(local_trade.volume - broker_pos.volume) > 0.001:
                    issues.append(ReconciliationItem(
                        issue_type=ReconciliationIssueType.MISMATCHED_LOT_SIZE,
                        ticket=ticket, symbol=local_trade.symbol, severity="INFO",
                        details=f"Local Vol: {local_trade.volume}, Broker: {broker_pos.volume}",
                        recommended_action="UPDATE_LOCAL_VOLUME"
                    ))
                # Similar checks for SL / TP mismatches...
                
        for ticket, broker_pos in broker_positions.items():
            if ticket not in local_open_trades:
                issues.append(ReconciliationItem(
                    issue_type=ReconciliationIssueType.BROKER_POSITION_MISSING_LOCALLY,
                    ticket=ticket, symbol=broker_pos.symbol, severity="CRITICAL",
                    details="Open position on broker not tracked in local DB.",
                    recommended_action="IMPORT_AS_EXTERNAL_TRADE"
                ))
                
        return issues
