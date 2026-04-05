import pandas as pd
import numpy as np
from datetime import datetime, timezone

class SMCIndicators:
    @staticmethod
    def calculate_atr(df, period=14):
        if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
            return pd.Series([0.0] * len(df), index=df.index)
        high_low = df['high'] - df['low']
        high_cp = np.abs(df['high'] - df['close'].shift())
        low_cp = np.abs(df['low'] - df['close'].shift())
        df_tr = pd.concat([high_low, high_cp, low_cp], axis=1)
        true_range = np.max(df_tr, axis=1)
        return true_range.rolling(period).mean()

    @staticmethod
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def detect_bos_choch(df, swing_len=5, lookback=250):
        """Optimized BOS Detection: Only scans the 'lookback' window."""
        df = df.copy()
        start_idx = max(0, len(df) - lookback)
        for col in ['bos', 'choch', 'swing_high', 'swing_low']:
            if col not in df.columns: df[col] = False if 'swing' in col else 0

        # Vectorized swing detection
        highs = df['high'].to_numpy()
        lows = df['low'].to_numpy()
        
        for i in range(max(swing_len, start_idx), len(df) - swing_len):
            if highs[i] == highs[i-swing_len : i+swing_len+1].max():
                df.at[df.index[i], 'swing_high'] = True
            if lows[i] == lows[i-swing_len : i+swing_len+1].min():
                df.at[df.index[i], 'swing_low'] = True

        # Sequential BOS detection (only tail)
        last_h = df[df['swing_high']].tail(1).high.iloc[0] if not df[df['swing_high']].empty else np.nan
        last_l = df[df['swing_low']].tail(1).low.iloc[0] if not df[df['swing_low']].empty else np.nan
        
        if np.isnan(last_h) or np.isnan(last_l): return df

        closes = df['close'].to_numpy()
        for i in range(start_idx, len(df)):
            if closes[i] > last_h: df.at[df.index[i], 'bos'] = 1
            elif closes[i] < last_l: df.at[df.index[i], 'bos'] = -1
        return df

    @staticmethod
    def detect_fvg(df, lookback=300):
        """Optimized FVG Detection."""
        df = df.copy()
        # Ensure all required FVG columns exist
        for col in ['fvg_bullish', 'fvg_bearish', 'fvg_mitigated']:
            if col not in df.columns: df[col] = False
        for col in ['fvg_top', 'fvg_bottom']:
            if col not in df.columns: df[col] = 0.0
        
        avg_range = (df['high'] - df['low']).rolling(20).mean()
        start_idx = max(2, len(df) - lookback)
        highs, lows = df['high'].to_numpy(), df['low'].to_numpy()

        for i in range(start_idx, len(df)):
            if df.at[df.index[i-1], 'fvg_bullish'] or df.at[df.index[i-1], 'fvg_bearish']: continue
            if (highs[i-1] - lows[i-1]) < avg_range.iloc[i-1] * 1.5: continue
            
            # Bullish FVG (Gap between candle i-2 high and candle i low)
            if lows[i] > highs[i-2]: 
                df.at[df.index[i-1], 'fvg_bullish'] = True
                df.at[df.index[i-1], 'fvg_bottom'] = highs[i-2]
                df.at[df.index[i-1], 'fvg_top'] = lows[i]
            # Bearish FVG (Gap between candle i-2 low and candle i high)
            elif highs[i] < lows[i-2]: 
                df.at[df.index[i-1], 'fvg_bearish'] = True
                df.at[df.index[i-1], 'fvg_bottom'] = highs[i]
                df.at[df.index[i-1], 'fvg_top'] = lows[i-2]
        return df

    @staticmethod
    def detect_liquidity_sweeps(df, lookback=50):
        """Detect sweeps of recent highs/lows."""
        df = df.copy()
        df['sweep'] = 0
        highs, lows, closes = df['high'].to_numpy(), df['low'].to_numpy(), df['close'].to_numpy()
        
        for i in range(max(lookback, len(df)-200), len(df)):
            window_h = highs[i-lookback:i].max()
            window_l = lows[i-lookback:i].min()
            if lows[i] < window_l and closes[i] > window_l: df.at[df.index[i], 'sweep'] = 1
            elif highs[i] > window_h and closes[i] < window_h: df.at[df.index[i], 'sweep'] = -1
        return df

    @staticmethod
    def detect_order_blocks(df, lookback=500):
        """Detect fresh Order Blocks."""
        df = df.copy()
        df['order_block'] = 0
        atr = SMCIndicators.calculate_atr(df)
        closes, opens = df['close'].to_numpy(), df['open'].to_numpy()
        
        for i in range(max(1, len(df)-lookback), len(df)-1):
            impulse = closes[i+1] - opens[i+1]
            if abs(impulse) > atr.iloc[i] * 2.0:
                df.at[df.index[i], 'order_block'] = 1 if impulse > 0 else -1
        return df

    @staticmethod
    def detect_supply_demand(df):
        df = df.copy()
        if 'supply_zone' not in df.columns: df['supply_zone'] = False
        if 'demand_zone' not in df.columns: df['demand_zone'] = False
        return df

    @staticmethod
    def detect_vsa(df):
        df = df.copy()
        v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
        if v_col in df.columns:
            v_avg = df[v_col].rolling(20).mean()
            df['vsa_vol_spike'] = df[v_col] > v_avg * 2.0
        return df

    @staticmethod
    def detect_mss(df, lookback=100):
        """
        Market Structure Shift (MSS) is essentially a CHOCH on lower TFs 
        that signals a reversal after a displacement.
        """
        df = df.copy()
        df['mss'] = 0
        if 'swing_high' not in df.columns: df = SMCIndicators.detect_bos_choch(df)
        
        highs = df['high'].to_numpy()
        lows = df['low'].to_numpy()
        closes = df['close'].to_numpy()
        
        for i in range(max(5, len(df)-lookback), len(df)):
            # Look for recent swing breaks
            last_sh = df[df['swing_high']].iloc[:i].tail(1)
            last_sl = df[df['swing_low']].iloc[:i].tail(1)
            
            if not last_sh.empty and closes[i] > last_sh.high.iloc[0]:
                df.at[df.index[i], 'mss'] = 1
            elif not last_sl.empty and closes[i] < last_sl.low.iloc[0]:
                df.at[df.index[i], 'mss'] = -1
        return df

    @staticmethod
    def detect_breaker_blocks(df, lookback=300):
        """
        Detects Breaker Blocks (failed Order Blocks that turned into S/R).
        """
        df = df.copy()
        df['breaker_block'] = 0
        if 'order_block' not in df.columns: df = SMCIndicators.detect_order_blocks(df)
        
        obs = df[df['order_block'] != 0].copy()
        closes = df['close'].to_numpy()
        
        for idx, row in obs.iterrows():
            ob_val = row['order_block']
            # Find when this OB was broken
            future_df = df.loc[idx:]
            if ob_val == 1: # Bullish OB
                broken = future_df[future_df['close'] < row['low']]
                if not broken.empty:
                    df.at[broken.index[0], 'breaker_block'] = -1 # Now a Bearish Breaker
            else: # Bearish OB
                broken = future_df[future_df['close'] > row['high']]
                if not broken.empty:
                    df.at[broken.index[0], 'breaker_block'] = 1 # Now a Bullish Breaker
        return df

    @staticmethod
    def detect_volume_profile(df, lookback=100):
        """Simple VPC (Volume POC) within lookback."""
        df = df.copy()
        if len(df) < lookback: return df
        df['poc'] = 0.0
        
        # Simple implementation: price bin with max volume
        v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
        if v_col not in df.columns: return df
        
        recent = df.tail(lookback)
        bins = 20
        price_min, price_max = recent['low'].min(), recent['high'].max()
        if price_max == price_min: return df
        
        bin_width = (price_max - price_min) / bins
        volume_bins = np.zeros(bins)
        
        for _, row in recent.iterrows():
            idx = int(min(bins - 1, (row['close'] - price_min) / bin_width))
            volume_bins[idx] += row[v_col]
            
        poc_idx = np.argmax(volume_bins)
        poc_price = price_min + (poc_idx + 0.5) * bin_width
        df.at[df.index[-1], 'poc'] = poc_price
        return df
