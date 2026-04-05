from app.storage.db import SessionLocal
from app.storage.models import BotState

db = SessionLocal()
state = db.query(BotState).first()
if state:
    state.live_charts = {}
    db.commit()
    print("Cleared live_charts to reset formatting")
db.close()
