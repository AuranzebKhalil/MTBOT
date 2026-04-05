import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def check_mt5_status():
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    acc = mt5.account_info()
    if acc:
        print("--- Account Info ---")
        print(f"Login: {acc.login}")
        print(f"Balance: {acc.balance}")
        print(f"Equity: {acc.equity}")
        print(f"Server: {acc.server}")
    else:
        print("Could not get account info")
    
    positions = mt5.positions_get()
    print("\n--- Open Positions ---")
    if positions:
        df = pd.DataFrame([p._asdict() for p in positions])
        print(df[['ticket', 'symbol', 'type', 'volume', 'price_open', 'profit', 'comment']])
    else:
        print("No open positions")
        
    # Get last 5 deals
    print("\n--- Last 5 Closed Trades (Deals) ---")
    deals = mt5.history_deals_get(datetime(2020,1,1), datetime.now())
    if deals:
        df_deals = pd.DataFrame([d._asdict() for d in deals])
        print(df_deals.tail(5)[['ticket', 'symbol', 'type', 'volume', 'price', 'profit', 'comment']])
    else:
        print("No history found")

    mt5.shutdown()

if __name__ == "__main__":
    check_mt5_status()
