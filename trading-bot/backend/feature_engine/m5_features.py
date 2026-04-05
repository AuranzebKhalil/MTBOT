import pandas as pd
from indicators import SMCIndicators

class M5Features:
    """
    Extracts features from the M5 timeframe (Structural Alignment).
    Focuses on BOS/CHoCH structural breaks and pullback quality.
    """
    
    @staticmethod
    def get_structure_alignment(df: pd.DataFrame) -> int:
        """
        Determines the structural direction based on BOS/CHoCH.
        Returns: 1 for Bullish, -1 for Bearish, 0 for Neutral/Wait
        """
        if len(df) < 20: return 0
        
        indicators = SMCIndicators()
        df_processed = indicators.detect_bos_choch(df)
        
        latest = df_processed.iloc[-2]  # Need completed bar
        
        # If there's a break of structure logic
        if latest['bos']:
            if latest['close'] > latest['open']:
                return 1
            else:
                return -1
                
        # If no immediate BOS, infer from recent price action
        ema20 = df['close'].rolling(20).mean().iloc[-1]
        close = df['close'].iloc[-1]
        return 1 if close > ema20 else -1
        
    @staticmethod
    def get_pullback_quality(df: pd.DataFrame) -> float:
        """
        Measures the depth and momentum of the recent pullback.
        Returns a score representing pullback quality.
        """
        if len(df) < 10: return 0.0
        
        recent_high = df['high'].iloc[-10:].max()
        recent_low = df['low'].iloc[-10:].min()
        close = df['close'].iloc[-1]
        
        # Determine relative position within the recent range (0.0 to 1.0)
        rng = recent_high - recent_low
        if rng == 0: return 0.5
        
        return (close - recent_low) / rng

    @staticmethod
    def extract_all(df: pd.DataFrame) -> dict:
        """Returns a compiled dictionary of M5 features."""
        if df is None or df.empty:
            return {"m5_structure": 0, "m5_pullback_quality": 0.5}
            
        return {
            "m5_structure": M5Features.get_structure_alignment(df),
            "m5_pullback_quality": M5Features.get_pullback_quality(df)
        }
