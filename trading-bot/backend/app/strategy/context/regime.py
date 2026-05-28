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
        if len(latest_bars) < 2: return RegimeResult(regime=MarketRegime.RANGING_COMPRESSED, confidence=0.0, metrics={})
        
        # Use pre-calculated indicators if available
        if 'atr_sma_m15' in latest_bars.columns:
            last = latest_bars.iloc[-1]
            curr_atr = last['atr_m15']
            baseline_atr = last['atr_sma_m15']
            ema_fast_last = last['ema20_m15']
            ema_fast_prev = latest_bars.iloc[-5]['ema20_m15'] if len(latest_bars) >= 5 else ema_fast_last
            slope = (ema_fast_last - ema_fast_prev) / 5
            volatility_ratio = curr_atr / baseline_atr if baseline_atr > 0 else 1.0
        else:
            # Fallback slow way
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
            slope = (ema_fast.iloc[-1] - ema_fast.iloc[-5]) / 5 if len(ema_fast) >= 5 else 0
        
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

        # Calculate detailed institutional regime flags
        adx = float(latest_bars['adx'].iloc[-1]) if 'adx' in latest_bars.columns else 20.0
        is_trending = adx > 25
        is_ranging = adx <= 20
        
        is_high_volatility = volatility_ratio > 1.25
        is_low_volatility = volatility_ratio < 0.75
        
        is_expansion = volatility_ratio > 1.15
        is_compression = volatility_ratio < 0.8

        # Calculate Choppiness Index (CI)
        if len(latest_bars) >= 14:
            high_14 = float(latest_bars['high'].tail(14).max())
            low_14 = float(latest_bars['low'].tail(14).min())
            range_14 = high_14 - low_14
            tr_14 = (latest_bars['high'] - latest_bars['low']).tail(14).sum()
            ci = 100 * np.log10(tr_14 / range_14) / np.log10(14) if range_14 > 0 and tr_14 > 0 else 50.0
        else:
            ci = 50.0
            
        choppiness = ci > 58.0 or adx < 15
        
        regime_details = {
            "is_trending": is_trending,
            "is_ranging": is_ranging,
            "is_expansion": is_expansion,
            "is_compression": is_compression,
            "is_high_volatility": is_high_volatility,
            "is_low_volatility": is_low_volatility,
            "choppiness": choppiness
        }
            
        return RegimeResult(regime=regime, confidence=0.85, 
                            metrics={
                                "vol_ratio": float(volatility_ratio), 
                                "slope": float(slope),
                                "atr": float(curr_atr),
                                "market_bias": bias,
                                "regime_details": regime_details
                            })
