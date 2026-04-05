import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from app.strategy.models import Signal
from app.core.enums import OrderSide, StrategyFamily
from indicators import SMCIndicators

logger = logging.getLogger("SMCStrategy")

class SMCStrategyFamily:
    def __init__(self, indicators: SMCIndicators):
        self.indicators = indicators

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Runs the entire SMC mapping stack. Recommended only for Context windows (M15/M5)."""
        logger.debug(f"Preprocessing {len(df)} candles...")
        df = self.indicators.detect_liquidity_sweeps(df)
        df = self.indicators.detect_bos_choch(df)
        df = self.indicators.detect_fvg(df)
        df = self.indicators.detect_order_blocks(df)
        df = self.indicators.detect_vsa(df)
        df = self.indicators.detect_mss(df)
        df = self.indicators.detect_breaker_blocks(df)
        df = self.indicators.detect_volume_profile(df)
        return df

    def check_sweep_reclaim(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M15 (Macro High/Low) + M1 (Trigger)"""
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        
        macro_high = m15['high'].max()
        macro_low = m15['low'].min()
        
        # PROXIMITY CHECK
        near_macro_low = latest['low'] < macro_low * 1.0005
        near_macro_high = latest['high'] > macro_high * 0.9995
        
        if not (near_macro_low or near_macro_high): return None

        # CANDLE GEOMETRY
        is_rejection = self._is_rejection_candle(latest)
        body = abs(latest['close'] - latest['open'])
        avg_body = abs(m1['close'] - m1['open']).tail(20).mean()
        displacement = body > (avg_body * 1.2) # Reclaim must have some strength

        # STRUCTURE CHECK
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)

        logger.info(f"[{symbol}] [SWEEP_RECLAIM] Check: ProximityL={near_macro_low}, ProximityH={near_macro_high} | Rejection={is_rejection}, Disp={displacement} | HL={higher_low}, LH={lower_high}")

        if bias == 1 and near_macro_low:
            # BUY Rule: Sweep happened, now we want Reclaim + HL
            swept = m1['low'].tail(5).min() < macro_low
            reclaimed = latest['close'] > macro_low
            if swept and reclaimed and (higher_low or is_rejection) and displacement:
                 sl = float(m1['low'].tail(5).min())
                 tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                 tp2 = self._get_extended_target(m15, OrderSide.BUY, latest['close'])
                 logger.info(f"[{symbol}] [SWEEP_RECLAIM] ✅ CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}, Disp={displacement}")
                 return self._create_signal(m1, OrderSide.BUY, StrategyFamily.SWEEP_RECLAIM, "Sweep Reclaim (Confirmed HL/Rejection)", symbol, "M1", sl=sl, tp1=tp1, tp2=tp2)
        
        if bias == -1 and near_macro_high:
            # SELL Rule: Sweep happened, now we want Reclaim + LH
            swept = m1['high'].tail(5).max() > macro_high
            reclaimed = latest['close'] < macro_high
            if swept and reclaimed and (lower_high or is_rejection) and displacement:
                 sl = float(m1['high'].tail(5).max())
                 tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                 tp2 = self._get_extended_target(m15, OrderSide.SELL, latest['close'])
                 logger.info(f"[{symbol}] [SWEEP_RECLAIM] ✅ CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}, Disp={displacement}")
                 return self._create_signal(m1, OrderSide.SELL, StrategyFamily.SWEEP_RECLAIM, "Sweep Reclaim (Confirmed LH/Rejection)", symbol, "M1", sl=sl, tp1=tp1, tp2=tp2)
             
        return None

    def check_vsa_shift(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M5 (Structural Context) + M1 (Momentum Trigger)"""
        m1 = data["M1"]
        m5 = data["M5"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        
        local_low = m5['low'].tail(20).min()
        local_high = m5['high'].tail(20).max()
        
        in_demand = latest['low'] < local_low * 1.001
        in_supply = latest['high'] > local_high * 0.999
        
        v_col = 'tick_volume' if 'tick_volume' in m1.columns else 'real_volume'
        if v_col not in m1.columns: return None
        
        v_avg = m1[v_col].rolling(20).mean().iloc[-1]
        v_spike_ratio = latest[v_col] / v_avg if v_avg > 0 else 0
        v_spike = v_spike_ratio > 2.0 
        
        # CONFIRMATION
        is_rejection = self._is_rejection_candle(latest)
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)

        logger.info(f"[{symbol}] [VSA_SHIFT] Check: Vol={v_spike_ratio:.1f}x | Demand/Supply: D={in_demand}, S={in_supply} | HL={higher_low}, LH={lower_high}, Reject={is_rejection}")
        
        if v_spike:
            if bias == 1 and in_demand and latest['close'] > latest['open']:
                # Buy Rule: Absorption detected, now confirm with Rejection OR Higher Low
                if is_rejection or higher_low:
                    sl = float(m1['low'].tail(3).min())
                    tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                    logger.info(f"[{symbol}] [VSA_SHIFT] ✅ CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}")
                    return self._create_signal(m1, OrderSide.BUY, StrategyFamily.VSA_SHIFT, "VSA Absorption (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
            
            if bias == -1 and in_supply and latest['close'] < latest['open']:
                # Sell Rule: Absorption detected, confirm LH or Rejection
                if is_rejection or lower_high:
                    sl = float(m1['high'].tail(3).max())
                    tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                    logger.info(f"[{symbol}] [VSA_SHIFT] ✅ CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}")
                    return self._create_signal(m1, OrderSide.SELL, StrategyFamily.VSA_SHIFT, "VSA Absorption (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
        return None

    def check_continuation(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M15 (BOS Trend) + M5 (OB Mitigated Check) + M1 (Entry)"""
        m1 = data["M1"]
        m5 = data["M5"]
        m15 = data["M15"]
        latest = m1.iloc[-1]

        if "bos" not in m15.columns: return None
        if "order_block" not in m5.columns: return None
        
        m15_bullish = m15['bos'].tail(5).sum() > 0
        m15_bearish = m15['bos'].tail(5).sum() < 0
        
        logger.info(f"[{symbol}] [CONTINUATION] Check: Bias={bias} | Trend: Bull={m15_bullish}, Bear={m15_bearish}")

        if bias == 1 and m15_bullish:
             fresh_ob = m5[m5['order_block'] == 1].tail(1)
             if not fresh_ob.empty:
                  ob_low = fresh_ob.iloc[0]['low']
                  dist_to_ob = latest['low'] / ob_low if ob_low > 0 else 0
                  logger.info(f"[{symbol}] [CONTINUATION] OB Found (Bullish) at {ob_low:.5f} | Dist={dist_to_ob:.4f}x")
                  if latest['low'] < ob_low * 1.002:
                       sl = ob_low
                       tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                       logger.info(f"[{symbol}] [CONTINUATION] ✅ TRIGGERED BUY: SL={sl:.5f}")
                       return self._create_signal(m1, OrderSide.BUY, StrategyFamily.CONTINUATION, "Trend Continuation", symbol, "M1", sl=sl, tp1=tp1)

        if bias == -1 and m15_bearish:
             fresh_ob = m5[m5['order_block'] == -1].tail(1)
             if not fresh_ob.empty:
                  ob_high = fresh_ob.iloc[0]['high']
                  dist_to_ob = latest['high'] / ob_high if ob_high > 0 else 0
                  logger.info(f"[{symbol}] [CONTINUATION] OB Found (Bearish) at {ob_high:.5f} | Dist={dist_to_ob:.4f}x")
                  if latest['high'] > ob_high * 0.998:
                       sl = ob_high
                       tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                       logger.info(f"[{symbol}] [CONTINUATION] ✅ TRIGGERED SELL: SL={sl:.5f}")
                       return self._create_signal(m1, OrderSide.SELL, StrategyFamily.CONTINUATION, "Trend Continuation", symbol, "M1", sl=sl, tp1=tp1)
        return None

    def check_mitigation(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M15 (FVG Creation) + M1 (Boundary Touch)"""
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]

        required_cols = {"fvg_bullish", "fvg_bearish", "fvg_mitigated", "fvg_bottom", "fvg_top"}
        if not required_cols.issubset(m1.columns): return None

        logger.info(f"[{symbol}] [MITIGATION] Check: Bias={bias} | Latest: BullFVG={latest['fvg_bullish']}, BearFVG={latest['fvg_bearish']} | Mitigated={latest['fvg_mitigated']}")

        if bias == 1 and latest['fvg_bullish'] and not latest['fvg_mitigated']:
            # Require Rejection from the FVG
            logger.info(f"[{symbol}] [MITIGATION] Bullish FVG Zone: {latest['fvg_bottom']:.5f} - {latest['fvg_top']:.5f} | Low={latest['low']:.5f}")
            if latest['low'] <= latest['fvg_bottom'] and latest['close'] > latest['fvg_bottom']:
                sl = latest['fvg_bottom'] - (latest['fvg_top'] - latest['fvg_bottom']) * 0.5
                tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                logger.info(f"[{symbol}] [MITIGATION] ✅ TRIGGERED BUY: SL={sl:.5f}")
                return self._create_signal(m1, OrderSide.BUY, StrategyFamily.MITIGATION, "FVG Mitigation (Strict)", symbol, "M1", sl=sl, tp1=tp1)
                
        if bias == -1 and latest['fvg_bearish'] and not latest['fvg_mitigated']:
            # Require Rejection from the FVG
            logger.info(f"[{symbol}] [MITIGATION] Bearish FVG Zone: {latest['fvg_bottom']:.5f} - {latest['fvg_top']:.5f} | High={latest['high']:.5f}")
            if latest['high'] >= latest['fvg_top'] and latest['close'] < latest['fvg_top']:
                sl = latest['fvg_top'] + (latest['fvg_top'] - latest['fvg_bottom']) * 0.5
                tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                logger.info(f"[{symbol}] [MITIGATION] ✅ TRIGGERED SELL: SL={sl:.5f}")
                return self._create_signal(m1, OrderSide.SELL, StrategyFamily.MITIGATION, "FVG Mitigation (Strict)", symbol, "M1", sl=sl, tp1=tp1)
        return None

    def check_exhaustion(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M5 (Overextended) + M1 (CHOCH Break)"""
        m1 = data["M1"]
        m5 = data["M5"]
        m15 = data["M15"]
        latest = m1.iloc[-1]

        if "choch" not in m1.columns: return None
        m5_rsi = self.indicators.calculate_rsi(m5['close']).iloc[-1]
        
        # CONFIRMATION
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)
        is_rejection = self._is_rejection_candle(latest)

        logger.info(f"[{symbol}] [EXHAUSTION] Check: Bias={bias} | M5 RSI={m5_rsi:.1f} | CHOCH={latest['choch']} | HL={higher_low}, LH={lower_high}, Reject={is_rejection}")

        if bias == -1 and m5_rsi > 70 and latest['choch'] == -1:
             # SELL Rule: RSI Extreme + CHOCH, confirm with Lower High or Rejection
             if lower_high or is_rejection:
                sl = float(m1['high'].tail(5).max())
                tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                logger.info(f"[{symbol}] [EXHAUSTION] ✅ CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.SELL, StrategyFamily.EXHAUSTION, "Overbought Exhaustion (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
             
        if bias == 1 and m5_rsi < 30 and latest['choch'] == 1:
             # BUY Rule: RSI Extreme + CHOCH, confirm with Higher Low or Rejection
             if higher_low or is_rejection:
                sl = float(m1['low'].tail(5).min())
                tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                logger.info(f"[{symbol}] [EXHAUSTION] ✅ CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.BUY, StrategyFamily.EXHAUSTION, "Oversold Exhaustion (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
             
        return None


    def check_mss(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M1 (MSS Shift) + Pullback Check"""
        m1 = data["M1"]
        latest = m1.iloc[-1]
        if "mss" not in m1.columns: return None
        
        # Displacement Check
        body = abs(latest['close'] - latest['open'])
        avg_body = abs(m1['close'] - m1['open']).tail(20).mean()
        displacement = body > (avg_body * 1.5)

        # STRUCTURE CHECK
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)

        logger.info(f"[{symbol}] [MSS] Check: M1 MSS={latest['mss']} | Disp={displacement} (Ratio={body/avg_body if avg_body>0 else 0:.1f}) | HL={higher_low}, LH={lower_high}")

        if displacement:
            if bias == 1 and latest['mss'] == 1 and latest['close'] > latest['open']:
                 # BUY Rule: Displacement MSS, confirm with Structure or Follow-through
                 if higher_low or latest['close'] > m1['high'].iloc[-2]:
                    logger.info(f"[{symbol}] [MSS] ✅ CONFIRMED BUY: Structure Confirmation")
                    return self._create_signal(m1, OrderSide.BUY, StrategyFamily.MSS, "Market Structure Shift (Confirmed)", symbol, "M1")
            if bias == -1 and latest['mss'] == -1 and latest['close'] < latest['open']:
                 # SELL Rule: Displacement MSS, confirm with Structure or Follow-through
                 if lower_high or latest['close'] < m1['low'].iloc[-2]:
                    logger.info(f"[{symbol}] [MSS] ✅ CONFIRMED SELL: Structure Confirmation")
                    return self._create_signal(m1, OrderSide.SELL, StrategyFamily.MSS, "Market Structure Shift (Confirmed)", symbol, "M1")
        return None

    def check_breaker_block(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M1 (Breaker Retest)"""
        m1 = data["M1"]
        latest = m1.iloc[-1]
        if "breaker_block" not in m1.columns: return None
        
        is_rejection = self._is_rejection_candle(latest)
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)

        logger.info(f"[{symbol}] [BREAKER] Check: M1 Breaker={latest['breaker_block']} | Reject={is_rejection}, HL={higher_low}, LH={lower_high}")

        if latest['breaker_block'] == 1 and bias == 1:
             # BUY Rule: Breaker hit, confirm with Rejection OR Higher Low
             if is_rejection or higher_low:
                logger.info(f"[{symbol}] [BREAKER] ✅ CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.BUY, StrategyFamily.BREAKER, "Breaker Block Retest (Confirmed)", symbol, "M1")
        if latest['breaker_block'] == -1 and bias == -1:
             # SELL Rule: Breaker hit, confirm with Rejection OR Lower High
             if is_rejection or lower_high:
                logger.info(f"[{symbol}] [BREAKER] ✅ CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.SELL, StrategyFamily.BREAKER, "Breaker Block Retest (Confirmed)", symbol, "M1")
        return None

    def check_volume_flow(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M1 (POC Interface)"""
        m1 = data["M1"]
        latest = m1.iloc[-1]
        if "poc" not in m1.columns: return None
        
        poc = latest['poc']
        if poc == 0: return None
        
        # Trade when price interacts with POC
        dist = abs(latest['close'] - poc) / latest['close']
        logger.info(f"[{symbol}] [VOLUME_FLOW] Check: Bias={bias} | POC={poc:.5f} | Dist={dist*100:.3f}%")

        if dist < 0.0005: # Within 0.05% of POC
             if bias == 1 and latest['close'] > latest['open']:
                  logger.info(f"[{symbol}] [VOLUME_FLOW] ✅ TRIGGERED BUY: Near POC")
                  return self._create_signal(m1, OrderSide.BUY, StrategyFamily.VOLUME, "POC Interaction (Bullish)", symbol, "M1")
             if bias == -1 and latest['close'] < latest['open']:
                  logger.info(f"[{symbol}] [VOLUME_FLOW] ✅ TRIGGERED SELL: Near POC")
                  return self._create_signal(m1, OrderSide.SELL, StrategyFamily.VOLUME, "POC Interaction (Bearish)", symbol, "M1")
        return None

    def _create_signal(self, df, direction, strategy_name, reason, symbol, timeframe, sl=None, tp1=None, tp2=None) -> Signal:
        latest = df.iloc[-1]
        price = float(latest['close'])
        atr = float(self.indicators.calculate_atr(df).iloc[-1])
        
        # Default distances if structural levels not provided
        sl_dist = atr * 1.5
        # Smarter Buffer: max(spread * 1.5, atr * 0.1, point * 10)
        # Fallback spread to 2.0 pips if not in df (rare)
        point = 0.0001
        spread_estimated = (df['high'] - df['low']).mean() * 0.1 # Very rough fallback
        buffer = max(spread_estimated * 1.5, atr * 0.1, point * 10)
        
        final_sl = sl if sl is not None else (price - sl_dist if direction == OrderSide.BUY else price + sl_dist)
        
        # Apply buffer to SL (away from price)
        if direction == OrderSide.BUY:
            final_sl -= buffer
        else:
            final_sl += buffer
            
        # TP logic: TP1 is main target, TP2 is runner target
        final_tp1 = tp1 if tp1 else (price + sl_dist * 2 if direction == OrderSide.BUY else price - sl_dist * 2)
        # Find TP2 if not provided
        final_tp2 = tp2 if tp2 else self._get_extended_target(df, direction, final_tp1)
        
        # Extract structural S/R if available
        anchors = {}
        if 'fvg_bottom' in latest and latest['fvg_bottom'] > 0: anchors['fvg_zone'] = [latest['fvg_bottom'], latest['fvg_top']]
        if 'order_block' in latest and latest['order_block'] != 0: anchors['ob_level'] = latest['close']
        
        return Signal(
            strategy=strategy_name.value,
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            entry=price,
            sl=final_sl,
            tp=final_tp2 if final_tp2 else final_tp1,
            score=70.0,
            reasons=[reason],
            metadata={
                "anchors": anchors, 
                "atr": atr,
                "tp1": final_tp1,
                "tp2": final_tp2,
                "structural_sl": True if sl else False,
                "setup_time": latest['time'] if 'time' in latest else datetime.now(timezone.utc)
            }
        )

    def _check_higher_low(self, df: pd.DataFrame, lookback: int = 5) -> bool:
        """Confirms that structure is building upwards."""
        if len(df) < lookback + 1: return False
        recent_lows = df['low'].tail(lookback).values
        # True if current low >= previous low and we have a low that was higher than the one before it
        # Actually, simpler: Is the lowest point in the last 2 candles higher than the lowest point in the 3 candles before that?
        current_min = df['low'].tail(2).min()
        prev_min = df['low'].iloc[-5:-2].min()
        return current_min > prev_min

    def _check_lower_high(self, df: pd.DataFrame, lookback: int = 5) -> bool:
        """Confirms that structure is building downwards."""
        if len(df) < lookback + 1: return False
        current_max = df['high'].tail(2).max()
        prev_max = df['high'].iloc[-5:-2].max()
        return current_max < prev_max

    def _is_rejection_candle(self, candle: pd.Series) -> bool:
        """Detects pins/rejections where wick is > 50% of the total range."""
        total_range = candle['high'] - candle['low']
        if total_range == 0: return False
        
        body = abs(candle['close'] - candle['open'])
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        
        # BUY Rejection (Long lower wick)
        if candle['close'] > candle['open'] and lower_wick > (total_range * 0.5):
            return True
        # SELL Rejection (Long upper wick)
        if candle['close'] < candle['open'] and upper_wick > (total_range * 0.5):
            return True
        return False

    def _get_nearest_liquidity(self, df: pd.DataFrame, direction: OrderSide, current_price: float) -> Optional[float]:
        """Finds the nearest swing high (for BUY) or swing low (for SELL)."""
        if direction == OrderSide.BUY:
            # Look for recent swing highs above current price
            highs = df[df['swing_high'] == True]['high']
            above = highs[highs > current_price]
            if not above.empty:
                return float(above.tail(5).min()) # Nearest of the recent highs
        else:
            # Look for recent swing lows below current price
            lows = df[df['swing_low'] == True]['low']
            below = lows[lows < current_price]
            if not below.empty:
                return float(below.tail(5).max()) # Nearest of the recent lows
        return None

    def _get_extended_target(self, df: pd.DataFrame, direction: OrderSide, current_price: float) -> Optional[float]:
        """Finds the second nearest swing high/low."""
        if direction == OrderSide.BUY:
            highs = df[df['swing_high'] == True]['high']
            above = highs[highs > current_price].sort_values()
            if len(above) >= 2:
                return float(above.iloc[1])
        else:
            lows = df[df['swing_low'] == True]['low']
            below = lows[lows < current_price].sort_values(ascending=False)
            if len(below) >= 2:
                return float(below.iloc[1])
        return None
