import os
import sys
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Ensure current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.backtest.runner import BacktestRunner
from app.backtest.config import BacktestSettings

def main():
    print("Initializing BacktestRunner for User's FULL Date Range (April 29 - May 22)...")
    
    cfg = BacktestSettings(
        symbol="XAUUSD",
        date_from=datetime(2026, 4, 29, 0, 0, tzinfo=timezone.utc),
        date_to=datetime(2026, 5, 22, 0, 0, tzinfo=timezone.utc),
        initial_balance=10000.0,
        risk_per_trade_pct=0.01,
        fixed_spread_points=55.0,
        ai_mode="disabled",
        gate_profile="balanced",
        include_rejections_in_report=True,
        diagnose_gates=True  # Force true to track funnel counts
    )
    
    # Set allowed strategies
    cfg.enabled_strategies = [
        "SMC_TREND", "SMC_MSS", "SMC_VOLUME", "HYBRID_REVERSION"
    ]
    cfg.excluded_strategies = []
    
    runner = BacktestRunner(cfg)
    
    # Run the backtest
    print(f"Running simulation for {cfg.symbol} from {cfg.date_from} to {cfg.date_to}")
    res = runner.run()
    
    if "error" in res:
        print(f"Backtest Error: {res['error in response']}")
        if "diagnostics" in res:
            print(f"Diagnostics: {res['diagnostics']}")
        return
        
    summary = res["summary"]
    trades = res["trades"]
    rejected = res["rejected_signals"]
    debug = res["debug_metrics"]
    
    print("\n" + "="*50)
    print("BACKTEST RESULTS SUMMARY:")
    
    tdf = pd.DataFrame(trades)
    total_trades = summary.get('total_trades', 0)
    wins = len(tdf[tdf['realized_pnl'] > 0]) if total_trades > 0 else 0
    losses = len(tdf[tdf['realized_pnl'] <= 0]) if total_trades > 0 else 0
    total_profit = tdf[tdf['realized_pnl'] > 0]['realized_pnl'].sum() if total_trades > 0 else 0
    total_loss = tdf[tdf['realized_pnl'] <= 0]['realized_pnl'].sum() if total_trades > 0 else 0

    print(f"Total Trades: {total_trades}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win Rate: {summary.get('win_rate', 0)}%")
    print(f"Total Profit: ${total_profit:.2f}")
    print(f"Total Loss: ${total_loss:.2f}")
    print(f"Net PnL: ${summary.get('net_pnl', 0):.2f}")
    print(f"Profit Factor: {summary.get('profit_factor', 0)}")
    print(f"Max Drawdown: {summary.get('max_drawdown', 0)}%")
    
    print("\nDEBUG METRICS:")
    for k, v in debug.items():
        if k != "top_rejection_reasons" and k != "top_rejection_rules":
            print(f"  {k}: {v}")
            
    print("\nTOP REJECTION RULES:")
    for rule, count in debug.get("top_rejection_rules", []):
        print(f"  - {rule}: {count}")
        
    print("\nTOP REJECTION REASONS:")
    for reason, count in debug.get("top_rejection_reasons", []):
        print(f"  - {reason}: {count}")
        
    print("\nSTRATEGY PERFORMANCE:")
    diag = res.get("diagnostics", {})
    for sid, perf in diag.get("strategy_performance", {}).items():
        if perf['raw_signals'] > 0 or perf['executed_trades'] > 0:
            print(f"  {sid}:")
            print(f"    Status: {perf['status']}")
            print(f"    Executed Trades: {perf['executed_trades']}")
            print(f"    Raw Signals: {perf['raw_signals']}")
            print(f"    Funnel: {perf['funnel']}")

if __name__ == "__main__":
    main()
