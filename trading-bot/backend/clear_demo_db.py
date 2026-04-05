from app.storage.db import DatabaseContext
from app.storage.models import Trade, TradeEvent, SignalLog, ExecutionLog
with DatabaseContext() as db:
    db.query(TradeEvent).delete()
    db.query(Trade).delete()
    db.query(SignalLog).delete()
    db.query(ExecutionLog).delete()
    db.commit()
print("DB Cleared")
