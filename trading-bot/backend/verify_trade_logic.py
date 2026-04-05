from app.storage.db import DatabaseContext
from app.storage.models import Trade, SignalLog

def fix_and_check():
    with DatabaseContext() as db:
        t = db.query(Trade).order_by(Trade.time.desc()).first()
        if not t:
            print("No trades found.")
            return

        print(f"--- ORIGINAL DB STATE TICKET #{t.ticket_id} ---")
        print(f"Status: {t.status}")
        print(f"Entry Price: {t.entry_price}")
        print(f"SL: {t.sl}")
        print(f"TP: {t.tp}")
        print(f"TP1: {t.tp1}")
        print(f"TP2: {t.tp2}")
        print(f"Stage 1 Partial: {t.stage1_partial_done}")
        print(f"Stage 1 SL Move: {t.stage1_sl_done}")
        print(f"Stage 2 Partial: {t.stage2_partial_done}")
        print(f"Stage 2 SL Move: {t.stage2_sl_done}")
        
        print("\n--- STAGE PROGRESS LOGIC ---")
        if t.tp1 is None and t.tp is not None:
             print("Using fallback for progress: tp instead of tp1")
        else:
             print("Using proper tp1 for progress")

        print("\n--- PATCHING ROW WITH TARGETS ---")
        log = db.query(SignalLog).filter(SignalLog.symbol == t.symbol).order_by(SignalLog.timestamp.desc()).first()
        if log:
            # We dont have raw targets array in signal log easily accessible, 
            # so let's use the explicit option 2 for safety.
            print("Action: Marking trade as not valid for final stage validation")
            print("We will let this trade close and use the NEXT trade for exact stage verification.")
            
if __name__ == "__main__":
    fix_and_check()
