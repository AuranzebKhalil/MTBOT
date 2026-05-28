# MTBOT - Advanced SMC Trading System

MTBOT is a high-performance automated trading system for MetaTrader 5 (MT5), specializing in **Smart Money Concepts (SMC)**. It identifies institutional footprints and executes high-probability trades based on market structure, liquidity, and volume analysis.

## 🚀 Key Features

### 1. Live Trading Engine
- **Multitimeframe Analysis**: Synchronizes data from M1, M5, and M15 timeframes to confirm high-probability setups.
- **Smart Execution**: Uses IOC (Immediate or Cancel), Return, and FOK (Fill or Kill) retry logic to ensure optimal entry.
- **Automated Trade Management**:
  - **Stage 1**: Closes 50% of the position at 60% progress and moves Stop Loss to Break-Even.
  - **Stage 2**: Closes 25% of the position at 80% progress and advances the Stop Loss to lock in profits.
- **Monotonic Protection**: Stop Loss only moves in favor of the trade (never backwards), protecting capital against sudden reversals.

### 2. Advanced Risk Management
- **Spread Guard**: Blocks trades if the spread exceeds a safety threshold (default: 55 points, adjusted for Gold).
- **Late Entry Protection**: Prevents entering a trade if more than 70% of the expected move has already occurred.
- **Gap Lock**: Halts activity if protection updates fail, ensuring the bot remains in a safe state.
- **AI Filtering**: Optional AI confidence check (0.48 threshold) to filter out low-probability signals based on historical patterns.

### 3. Comprehensive Backtesting
The bot includes a specialized **Quant Backtest Engine** that allows you to:
- **Simulate Real Market Conditions**: Replays historical M1 data candle-by-candle.
- **Strategy Validation**: Tests all 8 SMC strategies across various symbols like XAUUSD, GBPUSD, and EURUSD.
- **Detailed Reporting**: Generates reports showing every potential trade, entry reason, and strategy performance.
- **Cooldown Logic**: Simulates realistic trading intervals (30-minute cooldown between trades on the same symbol).

## 📊 Trading Strategies

MTBOT supports 13 high-probability trading setups across three specialized strategy families:

### 1. Smart Money Concepts (SMC) Family
These strategies identify institutional footprints and liquidity cycles:

| Strategy | Logic | Target Move |
| :--- | :--- | :--- |
| **Sweep Reclaim** | Reclaims liquidity after a sweep of major HTF H/L. | Mean Reversion |
| **VSA Shift** | Institutional absorption via Volume Spread Analysis. | Reversal |
| **MSS Shift** | Market Structure Shift confirming trend changes. | Reversal/Continuation |
| **Continuation** | Order Block mitigation in an established trend. | Trend Following |
| **Mitigation** | Precise entry at Fair Value Gap (FVG) boundaries. | Trend Following |
| **Breaker Block** | Retest of a failed OB (Institutional S/R flip). | Trend Following |
| **Exhaustion** | Counter-trend reversals at extreme RSI/ADX levels. | Mean Reversion |
| **Volume Flow** | High-volume reactions at the Point of Control (POC). | Reversal/Absorption |

### 2. Hybrid & Quantitative Family
Blends structural SMC logic with traditional quantitative signals:

| Strategy | Logic |
| :--- | :--- |
| **Hybrid Reversion** | Mean reversion using Bollinger Bands and RSI extremes. |
| **Hybrid S/R** | Volume-confirmed flips of major Support and Resistance levels. |
| **Hybrid Breakout** | Momentum-based breakouts with volatility expansion filters. |
| **Hybrid Master** | Multi-regime switcher that adapts to trend vs. range. |

### 3. Trend Optimization Family
| Strategy | Logic |
| :--- | :--- |
| **MAD Trend Loop** | Moving Average Deviation strategy that "loops" into strong trends. |

## 🛠 Technical Indicators
The bot calculates a wide array of technical and structural indicators:
- **Structure**: BOS (Break of Structure), CHoCH (Change of Character), MSS (Market Structure Shift).
- **Zones**: Order Blocks (OB), Fair Value Gaps (FVG), Supply/Demand Zones.
- **Volume**: VSA (Volume Spread Analysis), Volume Profile (POC).
- **Statistical**: ATR (for dynamic SL/TP), RSI, Bollinger Bands, ADX.

## 💻 Usage

### Backend (Python)
The backend manages MT5 connection, strategy execution, and risk management.
```bash
# Start the bot
python start.py

# Run a backtest
python backtest.py
```

### Frontend (Next.js)
The frontend provides a real-time dashboard to monitor trades and backtest results.
```bash
cd frontend
npm run dev
```

---
**Disclaimer**: This bot is for educational and demo purposes. Always test on a demo account before considering live deployment.
