import MetaTrader5 as mt5

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

pos = mt5.positions_get(ticket=571431449)
if pos:
    p = pos[0]._asdict()
    print(f"Ticket: {p['ticket']}")
    print(f"Comment: {p['comment']}")
    print(f"Symbol: {p['symbol']}")
    print(f"Type: {'BUY' if p['type'] == 0 else 'SELL'}")
    print(f"Volume: {p['volume']}")
    print(f"Price Open: {p['price_open']}")
    print(f"Profit: {p['profit']}")
else:
    print("Position not found or already closed.")

mt5.shutdown()
