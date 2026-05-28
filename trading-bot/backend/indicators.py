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
    def detect_bos_choch(df, swing_len=5, lookback=None):
        """Optimized BOS Detection: Scans the specified window or full dataframe."""
        df = df.copy()
        n = len(df)
        if lookback is None: lookback = n
        start_idx = max(swing_len, n - lookback)
        
        for col in ['bos', 'choch', 'swing_high', 'swing_low']:
            if col not in df.columns: df[col] = False if 'swing' in col else 0

        highs = df['high'].to_numpy()
        lows = df['low'].to_numpy()
        closes = df['close'].to_numpy()
        
        # Causal swing detection: swing at i-swing_len confirmed at index i
        for i in range(start_idx, n):
            # Check if i-swing_len was a high/low in the window [i-2*swing_len, i]
            idx = i - swing_len
            if idx < swing_len: continue
            
            window_h = highs[idx - swing_len : i + 1]
            window_l = lows[idx - swing_len : i + 1]
            
            if highs[idx] == window_h.max():
                df.at[df.index[idx], 'swing_high'] = True
            if lows[idx] == window_l.min():
                df.at[df.index[idx], 'swing_low'] = True

        # Sequential BOS detection (Rolling)
        # To avoid O(N^2), we keep track of the last confirmed swing
        last_h = np.nan
        last_l = np.nan
        
        # We need a first pass to find initial swings if not bulk
        initial_h = df[df['swing_high']].iloc[:start_idx]
        initial_l = df[df['swing_low']].iloc[:start_idx]
        if not initial_h.empty: last_h = initial_h.high.iloc[-1]
        if not initial_l.empty: last_l = initial_l.low.iloc[-1]

        for i in range(start_idx, n):
            # Update last swings if a new one was confirmed at this bar i (it happened at i-swing_len)
            conf_idx = i - swing_len
            if conf_idx >= 0:
                if df.at[df.index[conf_idx], 'swing_high']:
                    last_h = highs[conf_idx]
                if df.at[df.index[conf_idx], 'swing_low']:
                    last_l = lows[conf_idx]
            
            if not np.isnan(last_h) and closes[i] > last_h:
                df.at[df.index[i], 'bos'] = 1
            elif not np.isnan(last_l) and closes[i] < last_l:
                df.at[df.index[i], 'bos'] = -1
        return df

    @staticmethod
    def detect_fvg(df, lookback=None):
        """Optimized FVG Detection (Vectorized-ish)."""
        df = df.copy()
        n = len(df)
        if lookback is None: lookback = n
        start_idx = max(2, n - lookback)
        
        for col in ['fvg_bullish', 'fvg_bearish', 'fvg_mitigated']:
            if col not in df.columns: df[col] = False
        for col in ['fvg_top', 'fvg_bottom']:
            if col not in df.columns: df[col] = 0.0
        
        highs, lows = df['high'].to_numpy(), df['low'].to_numpy()
        avg_range = (df['high'] - df['low']).rolling(20).mean().to_numpy()

        for i in range(start_idx, n):
            # Bullish FVG (Gap between candle i-2 high and candle i low)
            if lows[i] > highs[i-2]:
                if (highs[i-1] - lows[i-1]) > avg_range[i-1] * 1.5:
                    df.at[df.index[i-1], 'fvg_bullish'] = True
                    df.at[df.index[i-1], 'fvg_bottom'] = highs[i-2]
                    df.at[df.index[i-1], 'fvg_top'] = lows[i]
            # Bearish FVG (Gap between candle i-2 low and candle i high)
            elif highs[i] < lows[i-2]:
                if (highs[i-1] - lows[i-1]) > avg_range[i-1] * 1.5:
                    df.at[df.index[i-1], 'fvg_bearish'] = True
                    df.at[df.index[i-1], 'fvg_bottom'] = highs[i]
                    df.at[df.index[i-1], 'fvg_top'] = lows[i-2]
        return df

    @staticmethod
    def detect_liquidity_sweeps(df, lookback=50):
        """Detect sweeps of recent highs/lows (Vectorized)."""
        df = df.copy()
        df['sweep'] = 0
        highs, lows, closes = df['high'].to_numpy(), df['low'].to_numpy(), df['close'].to_numpy()
        
        # Use rolling max/min for efficiency
        rolling_h = df['high'].shift(1).rolling(lookback).max().to_numpy()
        rolling_l = df['low'].shift(1).rolling(lookback).min().to_numpy()
        
        bull_sweep = (lows < rolling_l) & (closes > rolling_l)
        bear_sweep = (highs > rolling_h) & (closes < rolling_h)
        
        df.loc[bull_sweep, 'sweep'] = 1
        df.loc[bear_sweep, 'sweep'] = -1
        return df

    @staticmethod
    def detect_order_blocks(df, lookback=None):
        """Detect fresh Order Blocks (Vectorized)."""
        df = df.copy()
        n = len(df)
        if lookback is None: lookback = n
        
        df['order_block'] = 0
        atr = SMCIndicators.calculate_atr(df).to_numpy()
        closes, opens = df['close'].to_numpy(), df['open'].to_numpy()
        
        # OB is the candle before an impulsive move
        impulse = closes - opens
        is_impulse = np.abs(impulse) > atr * 2.0
        
        # Shift back: if candle i is impulse, candle i-1 is the OB
        df.loc[np.roll(is_impulse, -1) & (impulse[np.minimum(n-1, np.arange(n)+1)] > 0), 'order_block'] = 1
        df.loc[np.roll(is_impulse, -1) & (impulse[np.minimum(n-1, np.arange(n)+1)] < 0), 'order_block'] = -1
        # Clear the last row since we can't know if next is impulse
        df.at[df.index[-1], 'order_block'] = 0
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
    def detect_mss(df, lookback=None):
        """Market Structure Shift (MSS) with rolling confirmation."""
        df = df.copy()
        n = len(df)
        if lookback is None: lookback = n
        df['mss'] = 0
        if 'swing_high' not in df.columns: df = SMCIndicators.detect_bos_choch(df)
        
        highs = df['high'].to_numpy()
        lows = df['low'].to_numpy()
        closes = df['close'].to_numpy()
        
        # Use ffill to get last confirmed swing at each point
        df['last_sh_val'] = df['high'].where(df['swing_high']).ffill()
        df['last_sl_val'] = df['low'].where(df['swing_low']).ffill()
        
        df.loc[closes > df['last_sh_val'].shift(1), 'mss'] = 1
        df.loc[closes < df['last_sl_val'].shift(1), 'mss'] = -1
        
        df.drop(columns=['last_sh_val', 'last_sl_val'], inplace=True)
        return df

    @staticmethod
    def detect_breaker_blocks(df, lookback=None):
        """Detects Breaker Blocks (Vectorized)."""
        df = df.copy()
        if 'order_block' not in df.columns: df = SMCIndicators.detect_order_blocks(df)
        
        df['breaker_block'] = 0
        # This is harder to fully vectorize because it depends on first break after OB creation.
        # But we can approximate or use a faster loop.
        obs = df[df['order_block'] != 0].index
        closes = df['close'].to_numpy()
        highs = df['high'].to_numpy()
        lows = df['low'].to_numpy()
        
        for idx in obs:
            ob_val = df.at[idx, 'order_block']
            ob_idx = df.index.get_loc(idx)
            
            if ob_val == 1: # Bullish OB
                ob_low = df.at[idx, 'low']
                # Find first close below ob_low after this idx
                broken = np.where(closes[ob_idx:] < ob_low)[0]
                if len(broken) > 0:
                    df.at[df.index[ob_idx + broken[0]], 'breaker_block'] = -1
            else: # Bearish OB
                ob_high = df.at[idx, 'high']
                # Find first close above ob_high after this idx
                broken = np.where(closes[ob_idx:] > ob_high)[0]
                if len(broken) > 0:
                    df.at[df.index[ob_idx + broken[0]], 'breaker_block'] = 1
        return df

    @staticmethod
    def detect_volume_profile(df, lookback=100):
        """Rolling POC calculation (Approximated for speed)."""
        df = df.copy()
        n = len(df)
        df['poc'] = 0.0
        v_col = 'tick_volume' if 'tick_volume' in df.columns else 'real_volume'
        if v_col not in df.columns or n < lookback: return df

        closes = df['close'].to_numpy()
        volumes = df[v_col].to_numpy()
        lows = df['low'].to_numpy()
        highs = df['high'].to_numpy()
        
        # True rolling POC is expensive. For backtest speed, we'll calculate it every 10 bars
        # and ffill.
        for i in range(lookback, n, 10): 
            window_low = lows[i-lookback:i].min()
            window_high = highs[i-lookback:i].max()
            if window_high == window_low: continue
            
            bins = 20
            bin_width = (window_high - window_low) / bins
            v_bins = np.zeros(bins)
            
            w_closes = closes[i-lookback:i]
            w_vols = volumes[i-lookback:i]
            
            # Vectorized binning for the window
            bin_indices = np.minimum(bins - 1, ((w_closes - window_low) / bin_width).astype(int))
            np.add.at(v_bins, bin_indices, w_vols)
            
            poc_idx = np.argmax(v_bins)
            df.at[df.index[i], 'poc'] = window_low + (poc_idx + 0.5) * bin_width
            
        df['poc'] = df['poc'].replace(0, np.nan).ffill().fillna(0)
        return df

    @staticmethod
    def calculate_bollinger_bands(series, period=20, num_std=2):
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band

    @staticmethod
    def calculate_adx(df, period=14):
        """Standard Average Directional Index (ADX) implementation."""
        if len(df) < period * 2:
            return pd.Series([0.0] * len(df), index=df.index)
            
        high, low, close = df['high'], df['low'], df['close']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        plus_dm[plus_dm < minus_dm] = 0
        minus_dm[minus_dm < 0] = 0
        minus_dm[minus_dm < plus_dm] = 0
        
        tr = np.maximum(high - low, 
             np.maximum(np.abs(high - close.shift(1)), 
                        np.abs(low - close.shift(1))))
        
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()
        return adx

