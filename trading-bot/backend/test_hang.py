import MetaTrader5 as mt5
import logging

logging.basicConfig(level=logging.INFO)

def check():
    if not mt5.initialize():
        print("initialize() failed")
        return

    symbol = "SOLUSD"
    # Ensure symbol is selected
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}")
        # Try Gold instead
        symbol = "XAUUSD"
        if not mt5.symbol_select(symbol, True):
            print("Failed to select XAUUSD too")
            
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("No tick")
        return
        
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 0.01,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "sl": tick.ask - 10,
        "tp": tick.ask + 10,
        "deviation": 20,
        "magic": 202401,
        "comment": "Test",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    print("Executing check_order...")
    res = mt5.order_check(request)
    print(f"order_check returned: {res}")

if __name__ == '__main__':
    check()
