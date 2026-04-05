# 🛡️ Trading Bot: Technical Architecture & Operations Guide

This document provides a comprehensive, self-contained overview of the Smart Money Concepts (SMC) Trading Bot based on the current implementation. It is designed for developers, researchers, and other AI assistants to understand exactly how the bot interacts with MetaTrader 5 (MT5), evaluates market signals, and manages risk.

---

## 🏗️ 1. Project Overview

The bot is a high-frequency (scanning) automated system built in Python for the **MetaTrader 5** platform. It specializes in **Smart Money Concepts (SMC)**, identifying institutional footprints such as liquidity sweeps, order blocks, and market structure shifts.

### Core Components
- **Backend/Worker (`BotWorker`)**: The central engine orchestrating the loop, data fetching, and trade management.
- **Market Interface (`MT5Client`)**: A wrapper for the MetaTrader 5 API, handling connection, history, and raw order execution.
- **Strategy Engine (`StrategyEngine`)**: A multi-tiered evaluation layer that combines technical setups with AI confidence filters.
- **Risk Manager (`RiskManager`)**: A strict validation layer that guards against high spreads, volatility, and over-leverage.
- **Storage Layer (PostgreSQL/SQLAlchemy)**: Persists trade lifecycle data, analytics, and chart annotations.

---

## 📈 2. Full Trade Lifecycle

The bot operates in a continuous cycle (default interval defined in `settings.BOT_LOOP_INTERVAL`).

1.  **Connection & Safety Check**: On startup, `mt5_client` connects to the MT5 terminal and performs a **Hard Demo Guard**. It refuses to run if the account is not a demo account.
2.  **Market Data Sync**: The worker fetches OHLC data for **M1, M5, and M15** timeframes.
3.  **Strategy Scan**: The `StrategyEngine` runs 8 distinct SMC strategies against **closed candles** (to prevent repainting).
4.  **AI Filtering**: If a setup is found, it is sent to the `MarketPredictor` (AI filter). Any signal with a confidence score below **0.48** is rejected.
5.  **Risk Validation**: The `RiskManager` checks:
    - **Spread**: Rejects if Spread > 55 points (Gold override).
    - **Staleness**: Rejects if the latest market tick is >10 seconds old.
    - **Late Entry**: Rejects if the current price has already moved >70% toward the first target.
    - **RR Check**: Rejects if the current Live Risk/Reward is < 1.0.
6.  **Execution**: The `OrderExecutor` sends the order using MetaTrader's asynchronous API. It cycles through filling modes (**IOC -> RETURN -> FOK**) to ensure fill on brokers like XM.
7.  **Position Management**: Once open, the worker monitors the trade's progress.
    - **Stage 1 (60% Progress)**: Closes 50% of the position and moves Stop Loss to Break-Even (entry price + small buffer).
    - **Stage 2 (80% Progress)**: Closes another 25% of initial volume and advances SL to secure profits.
8.  **Exit & Sync**: The `TradeSynchronizer` identifies when a trade is closed on the broker side and records the final profit, exit price, and reason in the database.

---

## 🚀 3. Entry Logic (SMC Strategies)

The bot evaluates **8 specific strategies** defined in `backend/app/strategy/families/smc.py`. All strategies prioritize the **M15 Macro Trend** (Bias) while using **M1 for precise triggers**.

| Strategy Name | Logic Type | Primary Trigger (M1) | Confirmation |
| :--- | :--- | :--- | :--- |
| **Sweep Reclaim** | Reversal | Price breaks M15 High/Low and closes back inside. | M1 Crossover/Recapture. |
| **VSA Shift** | Reversal | Volume spike (>1.5x avg) at local Supply/Demand. | Price rejection wick + Volume. |
| **Continuation** | Trend | Price mitigates a 5-minute Order Block (OB). | M15 BOS Trend alignment. |
| **Mitigation** | Reversal | Price touches the boundary of an M15 FVG. | FVG boundary contact. |
| **MSS Shift** | Reversal | Market Structure Shift (Higher High/Lower Low break). | Candle close past M1 swing point. |
| **Breaker Block** | Reversal | Retest of a broken/failed Order Block. | Failure of original OB + Retest. |
| **Exhaustion** | Reversal | RSI > 70 or < 30 on M5 + CHoCH break on M1. | Momentum overextension. |
| **Volume Flow** | Breakout | Price interaction with the 100-bar POC. | Close > POC (Bull) or < POC (Bear). |

> [!NOTE]  
> **Why the bot might take "bad" trades**:  
> 1. **VSA Spikes**: Random spikes during news can trigger "Absorption" signals even if the trend is continuing.  
> 2. **Late CHoCH**: A Change of Character (CHoCH) on M1 can happen after the move is already exhausted.  
> 3. **News Volatility**: The bot does not currently have an economic news wiper; high-impact news can cause false "Sweep" reclaims.

