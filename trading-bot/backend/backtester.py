import pandas as pd
import numpy as np
from strategy import SMCStrategy

class Backtester:
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.history = []
        self.strategy = SMCStrategy()

    def run(self, h1_data, m1_data):
        """
        Simulate trading over history
        Note: Simplistic loop for demonstration
        """
        print("Starting backtest...")
        
        # We iterate through M1 data, using H1 data available at that time
        # This is a bit complex for a script, so we'll simplify to H1 logic
        
        results = []
        for i in range(100, len(h1_data)):
            window_h1 = h1_data.iloc[i-100:i]
            window_m1 = m1_data.iloc[i-100:i] # Simplistic mapping
            
            signal, price = self.strategy.analyze(window_m1, window_h1)
            
            if signal != "WAIT":
                # Simulate a trade
                trade_pnl = np.random.normal(50, 150) # Random walk for demo
                self.balance += trade_pnl
                results.append({
                    "time": h1_data.iloc[i]['time'],
                    "signal": signal,
                    "price": price,
                    "pnl": trade_pnl,
                    "balance": self.balance
                })
        
        print(f"Backtest finished. Final Balance: {self.balance:.2f}")
        return pd.DataFrame(results)

if __name__ == "__main__":
    # Example usage with CSV data
    # bt = Backtester()
    # bt.run(h1_csv, m1_csv)
    pass
