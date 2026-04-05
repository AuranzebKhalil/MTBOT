import pandas as pd
import numpy as np
import datetime
from indicators import SMCIndicators

class SMCStrategy:
    """
    Consolidated Institutional Strategy Framework.
    Merges 13 overlapping setups into 5 core families to prevent backtest overfitting.
    Focuses on 'Say No' logic and Macro Confluence Scoring.
    """
    def __init__(self, symbol="GOLD"):
        self.symbol = symbol
        self.indicators = SMCIndicators()

    def analyze(self, df_m1, df_m5, df_m15):
        """
        Institutional Intelligence Analysis: Tracks ALL 5 families simultaneously.
        """
        price = df_m1['close'].iloc[-1]
        
        # 1. Pipeline Status Tracking
        pipeline_status = {
            "Sweep Reclaim": {"status": "Waiting", "reason": "No sweep detected", "score": 0},
            "VSA Shift": {"status": "Waiting", "reason": "Volume below 2x avg", "score": 0},
            "Continuation": {"status": "Waiting", "reason": "No BOS detected", "score": 0},
            "Mitigation": {"status": "Waiting", "reason": "No FVG touched", "score": 0},
            "Exhaustion": {"status": "Waiting", "reason": "No CHOCH break", "score": 0}
        }

        # 2. Gate Checks
        bias = self._get_macro_bias(df_m15)
        bias_str = "BULLISH" if bias == 1 else ("BEARISH" if bias == -1 else "NEUTRAL")
        
        m5_structure = self._get_structural_alignment(df_m5)
        m5_str = "BULLISH" if m5_structure == 1 else "BEARISH"

        if bias == 0:
            return "WAIT", price, "M15 Bias Neutral", {"pipeline": pipeline_status, "bias": bias_str}

        # 3. Structural Alignment (Relaxed for SMC Pullbacks)
        m5_aligned = False
        if bias == 1:
            # Bullish: Either Price > EMA20 OR M5 has a recent Bullish BOS (Still structurally Bullish)
            m5_aligned = (df_m5['close'].iloc[-1] > df_m5['close'].rolling(20).mean().iloc[-1]) or (self._has_recent_m5_bos(df_m5, 1))
        elif bias == -1:
            # Bearish: Either Price < EMA20 OR M5 has a recent Bearish BOS
            m5_aligned = (df_m5['close'].iloc[-1] < df_m5['close'].rolling(20).mean().iloc[-1]) or (self._has_recent_m5_bos(df_m5, -1))

        if not m5_aligned:
             msg = f"Alignment Mismatch (M15: {bias_str}, M5: Structure Lag)"
             for k in pipeline_status: pipeline_status[k].update({"status": "Mismatched", "reason": "MTF Bias Conflict"})
             return "WAIT", price, msg, {"pipeline": pipeline_status, "bias": bias_str}

        # 3. Process Live Setups
        df_p = self._preprocess(df_m1)
        
        # Strategy 1 Check
        sig1, name1, det1 = self._sweep_reclaim_reversal(df_p, bias)
        if sig1 != "WAIT": pipeline_status["Sweep Reclaim"].update({"status": "Setup Found", "reason": det1.get('ent'), "score": 85})
        
        # Strategy 2 Check
        sig2, name2, det2 = self._vsa_family(df_p, bias)
        if sig2 != "WAIT": pipeline_status["VSA Shift"].update({"status": "Setup Found", "reason": det2.get('ent'), "score": 80})

        # Strategy 3 Check
        sig3, name3, det3 = self._continuation_retest(df_p, bias)
        if sig3 != "WAIT": pipeline_status["Continuation"].update({"status": "Setup Found", "reason": det3.get('ent'), "score": 75})

        # Strategy 4 Check
        sig4, name4, det4 = self._first_touch_mitigation(df_p, bias)
        if sig4 != "WAIT": pipeline_status["Mitigation"].update({"status": "Setup Found", "reason": det4.get('ent'), "score": 70})

        # Strategy 5 Check
        sig5, name5, det5 = self._exhaustion_reversal(df_p, bias)
        if sig5 != "WAIT": pipeline_status["Exhaustion"].update({"status": "Setup Found", "reason": det5.get('ent'), "score": 65})

        # 4. Result Selection (Priority Based)
        final_signal = "WAIT"
        final_name = "No setups qualified"
        final_details = {"pipeline": pipeline_status, "bias": bias_str}

        for sig, name, details in [(sig1, name1, det1), (sig2, name2, det2), (sig3, name3, det3), (sig4, name4, det4), (sig5, name5, det5)]:
            if sig != "WAIT":
                final_signal = sig
                final_name = name
                final_details.update(details)
                break

        if final_signal != "WAIT":
            return self._finalize(final_signal, final_name, final_details, df_p)

        return final_signal, price, final_name, final_details

    def _preprocess(self, df):
        df = self.indicators.detect_liquidity_sweeps(df)
        df = self.indicators.detect_bos_choch(df)
        df = self.indicators.detect_fvg(df)
        df = self.indicators.detect_order_blocks(df)
        df = self.indicators.detect_supply_demand(df)
        df = self.indicators.detect_vsa(df)
        return df

    def _vsa_family(self, df, bias):
        """Family 2: VSA Institutional Shift (Volume Absorption)."""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        v_avg = df['tick_volume'].rolling(20).mean().iloc[-1]
        
        # 1. Identify Volume Spike (> 2.0x 20-bar avg)
        v_spike = latest['tick_volume'] > v_avg * 2.0
        
        # 2. Immediate Entry on Rejection (VSA Spike + Rejection/Absorption)
        if v_spike:
            if bias == 1 and self._is_bullish_confirmation(latest):
                return "BUY", "VSA Institutional Shift", {"ent": "Immediate (VSA Absorption)", "vsa": "2BR"}
            if bias == -1 and self._is_bearish_confirmation(latest):
                return "SELL", "VSA Institutional Shift", {"ent": "Immediate (VSA Absorption)", "vsa": "2BR"}

        # 3. Confirmation Entry (Next candle after high-volume spike)
        prev_spike = prev['tick_volume'] > v_avg * 2.0
        if prev_spike:
            if bias == 1 and self._is_bullish_confirmation(latest) and latest['close'] > prev['high']:
                 return "BUY", "VSA Institutional Shift", {"ent": "Confirmation Candle", "vsa": "2BR"}
            if bias == -1 and self._is_bearish_confirmation(latest) and latest['close'] < prev['low']:
                 return "SELL", "VSA Institutional Shift", {"ent": "Confirmation Candle", "vsa": "2BR"}
            
        return "WAIT", "", {}

    def _get_macro_bias(self, df):
        """ Institutional Macro Bias: EMA 50 + Simple Structure """
        if len(df) < 50: return 0
        ema50 = df['close'].rolling(50).mean()
        
        latest_close = df['close'].iloc[-1]
        latest_ema = ema50.iloc[-1]
        
        # Simpler Bias: If price is above EMA50, we look for BUYS. vice versa.
        # This is less restrictive than HH/HL checks.
        if latest_close > latest_ema:
            return 1 # BULLISH
        elif latest_close < latest_ema:
            return -1 # BEARISH
        return 0

    def _get_structural_alignment(self, df):
        if len(df) < 20: return 0
        close = df['close'].iloc[-1]
        ema20 = df['close'].rolling(20).mean().iloc[-1]
        return 1 if close > ema20 else -1

    def _has_recent_m5_bos(self, df, direction):
        """Checks if M5 has a structural break in the specified direction within the last 50 bars."""
        df_p = self.indicators.detect_bos_choch(df)
        recent = df_p.tail(50)
        return (recent['bos'] == direction).any()

    def _relative_activity_absorption_filter(self, df):
        """
        MT5 Spot FX Volume is Relative Tick Activity.
        Blocks setups if there is zero activity or extreme blow-off volume.
        """
        v_latest = df['tick_volume'].iloc[-1]
        v_avg = df['tick_volume'].rolling(20).mean().iloc[-1]
        if v_latest == 0: return False
        # Relaxed filter for low-activity sessions: allow if > 0.3x avg
        if v_latest < v_avg * 0.3 or v_latest > v_avg * 4.0:
            return False
        return True

    def _sweep_reclaim_reversal(self, df, bias):
        """Family 1: Stop-hunts that take liquidity and reclaim structure."""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        # Look for a sweep in the last 3 candles
        recent = df.iloc[-3:]
        
        # BUY Setup (Bearish Sweep Reversal)
        if bias == 1 and (recent['sweep'] == 1).any():
            # 1. Immediate Entry (Touch Reclaim)
            if latest['close'] > latest['open']:
                return "BUY", "Sweep Reclaim Reversal", {"ent": "Immediate (Touch Reclaim)", "conf": "High"}
            # 2. Confirmation Entry (Wait for next bullish)
            if prev['close'] > prev['open'] and latest['close'] > prev['high']:
                return "BUY", "Sweep Reclaim Reversal", {"ent": "Confirmation Candle", "conf": "Ultra"}

        # SELL Setup (Bullish Sweep Reversal)
        if bias == -1 and (recent['sweep'] == -1).any():
            if latest['close'] < latest['open']:
                return "SELL", "Sweep Reclaim Reversal", {"ent": "Immediate (Touch Reclaim)", "conf": "High"}
            if prev['close'] < prev['open'] and latest['close'] < prev['low']:
                return "SELL", "Sweep Reclaim Reversal", {"ent": "Confirmation Candle", "conf": "Ultra"}

        return "WAIT", "", {}

    def _continuation_retest(self, df, bias):
        """Family 3: Continuation retest after BOS (Trend Following)."""
        latest = df.iloc[-1]
        recent_bos = df.iloc[-15:]
        
        if bias == 1 and (recent_bos['bos'] == 1).any():
            # 1. Immediate (Touch)
            if latest['order_block'] == 1:
                return "BUY", "Continuation Retest", {"ent": "Immediate (OB Touch)", "conf": "High"}
            # 2. Confirmation
            if self._is_bullish_confirmation(latest) and latest['close'] > latest['open']:
                 return "BUY", "Continuation Retest", {"ent": "Confirmation (OB Rejection)", "conf": "Ultra"}
        
        if bias == -1 and (recent_bos['bos'] == -1).any():
            if latest['order_block'] == -1:
                return "SELL", "Continuation Retest", {"ent": "Immediate (OB Touch)", "conf": "High"}
            if self._is_bearish_confirmation(latest) and latest['close'] < latest['open']:
                 return "SELL", "Continuation Retest", {"ent": "Confirmation (OB Rejection)", "conf": "Ultra"}
        return "WAIT", "", {}

    def _first_touch_mitigation(self, df, bias):
        """Family 4: First touch of unmitigated FVG boundary."""
        latest = df.iloc[-1]
        
        if bias == 1 and latest['fvg_bullish'] and not latest['fvg_mitigated']:
            # 1. Immediate (Touch)
            if latest['low'] <= latest['fvg_bottom']:
                return "BUY", "First Touch Mitigation", {"ent": "Immediate (FVG Touch)"}
            # 2. Partial Pullback (Mid-zone)
            fvg_mid = (latest['fvg_top'] + latest['fvg_bottom']) / 2
            if latest['low'] <= fvg_mid:
                 return "BUY", "First Touch Mitigation", {"ent": "Partial Pullback (Mid-FVG)"}

        if bias == -1 and latest['fvg_bearish'] and not latest['fvg_mitigated']:
            if latest['high'] >= latest['fvg_top']:
                return "SELL", "First Touch Mitigation", {"ent": "Immediate (FVG Touch)"}
            fvg_mid = (latest['fvg_top'] + latest['fvg_bottom']) / 2
            if latest['high'] >= fvg_mid:
                 return "SELL", "First Touch Mitigation", {"ent": "Partial Pullback (Mid-FVG)"}
        return "WAIT", "", {}

    def _exhaustion_reversal(self, df, bias):
        """Family 5: Low Frequency Parabolic Exhaustion + CHOCH break."""
        latest = df.iloc[-1]
        recent = df.iloc[-10:] # Stable lookback
        
        # 1. Volume Exhaustion (VSA Principle: Is institutional activity dying?)
        vol_mean = recent['tick_volume'].mean()
        vol_declining = latest['tick_volume'] < vol_mean
        
        if vol_declining:
            # 2. Institutional CHOCH Break (Must break local range, not just 1 candle)
            local_high = recent['high'].iloc[-6:-1].max()
            local_low = recent['low'].iloc[-6:-1].min()

            # BUY Setup: Parabolic move down ends -> Institutional range break bullish
            if latest['close'] > local_high:
                 return "BUY", "Exhaustion Reversal", {
                     "ent": "CHOCH Break", 
                     "vsa": "No Supply detected",
                     "conf": "Volume Exhaustion"
                 }
            # SELL Setup: Parabolic move up ends -> Institutional range break bearish
            if latest['close'] < local_low:
                 return "SELL", "Exhaustion Reversal", {
                     "ent": "CHOCH Break", 
                     "vsa": "No Demand detected",
                     "conf": "Volume Exhaustion"
                 }

        return "WAIT", "", {}

    def _is_bullish_confirmation(self, row):
        """Identify bullish rejection (Pin bar, engulfing, or strong close)."""
        body = row['close'] - row['open']
        lower_wick = min(row['close'], row['open']) - row['low']
        return body > 0 or lower_wick > body

    def _is_bearish_confirmation(self, row):
        """Identify bearish rejection."""
        body = row['open'] - row['close']
        upper_wick = row['high'] - max(row['close'], row['open'])
        return body > 0 or upper_wick > body

    def _get_confluence_score(self, df, signal):
        """
        Macro Confluence Score (MCS) - Sticky Memory Layer.
        Now looks back 20 bars so it doesn't 'forget' BOS/Sweeps during pullbacks.
        """
        score = 0
        recent = df.tail(20)
        
        if (recent['sweep'] != 0).any(): score += 1
        if (recent['bos'] != 0).any(): score += 1
        if (recent['fvg_bullish'] | recent['fvg_bearish']).any(): score += 1
        if (recent['order_block'] != 0).any(): score += 1
        if (recent['demand_zone'] | recent['supply_zone']).any(): score += 1
        
        # 1. Relative activity check (last 3 candles to catch momentum)
        v_latest = df['tick_volume'].tail(3).max()
        v_avg = df['tick_volume'].rolling(20).mean().iloc[-1]
        if v_latest > v_avg * 1.5: score += 1

        # 2. Session Killzone Boost
        if self._is_in_killzone():
            score += 1

        # 3. Psychological Round Level Confluence
        price = df['close'].iloc[-1]
        if self._is_near_round_level(price):
            score += 1
        
        return score

    def _is_in_killzone(self):
        """ Institutional Killzones (London/NY) - UTC Time """
        now_utc = datetime.datetime.now(datetime.timezone.utc).time()
        # London Open: 08:00 - 11:00 UTC
        # NY Open: 13:00 - 16:00 UTC
        london_start, london_end = datetime.time(8, 0), datetime.time(11, 0)
        ny_start, ny_end = datetime.time(13, 0), datetime.time(16, 0)
        
        is_london = london_start <= now_utc <= london_end
        is_ny = ny_start <= now_utc <= ny_end
        return is_london or is_ny

    def _is_near_round_level(self, price):
        """ 00 and 50 Psychological Magnets """
        # For GOLD/Forex (e.g. 1.08000, 2150.00)
        # Check if price is within 5-10 pips of a .00 or .50 level
        p00 = round(price) 
        p50 = round(price * 2) / 2
        
        dist00 = abs(price - p00)
        dist50 = abs(price - p50)
        
        # 0.1 for Gold (~10 pips), 0.0005 for FX
        threshold = 0.5 if price > 500 else 0.0005 
        return dist00 < threshold or dist50 < threshold

    def _finalize(self, signal, name, details, df):
        """Final gate: confluence scoring and activity filter."""
        price = df['close'].iloc[-1]
        
        # Gate A: Relative Activity Filter
        if not self._relative_activity_absorption_filter(df):
            return "WAIT", price, f"Filter Blocked: Invalid Relative Activity Level", {}
            
        # Gate B: Confluence Scoring
        score = self._get_confluence_score(df, signal)
        details['mcs_score'] = score
        
        # We only take the trade if score >= 2 (Institutional Quality)
        if score < 2:
            return "WAIT", price, f"Qualify Fail: MCS Score ({score}) below threshold (2)", {}
            
        return signal, price, name, details

    def _get_bias(self, df, label): # Legacy wrapper for compatibility if needed
        res = self._get_macro_bias(df)
        return "BULLISH" if res == 1 else ("BEARISH" if res == -1 else "WAIT")
