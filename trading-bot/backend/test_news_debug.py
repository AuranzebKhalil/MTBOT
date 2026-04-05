import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.market_data.mt5_client import MT5Client

def test_news():
    client = MT5Client()
    print("Connecting...")
    if client.connect():
        print("Connected. Fetching events...")
        try:
            events = client.get_calendar_events()
            print(f"Found {len(events)} events.")
            impact_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}
            transformed = [{
                "symbol": e["currency"],
                "name": e["event"],
                "time": e["time"].split("T")[1][:5] if "T" in e["time"] else e["time"],
                "impact": impact_map.get(e["importance"], "LOW")
            } for e in events]
            print(f"Transformed {len(transformed)} events.")
            print(transformed[:2])
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Failed to connect to MT5.")

if __name__ == "__main__":
    test_news()
