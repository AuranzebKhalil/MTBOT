import os
import sys
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

# Ensure current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.backtest.runner import BacktestRunner
from app.backtest.config import BacktestSettings

def main():
    print("Initializing BacktestRunner for diagnostics...")
    
    # 1. Setup a short date range (3 days) in May 2026 to see what's happening
    cfg = BacktestSettings(
        symbol="XAUUSD",
        date_from=datetime(2026, 5, 4, 8, 58, tzinfo=timezone.utc),
        date_to=datetime(2026, 5, 7, 8, 58, tzinfo=timezone.utc),
        initial_balance=10000.0,
        risk_per_trade_pct=0.01,
        fixed_spread_points=35,
        ai_mode="disabled",
        gate_profile="balanced",
        include_rejections_in_report=True
    )
    
    runner = BacktestRunner(cfg)
    
    # Run the standard simulation logic manually with print/logging overrides
    print(f"Running simulation for {cfg.symbol} from {cfg.date_from} to {cfg.date_to}")
    
    # Check MT5 connection
    print(f"MT5 Connected: {runner.mt5._connected}")
    if not runner.mt5._connected:
        print("Attempting to connect to MT5...")
        if runner.mt5.connect():
            print("Connected successfully!")
        else:
            print("Failed to connect to MT5. Make sure MetaTrader 5 is running.")
            return

    resolved_symbol = runner.mt5.resolve_symbol(cfg.symbol)
    print(f"Resolved symbol: {resolved_symbol}")
    
    d_f = cfg.date_from.replace(tzinfo=None)
    d_t = cfg.date_to.replace(tzinfo=None)
    warmup_days = 5
    warmup_start = d_f - timedelta(days=warmup_days)
    
    print(f"Fetching M1 bars from {warmup_start} to {d_t}...")
    df = runner.mt5.get_bars_range(resolved_symbol, "M1", warmup_start, d_t)
    if df is None or df.empty:
        print("Error: No candles returned from MT5 client.")
        return
        
    print(f"Fetched {len(df)} candles.")
    print(f"First candle time: {df.iloc[0]['time']}")
    print(f"Last candle time: {df.iloc[-1]['time']}")
    
    # Let's run a standard simulation slice and inspect the variables
    # Let's calculate the indicators first
    print("Calculating indicators...")
    df = df.sort_values("time").reset_index(drop=True)
    df['tr'] = np.maximum(df['high'] - df['low'], 
                 np.maximum(abs(df['high'] - df['close'].shift()), 
                             abs(df['low'] - df['close'].shift())))
    df['atr_m1'] = df['tr'].rolling(14).mean()
    df['body_avg_m1'] = abs(df['close'] - df['open']).rolling(20).mean()
    df['rsi'] = runner.smc_family.indicators.calculate_rsi(df['close'])
    upper, mid, lower = runner.smc_family.indicators.calculate_bollinger_bands(df['close'])
    df['bb_upper'] = upper
    df['bb_mid'] = mid
    df['bb_lower'] = lower
    df['adx'] = runner.smc_family.indicators.calculate_adx(df)
    
    v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
    if v_col in df.columns:
        df['v_avg'] = df[v_col].rolling(20).mean()
        df['rel_activity'] = df[v_col] / df['v_avg']
    df['volatility'] = df['close'].rolling(window=20).std()
    
    m1_full = runner.smc_family.preprocess(df)
    
    # Resample to M5 / M15
    df5 = df.set_index('time').resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','tick_volume':'sum'}).dropna().reset_index()
    df5['ema20_m5'] = df5['close'].rolling(20).mean()
    df5['adx'] = runner.smc_family.indicators.calculate_adx(df5)
    m5_full = runner.smc_family.preprocess(df5)
    
    df15 = df.set_index('time').resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','tick_volume':'sum'}).dropna().reset_index()
    df15['ema50_m15'] = df15['close'].rolling(50).mean()
    df15['tr'] = np.maximum(df15['high'] - df15['low'], 
                 np.maximum(abs(df15['high'] - df15['close'].shift()), 
                             abs(df15['low'] - df15['close'].shift())))
    df15['atr_m15'] = df15['tr'].rolling(14).mean()
    df15['atr_sma_m15'] = df15['atr_m15'].rolling(50).mean()
    df15['ema20_m15'] = df15['close'].rolling(20).mean()
    df15['adx'] = runner.smc_family.indicators.calculate_adx(df15)
    m15_full = runner.smc_family.preprocess(df15)
    
    # Check if indicators calculated successfully and check some values
    print("\nIndicator Column Summary:")
    for key, frame in [("M1", m1_full), ("M5", m5_full), ("M15", m15_full)]:
        print(f"  Timeframe {key} columns: {list(frame.columns)}")
        # Check non-zero/non-null counts for some key columns
        for col in ['bos', 'choch', 'sweep', 'order_block', 'breaker_block', 'poc']:
            if col in frame.columns:
                non_zero = (frame[col] != 0).sum()
                non_null = frame[col].notna().sum()
                print(f"    - {col}: {non_zero} non-zero values, {non_null} non-null values")
                
    # Run evaluation at every step of M1 slice and print the first 10 skipped reasons
    print("\nRunning causal evaluation check...")
    search_from = d_f
    idx = df['time'].searchsorted(search_from)
    idx = max(idx, cfg.warmup_candles_m1)
    
    total_evals = 0
    skips = {}
    context_skips = 0
    gate_skips = 0
    
    # Set logging to debug during our check
    import logging
    logging.getLogger("StrategyEngine").setLevel(logging.INFO)
    logging.getLogger("SMCStrategy").setLevel(logging.INFO)
    
    for i in range(idx, min(idx + 1000, len(df))):
        c = df.iloc[i]
        t = c['time']
        t_naive = t.to_pydatetime().replace(tzinfo=None)
        
        m1_slice = m1_full.iloc[:i+1]
        m5_idx = m5_full['time'].searchsorted(t_naive - pd.Timedelta('5min'), side='right')
        m5_slice = m5_full.iloc[:m5_idx]
        m15_idx = m15_full['time'].searchsorted(t_naive - pd.Timedelta('15min'), side='right')
        m15_slice = m15_full.iloc[:m15_idx]
        
        if m5_slice.empty or m15_slice.empty: 
            continue
            
        data = {"M1": m1_slice, "M5": m5_slice, "M15": m15_slice}
        
        # Evaluate context
        context = runner.engine.context_eval.evaluate(m1_slice, m5_slice, m15_slice, cfg.symbol)
        if not context.is_tradable:
            context_skips += 1
            continue
            
        total_evals += 1
        
        # Check strategy setup detection manually
        for strategy in runner.engine.strategies:
            sid = strategy.strategy_id
            setup = strategy.detect_setup(data, context)
            if setup:
                print(f"[{t}] Detected Setup: {sid} | Direction={setup.direction} | Entry={setup.entry_price}")
                # Try to evaluate it
                app, rej, stats = runner.engine.evaluate(cfg.symbol, data)
                if app:
                    print(f"  -> Approved Signal: {app}")
                if rej:
                    print(f"  -> Rejected Signal: {rej}")
            else:
                reason = getattr(strategy, "last_skip_reason", "No Raw Setup")
                skips[reason] = skips.get(reason, 0) + 1
                
    print(f"\nCompleted check on 1000 candles starting at index {idx}.")
    print(f"Total evaluated candles (where context was tradable): {total_evals}")
    print(f"Total non-tradable candles (e.g. DEAD_ZONE, high spread): {context_skips}")
    print(f"Setup skip reason counts: {skips}")

if __name__ == "__main__":
    main()