---

## 🛡️ 4. Stop Loss & Take Profit

### Original Calculation
1.  **Stop Loss (SL)**: Structural by default. It finds the nearest Swing High/Low and adds a buffer. If no structural level is found, it falls back to **1.5x ATR**.
2.  **Take Profit (TP)**: The bot calculates two targets:
    - **TP1**: Nearest liquidity level (Support/Resistance).
    - **TP2**: Extended target (Second nearest S/R).
    - **Hard Target**: The MT5 order is always set to **TP2** to allow a "Runner" to catch bigger moves.

### Monotonic SL Guard
The bot has a hard rule: **Stop Loss can only move in favor of protection.**
- **BUY**: New SL must be $\ge$ Current SL.
- **SELL**: New SL must be $\le$ Current SL.
If a proposed SL movement increases risk, the worker rejects the update and logs a "STRICT GUARD FAILURE."

---

## 🔄 5. Partial Close Management (Stages)

The bot manages trades in three distinct stages to ensure "Risk-Free" runs.

| Stage | Trigger Condition | Volume Action | SL Action |
| :--- | :--- | :--- | :--- |
| **Stage 1** | Price reaches 60% of TP1 distance. | Close **50%** of initial size. | Move SL to BE + Buffer. |
| **Stage 2** | Price reaches 80% of TP1 distance. | Close **25%** of initial size. | Advance SL to Stage 1 Target. |
| **Runner** | TP2 hit or SL hit. | Close Remaining. | - |

- **Protection Gap Recovery**: If a partial close succeeds but the SL update fails (e.g., due to MT5 latency), the bot identifies this "Gap" on the next cycle, halts new entries, and retries the SL update until the trade is secured.
- **CLOSED_FULL Logic**: If the remaining units after a partial would be less than the broker’s minimum (e.g., < 0.01 lots), the bot performs a full exit to avoid "dust" positions.

---

## 📊 6. Risk Filters & Broker Handling

### Execution Safety
- **XM Filling Modes**: The bot cycles through `IOC` -> `RETURN` -> `FOK`. This prevents the "Unsupported Filling Mode" error on standard accounts.
- **Spread Guard**: A hard limit (55 points for Gold) rejects trades during high-volatility sessions or rollovers.
- **Stale Market**: If the bot hasn't received a tick from MT5 in 10 seconds, it stops scanning to avoid trading on old data.

### Demo Limits (Current State)
- **Symbol Lock**: Focused exclusively on `XAUUSD` for consistency.
- **Trade Capacity**: Strictly limited to **1 open trade** at any time.
- **Volume**: All trades are forced to **minimum lot size (0.01)** for safety.

---

## 🗄️ 7. Database Model (Core Fields)

| Field | Description |
| :--- | :--- |
| `ticket_id` | The unique MetaTrader 5 position ID. |
| `ai_score` | Confidence from the AI Predictor (0.0 to 1.0). |
| `tp1` / `tp2` | Specific targets for partial takes. |
| `stage1_sl_done` | Boolean flag confirming protection is active. |
| `market_regime` | Detected condition (Trending, Ranging, Volatile). |
| `final_exit_reason` | Audit trail: `TP2_HIT`, `TRAILING_STOP_HIT`, `STAGE_2_CLOSED_FULL`. |

---

## ✅ 8. Confirmation Status

| Feature | Confirmed from Code | Needs Live Demo Proof |
| :--- | :--- | :--- |
| **Stop Loss Guard** | ✅ Verified Strict Guard | Needs check on high slippage. |
| **Stage 2 Partial Logic** | ✅ Verified Fractional Math | Already demoed successfully. |
| **AI Filtering** | ✅ Logic Integrated | Needs long-term accuracy check. |
| **XM Filling modes** | ✅ Automated Retry Logic | IOC works reliably now. |
| **Protection Gap Lock** | ✅ Verified Hitting Lock | Needs check on system restart. |

---

## 📝 9. Final Summary

**What is Solid**:
- The **Staged Close** mechanism is robust and handles broker lot-size limits well.
- The **MT5 Connection** and filling mode retries make it stable on restrictive brokers like XM.
- The **SL Guard** ensures that a trade never increases its risk once protection starts.

**What Needs Testing**:
- **Strategy Overlap**: Testing how strategies compete if two setups form at the exact same price.
- **High-Impact News**: Validating if the 55-point spread filter is enough to keep the bot out of toxic news volatility.
- **Re-Entry Frequency**: Monitoring if the bot enters too many times after an SL hit in a choppy market.
