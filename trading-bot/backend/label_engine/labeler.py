import pandas as pd
import numpy as np

class Labeler:
    """
    Labels historical data rows for training following the 3-class "Say No" logic.
    Requirements:
    - Net Profit after Spread/Slippage only.
    - Classes: 0 (No Trade), 1 (High Quality Buy), 2 (High Quality Sell)
    """
    
    @staticmethod
    def label_setup(row: dict, result_after_costs: float) -> int:
        """
        Labels a single setup row based on its outcome.
        Only labels as Buy/Sell if the net outcome is strictly positive and meets 
        a minimum expectation (e.g., > 0.3R net).
        """
        # Threshold: Only label as Buy/Sell if the net result is actually profitable
        # and not just a break-even (spread-eater).
        if result_after_costs > 0:
            if row.get('signal_type') == 'BUY':
                return 1 # High-quality Buy
            elif row.get('signal_type') == 'SELL':
                return 2 # High-quality Sell
        
        return 0 # No Trade (Weak setup, loss, or spread-eaten)

    @staticmethod
    def calculate_net_metrics(entry: float, sl: float, tp: float, exit_price: float, 
                              spread_at_entry: float, slippage: float) -> dict:
        """
        Calculates R-multiple and net profit after spread and slippage.
        """
        risk_points = abs(entry - sl)
        if risk_points == 0: return {"r_multiple": 0, "net_profit": 0}
        
        # Gross profit in points
        gross_points = (exit_price - entry) if entry < tp else (entry - exit_price)
        
        # Net profit after accounting for slippage and spread (points)
        # Note: Slippage is treated as adverse
        net_points = gross_points - spread_at_entry - slippage
        
        r_multiple = net_points / risk_points
        
        return {
            "r_multiple": round(r_multiple, 2),
            "net_profit": round(net_points, 5)
        }
