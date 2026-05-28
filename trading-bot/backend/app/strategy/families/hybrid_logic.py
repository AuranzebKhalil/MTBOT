import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from app.strategy.models import Signal
from app.core.enums import OrderSide, SetupFamily
from indicators import SMCIndicators

logger = logging.getLogger("HybridLogic")

class HybridLogicFamily:
    def __init__(self, indicators: SMCIndicators):
        self.indicators = indicators

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds hybrid indicators. In backtests, these are often already pre-calculated."""
        # Only add if missing (speedup)
        if 'bb_upper' not in df.columns:
            df = df.copy()
            upper, mid, lower = self.indicators.calculate_bollinger_bands(df['close'])
            df['bb_upper'] = upper
            df['bb_mid'] = mid
            df['bb_lower'] = lower
        if 'rsi' not in df.columns:
            df['rsi'] = self.indicators.calculate_rsi(df['close'])
        if 'adx' not in df.columns:
            df['adx'] = self.indicators.calculate_adx(df)
        if 'atr' not in df.columns:
            # Check for atr_m1 alias
            if 'atr_m1' in df.columns:
                df['atr'] = df['atr_m1']
            else:
                df['atr'] = self.indicators.calculate_atr(df)
        return df

    def detect_regime(self, df: pd.DataFrame) -> str:
        latest = df.iloc[-1]
        adx = latest.get('adx', 0)
        
        # Consolidation check: price range vs ATR
        recent = df.tail(20)
        range_pct = (recent['high'].max() - recent['low'].min()) / recent['close'].iloc[-1]
        
        if range_pct < 0.001: # 10 pips on EURUSD approx
            return "CONSOLIDATION"
        elif adx < 25:
            return "RANGING"
        else:
            return "TRENDING"

    def check_mean_reversion(self, data: Dict[str, pd.DataFrame], symbol: str) -> Optional[Signal]:
        m1 = data["M1"]
        latest = m1.iloc[-1]
        
        if latest['rsi'] < 30 and latest['close'] <= latest['bb_lower']:
            return self._create_signal(m1, OrderSide.BUY, SetupFamily.MEAN_REVERSION, "Mean Reversion: BB Lower + RSI Oversold", symbol)
        if latest['rsi'] > 70 and latest['close'] >= latest['bb_upper']:
            return self._create_signal(m1, OrderSide.SELL, SetupFamily.MEAN_REVERSION, "Mean Reversion: BB Upper + RSI Overbought", symbol)
        return None

    def check_support_resistance(self, data: Dict[str, pd.DataFrame], symbol: str) -> Optional[Signal]:
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        
        # Simple S/R from M15 swing points
        support = m15[m15['swing_low'] == True]['low'].tail(3).max()
        resistance = m15[m15['swing_high'] == True]['high'].tail(3).min()
        
        if np.isnan(support) or np.isnan(resistance): return None
        
        # Confirmation logic: Rejection candle at level
        if latest['low'] <= support * 1.0005 and latest['close'] > support:
            if self._is_bullish_rejection(latest):
                return self._create_signal(m1, OrderSide.BUY, SetupFamily.SUPPORT_RESISTANCE, "S/R Reversal: Support Rejection", symbol)
        
        if latest['high'] >= resistance * 0.9995 and latest['close'] < resistance:
            if self._is_bearish_rejection(latest):
                return self._create_signal(m1, OrderSide.SELL, SetupFamily.SUPPORT_RESISTANCE, "S/R Reversal: Resistance Rejection", symbol)
                
        return None

    def check_breakout(self, data: Dict[str, pd.DataFrame], symbol: str) -> Optional[Signal]:
        m1 = data["M1"]
        latest = m1.iloc[-1]
        
        # Use a 50-bar range for breakout
        range_h = m1['high'].shift(1).tail(50).max()
        range_l = m1['low'].shift(1).tail(50).min()
        
        v_col = 'tick_volume' if 'tick_volume' in m1.columns else 'real_volume'
        vol_spike = False
        if v_col in m1.columns:
            v_avg = m1[v_col].tail(20).mean()
            vol_spike = latest[v_col] > v_avg * 1.5

        if latest['close'] > range_h and vol_spike:
            return self._create_signal(m1, OrderSide.BUY, SetupFamily.BREAKOUT, "Breakout: Range High + Volume", symbol)
        if latest['close'] < range_l and vol_spike:
            return self._create_signal(m1, OrderSide.SELL, SetupFamily.BREAKOUT, "Breakout: Range Low + Volume", symbol)
        return None

    def _create_signal(self, df, side, family, reason, symbol, sl=None, tp=None) -> Signal:
        latest = df.iloc[-1]
        # Use pre-calculated ATR if available
        if 'atr' in df.columns:
            atr = latest['atr']
        elif 'atr_m1' in df.columns:
            atr = latest['atr_m1']
        else:
            atr = self.indicators.calculate_atr(df).iloc[-1]
        price = float(latest['close'])
        
        if sl is None:
            sl = price - (atr * 2) if side == OrderSide.BUY else price + (atr * 2)
        if tp is None:
            tp = price + (atr * 4) if side == OrderSide.BUY else price - (atr * 4)
            
        return Signal(
            strategy=family,
            symbol=symbol,
            timeframe="M1",
            direction=side,
            entry=price,
            sl=sl,
            tp=tp,
            score=70.0,
            reasons=[reason],
            metadata={"atr": float(atr), "timestamp": latest['time'] if 'time' in latest else df.index[-1]}
        )

    def _is_bullish_rejection(self, candle):
        total = candle['high'] - candle['low']
        if total == 0: return False
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        return lower_wick > total * 0.5

    def _is_bearish_rejection(self, candle):
        total = candle['high'] - candle['low']
        if total == 0: return False
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        return upper_wick > total * 0.5

    def evaluate(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Tuple[List[Signal], List[Any]]:
        """Used by HybridSwitcherStrategy to check all rules simultaneously based on regime"""
        approved = []
        regime = self.detect_regime(data["M15"])
        
        if regime == "RANGING":
            s1 = self.check_mean_reversion(data, symbol)
            if s1: approved.append(s1)
            s2 = self.check_support_resistance(data, symbol)
            if s2: approved.append(s2)
        elif regime == "CONSOLIDATION":
            s3 = self.check_breakout(data, symbol)
            if s3: approved.append(s3)
            
        return approved, []
