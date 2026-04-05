from app.storage.db import DatabaseContext
from app.storage.models import BotState
import json

with DatabaseContext() as db:
    state = db.query(BotState).first()
    if state:
        print("Bot Running:", state.is_running)
        print("Active Symbols:", state.active_symbols)
        for sym, data in state.live_charts.items():
            if isinstance(data, dict):
                chart = data.get("chart", [])
                overlays = data.get("overlays", {})
                print(f"Symbol: {sym}, Chart Bars: {len(chart)}, Overlays: {list(overlays.keys())}")
                if chart:
                    print(f"  First bar time: {chart[0]['time']}")
            else:
                print(f"Symbol: {sym}, Data type: {type(data)} (Old format)")
                if data:
                    print(f"  First item time: {data[0].get('time')}")
    else:
        print("No BotState found in database.")
