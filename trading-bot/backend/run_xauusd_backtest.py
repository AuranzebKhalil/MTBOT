import os
import sys
from datetime import datetime, timezone
import logging

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.backtest.runner import BacktestRunner, BacktestConfig

# Setup logging
logging.basicConfig(level=logging.INFO)

def run():
    runner = BacktestRunner()
    
    # Configuration for XAUUSD backtest
    # Using 10 points for spread (0.10) and 0.01 for point for XAUUSD
    cfg = BacktestConfig(
        symbol="XAUUSD",
        timeframe="M1",
        date_from=datetime(2026, 5, 4, tzinfo=timezone.utc),
        date_to=datetime(2026, 5, 6, tzinfo=timezone.utc),
        initial_balance=10000.0,
        risk_per_trade=0.01,
        spread_points=20.0,  # $0.20 spread is typical
        point=0.01,          # XAUUSD point is 0.01
        use_risk_manager=True,
        max_trades=1
    )
    
    print("\nStarting 'AFTER' Backtest with New Filters...")
    result = runner.run(cfg)
    
    summary = result["summary"]
    metrics = result["debug_metrics"]
    
    print("\n" + "="*40)
    print(" [BACKTEST AFTER STATS]")
    print(f" Total trades: {summary['total_trades']}")
    print(f" Wins: {summary['wins']}")
    print(f" Losses: {summary['losses']}")
    print(f" Win rate: {summary['win_rate']}%")
    print(f" Final equity: ${metrics['final_equity']:.2f}")
    print(f" Max drawdown: {summary['max_drawdown'] * 100:.2f}%")
    print(f" Best setup: {summary['best_setup_type']}")
    print(f" Worst setup: {summary['worst_setup_type']}")
    print(f" Best session: {summary['best_session']}")
    print(f" Worst session: {summary['worst_session']}")
    print("="*40 + "\n")

if __name__ == "__main__":
    run()
