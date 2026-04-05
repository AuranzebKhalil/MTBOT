import pandas as pd
import numpy as np

class PerformanceAnalytics:
    """
    Calculates institutional performance metrics for model promotion and dashboard.
    """
    
    @staticmethod
    def calculate_expectancy(trades: list) -> float:
        """
        Expectancy = (Win% * Avg Win) - (Loss% * Avg Loss)
        """
        if not trades: return 0.0
        
        df = pd.DataFrame(trades)
        if 'profit' not in df.columns: return 0.0
        
        wins = df[df['profit'] > 0]['profit']
        losses = df[df['profit'] <= 0]['profit']
        
        win_rate = len(wins) / len(df)
        avg_win = wins.mean() if not wins.empty else 0
        avg_loss = abs(losses.mean()) if not losses.empty else 0
        
        return round((win_rate * avg_win) - ((1 - win_rate) * avg_loss), 2)

    @staticmethod
    def calculate_profit_factor(trades: list) -> float:
        """
        Profit Factor = Total Gross Profit / Total Gross Loss
        """
        if not trades: return 0.0
        
        df = pd.DataFrame(trades)
        gross_profit = df[df['profit'] > 0]['profit'].sum()
        gross_loss = abs(df[df['profit'] < 0]['profit'].sum())
        
        if gross_loss == 0: return round(gross_profit, 2)
        return round(gross_profit / gross_loss, 2)

    @staticmethod
    def calculate_max_drawdown(balance_history: list) -> float:
        if not balance_history: return 0.0
        
        bh = pd.Series(balance_history)
        rolling_max = bh.cummax()
        drawdown = (bh - rolling_max) / rolling_max
        return round(abs(drawdown.min()), 4) * 100 # %
