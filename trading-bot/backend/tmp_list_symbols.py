import MetaTrader5 as mt5

def list_symbols():
    if not mt5.initialize():
        print("Init Failed")
        return
    
    symbols = mt5.symbols_get()
    if symbols:
        # Print first 20 just to see samples of naming convention
        print(f"Total symbols found: {len(symbols)}")
        print("Sample symbols: " + ", ".join([s.name for s in symbols[:20]]))
        
        # Look specifically for Gold/XAU
        matches = [s.name for s in symbols if "XAU" in s.name or "GOLD" in s.name]
        print(f"XAU/GOLD matches: {matches}")
        
    mt5.shutdown()

if __name__ == "__main__":
    list_symbols()
