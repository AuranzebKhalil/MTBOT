import pandas as pd
import numpy as np

class M15Features:
    """
    Extracts features from the M15 timeframe (Macro Bias).
    Focuses on institutional order flow, high-timeframe direction, and ATR state.
    """
    
    @staticmethod
    def get_bias(df: pd.DataFrame) -> int:
        """
        Determines the macroeconomic bias (trend direction).
        Returns: 1 for Bullish, -1 for Bearish, 0 for Neutral/Wait
        """
        if len(df) < 50:
            return 0
            
        ema50 = df['close'].rolling(50).mean().iloc[-1]
        close = df['close'].iloc[-1]
        
        # Structure check over the last 40 bars (in two 20-bar halves)
        hh_hl = df['high'].iloc[-20:].max() >= df['high'].iloc[-40:-20].max() and \
                df['low'].iloc[-20:].min() >= df['low'].iloc[-40:-20].min()
        
        ll_lh = df['low'].iloc[-20:].min() <= df['low'].iloc[-40:-20].min() and \
                df['high'].iloc[-20:].max() <= df['high'].iloc[-40:-20].max()

        if close > ema50 and hh_hl:
            return 1
        if close < ema50 and ll_lh:
            return -1
            
        return 0

    @staticmethod
    def get_atr(df: pd.DataFrame, period=14) -> float:
        """
        Calculates Average True Range (Volatility proxy)
        """
        if len(df) < period + 1:
            return 0.0
            
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean().iloc[-1]
        
    @staticmethod
    def extract_all(df: pd.DataFrame) -> dict:
        """Returns a compiled dictionary of M15 features."""
        if df is None or df.empty:
            return {"m15_bias": 0, "m15_atr": 0.0}
            
        return {
            "m15_bias": M15Features.get_bias(df),
            "m15_atr": M15Features.get_atr(df)
        }
