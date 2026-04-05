from app.storage.db import DatabaseContext
from app.storage.models import SignalLog, Trade
from datetime import datetime, timezone, timedelta

# Define "Today" (UTC)
today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

with DatabaseContext() as db:
    print(f"--- Analysis for {today_start.date()} ---")
    
    # 1. Check total detected signals
    total_logs = db.query(SignalLog).filter(SignalLog.timestamp >= today_start).count()
    print(f"Total signals processed today: {total_logs}")
    
    # 2. Breakdown by status
    status_counts = {}
    logs = db.query(SignalLog).filter(SignalLog.timestamp >= today_start).all()
    for log in logs:
        status_counts[log.status] = status_counts.get(log.status, 0) + 1
        
    print("\nStatus Breakdown:")
    for status, count in status_counts.items():
        print(f"- {status}: {count}")
        
    # 3. List common rejection reasons
    print("\nDetailed Rejection Reasons (Top 15):")
    reasons = db.query(SignalLog.rejection_reason, SignalLog.status).filter(SignalLog.timestamp >= today_start, SignalLog.status != "APPROVED").limit(15).all()
    for res, stat in reasons:
        print(f"- [{stat}] {res}")

    # 4. Check Risk Events
    from app.storage.models import RiskEvent, ExecutionLog
    risk_events = db.query(RiskEvent).filter(RiskEvent.timestamp >= today_start).all()
    print(f"\nRisk Events today: {len(risk_events)}")
    for e in risk_events[:5]:
        print(f"- {e.event_type}: {e.details}")

    # 4b. Check Execution Logs (Failed Trades)
    exec_logs = db.query(ExecutionLog).filter(ExecutionLog.timestamp >= today_start).all()
    print(f"\nExecution Logs today: {len(exec_logs)}")
    for ex in exec_logs[:10]:
        print(f"- [{ex.symbol}] Retcode: {ex.retcode}, Msg: {ex.error_message}")

    # 5. Check if any actual trades were opened
    trades_today = db.query(Trade).filter(Trade.time >= today_start).count()
    print(f"\nActual trades opened today: {trades_today}")
