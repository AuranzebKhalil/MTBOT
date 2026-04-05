from app.storage.db import SessionLocal
from app.storage.models import BotState, Trade
import json

db = SessionLocal()
state = db.query(BotState).first()
if state:
    print("--- BotState ---")
    print(f"Is Running: {state.is_running}")
    print(f"Active Symbols: {state.active_symbols}")
    print(f"Current Metrics: {json.dumps(state.current_metrics, indent=2)}")
    print(f"Live Logs Count: {len(state.live_logs) if state.live_logs else 0}")
    
    if state.live_charts:
        print("\n--- Live Charts ---")
        for sym, data in state.live_charts.items():
            if isinstance(data, dict):
                chart_len = len(data.get("chart", []))
                print(f"{sym}: {chart_len} bars")
                if chart_len > 0:
                    print(f"  Latest bar: {data['chart'][-1]}")
            else:
                print(f"{sym}: (old format) {len(data)} bars")
    else:
        print("\nNo live charts in DB")
else:
    print("No BotState record found")

open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
print(f"\n--- Open Trades in DB ({len(open_trades)}) ---")
for t in open_trades:
    print(f"ID: {t.id}, Ticket: {t.ticket_id}, Symbol: {t.symbol}, PnL: {t.profit}")

db.close()
