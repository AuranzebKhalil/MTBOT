import pandas as pd
import logging
from datetime import datetime
from data_layer.mt5_connector import MT5Connector

logger = logging.getLogger(__name__)

class DataCollector:
    """
    Higher-level data orchestrator that uses MT5Connector to aggregate 
    Multi-Timeframe (MTF) bars, execution logs, and trade outcomes 
    to feed into the Feature Engine and Training Pipeline.
    """
    def __init__(self, mt5_connector: MT5Connector):
        self.mt5 = mt5_connector

    def fetch_live_bars(self, symbol: str, count: int = 500) -> dict:
        """
        Fetches M1, M5, and M15 bars for live and historical processing.
        Returns a dictionary of DataFrames.
        """
        data = {
            "M1": self.mt5.get_market_data(symbol, "M1", count),
            "M5": self.mt5.get_market_data(symbol, "M5", count),
            "M15": self.mt5.get_market_data(symbol, "M15", count)
        }
        
        if any(df is None or df.empty for df in data.values()):
            logger.error(f"Failed to fetch complete MTF data for {symbol}")
            return None
            
        return data

    def fetch_execution_environment(self, symbol: str) -> dict:
        """
        Fetches live execution parameters: spread, tick volume, and depth.
        Important for the Execution-Risk model.
        """
        import MetaTrader5 as mt5
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        
        if not tick or not info:
            return None
            
        spread_points = info.spread
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": spread_points,
            "tick_volume": tick.volume,
            "digits": info.digits
        }

    def fetch_trade_history(self, days: int = 30) -> list:
        """
        Fetches historical trades, finding their entry/exit prices, spreads (if available),
        slippage, and net results. This feeds the Label Engine.
        """
        return self.mt5.get_history_deals(days=days)

