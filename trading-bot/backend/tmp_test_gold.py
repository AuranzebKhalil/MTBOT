import MetaTrader5 as mt5

if not mt5.initialize():
    print("Failed to initialize MT5")
    quit()

symbol = "GOLD"
res = mt5.symbol_select(symbol, True)
if res:
    print(f"Successfully selected {symbol}")
    info = mt5.symbol_info(symbol)
    if info:
        print(f"Symbol Info: {info.name}, Bid: {info.bid}, Ask: {info.ask}")
    else:
        print(f"Could not get info for {symbol}")
else:
    print(f"Failed to select {symbol}. Error: {mt5.last_error()}")

mt5.shutdown()
