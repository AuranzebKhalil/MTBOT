import MetaTrader5 as mt5

def list_symbols():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return

    # get all symbols
    symbols = mt5.symbols_get()
    print(f"Total symbols: {len(symbols)}")
    
    keywords = ["#", "BTC", "ETH", "SOL", "GOLD"]
    
    print("\nSymbols with # or Crypto keywords:")
    for s in symbols:
        if "#" in s.name or any(key in s.name.upper() for key in keywords):
            print(f"- {s.name} (Visible: {s.visible})")
            
    mt5.shutdown()

if __name__ == "__main__":
    list_symbols()
