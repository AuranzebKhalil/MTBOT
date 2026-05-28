import argparse
import logging
import sys
from datetime import datetime
from app.backtest.runner import BacktestRunner
from app.backtest.config import BacktestSettings

def main():
    parser = argparse.ArgumentParser(description="MTBOT Advanced Backtest CLI")
    parser.add_argument("--symbol", type=str, default="XAUUSD", help="Symbol to test")
    parser.add_argument("--from", dest="from_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--balance", type=float, default=10000.0, help="Initial balance")
    parser.add_argument("--risk", type=float, default=0.01, help="Risk per trade (0.01 = 1%)")
    parser.add_argument("--debug", type=str, default="false", help="Enable debug logging")
    parser.add_argument("--apply-recommended-filters", type=str, default="false", help="Run second pass with optimized filters")
    
    # Walk-Forward Arguments
    parser.add_argument("--walk-forward", type=str, default="false", help="Enable walk-forward validation")
    parser.add_argument("--train-from", type=str, help="Train start date")
    parser.add_argument("--train-to", type=str, help="Train end date")
    parser.add_argument("--test-from", type=str, help="Test start date")
    parser.add_argument("--test-to", type=str, help="Test end date")
    parser.add_argument("--rolling-wf", type=str, default="false", help="Enable rolling walk-forward")
    
    # Monte Carlo Arguments
    parser.add_argument("--monte-carlo", type=str, default="false", help="Enable Monte Carlo robustness testing")
    parser.add_argument("--mc-runs", type=int, default=1000, help="Number of MC simulations")
    parser.add_argument("--mc-noise", type=float, default=0.10, help="PnL noise percentage (0.10 = 10%)")
    parser.add_argument("--mc-ruin", type=float, default=20.0, help="Ruin drawdown threshold (%)")
    parser.add_argument("--mc-seed", type=int, default=42, help="Seed for reproducibility")
    parser.add_argument("--test-data", action="store_true", help="Quickly test candle fetching only")
    parser.add_argument("--diagnose-gates", type=str, default="false", help="Enable advanced pipeline gate diagnostics")
    parser.add_argument("--gate-profile", type=str, default="balanced", choices=["strict", "balanced", "research"], help="Strictness of structure gates")
    parser.add_argument("--ai-mode", type=str, default="disabled", choices=["disabled", "fallback", "live_model"], help="AI gate behavior in backtest")
    parser.add_argument("--compare-gates", type=str, default="false", help="Run comparison across all gate profiles")

    args = parser.parse_args()

    # Setup Logging
    log_level = logging.DEBUG if args.debug.lower() == "true" else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)

    try:
        d_from = datetime.strptime(args.from_date, "%Y-%m-%d") if args.from_date else None
        d_to = datetime.strptime(args.to_date, "%Y-%m-%d") if args.to_date else None
        tr_from = datetime.strptime(args.train_from, "%Y-%m-%d") if args.train_from else None
        tr_to = datetime.strptime(args.train_to, "%Y-%m-%d") if args.train_to else None
        ts_from = datetime.strptime(args.test_from, "%Y-%m-%d") if args.test_from else None
        ts_to = datetime.strptime(args.test_to, "%Y-%m-%d") if args.test_to else None
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. Details: {e}")
        sys.exit(1)

    cfg = BacktestSettings(
        symbol=args.symbol, date_from=d_from, date_to=d_to, initial_balance=args.balance, risk_per_trade_pct=args.risk,
        apply_recommended_filters=(args.apply_recommended_filters.lower() == "true"),
        walk_forward_enabled=(args.walk_forward.lower() == "true"),
        train_date_from=tr_from, train_date_to=tr_to, test_date_from=ts_from, test_date_to=ts_to,
        rolling_walk_forward_enabled=(args.rolling_wf.lower() == "true"),
        monte_carlo_enabled=(args.monte_carlo.lower() == "true"),
        mc_runs=args.mc_runs, mc_pnl_noise=args.mc_noise, mc_ruin_dd_pct=args.mc_ruin / 100.0, mc_seed=args.mc_seed,
        diagnose_gates=(args.diagnose_gates.lower() == "true"),
        gate_profile=args.gate_profile,
        ai_mode=args.ai_mode,
        compare_gates=(args.compare_gates.lower() == "true")
    )

    print(f"\n{'='*50}\n  MTBOT HIGH-FIDELITY BACKTEST ENGINE v2.6\n{'='*50}")
    print(f" Symbol:       {cfg.symbol}")
    if cfg.monte_carlo_enabled:
        print(f" Mode:         MONTE CARLO ROBUSTNESS TEST ({cfg.mc_runs} runs)")
    elif cfg.walk_forward_enabled:
        print(f" Mode:         WALK-FORWARD VALIDATION")
    elif cfg.diagnose_gates:
        print(f" Mode:         PIPELINE GATE DIAGNOSTICS")
    else:
        print(f" Mode:         STANDARD BACKTEST")
    print(f" Period:       {args.from_date} to {args.to_date}")
    print(f" Profile:      {cfg.gate_profile.upper()}")
    print(f" AI Mode:      {cfg.ai_mode.upper()}")
    print(f" Initial Bal:  ${cfg.initial_balance:,.2f}")
    print(f"{'='*50}\n")

    runner = BacktestRunner(cfg)
    
    if args.test_data:
        print(f"[TEST] Verifying MT5 Data Connection...")
        resolved = runner.mt5.resolve_symbol(cfg.symbol)
        if not resolved:
            print(f"[ERROR] Could not resolve symbol: {cfg.symbol}")
            sys.exit(1)
        
        print(f" - Resolved Symbol: {resolved}")
        df = runner.mt5.get_bars_range(resolved, "M1", cfg.date_from, cfg.date_to)
        
        if df is None or df.empty:
            print(f"[ERROR] No candles found for {resolved} in range.")
            print(f" - MT5 Last Error: {runner.mt5.get_last_error()}")
            sys.exit(1)
            
        print(f" - Candles Count:  {len(df)}")
        print(f" - First Candle:   {df.iloc[0]['time']}")
        print(f" - Last Candle:    {df.iloc[-1]['time']}")
        print(f"\n[SUCCESS] MT5 data feed is working for {resolved}.")
        sys.exit(0)

    results = runner.run()

    if "error" in results:
        print(f"[ERROR] {results['error']}")
        sys.exit(1)

    print(f"\n[DONE] Reports saved in '{cfg.export_folder}/'")

if __name__ == "__main__":
    main()
