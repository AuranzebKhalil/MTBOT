
import pandas as pd
import MetaTrader5 as mt5
from data_layer.mt5_connector import MT5Connector
from strategy import SMCStrategy
from risk_management import RiskManager

def run_debug():
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    symbol = "GOLD"
    
    print(f"--- FETCHING DATA FOR {symbol} ---")
    data_m1 = connector.get_market_data(symbol, "M1", 500)
    data_m5 = connector.get_market_data(symbol, "M5", 500)
    data_m15 = connector.get_market_data(symbol, "M15", 500)

    if data_m1 is None or data_m5 is None or data_m15 is None:
        print("Failed to fetch data")
        return

    strategy = SMCStrategy()
    risk_manager = RiskManager()

    print(f"--- ANALYZING {symbol} ---")
    signal, price, str_name, details = strategy.analyze(data_m1, data_m5, data_m15)
    
    print(f"Signal: {signal}")
    print(f"Price: {price}")
    print(f"Strategy: {str_name}")
    print(f"Details: {details}")

    if signal != "WAIT":
        print(f"--- CHECKING RISK ---")
        open_positions = connector.get_open_positions()
        history = connector.get_history_deals(days=1)
        acc_info = connector.get_account_info()
        
        is_acceptable, reason = risk_manager.is_risk_acceptable(
            open_positions, history, acc_info.get('balance', 0), symbol=symbol
        )
        
        print(f"Is Acceptable: {is_acceptable}")
        print(f"Reason: {reason}")
        
        if is_acceptable:
            direction = 1 if signal == "BUY" else -1
            sl, tp = risk_manager.calculate_sl_tp(price, direction)
            
            if "stop_loss" in details and "take_profit" in details:
                sl = details["stop_loss"]
                tp = details["take_profit"]
            
            symbol_info = mt5.symbol_info(symbol)
            lot_size = risk_manager.calculate_lot_size(acc_info.get('balance', 0), price, sl, symbol_info)
            
            print(f"Proposed Order: {signal} {lot_size} lots, SL: {sl}, TP: {tp}")

    connector.disconnect()

if __name__ == "__main__":
    run_debug()
