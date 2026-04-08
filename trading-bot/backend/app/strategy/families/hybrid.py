import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from app.strategy.models import Signal
from app.core.enums import OrderSide, StrategyFamily
from indicators import SMCIndicators

logger = logging.getLogger("HybridStrategy")

class HybridStrategyFamily:
    def __init__(self, indicators: SMCIndicators):
        self.indicators = indicators
        self.name = "HYBRID_AI"

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates all indicators for the hybrid system."""
        df = df.copy()
        # 1. BB for Mean Reversion
        upper, mid, lower = self.indicators.calculate_bollinger_bands(df['close'])
        df['bb_upper'] = upper
        df['bb_mid'] = mid
        df['bb_lower'] = lower
        
        # 2. RSI for Reversion/SR
        df['rsi'] = self.indicators.calculate_rsi(df['close'])
        
        # 3. ADX for Market Detection
        df['adx'] = self.indicators.calculate_adx(df)
        
        # 4. ATR for dynamic SL
        df['atr'] = self.indicators.calculate_atr(df)

        return df

    def detect_regime(self, df: pd.DataFrame) -> str:
        """Determines if market is RANGING, TRENDING, or CONSOLIDATING."""
        latest = df.iloc[-1]
        adx = latest.get('adx', 0)
        
        # 1. CONSOLIDATION (Very tight range)
        atr_range = (df['high'] - df['low']).tail(20).mean()
        price = latest['close']
        if atr_range / price < 0.0005: # Extremely tight
            return "CONSOLIDATION"
            
        # 2. RANGING
        if adx < 25:
            return "RANGING"
            
        # 3. TRENDING
        return "TRENDING"

    def evaluate(self, symbol: str, data: Dict[str, pd.DataFrame], strategy_settings: Dict = None) -> Tuple[List[Signal], List[Signal]]:
        """
        The Master Switcher. Chooses the best strategy based on detected regime.
        """
        m1 = data["M1"]
        m5 = data["M5"]
        m15 = data["M15"]
        
        # We use M15 to detect the high-level regime
        regime = self.detect_regime(m15)
        logger.info(f"[{symbol}] Detected Market Regime: {regime}")
        
        approved = []
        rejected = []
        
        # Strategy selection logic
        if regime == "RANGING":
            signal = self.check_mean_reversion(data, symbol)
            if signal: approved.append(signal)
            
            # Also check S/R during range
            sr_signal = self.check_support_resistance(data, symbol)
            if sr_signal: approved.append(sr_signal)
            
        elif regime == "CONSOLIDATION":
            signal = self.check_breakout(data, symbol)
            if signal: approved.append(signal)
            
        elif regime == "TRENDING":
            # During trends, we might want to skip Mean Reversion 
            # Or use S/R for pullbacks (Continuation)
            sr_signal = self.check_support_resistance(data, symbol)
            if sr_signal: approved.append(sr_signal)

        return approved, rejected

    def check_mean_reversion(self, data: Dict[str, pd.DataFrame], symbol: str) -> Optional[Signal]:
        """Mean Reversion: BB + RSI logic."""
        df = data["M1"]
        latest = df.iloc[-1]
        
        # Parameters
        rsi_low = 30
        rsi_high = 70
        
        # BUY Condition: Touch/Close below Lower BB + RSI Oversold
        if latest['low'] <= latest['bb_lower'] and latest['rsi'] < rsi_low:
            sl = latest['bb_lower'] - (latest['atr'] * 1.5)
            tp = latest['bb_mid']
            return self._create_signal(df, OrderSide.BUY, "MEAN_REVERSION", "Bollinger Oversold Reversal", symbol, sl, tp)

        # SELL Condition: Touch/Close above Upper BB + RSI Overbought
        if latest['high'] >= latest['bb_upper'] and latest['rsi'] > rsi_high:
            sl = latest['bb_upper'] + (latest['atr'] * 1.5)
            tp = latest['bb_mid']
            return self._create_signal(df, OrderSide.SELL, "MEAN_REVERSION", "Bollinger Overbought Reversal", symbol, sl, tp)
            
        return None

    def check_support_resistance(self, data: Dict[str, pd.DataFrame], symbol: str) -> Optional[Signal]:
        """S/R Logic: Key zone rejections."""
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        
        # Identify zones (Using Swing Highs/Lows from M15)
        # Assuming indicators has detect_bos_choch which marks swing points
        recent_lows = m15[m15['swing_low'] == True]['low'].tail(5)
        recent_highs = m15[m15['swing_high'] == True]['high'].tail(5)
        
        if recent_lows.empty or recent_highs.empty: return None
        
        support_zone = recent_lows.max() # Top of the support area
        resistance_zone = recent_highs.min() # Bottom of the resistance area
        
        # BUY: Price in support zone + Bullish Rejection
        if latest['low'] < support_zone * 1.0005 and latest['close'] > latest['open']:
            # Check for wick rejection (Candle logic)
            if self._is_rejection(latest, OrderSide.BUY):
                sl = latest['low'] - (latest['atr'] * 1.0)
                tp = resistance_zone
                return self._create_signal(m1, OrderSide.BUY, "SUPPORT_RESISTANCE", "Key Support Rejection", symbol, sl, tp)

        # SELL: Price in resistance zone + Bearish Rejection
        if latest['high'] > resistance_zone * 0.9995 and latest['close'] < latest['open']:
            if self._is_rejection(latest, OrderSide.SELL):
                sl = latest['high'] + (latest['atr'] * 1.0)
                tp = support_zone
                return self._create_signal(m1, OrderSide.SELL, "SUPPORT_RESISTANCE", "Key Resistance Rejection", symbol, sl, tp)

        return None

    def check_breakout(self, data: Dict[str, pd.DataFrame], symbol: str) -> Optional[Signal]:
        """Breakout: Volatility expansion after consolidation."""
        df = data["M1"]
        latest = df.iloc[-1]
        
        # Detect range of last 20 candles
        range_h = df['high'].shift(1).tail(20).max()
        range_l = df['low'].shift(1).tail(20).min()
        range_height = range_h - range_l
        
        # Entry: Close outside range + Volatility spike
        vol_ratio = latest['atr'] / df['atr'].shift(1).tail(20).mean()
        
        # BUY Breakout
        if latest['close'] > range_h and vol_ratio > 1.2:
            sl = range_h - (range_height * 0.5)
            tp = latest['close'] + range_height
            return self._create_signal(df, OrderSide.BUY, "BREAKOUT", "Range Breakout Expansion", symbol, sl, tp)
            
        # SELL Breakout
        if latest['close'] < range_l and vol_ratio > 1.2:
            sl = range_l + (range_height * 0.5)
            tp = latest['close'] - range_height
            return self._create_signal(df, OrderSide.SELL, "BREAKOUT", "Range Breakout Expansion", symbol, sl, tp)

        return None

    def _create_signal(self, df, side, name, reason, symbol, sl, tp) -> Signal:
        latest = df.iloc[-1]
        return Signal(
            strategy=name,
            symbol=symbol,
            timeframe="M1",
            direction=side,
            entry=float(latest['close']),
            sl=float(sl),
            tp=float(tp),
            score=75.0,
            reasons=[reason],
            metadata={
                "atr": float(latest.get('atr', 0)),
                "regime": "HYBRID"
            }
        )

    def _is_rejection(self, candle, side):
        body = abs(candle['close'] - candle['open'])
        range_total = candle['high'] - candle['low']
        if range_total == 0: return False
        
        if side == OrderSide.BUY:
            lower_wick = min(candle['open'], candle['close']) - candle['low']
            return lower_wick > (range_total * 0.6) # Wick is 60%+ of candle
        else:
            upper_wick = candle['high'] - max(candle['open'], candle['close'])
            return upper_wick > (range_total * 0.6)
