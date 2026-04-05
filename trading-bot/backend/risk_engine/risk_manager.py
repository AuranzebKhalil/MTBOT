import datetime

class RiskManager:
    def __init__(self, risk_per_trade=0.005, max_trades=2, max_daily_losses=2, daily_loss_limit=0.02):
        # STRICTIONS - Strict Risk Controls
        self.risk_per_trade = risk_per_trade  # Default 0.5% per trade
        self.max_trades = max_trades          # Max simultaneous open trades
        self.max_daily_losses = max_daily_losses # Stop for the day after 2 losses
        self.daily_loss_limit = daily_loss_limit # Overall daily drawdown limit %

    def calculate_lot_size(self, balance, entry_price, sl_price, symbol_info):
        """
        Calculate precise position size based on risk_per_trade (0.25% - 0.5%)
        """
        if entry_price == sl_price:
            return getattr(symbol_info, 'volume_min', 0.01)
            
        risk_amount = balance * self.risk_per_trade
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
            # Fallback if tick data missing
            lot_size = risk_amount / (max(price_distance_points * 100, 1))
            
        step = getattr(symbol_info, 'volume_step', 0.01)
        if step > 0:
            lot_size = round(lot_size / step) * step
            
        vol_min = getattr(symbol_info, 'volume_min', 0.01)
        vol_max = getattr(symbol_info, 'volume_max', 100.0)
        lot_size = max(vol_min, min(vol_max, lot_size))
        
        return round(lot_size, 2)

    def is_risk_acceptable(self, open_trades, history_deals, current_balance, symbol=None, spread=0.0):
        """
        Checks institutional logic:
        - Max 1 position per symbol
        - Max 2 global positions
        - Stop for day after 2 losses
        - Block trading if spread abnormal
        """
        # 1. ONE TRADE PER SYMBOL RULE
        if symbol:
            if any(t.get('symbol') == symbol for t in open_trades):
                return False, f"Already have an open position on {symbol}"

        # 2. MAX GLOBAL TRADES RULE (Max 2 total)
        if len(open_trades) >= self.max_trades:
            return False, f"Max open trades reached ({self.max_trades})"
            
        # Optional spread check (can be expanded via execution model later)
        if spread > 200: # Arbitrary high spread block
            return False, f"Spread too high ({spread})"

        now = datetime.datetime.now(datetime.timezone.utc)
        today = now.date()
        
        losses_today = 0
        total_pnl_today = 0
        
        if history_deals:
            for deal in history_deals:
                try:
                    raw_time = deal.get('time') if isinstance(deal, dict) else getattr(deal, 'time', None)
                    if not raw_time: continue
                    
                    if isinstance(raw_time, str):
                        deal_time = datetime.datetime.strptime(raw_time, '%Y-%m-%d %H:%M')
                    else:
                        deal_time = datetime.datetime.fromtimestamp(int(raw_time), datetime.timezone.utc)
                    
                    if deal_time.date() == today:
                        profit = float(deal.get('profit', 0) if isinstance(deal, dict) else getattr(deal, 'profit', 0))
                        total_pnl_today += profit
                        if profit < 0:
                            losses_today += 1
                except Exception:
                    continue
                            
        # 3. MAX DAILY LOSSES CHECK (Strict 2 losses rule)
        if losses_today >= self.max_daily_losses:
            return False, f"Max losing trades reached today ({self.max_daily_losses})"
            
        # 4. PERCENTAGE LOSS LIMIT CHECK
        if self.daily_loss_limit and current_balance > 0:
            loss_percentage = abs(total_pnl_today) / current_balance if total_pnl_today < 0 else 0
            if loss_percentage >= self.daily_loss_limit:
                return False, f"Daily drawdown limit hit ({loss_percentage*100:.2f}%)"
            
        return True, ""

    def calculate_sl_tp(self, entry_price, direction, atr=None):
        """
        Calculate suggested SL and TP. Hard 1:2 R/R min.
        """
        if atr is None:
            atr = entry_price * 0.003 # tighter dynamic base 0.3%
            
        if direction == 1:
            sl = entry_price - atr
            tp = entry_price + (atr * 2)
        else:
            sl = entry_price + atr
            tp = entry_price - (atr * 2)
            
        return sl, tp

    def calculate_trailing_stop(self, current_price, entry_price, current_sl, direction, atr):
        """
        Institutional Profit Guard:
        1. Move to Break-Even (BE) at 1:1 RR (1R profit)
        2. Trail with 1.5x ATR buffer once past 1R
        """
        profit_points = abs(current_price - entry_price)
        risk_points = abs(entry_price - current_sl) if current_sl != entry_price else atr
        
        # 1. 1R reached -> Move to Break-Even
        if profit_points >= risk_points and current_sl != entry_price:
            return entry_price # Lock in zero risk

        # 2. Trail after BE is set
        if (direction == 1 and current_price > entry_price) or (direction == -1 and current_price < entry_price):
            new_trailing_sl = current_price - (atr * 1.5) if direction == 1 else current_price + (atr * 1.5)
            
            # Only move SL in the direction of profit
            if direction == 1:
                return max(current_sl, new_trailing_sl)
            else:
                return min(current_sl, new_trailing_sl)
                
        return current_sl
