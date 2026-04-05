import datetime

class RiskManager:
    def __init__(self, risk_per_trade=0.01, max_trades=2, daily_loss_limit=None):
        # DEMO MODE — relaxed limits for testing
        self.risk_per_trade = 0.01  # 1% per trade
        self.max_trades = 2         # Max simultaneous open trades
        self.max_daily_trades = 5   # Max trades per day
        self.max_daily_losses = 3   # Max losing trades per day

    def calculate_lot_size(self, balance, entry_price, sl_price, symbol_info):
        """
        Calculate precise position size across Forex, Crypto, and Metals
        using MT5's dynamic Tick Size and Tick Value data.
        """
        if entry_price == sl_price:
            return getattr(symbol_info, 'volume_min', 0.01)
            
        # Exactly 1% of account balance
        risk_amount = balance * 0.01
        price_distance_points = abs(entry_price - sl_price)
        
        tick_size = getattr(symbol_info, 'trade_tick_size', 0)
        tick_value = getattr(symbol_info, 'trade_tick_value', 0)
        
        if tick_size > 0 and tick_value > 0:
            risk_per_lot = (price_distance_points / tick_size) * tick_value
            if risk_per_lot > 0:
                lot_size = risk_amount / risk_per_lot
            else:
                lot_size = symbol_info.volume_min
        else:
            lot_size = risk_amount / (price_distance_points * 100)
            
        step = getattr(symbol_info, 'volume_step', 0.01)
        if step > 0:
            lot_size = round(lot_size / step) * step
            
        vol_min = getattr(symbol_info, 'volume_min', 0.01)
        vol_max = getattr(symbol_info, 'volume_max', 100.0)
        lot_size = max(vol_min, min(vol_max, lot_size))
        
        return round(lot_size, 2)

    def is_risk_acceptable(self, open_trades, history_deals, current_balance, symbol=None):
        """
        Check if we can open a new trade strictly based on institutional rules:
        - Max 1 position per symbol simultaneously
        - Max open trades globally: 2
        - Max trades per day: 5
        - Stop trading after 3 losses in one day
        """
        # 1. ONE TRADE PER SYMBOL RULE
        if symbol:
            if any(t.get('symbol') == symbol for t in open_trades):
                return False, f"Already have an open position on {symbol}"

        # 2. MAX GLOBAL TRADES RULE
        if len(open_trades) >= self.max_trades:
            return False, f"Max open trades reached ({self.max_trades})"
            
        now = datetime.datetime.now(datetime.timezone.utc)
        today = now.date()
        
        trades_today = 0
        losses_today = 0
        
        total_profit_today = 0
        
        if history_deals:
            for deal in history_deals:
                try:
                    raw_time = deal.get('time') if isinstance(deal, dict) else getattr(deal, 'time', None)
                    if raw_time is None: continue
                    if isinstance(raw_time, str):
                        deal_time = datetime.datetime.strptime(raw_time, '%Y-%m-%d %H:%M')
                    else:
                        deal_time = datetime.datetime.fromtimestamp(int(raw_time), datetime.timezone.utc)
                    
                    if deal_time.date() == today:
                        deal_type = deal.get('type') if isinstance(deal, dict) else getattr(deal, 'type', None)
                        if deal_type in [0, 1, 'BUY', 'SELL']:
                            trades_today += 1
                            deal_profit = float(deal.get('profit', 0) if isinstance(deal, dict) else getattr(deal, 'profit', 0))
                            total_profit_today += deal_profit
                            if deal_profit < 0:
                                losses_today += 1
                except Exception:
                    continue
                            
        # Max Daily Trades Check
        if trades_today >= self.max_daily_trades:
            return False, f"Max trades per day reached ({self.max_daily_trades})"
            
        # Max Daily Losses (Count) Check
        if losses_today >= self.max_daily_losses:
            return False, f"Max losing trades reached ({self.max_daily_losses})"
            
        # Percentage Loss Limit Check
        if self.daily_loss_limit and current_balance > 0:
            loss_percentage = abs(total_profit_today) / current_balance if total_profit_today < 0 else 0
            if loss_percentage >= self.daily_loss_limit:
                return False, f"Daily drawdown limit hit ({loss_percentage*100:.1f}%)"
            
        return True, ""

    def calculate_sl_tp(self, entry_price, direction, atr=None):
        """
        Calculate suggested SL and TP dynamically. Minimum R:R is 1:2.
        direction: 1 for Buy, -1 for Sell
        """
        if atr is None:
            atr = entry_price * 0.005 # Dynamic 0.5% base
            
        if direction == 1:
            sl = entry_price - atr
            tp = entry_price + (atr * 2) # Exactly 1:2 R/R
        else:
            sl = entry_price + atr
            tp = entry_price - (atr * 2) # Exactly 1:2 R/R
            
        return sl, tp
