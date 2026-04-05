import pandas as pd
import numpy as np
from app.ai.predictor import MarketPredictor
from app.market_data.mt5_client import MT5Client
import os
import sys

def deep_train(symbol="XAUUSD", timeframe="M1"):
    print(f"--- 🧠 STARTING DEEP AI TRAINING FOR {symbol} ---")
    
    mt5 = MT5Client()
    if not mt5.connect():
        print("Error: Could not connect to MetaTrader 5 terminal.")
        return

    # Fetch 25,000 candles (approx 2-3 weeks of M1 data) for a strong base
    print(f"Downloading 25,000 bars of historical institutional flow for {symbol}...")
    data = mt5.get_bars(symbol, timeframe, 25000)

    # ─── DATA INSPECTOR ───────────────────────────────────────────────
    if data is None or data.empty:
        print(f"❌ Error: No data received from MT5 for {symbol}.")
        return

    print("\n" + "="*60)
    print(f"  ✅ DATA LOADED SUCCESSFULLY FOR {symbol} ({timeframe})")
    print("="*60)

    print(f"  📊 Total Candles Loaded : {len(data):,}")
    print(f"  📋 Columns Available    : {list(data.columns)}")
    print(f"  🗓️  Earliest Candle      : {data['time'].iloc[0]}")
    print(f"  🗓️  Latest Candle        : {data['time'].iloc[-1]}")
    print(f"  💰 Price Range          : {data['low'].min():.5f}  →  {data['high'].max():.5f}")
    print(f"  📈 Avg Tick Volume      : {data['tick_volume'].mean():.1f}")
    print("="*60)

    print("\n── FIRST 5 CANDLES (Oldest) ──────────────────────────────")
    print(data[['time', 'open', 'high', 'low', 'close', 'tick_volume']].head(5).to_string(index=False))

    print("\n── LAST 5 CANDLES (Most Recent) ──────────────────────────")
    print(data[['time', 'open', 'high', 'low', 'close', 'tick_volume']].tail(5).to_string(index=False))

    print("\n── PRICE STATISTICS ──────────────────────────────────────")
    print(data[['open', 'high', 'low', 'close', 'tick_volume']].describe().round(5).to_string())
    print("="*60 + "\n")
    # ──────────────────────────────────────────────────────────────────


    predictor = MarketPredictor()
    print("Engineering features and training Quant engine...")
    
    success = predictor.train(data)
    
    if success:
        print(f"✅ SUCCESS: Deep Training complete for {symbol}.")
        print(f"Brain saved to: models/rf_model.pkl")
    else:
        print("❌ FAILED: Training error — check if market data is available.")

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSD"
    deep_train(symbol=symbol)
