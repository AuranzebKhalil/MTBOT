import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_layer.mt5_connector import MT5Connector
from strategy import SMCStrategy
from risk_engine.risk_manager import RiskManager

class SnapshotBacktester:
    """
    Rapidly verifies the 15-Family Strategy Matrix on historical data.
    Optimized to pre-calculate indicators for the entire dataset.
    """
    def __init__(self, symbol="GOLD", timeframe="M5", lookback=5000):
        self.symbol = symbol
        self.timeframe = timeframe
        self.lookback = lookback
        self.connector = MT5Connector()
        self.strategy = SMCStrategy(symbol=symbol)
        self.risk_manager = RiskManager()
        
    def _is_in_killzone(self, timestamp):
        """Simulated Killzone check for backtest (UTC)"""
        hour = timestamp.hour
        is_london = 8 <= hour <= 11
        is_ny = 13 <= hour <= 16
        return is_london or is_ny

    def run(self):
        print(f"STARTING ULTRA-PRECISION BACKTEST: {self.symbol} ({self.timeframe}) | Lookback: {self.lookback}")
        
        if not self.connector.connect():
            print("Error: Could not connect to MT5.")
            return

        data = self.connector.get_market_data(self.symbol, self.timeframe, self.lookback)
        if data is None or data.empty:
            print("Error: No data received.")
            return

        print(f"Pre-calculating indicators for {len(data)} bars...")
        data = self.strategy._preprocess(data)
        
        # Calculate Bias (EMA50) on the whole set
        data['ema50'] = data['close'].rolling(50).mean()
        data['bias'] = 0
        data.loc[data['close'] > data['ema50'], 'bias'] = 1
        data.loc[data['close'] < data['ema50'], 'bias'] = -1

        print(f"Processing {len(data)} bars for 80% precision...")
        trades = []
        balance = 10000
        
        for i in range(100, len(data) - 50):
            bias = data['bias'].iloc[i]
            if bias == 0: continue
            
            row = data.iloc[i]
            prev = data.iloc[i-1]
            is_killzone = self._is_in_killzone(row['time'])
            
            signal = "WAIT"
            name = ""
            
            # --- ULTRA-PRECISION 15-FAMILY ENGINE ---

            # 1. VAS (Volume Absorption) -> Boosted threshold
            v_avg = data['tick_volume'].iloc[i-20:i].mean()
            if row['tick_volume'] > v_avg * 2.0 and abs(row['close'] - row['open']) < (row['high'] - row['low']) * 0.3:
                if is_killzone:
                    signal = "BUY" if bias == 1 else "SELL"
                    name = "1. VAS (Ultra-Absorption)"

            # 2 & 7. CRT / LTR (Manipulation Traps) -> Session + Zone Nesting
            elif abs(prev['high'] - prev['low']) > (data['high'] - data['low']).iloc[i-20:i].mean() * 2.2:
                if is_killzone:
                    if bias == 1 and row['close'] > prev['high'] and row['demand_zone']:
                        signal = "BUY"; name = "2. CRT (Nested-Trap)"
                    elif bias == -1 and row['close'] < prev['low'] and row['supply_zone']:
                        signal = "SELL"; name = "7. LTR (Nested-Trap)"

            # 3. LSR (Liquidity Sweep Reversal) -> Session + Zone
            elif row['sweep'] != 0 and bias == row['sweep'] and is_killzone:
                if (bias == 1 and row['demand_zone']) or (bias == -1 and row['supply_zone']):
                    signal = "BUY" if bias == 1 else "SELL"
                    name = "3. LSR (Nested Sweep)"

            # 4 & 8. SBC / SSC (Continuation) -> Room Filter (mocked by structural strength)
            elif row['bos'] and is_killzone:
                if row['order_block'] != 0 and ((bias == 1 and row['demand_zone']) or (bias == -1 and row['supply_zone'])):
                    signal = "BUY" if bias == 1 else "SELL"
                    name = "8. SSC (Nested Structure)"
                elif row['order_block'] != 0:
                    signal = "BUY" if bias == 1 else "SELL"
                    name = "4. SBC (OB-Continuation)"

            # 9. PDF (Premium/Discount FVG) -> Heavy Precision
            elif ((row['fvg_bullish'] and bias == 1) or (row['fvg_bearish'] and bias == -1)) and is_killzone:
                if (bias == 1 and row['demand_zone']) or (bias == -1 and row['supply_zone']):
                    signal = "BUY" if bias == 1 else "SELL"
                    name = "9. PDF (Sovereign Zone)"

            # 10. OBM (Order Block Momentum)
            elif row['order_block'] != 0 and bias == row['order_block'] and is_killzone:
                signal = "BUY" if bias == 1 else "SELL"
                name = "10. OBM (Institutional OB)"

            # 11. SND (Supply & Demand Mitigation)
            elif (row['demand_zone'] and bias == 1) or (row['supply_zone'] and bias == -1):
                if is_killzone:
                    signal = "BUY" if bias == 1 else "SELL"
                    name = "11. SND (Primary Mitigation)"

            # 14 & 15. VSA Family -> Triple Lock (Session + Zone + Vol)
            elif row['vsa'] == "TWO_BAR_REVERSAL" and row['tick_volume'] > v_avg * 2.0:
                if is_killzone and ((bias == 1 and row['demand_zone']) or (bias == -1 and row['supply_zone'])):
                    signal = "BUY" if row['vsa_type'] == 1 else "SELL"
                    name = "14. 2BR (Ultra-Reversal)"
            elif row['vsa'] == "NO_SUPPLY" and bias == 1 and row['tick_volume'] < v_avg * 0.7:
                if is_killzone and row['demand_zone']:
                    signal = "BUY"; name = "15. NSND (No Supply)"
            elif row['vsa'] == "NO_DEMAND" and bias == -1 and row['tick_volume'] < v_avg * 0.7:
                if is_killzone and row['supply_zone']:
                    signal = "SELL"; name = "15. NSND (No Demand)"

            if signal != "WAIT":
                # CONFIRMATION WICK FILTER (Institutional Rejection)
                is_rejection = False
                if signal == "BUY":
                    # Lower wick must be > 30% of candle
                    if (min(row['open'], row['close']) - row['low']) > (row['high'] - row['low']) * 0.3:
                        is_rejection = True
                else:
                    # Upper wick must be > 30% of candle
                    if (row['high'] - max(row['open'], row['close'])) > (row['high'] - row['low']) * 0.3:
                        is_rejection = True
                
                if not is_rejection and "NSND" not in name: # NSND doesn't need wicks
                     signal = "WAIT"

            if signal != "WAIT":
                # Outcome simulation
                price = row['close']
                direction = 1 if signal == "BUY" else -1
                
                # Dynamic ATR-based exits
                atr = (data['high'] - data['low']).iloc[i-14:i].mean()
                sl = price - (atr * 2.0) if direction == 1 else price + (atr * 2.0) 
                tp = price + (atr * 3.0) if direction == 1 else price - (atr * 3.0) # 1:1.5 RR for higher hit rate
                
                future = data.iloc[i+1 : i+100] 
                outcome = None
                for _, f_bar in future.iterrows():
                    if direction == 1:
                        if f_bar['high'] >= tp: outcome = "WIN"; break
                        if f_bar['low'] <= sl: outcome = "LOSS"; break
                    else:
                        if f_bar['low'] <= tp: outcome = "WIN"; break
                        if f_bar['high'] >= sl: outcome = "LOSS"; break
                
                if outcome:
                    profit = balance * 0.01 if outcome == "WIN" else -balance * 0.01
                    balance += profit
                    trades.append({"strategy": name, "outcome": outcome, "profit": profit})

        self.print_report(trades, balance)

    def print_report(self, trades, final_balance):
        import json
        if not trades:
            print("No trades triggered.")
            return
            
        df_trades = pd.DataFrame(trades)
        wins = len(df_trades[df_trades['outcome'] == 'WIN'])
        loss = len(df_trades[df_trades['outcome'] == 'LOSS'])
        
        report = {
            "total_trades": len(df_trades),
            "win_rate": (wins/len(df_trades))*100,
            "net_profit": final_balance - 10000,
            "strategy_breakdown": df_trades.groupby('strategy')['outcome'].value_counts().unstack().fillna(0).to_dict()
        }
        
        with open("backtest_report.json", "w") as f:
            json.dump(report, f, indent=4)

        print("\n" + "="*50)
        print("PERFORMANCE REPORT: 15-FAMILY MATRIX")
        print("="*50)
        print(f"Total Trades: {len(df_trades)}")
        print(f"Win Rate:     {report['win_rate']:.2f}%")
        print(f"Net Profit:   ${report['net_profit']:.2f}")
        print("-" * 50)
        print("Results saved to backtest_report.json")
        print("="*50)

if __name__ == "__main__":
    tester = SnapshotBacktester(symbol="GOLD", timeframe="M5", lookback=10000)
    tester.run()
