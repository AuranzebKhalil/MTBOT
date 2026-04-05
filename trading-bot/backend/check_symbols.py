import MetaTrader5 as mt5
import sys

def check_symbols():
    if not mt5.initialize():
        print(f"initialize() failed, error code = {mt5.last_error()}")
        quit()

    symbols = mt5.symbols_get()
    print(f"Total symbols found: {len(symbols)}")
    
    gold_symbols = [s.name for s in symbols if "XAU" in s.name.upper() or "GOLD" in s.name.upper()]
    
    if gold_symbols:
        print("\nPossible Gold symbols on your broker:")
        for name in gold_symbols:
            selected = mt5.symbol_select(name, True)
            print(f"- {name} (Selected: {selected})")
    else:
        print("\nNo Gold-related symbols found. Please check your Market Watch.")
        print("Common names: XAUUSD, GOLD, XAUUSD.m, XAUUSD+, XAUUSD.pro")

    mt5.shutdown()

if __name__ == "__main__":
    check_symbols()
