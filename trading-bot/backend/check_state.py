from app.storage.db import DatabaseContext
from app.storage.models import BotState
with DatabaseContext() as db:
    s = db.query(BotState).first()
    if s:
        print(f"Status: {s.status_message} | Action: {s.current_action} | Last Loop: {s.last_loop_at}")
    else:
        print("No BotState found")
