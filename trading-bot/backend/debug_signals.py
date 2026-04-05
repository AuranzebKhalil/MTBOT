from app.storage.db import DatabaseContext
from app.storage.models import SignalLog
from datetime import datetime, timezone, timedelta

t = datetime.now(timezone.utc) - timedelta(minutes=60)
with DatabaseContext() as db:
    logs = db.query(SignalLog).filter(SignalLog.timestamp >= t).all()
    print(f"Newly processed signals in last 60 mins: {len(logs)}")
    for l in logs[-5:]:
        print(f"[{l.symbol}] {l.status}: {l.rejection_reason}")
