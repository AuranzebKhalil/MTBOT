import pandas as pd
import numpy as np

class MeanDeviationLoopStrategy:
    """
    Mean Deviation Loop | Lyro RS
    Implementation of the Pine Script indicator for generating buy/sell signals.
    """
    
    @staticmethod
    def calc_ema(series, length):
        return series.ewm(span=length, adjust=False).mean()
        
    @staticmethod
    def calc_alma(series, window, offset=0.0, sigma=20.0):
        if len(series) < window: 
            return pd.Series(np.nan, index=series.index)
        m = offset * (window - 1)
        s = window / sigma
        weights = np.exp(-((np.arange(window) - m) ** 2) / (2 * s ** 2))
        weights /= weights.sum()
        return series.rolling(window).apply(lambda x: np.dot(x, weights), raw=True)

    @staticmethod
    def calc_mad(src_series, bench_series, length):
        src = src_series.to_numpy()
        bench = bench_series.to_numpy()
        out = np.full_like(src, np.nan)
        if len(src) < length:
            return pd.Series(out, index=src_series.index)
            
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(src, window_shape=length)
        bench_aligned = bench[length-1:].reshape(-1, 1)
        
        mads = np.mean(np.abs(windows - bench_aligned), axis=1)
        out[length-1:] = mads
        return pd.Series(out, index=src_series.index)

    @staticmethod
    def calc_system(src_series, a, b):
        total = pd.Series(0.0, index=src_series.index)
        for i in range(a, b + 1):
            diff = src_series - src_series.shift(i)
            val = pd.Series(-1, index=src_series.index)
            val[diff > 0] = 1
            total += val
        return total

    @staticmethod
    def crossover(s1, s2):
        if isinstance(s2, (int, float)):
            return (s1 > s2) & (s1.shift(1) <= s2)
        return (s1 > s2) & (s1.shift(1) <= s2.shift(1))

    @staticmethod
    def crossunder(s1, s2):
        if isinstance(s2, (int, float)):
            return (s1 < s2) & (s1.shift(1) >= s2)
        return (s1 < s2) & (s1.shift(1) >= s2.shift(1))

    @classmethod
    def apply_indicator(cls, df, signal_mode="Bollinger Bands"):
        """
        signal_mode options: "Bollinger Bands", "For Loop", "Combined Signal"
        Returns the dataframe with new boolean columns `buy_signal` and `sell_signal`
        """
        if df.empty:
            return df
            
        df = df.copy()
        
        source = df['close'] if 'close' in df.columns else df
        
        # --- Parameters ---
        # BB
        mad_length_bb = 25
        mad_multp = 1.4
        mad_multn = 1.0
        
        # For Loop
        mad_length_fl = 10
        a_ = 10
        b_ = 60
        Threshold_L_Fl = 23
        Threshold_S_Fl = 3
        
        # Combined
        Threshold_L_C = 0.0
        Threshold_S_C = 0.0
        
        # --- Calculation ---
        avg_bb = cls.calc_ema(source, mad_length_bb)
        avg_fl = cls.calc_alma(source, mad_length_fl, offset=0.0, sigma=20.0)
        
        mad_value = cls.calc_mad(source, avg_bb, mad_length_bb)
        mad2 = cls.calc_mad(source, avg_fl, mad_length_fl)
        
        # BB bands
        bb_positive_band = avg_bb + (mad_value * mad_multp)
        bb_negative_band = avg_bb - (mad_value * mad_multn)
        
        # For Loop
        source_x_mad2 = source * mad2
        ma_num = cls.calc_alma(source_x_mad2, mad_length_fl, offset=0.0, sigma=20.0)
        ma_den = cls.calc_alma(mad2, mad_length_fl, offset=0.0, sigma=20.0)
        mad_w_src = ma_num / ma_den
        
        mad_fl = cls.calc_system(mad_w_src, a_, b_)
        
        # Conditions 
        bb_co = cls.crossover(source, bb_positive_band)
        bb_cu = cls.crossunder(source, bb_negative_band)
        
        fl_co = cls.crossover(mad_fl, Threshold_L_Fl)
        fl_cu = cls.crossunder(mad_fl, Threshold_S_Fl)
        
        # Simulate persistent state iteratively
        bb_score_arr = np.zeros(len(df))
        fl_score_arr = np.zeros(len(df))
        
        curr_bb_score = 0
        curr_fl_score = 0
        
        bb_co_arr = bb_co.to_numpy()
        bb_cu_arr = bb_cu.to_numpy()
        fl_co_arr = fl_co.to_numpy()
        fl_cu_arr = fl_cu.to_numpy()
        
        for i in range(len(df)):
            if bb_co_arr[i]: curr_bb_score = 1
            if bb_cu_arr[i]: curr_bb_score = -1
            bb_score_arr[i] = curr_bb_score
            
            if fl_co_arr[i]: curr_fl_score = 1
            if fl_cu_arr[i]: curr_fl_score = -1
            fl_score_arr[i] = curr_fl_score
            
        bb_score_series = pd.Series(bb_score_arr, index=source.index)
        fl_score_series = pd.Series(fl_score_arr, index=source.index)
        
        # Combined
        c_signal_series = (bb_score_series + fl_score_series) / 2.0
        
        cb_co = cls.crossover(c_signal_series, Threshold_L_C)
        cb_cu = cls.crossunder(c_signal_series, Threshold_S_C)
        
        cb_score_arr = np.zeros(len(df))
        curr_cb_score = 0
        cb_co_arr = cb_co.to_numpy()
        cb_cu_arr = cb_cu.to_numpy()
        
        for i in range(len(df)):
            if cb_co_arr[i]: curr_cb_score = 1
            if cb_cu_arr[i]: curr_cb_score = -1
            cb_score_arr[i] = curr_cb_score
            
        # Final Score logic
        if signal_mode == "Bollinger Bands":
            final_scores = bb_score_arr
        elif signal_mode == "For Loop":
            final_scores = fl_score_arr
        else: # Combined Signal
            final_scores = cb_score_arr
            
        final_scores_series = pd.Series(final_scores, index=source.index)
        
        # Trigger buy/sell when score transitions to 1 or -1
        buy_signal = (final_scores_series == 1) & (final_scores_series.shift(1) != 1)
        sell_signal = (final_scores_series == -1) & (final_scores_series.shift(1) != -1)
        
        df['mad_score'] = final_scores_series
        df['buy_signal'] = buy_signal
        df['sell_signal'] = sell_signal
        
        return df
