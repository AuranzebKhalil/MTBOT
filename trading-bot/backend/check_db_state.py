from app.storage.db import SessionLocal
from app.storage.models import BotState

db = SessionLocal()
state = db.query(BotState).first()
if state:
    charts = state.live_charts
    if charts:
        for symbol, chart_data in charts.items():
            print(f"{symbol} chart length:", len(chart_data))
            if len(chart_data) > 0:
                print(f"First candle for {symbol}:", chart_data[0])
    
    print("live_logs length:", len(state.live_logs) if state.live_logs else 0)
    print("current_metrics:", state.current_metrics)
else:
    print("No BotState found")
db.close()
