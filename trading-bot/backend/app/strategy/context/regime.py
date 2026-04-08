from dataclasses import dataclass
import pandas as pd
import numpy as np
from app.core.datatypes import MarketRegime

@dataclass
class RegimeResult:
    regime: MarketRegime
    confidence: float
    metrics: dict

class RegimeDetector:
    def identify(self, latest_bars: pd.DataFrame) -> RegimeResult:
        """Uses True Range, STD, and Structural slopes."""
        df = latest_bars.copy()
        
        df['tr'] = np.maximum(df['high'] - df['low'], 
                     np.maximum(abs(df['high'] - df['close'].shift()), 
                                abs(df['low'] - df['close'].shift())))
        
        atr = df['tr'].rolling(14).mean()
        atr_sma = atr.rolling(50).mean()
        curr_atr = atr.iloc[-1]
        baseline_atr = atr_sma.iloc[-1]
        
        volatility_ratio = curr_atr / baseline_atr if baseline_atr > 0 else 1.0
        
        # Slope logic
        ema_fast = df['close'].rolling(20).mean()
        ema_slow = df['close'].rolling(50).mean()
        slope = (ema_fast.iloc[-1] - ema_fast.iloc[-5]) / 5
        
        regime = MarketRegime.RANGING_COMPRESSED
        bias = "NEUTRAL"
        
        if volatility_ratio > 1.8: regime = MarketRegime.RANGING_EXPANDED
        elif volatility_ratio < 0.6: regime = MarketRegime.RANGING_COMPRESSED
        elif volatility_ratio >= 0.6 and volatility_ratio <= 1.5:
            if slope > (curr_atr * 0.1): 
                regime = MarketRegime.TRENDING_BULLISH
                bias = "BULLISH"
            elif slope < -(curr_atr * 0.1): 
                regime = MarketRegime.TRENDING_BEARISH
                bias = "BEARISH"
            else: 
                regime = MarketRegime.RANGING_EXPANDED
            
        return RegimeResult(regime=regime, confidence=0.85, 
                            metrics={
                                "vol_ratio": float(volatility_ratio), 
                                "slope": float(slope),
                                "atr": float(curr_atr),
                                "market_bias": bias
                            })
