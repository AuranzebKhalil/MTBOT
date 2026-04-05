import time
import datetime
import pandas as pd
import sys
import os
import MetaTrader5 as mt5
from data_layer.mt5_connector import MT5Connector
from strategy import SMCStrategy
from indicators import SMCIndicators

def run_backtest():
    connector = MT5Connector()
    if not connector.connect():
        print("Failed to connect to MT5")
        return

    # 1. Define Time Window: Today at 13:00 (1 PM)
    now_local = datetime.datetime.now()
    start_time = now_local.replace(hour=13, minute=0, second=0, microsecond=0)
    
    # If now is before 13:00, go back one day
    if now_local < start_time:
        start_time -= datetime.timedelta(days=1)
        
    end_time = datetime.datetime.now()

    print(f"--- Quant Backtest Report ---")
    print(f"Window: {start_time} to {end_time}")
    print(f"------------------------------")

    # 2. Pairs to Test
    test_symbols = ["GOLD", "XAUUSD", "BTCUSD", "ETHUSD", "GBPUSD", "EURUSD"]
    
    results = {}
    strategy = SMCStrategy()
    
    for symbol in test_symbols:
        # Check if symbol exists using the mt5 package directly
        if not mt5.symbol_info(symbol):
            continue
            
        print(f"Analyzing {symbol}...")
        
        # Fetch data up to end_time
        data_m1 = connector.get_market_data(symbol, "M1", 5000) 
        data_m5 = connector.get_market_data(symbol, "M5", 2000)
        data_m15 = connector.get_market_data(symbol, "M15", 1000)
        
        if data_m1 is None or data_m5 is None or data_m15 is None:
            continue
            
        if data_m1.empty or data_m5.empty or data_m15.empty:
            continue

        # Convert times to comparable datetime objects
        # get_market_data already converts them, but let's be sure
        data_m1['time'] = pd.to_datetime(data_m1['time'])
        data_m5['time'] = pd.to_datetime(data_m5['time'])
        data_m15['time'] = pd.to_datetime(data_m15['time'])
        
        # Filter M1 to start from 13:00
        test_bars = data_m1[data_m1['time'] >= start_time].copy()
        
        if test_bars.empty:
            print(f"  ✗ No data found starting from {start_time}")
            continue

        trades = []
        last_trade_time = datetime.datetime.min
        cooldown = datetime.timedelta(minutes=30) 

        # Simulation Loop (Optimized for speed: Sample every 5 minutes)
        total_steps = len(test_bars)
        for i in range(0, total_steps, 5): 
            sim_time = test_bars.iloc[i]['time']
            
            # Slice historical data up to this exact M1 candle
            m1_history = data_m1[data_m1['time'] <= sim_time].tail(1000)
            m5_history = data_m5[data_m5['time'] <= sim_time].tail(500)
            m15_history = data_m15[data_m15['time'] <= sim_time].tail(500)
            
            if len(m1_history) < 100 or len(m5_history) < 50 or len(m15_history) < 50:
                continue

            # Run Analysis
            signal, price, name, details = strategy.analyze(m1_history, m5_history, m15_history)
            
            if signal != "WAIT" and (sim_time - last_trade_time) > cooldown:
                trades.append({
                    "time": sim_time.strftime("%H:%M"),
                    "type": signal,
                    "price": price,
                    "strategy": name,
                    "reason": details.get("reason", "N/A")
                })
                last_trade_time = sim_time
                
        results[symbol] = trades
        print(f"  ↳ Found {len(trades)} potential trades.")

    # 3. Generate Report
    report_path = "backtest_report.md"
    try:
        with open(report_path, "w") as f:
            f.write(f"# Quant Backtest Report\n\n")
            f.write(f"**Period:** {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Engine:** Alpha Flux v4.2 Pro\n\n")
            
            f.write("## Summary\n\n")
            f.write("| Symbol | Total Trades | Top Strategy |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            for sym, t_list in results.items():
                top_strat = "N/A"
                if t_list:
                    strats = [t['strategy'] for t in t_list]
                    top_strat = max(set(strats), key=strats.count)
                f.write(f"| {sym} | {len(t_list)} | {top_strat} |\n")
            
            f.write("\n## Detailed Execution Logs\n\n")
            for sym, t_list in results.items():
                if not t_list:
                    continue
                f.write(f"### {sym}\n\n")
                f.write("| Time | Signal | Price | Strategy | Core Logic |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                for t in t_list:
                    f.write(f"| {t['time']} | {t['type']} | {t['price']:.5f} | {t['strategy']} | {t['reason']} |\n")
                f.write("\n")
                
        print(f"--- Backtest Complete. Report saved to {report_path} ---")
    except Exception as e:
        print(f"Failed to write report: {e}")

    connector.disconnect()

if __name__ == "__main__":
    run_backtest()
