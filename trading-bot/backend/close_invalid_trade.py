from app.storage.db import DatabaseContext
from app.market_data.mt5_client import MT5Client
from app.storage.models import Trade

def close_invalid_open_trade():
    mt5 = MT5Client()
    mt5.connect()
    with DatabaseContext() as db:
        t = db.query(Trade).filter(Trade.status == "OPEN").first()
        if t:
            print(f"Closing trade {t.ticket_id} since TP1 is NULL.")
            mt5.close_position(int(t.ticket_id))
            t.status = "CLOSED"
            t.final_exit_reason = "MANUAL_INVALID_TEST_TRADE"
            db.commit()
            print("Trade closed in DB and MT5.")
        else:
            print("No open trades.")
    mt5.disconnect()

if __name__ == "__main__":
    close_invalid_open_trade()
