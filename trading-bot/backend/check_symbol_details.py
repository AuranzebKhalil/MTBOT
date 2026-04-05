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
    print(f"  Digits: {info.digits}")
    print(f"  Trade Mode: {info.trade_mode}")
    print(f"  Execution Mode: {info.trade_exemode}")
    print(f"  Filling Mode Filter: {info.filling_mode}")
    print(f"  Stops Level: {info.trade_stops_level}")
    
    # Try an order check with different filling modes
    tick = mt5.symbol_info_tick(symbol)
    
    filling_modes = [
        ("IOC", mt5.ORDER_FILLING_IOC),
        ("FOK", mt5.ORDER_FILLING_FOK),
        ("RETURN", mt5.ORDER_FILLING_RETURN)
    ]
    
    for name, mode in filling_modes:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": 0.01,
            "type": mt5.ORDER_TYPE_BUY,
            "price": tick.ask,
            "deviation": 20,
            "magic": 202401,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mode,
        }
        res = mt5.order_check(request)
        print(f"  Order Check ({name}): {res.comment if res else 'None'} (Retcode: {res.retcode if res else 'N/A'})")

    mt5.shutdown()

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "SOLUSD"
    check_symbol(sym)
