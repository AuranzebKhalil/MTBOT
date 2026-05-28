
import sys
import os
from datetime import datetime
import pandas as pd
import logging

# Configure logging to see runner output
logging.basicConfig(level=logging.INFO)

# Add backend to path
sys.path.append(r"c:\Users\Auranzeb Khalil\OneDrive\Desktop\APP\My project\trading-bot\backend")

from app.backtest.runner import BacktestRunner
from app.backtest.config import BacktestSettings

def test():
    print("Initializing test...")
    cfg = BacktestSettings(
        symbol="XAUUSD",
        date_from=datetime(2026, 4, 29),
        date_to=datetime(2026, 5, 9),
        initial_balance=10000.0,
        warmup_candles_m1=100 # Smaller warmup for testing
    )
    runner = BacktestRunner(cfg)
    
    def progress(p):
        print(f"Progress: {p}%")

    try:
        print("Starting backtest runner.run()...")
        result = runner.run(progress_callback=progress)
        print("Backtest finished successfully!")
    except Exception as e:
        print(f"Backtest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
