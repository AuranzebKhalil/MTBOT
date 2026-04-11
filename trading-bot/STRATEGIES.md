# 🛡️ Alpha Engine Institutional Strategies

This document provides a comprehensive breakdown of the algorithmic strategies powering the **MTBOT Alpha Engine**. Each strategy is designed following institutional "Smart Money" principles, focusing on liquidity, structure, and high-momentum displacement.

---

## 1. Strategy Pipeline: The "Sentinel" Protocol

All strategies follow a uniform 6-step execution pipeline:
1.  **Scan**: Multi-timeframe scanner identifies potential setups.
2.  **Context**: Market regime detection (Trending vs Ranging) via ADX/ATR.
3.  **Detection**: Specific strategy logic (e.g., Sweep, MSS) triggers a "Raw Setup".
4.  **AI Scoring**: The Sentinel AI predicts the probability of success.
5.  **Risk Validation**: Risk Manager verifies session filters, news, spread, and RR.
6.  **Execution**: Staged entry and managed exit via MT5 integration.

---

## 2. Institutional Execution Specs

### 🔷 Strategy 1: Sweep & Reclaim (SRR)
- **Scan Timeframe**: M15 (Primary Bias) & M5 (Liquidity Detection).
- **Execute Timeframe**: M1 (Precision Trigger).
- **Entry Logic**: Wait for a "Stop Hunt" outside M15/M5 structural highs/lows. Enter on an M1 candle close back inside the level (Reclaim) accompanied by an M1 Market Structure Shift.
- **Stop Loss**: Placed 2-5 pips beyond the "Sweep Wick" extreme.
- **Take Profit**: 
    - TP1: Nearest internal liquidity (Swing High/Low).
    - TP2: 1:3 RR or major HTF target zone.

### 🔷 Strategy 2: Continuation Retest (CR)
- **Scan Timeframe**: M30 / M15 (Trend Determination).
- **Execute Timeframe**: M1 (Entry).
- **Entry Logic**: Identify a Break of Structure (BOS) on M15. Wait for a "controlled" pullback to a fresh Order Block (OB) or FVG. Entry triggers on an M1 rejection candle at the level.
- **Stop Loss**: Placed behind the Order Block or the recent swing low.
- **Take Profit**: 
    - TP1: 1:1.5 RR (Risk Mitigation).
    - TP2: Extension to the next structural expansion.

### 🔷 Strategy 3: FVG Mitigation (FTM)
- **Scan Timeframe**: M15 / M5 (Detection of Displacement).
- **Execute Timeframe**: M1 (Boundary Touch).
- **Entry Logic**: Look for massive candles (displacement) that leave behind a Fair Value Gap. Enter on the *first* return to the 50% equilibrium of that FVG with M1 momentum confirmation.
- **Stop Loss**: Placed beyond the FVG boundary (opposite side of the rally).
- **Take Profit**: 
    - TP1: Start of the displacement move.
    - TP2: 1:2.5 RR.

### 🔷 Strategy 4: Market Structure Shift (MSS)
- **Scan Timeframe**: M5 / M1 (Structural Focus).
- **Execute Timeframe**: M1 (Aggressive Entry).
- **Entry Logic**: Detect a Change of Character (CHOCH) where a swing high/low is broken with a large displacement candle (>2.0x average size). Enter on the close of the break candle or a tiny retest of its shadow.
- **Stop Loss**: Placed below the expansion candle low (for BUY) or high (for SELL).
- **Take Profit**: 
    - TP1: 1:2 RR.
    - TP2: Major structural swing point.

### 🔷 Strategy 5: Mad Trend Loop (Lyro RS)
- **Scan Timeframe**: M1 / M5 (Momentum Overlays).
- **Execute Timeframe**: M1 (Indicator Signal).
- **Entry Logic**: Proprietary score-based entry. Triggers when the Mean Deviation Loop transitions from negative to positive (or vice-versa) AND the Alpha momentum score is > 85.
- **Stop Loss**: ATR-based dynamic stop (1.5 * ATR).
- **Take Profit**: 
    - TP1: 2 * ATR.
    - TP2: 4 * ATR or Signal Flip.

---

## 3. Trade Management (Partials & Trailing)

To maximize win rate and protect capital, the bot uses a **Staged Exit System**:

- **Stage 1 (Partial Close)**: At 60% progress towards TP, the bot closes **50% of the position** and moves SL to **Break Even + Buffer**.
- **Stage 2 (Final Partial)**: At 80% progress, it closes another **30%**, leaving 20% to run for major targets.
- **Structural Trailing**: The SL is dynamically trailed behind the latest M1 swing structure once Stage 1 is hit.

---

## 4. High-Probability Refinement (April 2026)

The bot has been refined to eliminate low-probability setups:
1.  **Strict Displacement**: MSS require **2.0x displacement**.
2.  **Candle Confirmation**: Continuation/Mitigation require **M1 Rejection**.
3.  **Filtered Reversals**: Retired noisy BB/RSI reversals and M1 range breakouts.

---

*Note: All parameters can be configured via the Dashboard Engine Settings.*
