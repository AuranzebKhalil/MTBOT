# 🤖 Alertli AI Trading Bot - Volume & Execution Logic

This document explains how the bot calculates and executes trades, specifically focused on the **Volume Strategy** (Manual Lot vs. Dynamic Risk).

## 📊 Volume Selection Modes

The bot supports two distinct modes for deciding how many "Lots" to trade. These can be controlled directly from your **Engine Configurations** dashboard.

### 1. Fixed Lot Precision (Manual Mode)

When you select a specific volume button (e.g., `0.01`, `0.1`, `0.5`) in the UI, the bot enters **Fixed Mode**.

- **How it works**: The bot will ignore your "% Risk per Trade" setting and execute precisely the number of lots you've selected.
- **Best for**: Traders who want total control over their exposure regardless of the account balance or the size of the Stop Loss.
- **UI Location**: Settings -> Execution Lot Precision.

### 2. Institutional Dynamic Risk (Automatic Mode)

If no manual volume is selected (fallback), the bot uses a institutional-grade risk calculation.

- **The Formula**:
  `Lots = (Account Balance * Risk %) / (Stop Loss Distance * Symbol Multiplier)`
- **Example**: On a $10,000 account with 1% risk ($100), if your Stop Loss is 2.0 pips away on Gold, the bot will automatically calculate a lot size that ensures you only lose exactly $100 if the Stop Loss is hit.
- **Security**: It automatically rounds the calculation to your broker's "Volume Step" (usually 0.01) to prevent execution errors.

---

## 🛠️ Broker Compatibility (The Symbol Resolver)

Brokers have different names for the same assets (e.g., XM uses `GOLD`, while Exness might use `XAUUSDm`).

The bot features a **Smart Symbol Mapper** that automatically:

1.  Detects your broker's naming convention.
2.  Maps the bot's internal analysis logic to your broker's specific "Gold" or "Currency" asset.
3.  Ensures your user settings (Volume/Risk) follow the mapped asset correctly.

---

## 🛡️ Execution & Risk Safety Layer

Every trade goes through a "Triple Check" before being sent to MetaTrader 5:

1.  **The Spread Check**: If the spread is higher than your configuration (e.g., > 50 points), the trade is rejected to prevent "slippage."
2.  **The Protection Gap**: If an open trade hasn't had its Stop Loss moved to "Break Even" yet, the bot may halt new entries until the current trade is secured.
3.  **The Late Entry Filter**: If the price has already moved past 70% of the distance to the target, the bot will "Ignore" the signal to avoid chasing a bad entry price.

---

## 🚀 Getting Started

To trade with your preferred volume:

1.  Go to **Settings**.
2.  Navigate to **Engine Configurations**.
3.  Click the button for your desired **Lot Precision**.
4.  The "Volume Saved" toast notification will appear.
5.  Your next trade will now use that exact volume!

New Strategies

Hybrid Master Switcher (HYBRID_MASTER): The core "brain" that automatically detects market conditions (Ranging vs. Trending) and switches to the best-performing sub-strategy for that environment.
Mean Reversion - BB/RSI (HYBRID_REVERSION): Specifically built for sideways/ranging markets. It uses Bollinger Bands and RSI extremes to catch "rubber-band" price reversals back to the average.
Advanced Support & Resistance (HYBRID_SR): A structure-based strategy that identifies high-timeframe (M15) zones and waits for M1 price rejection (like pin-bars or engulfing candles) before entering high-probability reversals.
Momentum Breakout (HYBRID_BREAKOUT): Designed to capture explosive price moves during high-volatility transitions. It identifies tight consolidation ranges and enters when price breaks out with a volume surge.
You can now find these in your Strategies Dashboard, where you can toggle them on/off and adjust their AI confidence thresholds individually.
