from app.storage.db import DatabaseContext
from app.storage.models import BotState

def check_logs():
    try:
        with DatabaseContext() as db:
            state = db.query(BotState).first()
            if state:
                print(f"Is Running: {state.is_running}")
                print(f"Live Logs Count: {len(state.live_logs or [])}")
                print("Last 10 Logs:")
                for log in (state.live_logs or [])[:10]:
                    print(log)
                
                health_logs = [l for l in (state.live_logs or []) if "[HEALTH]" in l]
                print(f"Health Logs Count: {len(health_logs)}")
                for l in health_logs:
                    print(f"Found HEALTH: {l}")
            else:
                print("No BotState found in database.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_logs()
