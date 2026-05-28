# 📊 MTBOT Backtest Engine Documentation

## 🚀 Overview
The **MTBOT Backtest Engine** is a high-fidelity, institutional-grade simulation environment. It is designed to stress-test Smart Money Concepts (SMC) and Hybrid strategies against historical data with maximum accuracy. Unlike basic backtesters, this engine uses **M1-resolution candle replay** to ensure SL/TP hits are simulated realistically, accounting for spreads and intra-candle volatility.

---

## 🏗️ The Execution Pipeline
The engine follows a strict 5-stage pipeline for every single candle in the historical range:

### 1. Data Acquisition & Resampling
*   **Base Resolution**: The engine pulls 1-minute (M1) data from MetaTrader 5.
*   **Multi-Timeframe (MTF)**: M1 data is automatically resampled into **M5** and **M15** timeframes to feed the institutional structure logic.
*   **Warmup Phase**: The engine requires a **600-candle warmup period**. This ensures that M15 indicators (like Order Blocks and Swing Structures) have enough historical context to be 100% accurate before the first trade is evaluated.

### 2. Bulk Pre-calculation (Speed Optimization)
To avoid redundant processing, all technical indicators (SMC, VSA, Volatility) are pre-calculated for the entire dataset before the loop starts. This allows the engine to process months of data in seconds.

### 3. Strategy Evaluation (The "Gatekeeper")
Every candle is passed through the `StrategyEngine`. For a signal to be generated, it must pass:
*   **Structural Alignment**: M15 trend must align with M5/M1 entry zones.
*   **SMC Logic**: Specific patterns like *Liquidity Sweeps*, *Market Structure Shifts (MSS)*, or *Order Block Mitigations* must be present.
*   **AI Filtering**: The signal is graded by an AI model. If the probability of success is below the threshold, the signal is discarded before it even reaches the Risk Manager.

### 4. Institutional Risk Management
If a strategy generates a "Candidate Signal," the `RiskManager` performs a surgical validation:
*   **Spread Guard**: Rejects trades where the spread is too large relative to the Stop Loss (SL).
*   **Risk Sizing**: Calculates the exact lot size based on **1% risk** (or user-defined %) of the *current equity* at that specific moment.
*   **Side Validation**: Ensures SL and TP are on the correct side of the entry (e.g., SL must be below entry for a BUY).
*   **Session Filters**: Rejects trades during low-liquidity hours (e.g., late Friday or early Monday).

### 5. High-Fidelity Simulation
Once a trade is "Live," the engine enters a candle-by-candle replay mode:
*   **Conservative Fills**: If a single M1 candle hits both the SL and TP, the engine **always assumes the SL was hit first**. This provides a "worst-case scenario" result, ensuring your real-world performance is likely better than the backtest.
*   **Spread Awareness**: For BUYs, we enter at the **Ask** (Bid + Spread) and exit at the **Bid**. For SELLs, we enter at the **Bid** and exit at the **Ask**. This accurately simulates the "cost of doing business."

---

## 🔍 Understanding the Results

### Why are there 0 trades?
This is the most common question. It usually means the bot is doing its job correctly.
1.  **Grade-A Only**: The bot is programmed to ignore "maybe" setups. It only takes high-probability, institutionally-aligned trades.
2.  **Rejection Stages**: Check the **Debug Metrics**. A signal might have been found but rejected by the `AI_GATE` or `STRUCTURE_GATE`.
3.  **Spread Protection**: In high-volatility symbols (like Gold), the SL might be too tight compared to the spread, causing the Risk Manager to block the trade for safety.

### Key Metrics Explained
*   **Max Drawdown**: The largest "peak-to-valley" drop in your account balance. Essential for understanding risk.
*   **Average R:R**: The average Reward-to-Risk ratio. A strategy with a 40% win rate can be highly profitable if the Average R:R is > 2.0.
*   **Equity Curve**: A visual representation of your account growth. Look for smooth upward slopes; jagged lines indicate high volatility/risk.
*   **Both Hit Count**: Number of times SL and TP were hit in the same minute. We count these as losses for safety.

---

## 🛠️ Technical Specifications
*   **Contract Sizes**:
    *   **XAUUSD/Gold**: 100 units per lot.
    *   **Forex**: 100,000 units per lot.
    *   **JPY Pairs**: 1,000 units per lot.
*   **Entry Point**: `BacktestRunner.run()` in `backend/app/backtest/runner.py`.
*   **Language**: Python 3.9+ with Pandas/NumPy for heavy lifting.

---

> [!TIP]
> **Pro Tip**: Always run backtests over at least 30 days. Short ranges (e.g., 2 days) might not contain a single "Grade A" setup, leading to 0 trades and giving a false impression that the bot isn't working.

