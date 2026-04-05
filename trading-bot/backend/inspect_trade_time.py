import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    quit()

deals = mt5.history_deals_get(position=571431449)
if deals:
    for deal in deals:
        d = deal._asdict()
        print(f"Ticket: {d['ticket']} | Time: {datetime.fromtimestamp(d['time'])} | Comment: {d['comment']} | Symbol: {d['symbol']}")
else:
    print("No deals found for this position.")

mt5.shutdown()
