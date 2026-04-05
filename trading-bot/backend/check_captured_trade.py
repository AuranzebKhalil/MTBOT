from app.storage.db import DatabaseContext
from app.storage.models import Trade

def check():
    with DatabaseContext() as db:
        t = db.query(Trade).order_by(Trade.time.desc()).first()
        if t:
            print(f"Ticket: {t.ticket_id}")
            print(f"Status: {t.status}")
            print(f"Symbol: {t.symbol}")
            print(f"Final Exit Reason: {t.final_exit_reason}")
            print(f"Entry Price: {t.entry_price}")
            print(f"SL: {t.sl}")
            print(f"TP: {t.tp}")
            print(f"TP1: {t.tp1}")
            print(f"TP2: {t.tp2}")
            print(f"Bid at Entry: {t.bid_at_entry}")
            print(f"Ask at Entry: {t.ask_at_entry}")
            print(f"Spread at Entry: {t.spread_at_entry}")
            print(f"Stage 1 Partial: {t.stage1_partial_done}")
            print(f"Stage 1 SL Move: {t.stage1_sl_done}")
            print(f"Stage 2 Partial: {t.stage2_partial_done}")
            print(f"Stage 2 SL Move: {t.stage2_sl_done}")
            print(f"AI Score: {t.ai_score}")
        else:
            print("No trades found.")

if __name__ == "__main__":
    check()
