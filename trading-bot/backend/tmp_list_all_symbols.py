import MetaTrader5 as mt5

if not mt5.initialize():
    print("Failed to initialize MT5")
    quit()

symbols = mt5.symbols_get()
if symbols:
    print(f"Total symbols found: {len(symbols)}")
    # Print symbols that look like Gold or XAU
    gold_like = [s.name for s in symbols if "XAU" in s.name.upper() or "GOLD" in s.name.upper()]
    print(f"Gold-like symbols: {gold_like}")
    
    # Print first 20 symbols just to see names
    print(f"First 20 symbols: {[s.name for s in symbols[:20]]}")
else:
    print("No symbols found. This usually means you are not logged in or the terminal has not synced.")

mt5.shutdown()
