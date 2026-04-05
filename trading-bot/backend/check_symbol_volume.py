import MetaTrader5 as mt5
import sys

def check_symbol(symbol):
    if not mt5.initialize():
        print("Init failed")
        return
        
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"Symbol {symbol} not found")
        return
        
    print(f"Symbol: {symbol}")
    print(f"  Volume Min: {info.volume_min}")
    print(f"  Volume Max: {info.volume_max}")
    print(f"  Volume Step: {info.volume_step}")
    print(f"  Volume Limit: {info.volume_limit}")

    mt5.shutdown()

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "SOLUSD"
    check_symbol(sym)
