import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.core.datatypes import StrategyContext
from app.strategy.context.session import SessionManager
from app.strategy.context.regime import RegimeDetector

class ContextEvaluator:
    """Institutional Market State Engine (Bias, Regime, Session)."""
    
    def __init__(self):
        self.session_manager = SessionManager({})
        self.regime_detector = RegimeDetector()

    def evaluate(self, df_m1: pd.DataFrame, df_m5: pd.DataFrame, df_m15: pd.DataFrame, symbol: str) -> StrategyContext:
        """
        Builds the StrategyContext required for decision making.
        Handles MTF Bias and Alignment.
        """
        m15_bias = self._calculate_macro_bias(df_m15)
        m5_align = self._calculate_m5_alignment(df_m5, m15_bias)
        sessions = self.session_manager.get_current_session()
        regime_res = self.regime_detector.identify(df_m15)
        
        # Tradability Filter
        is_tradable = self._check_tradability(sessions, df_m1)
        
        return StrategyContext(
            symbol=symbol,
            timeframe="M1",
            m15_bias=m15_bias,
            m5_alignment=m5_align,
            session=", ".join(sessions),
            regime=regime_res.regime.name if hasattr(regime_res.regime, "name") else str(regime_res.regime),
            is_tradable=is_tradable,
            spread_v_atr=self._calculate_spread_ratio(df_m1),
            current_tick=df_m1.iloc[-1].to_dict()
        )

    def _calculate_macro_bias(self, df: pd.DataFrame) -> int:
        """EMA 50 + Peak/Trough structure logic."""
        if len(df) < 50: return 0
        ema50 = df['close'].rolling(50).mean().iloc[-1]
        price = df['close'].iloc[-1]
        if price > ema50: return 1
        if price < ema50: return -1
        return 0

    def _calculate_m5_alignment(self, df: pd.DataFrame, m15_bias: int) -> int:
        """Checks if M5 is already trending with M15."""
        if len(df) < 20: return 0
        ema20 = df['close'].rolling(20).mean().iloc[-1]
        price = df['close'].iloc[-1]
        if m15_bias == 1 and price > ema20: return 1
        if m15_bias == -1 and price < ema20: return -1
        return 0

    def _check_tradability(self, sessions: List[str], df_m1: pd.DataFrame) -> bool:
        """Is spread low? Is volume sufficient? Is session dead?"""
        # Reject DEAD_ZONE if not overriding
        if "DEAD_ZONE" in sessions: return False
        
        # Check spread ratio
        ratio = self._calculate_spread_ratio(df_m1)
        if ratio > 0.8: return False # Spread is too high compared to ATR
        
        return True

    def _calculate_spread_ratio(self, df_m1: pd.DataFrame) -> float:
        """Spread / ATR ratio."""
        if len(df_m1) < 20: return 0.5
        # Calculate ATR on M1
        df = df_m1.copy()
        df['tr'] = np.maximum(df['high'] - df['low'], 
                     np.maximum(abs(df['high'] - df['close'].shift()), 
                                 abs(df['low'] - df['close'].shift())))
        atr = df['tr'].rolling(14).mean().iloc[-1]
        
        # Approximate spread from tick if possible, else use ATR factor
        latest = df_m1.iloc[-1]
        if 'ask' in latest and 'bid' in latest:
            spread = latest['ask'] - latest['bid']
            return spread / atr if atr > 0 else 0.5
            
        return 0.2 # Default safe ratio
