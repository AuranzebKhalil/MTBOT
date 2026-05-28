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
        
        # New Hybrid Indicators
        upper, mid, lower = self.indicators.calculate_bollinger_bands(df['close'])
        df['bb_upper'] = upper
        df['bb_mid'] = mid
        df['bb_lower'] = lower
        df['rsi'] = self.indicators.calculate_rsi(df['close'])
        df['adx'] = self.indicators.calculate_adx(df)
        
        return df

    def check_sweep_reclaim(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M15 (Macro High/Low) + M1 (Trigger)"""
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]
        
        # Use pre-calculated or limited lookback for macro levels
        macro_high = m15['high'].tail(100).max()
        macro_low = m15['low'].tail(100).min()
        
        # PROXIMITY CHECK
        near_macro_low = latest['low'] < macro_low * 1.0005
        near_macro_high = latest['high'] > macro_high * 0.9995
        
        if not (near_macro_low or near_macro_high): return None

        # CANDLE GEOMETRY
        is_rejection = self._is_rejection_candle(latest)
        body = abs(latest['close'] - latest['open'])
        # Use pre-calculated body average if available
        if 'body_avg_m1' in m1.columns:
            avg_body = latest['body_avg_m1']
        else:
            avg_body = abs(m1['close'] - m1['open']).tail(20).mean()
        displacement = body > (avg_body * 1.2) if avg_body > 0 else True # Reclaim must have some strength

        # STRUCTURE CHECK
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)

        logger.debug(f"[{symbol}] [SWEEP_RECLAIM] Check: ProximityL={near_macro_low}, ProximityH={near_macro_high} | Rejection={is_rejection}, Disp={displacement} | HL={higher_low}, LH={lower_high}")

        if bias == 1 and near_macro_low:
            # BUY Rule: Sweep happened, now we want Reclaim + HL
            swept = m1['low'].tail(5).min() < macro_low
            reclaimed = latest['close'] > macro_low
            if swept and reclaimed and (higher_low or is_rejection) and displacement:
                 sl = float(m1['low'].tail(5).min())
                 tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                 tp2 = self._get_extended_target(m15, OrderSide.BUY, latest['close'])
                 logger.info(f"[{symbol}] [SWEEP_RECLAIM] CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}, Disp={displacement}")
                 return self._create_signal(m1, OrderSide.BUY, StrategyFamily.SWEEP_RECLAIM, "Sweep Reclaim (Confirmed HL/Rejection)", symbol, "M1", sl=sl, tp1=tp1, tp2=tp2)
        
        if bias == -1 and near_macro_high:
            # SELL Rule: Sweep happened, now we want Reclaim + LH
            swept = m1['high'].tail(5).max() > macro_high
            reclaimed = latest['close'] < macro_high
            if swept and reclaimed and (lower_high or is_rejection) and displacement:
                 sl = float(m1['high'].tail(5).max())
                 tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                 tp2 = self._get_extended_target(m15, OrderSide.SELL, latest['close'])
                 logger.info(f"[{symbol}] [SWEEP_RECLAIM] CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}, Disp={displacement}")
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

        logger.debug(f"[{symbol}] [VSA_SHIFT] Check: Vol={v_spike_ratio:.1f}x | Demand/Supply: D={in_demand}, S={in_supply} | HL={higher_low}, LH={lower_high}, Reject={is_rejection}")
        
        if v_spike:
            if bias == 1 and in_demand and latest['close'] > latest['open']:
                # Buy Rule: Absorption detected, now confirm with Rejection OR Higher Low
                if is_rejection or higher_low:
                    sl = float(m1['low'].tail(3).min())
                    tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                    logger.info(f"[{symbol}] [VSA_SHIFT] CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}")
                    return self._create_signal(m1, OrderSide.BUY, StrategyFamily.VSA_SHIFT, "VSA Absorption (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
            
            if bias == -1 and in_supply and latest['close'] < latest['open']:
                # Sell Rule: Absorption detected, confirm LH or Rejection
                if is_rejection or lower_high:
                    sl = float(m1['high'].tail(3).max())
                    tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                    logger.info(f"[{symbol}] [VSA_SHIFT] CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}")
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
        
        m15_bullish = m15['bos'].iloc[-1] == 1
        m15_bearish = m15['bos'].iloc[-1] == -1
        
        logger.debug(f"[{symbol}] [CONTINUATION] Check: Bias={bias} | Trend: Bull={m15_bullish}, Bear={m15_bearish}")

        if bias == 1 and m15_bullish:
             fresh_ob = m5[m5['order_block'] == 1].tail(1)
             if not fresh_ob.empty:
                  ob_low = fresh_ob.iloc[0]['low']
                  dist_to_ob = latest['low'] / ob_low if ob_low > 0 else 0
                  logger.info(f"[{symbol}] [CONTINUATION] OB Found (Bullish) at {ob_low:.5f} | Dist={dist_to_ob:.4f}x")
                  if latest['low'] < ob_low * 1.002 and ob_low < latest['close']:
                       sl = ob_low
                       tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                       logger.info(f"[{symbol}] [CONTINUATION] TRIGGERED BUY: SL={sl:.5f}")
                       return self._create_signal(m1, OrderSide.BUY, StrategyFamily.CONTINUATION, "Trend Continuation", symbol, "M1", sl=sl, tp1=tp1)

        if bias == -1 and m15_bearish:
             fresh_ob = m5[m5['order_block'] == -1].tail(1)
             if not fresh_ob.empty:
                  ob_high = fresh_ob.iloc[0]['high']
                  dist_to_ob = latest['high'] / ob_high if ob_high > 0 else 0
                  logger.info(f"[{symbol}] [CONTINUATION] OB Found (Bearish) at {ob_high:.5f} | Dist={dist_to_ob:.4f}x")
                  if latest['high'] > ob_high * 0.998 and ob_high > latest['close']:
                       sl = ob_high
                       tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                       logger.info(f"[{symbol}] [CONTINUATION] TRIGGERED SELL: SL={sl:.5f}")
                       return self._create_signal(m1, OrderSide.SELL, StrategyFamily.CONTINUATION, "Trend Continuation", symbol, "M1", sl=sl, tp1=tp1)
        return None

    def check_mitigation(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M15 (FVG Creation) + M1 (Boundary Touch)"""
        m1 = data["M1"]
        m15 = data["M15"]
        latest = m1.iloc[-1]

        required_cols = {"fvg_bullish", "fvg_bearish", "fvg_mitigated", "fvg_bottom", "fvg_top"}
        if not required_cols.issubset(m1.columns): return None

        logger.debug(f"[{symbol}] [MITIGATION] Check: Bias={bias} | Latest: BullFVG={latest['fvg_bullish']}, BearFVG={latest['fvg_bearish']} | Mitigated={latest['fvg_mitigated']}")

        if bias == 1 and latest['fvg_bullish'] and not latest['fvg_mitigated']:
            # Require Rejection from the FVG
            logger.info(f"[{symbol}] [MITIGATION] Bullish FVG Zone: {latest['fvg_bottom']:.5f} - {latest['fvg_top']:.5f} | Low={latest['low']:.5f}")
            if latest['low'] <= latest['fvg_bottom'] and latest['close'] > latest['fvg_bottom']:
                sl = latest['fvg_bottom'] - (latest['fvg_top'] - latest['fvg_bottom']) * 0.5
                tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                logger.info(f"[{symbol}] [MITIGATION] TRIGGERED BUY: SL={sl:.5f}")
                return self._create_signal(m1, OrderSide.BUY, StrategyFamily.MITIGATION, "FVG Mitigation (Strict)", symbol, "M1", sl=sl, tp1=tp1)
                
        if bias == -1 and latest['fvg_bearish'] and not latest['fvg_mitigated']:
            # Require Rejection from the FVG
            logger.info(f"[{symbol}] [MITIGATION] Bearish FVG Zone: {latest['fvg_bottom']:.5f} - {latest['fvg_top']:.5f} | High={latest['high']:.5f}")
            if latest['high'] >= latest['fvg_top'] and latest['close'] < latest['fvg_top']:
                sl = latest['fvg_top'] + (latest['fvg_top'] - latest['fvg_bottom']) * 0.5
                tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                logger.info(f"[{symbol}] [MITIGATION] TRIGGERED SELL: SL={sl:.5f}")
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

        logger.debug(f"[{symbol}] [EXHAUSTION] Check: Bias={bias} | M5 RSI={m5_rsi:.1f} | CHOCH={latest['choch']} | HL={higher_low}, LH={lower_high}, Reject={is_rejection}")

        if bias == -1 and m5_rsi > 70 and latest['choch'] == -1:
             # SELL Rule: RSI Extreme + CHOCH, confirm with Lower High or Rejection
             if lower_high or is_rejection:
                sl = float(m1['high'].tail(5).max())
                tp1 = self._get_nearest_liquidity(m15, OrderSide.SELL, latest['close'])
                logger.info(f"[{symbol}] [EXHAUSTION] CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.SELL, StrategyFamily.EXHAUSTION, "Overbought Exhaustion (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
             
        if bias == 1 and m5_rsi < 30 and latest['choch'] == 1:
             # BUY Rule: RSI Extreme + CHOCH, confirm with Higher Low or Rejection
             if higher_low or is_rejection:
                sl = float(m1['low'].tail(5).min())
                tp1 = self._get_nearest_liquidity(m15, OrderSide.BUY, latest['close'])
                logger.info(f"[{symbol}] [EXHAUSTION] CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.BUY, StrategyFamily.EXHAUSTION, "Oversold Exhaustion (Confirmed)", symbol, "M1", sl=sl, tp1=tp1)
             
        return None


    def check_mss(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M1 (MSS Shift) + Pullback Check"""
        m1 = data["M1"]
        latest = m1.iloc[-1]
        if "mss" not in m1.columns: return None
        
        # Displacement Check
        body = abs(latest['close'] - latest['open'])
        # Use pre-calculated body average if available
        if 'body_avg_m1' in m1.columns:
            avg_body = latest['body_avg_m1']
        else:
            avg_body = abs(m1['close'] - m1['open']).tail(20).mean()
        displacement = body > (avg_body * 1.5) if avg_body > 0 else True

        # STRUCTURE CHECK
        higher_low = self._check_higher_low(m1)
        lower_high = self._check_lower_high(m1)

        logger.info(f"[{symbol}] [MSS] Check: M1 MSS={latest['mss']} | Disp={displacement} (Ratio={body/avg_body if avg_body>0 else 0:.1f}) | HL={higher_low}, LH={lower_high}")

        if displacement:
            if bias == 1 and latest['mss'] == 1 and latest['close'] > latest['open']:
                 # BUY Rule: Displacement MSS, confirm with Structure or Follow-through
                 if higher_low or latest['close'] > m1['high'].iloc[-2]:
                    logger.info(f"[{symbol}] [MSS] CONFIRMED BUY: Structure Confirmation")
                    return self._create_signal(m1, OrderSide.BUY, StrategyFamily.MSS, "Market Structure Shift (Confirmed)", symbol, "M1")
            if bias == -1 and latest['mss'] == -1 and latest['close'] < latest['open']:
                 # SELL Rule: Displacement MSS, confirm with Structure or Follow-through
                 if lower_high or latest['close'] < m1['low'].iloc[-2]:
                    logger.info(f"[{symbol}] [MSS] CONFIRMED SELL: Structure Confirmation")
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
                logger.info(f"[{symbol}] [BREAKER] CONFIRMED BUY: HL={higher_low}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.BUY, StrategyFamily.BREAKER, "Breaker Block Retest (Confirmed)", symbol, "M1")
        if latest['breaker_block'] == -1 and bias == -1:
             # SELL Rule: Breaker hit, confirm with Rejection OR Lower High
             if is_rejection or lower_high:
                logger.info(f"[{symbol}] [BREAKER] CONFIRMED SELL: LH={lower_high}, Reject={is_rejection}")
                return self._create_signal(m1, OrderSide.SELL, StrategyFamily.BREAKER, "Breaker Block Retest (Confirmed)", symbol, "M1")
        return None

    def check_volume_flow(self, data: Dict[str, pd.DataFrame], bias: int, symbol: str) -> Optional[Signal]:
        """Tiers: M1 (POC Interface) + Volume Strength Filter"""
        m1 = data["M1"]
        latest = m1.iloc[-1]
        if "poc" not in m1.columns: return None
        
        poc = latest['poc']
        if poc == 0: return None
        
        # 1. Proximity Check
        dist = abs(latest['close'] - poc) / latest['close']
        
        if dist < 0.0005: # Within 0.05% of POC
             # 2. Volume Strength Filter (Safe Fix: Moved from validation to detection)
             res = self._has_volume_strength(m1)
             if not res["has_strength"]:
                 logger.debug(f"[{symbol}] [VOLUME_FLOW] POC touch detected but weak volume ({res['ratio']:.2f}x < {res['required']:.2f}x). Skipping.")
                 # Using a special return value or side channel to signal silent skip reason
                 # For now, we'll let the engine track it if we add it to a metadata field or similar.
                 # But BaseStrategy.detect_setup returns Optional[RawSetup].
                 # We'll use a hack: if we want to count this specifically, we need to pass it back.
                 # The user requested a silent skip counter "SMC_VOLUME_WEAK_POC_TOUCH".
                 return None

             if bias == 1 and latest['close'] > latest['open']:
                  logger.info(f"[{symbol}] [VOLUME_FLOW] TRIGGERED BUY: Near POC with Volume Strength ({res['ratio']:.2f}x)")
                  sig = self._create_signal(m1, OrderSide.BUY, StrategyFamily.VOLUME, "POC Interaction (Bullish)", symbol, "M1")
                  if sig:
                      sig.metadata.update({
                          "volume_current": res["current"],
                          "volume_average": res["average"],
                          "volume_ratio": res["ratio"],
                          "required_volume_ratio": res["required"],
                          "poc": poc,
                          "distance_to_poc_percent": dist * 100
                      })
                  return sig
                  
             if bias == -1 and latest['close'] < latest['open']:
                  logger.info(f"[{symbol}] [VOLUME_FLOW] TRIGGERED SELL: Near POC with Volume Strength ({res['ratio']:.2f}x)")
                  sig = self._create_signal(m1, OrderSide.SELL, StrategyFamily.VOLUME, "POC Interaction (Bearish)", symbol, "M1")
                  if sig:
                      sig.metadata.update({
                          "volume_current": res["current"],
                          "volume_average": res["average"],
                          "volume_ratio": res["ratio"],
                          "required_volume_ratio": res["required"],
                          "poc": poc,
                          "distance_to_poc_percent": dist * 100
                      })
                  return sig
        return None

    def _has_volume_strength(self, df: pd.DataFrame, lookback: int = 20, ratio: float = 1.2) -> Dict[str, Any]:
        """Helper to verify if current volume shows enough 'strength' relative to average."""
        res = {"has_strength": False, "current": 0.0, "average": 0.0, "ratio": 0.0, "required": ratio}
        
        v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
        if v_col not in df.columns or len(df) < lookback:
            return res
            
        latest_vol = float(df[v_col].iloc[-1])
        avg_vol = float(df[v_col].tail(lookback).mean())
        
        if avg_vol <= 0:
            return res
            
        v_ratio = latest_vol / avg_vol
        res.update({
            "current": latest_vol,
            "average": avg_vol,
            "ratio": v_ratio,
            "has_strength": v_ratio >= ratio
        })
        return res

    def _create_signal(self, df, direction, strategy_name, reason, symbol, timeframe, sl=None, tp1=None, tp2=None) -> Signal:
        latest = df.iloc[-1]
        price = float(latest['close'])
        # Use pre-calculated ATR if available to avoid O(N^2)
        if 'atr_m1' in df.columns:
            atr = float(latest['atr_m1'])
        else:
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
        
        # VALIDATE SL/TP SIDES
        invalid_sl = (direction == OrderSide.BUY and final_sl >= price) or (direction == OrderSide.SELL and final_sl <= price)
        invalid_tp = (direction == OrderSide.BUY and final_tp1 <= price) or (direction == OrderSide.SELL and final_tp1 >= price)
        
        if invalid_sl or invalid_tp:
             logger.warning(f"[{symbol}] [{strategy_name.name}] REJECTED: Invalid levels. SL={final_sl:.5f}, TP1={final_tp1:.5f}, Price={price:.5f}")
             # We return a dummy signal with metadata for rejection tracking if needed, 
             # but for now we'll just return a signal that will be caught by the engine.
             # Actually, the strategy engine expects a Signal object or None.
             # I'll return None if invalid, which effectively rejects it.
             return None

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
                "setup_time": latest['time'] if 'time' in latest else pd.Timestamp(0, tz=timezone.utc)
            }
        )

    def _check_higher_low(self, df: pd.DataFrame, lookback: int = 5) -> bool:
        """Confirms that structure is building upwards."""
        if len(df) < lookback + 1: return False
        # Vectorized access is faster than .iloc in a tight loop
        lows = df['low'].values
        current_min = min(lows[-1], lows[-2])
        prev_min = min(lows[-5], lows[-4], lows[-3])
        return current_min > prev_min

    def _check_lower_high(self, df: pd.DataFrame, lookback: int = 5) -> bool:
        """Confirms that structure is building downwards."""
        if len(df) < lookback + 1: return False
        highs = df['high'].values
        current_max = max(highs[-1], highs[-2])
        prev_max = max(highs[-5], highs[-4], highs[-3])
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
