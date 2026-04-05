import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def debug_symbol(symbol):
    if not mt5.initialize():
        print("initialize() failed")
        return

    print(f"--- Diagnosing {symbol} ---")
    
    # Check if symbol exists
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"Symbol {symbol} NOT FOUND in broker database.")
        # Try to find a similar one
        all_syms = mt5.symbols_get()
        print(f"Total symbols available: {len(all_syms)}")
        matches = [s.name for s in all_syms if symbol.split('USD')[0] in s.name]
        print(f"Similar symbols found: {matches}")
        return

    print(f"Symbol {symbol} found.")
    print(f"Visible: {info.visible}")
    print(f"Trade Mode: {info.trade_mode}")
    print(f"Path: {info.path}")
    
    if not info.visible:
        print(f"Selecting symbol {symbol}...")
        mt5.symbol_select(symbol, True)
        
    print(f"Force ticking {symbol}...")
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"Last Tick: Bid={tick.bid}, Ask={tick.ask}")
    else:
        print(f"Could not get tick for {symbol}. Error: {mt5.last_error()}")

    for tf_name in ["M1", "M5", "M15"]:
        print(f"\nAttempting to fetch {tf_name} data (500 bars)...")
        tf = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15}[tf_name]
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, 500)
        if rates is not None and len(rates) > 0:
            print(f"Success! Received {len(rates)} bars for {tf_name}.")
        else:
            print(f"FAILED to fetch {tf_name} rates. Error code: {mt5.last_error()}")

    mt5.shutdown()

if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else "ETHUSD"
    debug_symbol(sym)
