import pandas as pd
from indicators import SMCIndicators

class M1Features:
    """
    Extracts features from the M1 timeframe.
    Focuses on entry triggers like FVG, order blocks, and liquidity sweeps.
    """
    
    @staticmethod
    def get_trigger_features(df: pd.DataFrame) -> dict:
        """
        Determines the current entry trigger state based on recent bars.
        Extracts Sweep (-1, 0, 1), FVG (-1, 0, 1), and Order Block (-1, 0, 1).
        """
        if len(df) < 15:
            return {"sweep_signal": 0, "fvg_signal": 0, "ob_signal": 0, "candle_expansion": 0.0}
            
        indicators = SMCIndicators()
        
        # Process data
        df_processed = indicators.detect_liquidity_sweeps(df)
        df_processed = indicators.detect_fvg(df)
        df_processed = indicators.detect_order_blocks(df)
        
        latest = df_processed.iloc[-2]  # Most recent closed bar
        recent_bars = df_processed.iloc[-10:-2]
        
        sweep_signal = 0
        if (recent_bars['sweep'] == 1).any(): sweep_signal = 1
        elif (recent_bars['sweep'] == -1).any(): sweep_signal = -1
        
        fvg_signal = 0
        if latest['fvg_bullish']: fvg_signal = 1
        elif latest['fvg_bearish']: fvg_signal = -1
        
        ob_signal = latest['order_block']
        
        # Candle Expansion (momentum) - body size compared to recent average
        avg_body = (abs(df['close'] - df['open'])).rolling(10).mean().iloc[-2]
        current_body = abs(latest['close'] - latest['open'])
        candle_expansion = current_body / avg_body if avg_body > 0 else 1.0
        
        return {
            "sweep_signal": sweep_signal,
            "fvg_signal": fvg_signal,
            "ob_signal": ob_signal,
            "candle_expansion": round(candle_expansion, 2)
        }
        
    @staticmethod
    def extract_all(df: pd.DataFrame) -> dict:
        """Returns a compiled dictionary of M1 features."""
        if df is None or df.empty:
            return {"sweep_signal": 0, "fvg_signal": 0, "ob_signal": 0, "candle_expansion": 1.0}
            
        return M1Features.get_trigger_features(df)
