import MetaTrader5 as mt5
from datetime import datetime, timedelta

if not mt5.initialize():
    print("initialize() failed")
    quit()

# Fetch history for the last 24 hours
from_date = datetime.now() - timedelta(hours=24)
to_date = datetime.now()

deals = mt5.history_deals_get(from_date, to_date)
if deals:
    for deal in deals[-10:]: # Print last 10 deals
        d = deal._asdict()
        print(f"Ticket: {d['ticket']} | Symbol: {d['symbol']} | Type: {'IN' if d['entry']==0 else 'OUT'} | Time: {datetime.fromtimestamp(d['time'])} | Comment: {d['comment']} | Profit: {d['profit']}")
else:
    print("No deals in history.")

print("\n--- OPEN POSITIONS ---")
pos = mt5.positions_get()
if pos:
    for p in pos:
        pd = p._asdict()
        print(f"Ticket: {pd['ticket']} | Symbol: {pd['symbol']} | Comment: {pd['comment']} | Profit: {pd['profit']}")
else:
    print("No open positions.")
    
mt5.shutdown()
