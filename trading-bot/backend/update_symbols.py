from app.storage.db import DatabaseContext
from app.storage.models import BotState, User

with DatabaseContext() as db:
    # 1. Update Bot State
    s = db.query(BotState).first()
    new_symbols = ["EURUSD", "USDJPY", "AUDUSD", "USDCHF", "USDCAD", "GBPUSD", "XAUUSD"]
    if s:
        s.active_symbols = new_symbols
        print(f"BotState Active Symbols Updated: {s.active_symbols}")
    
    # 2. Update User Defaults
    u = db.query(User).first()
    if u:
        u.preferred_symbol = "XAUUSD"
        u.active_symbols = ",".join(new_symbols)
        print(f"User Preferred/Active Symbols Updated: {u.preferred_symbol}, {u.active_symbols}")
        
    db.commit()
    print("Database sync complete.")
