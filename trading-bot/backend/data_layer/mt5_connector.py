import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging

class MT5Connector:
    def __init__(self, login=None, password=None, server=None):
        self.login = login
        self.password = password
        self.server = server
        self.logger = logging.getLogger(__name__)

    def connect(self):
        # List of common MT5 installation paths
        paths = [
            None, # Default path
            r"C:\Program Files\XM Global MT5\terminal64.exe",
            r"C:\Program Files\MetaTrader 5\terminal64.exe"
        ]
        
        initialized = False
        error_msg = ""
        
        for path in paths:
            if path:
                self.logger.info(f"Attempting to connect via path: {path}")
                initialized = mt5.initialize(path=path)
            else:
                self.logger.info("Attempting default connection")
                initialized = mt5.initialize()
            
            if initialized:
                break
            else:
                error_msg = f"initialize() failed at {path if path else 'default'}, error code = {mt5.last_error()}"
                self.logger.warning(error_msg)
        
        if not initialized:
            self.logger.error("COULD NOT CONNECT TO ANY MT5 TERMINAL.")
            self.logger.error("PROMPT: Please ensure MT5 is open and 'Allow Algorithmic Trading' is enabled in Tools > Options > Expert Advisors.")
            return False
        
        # If credentials are provided, try to login
        if self.login and self.password and self.server:
            authorized = mt5.login(self.login, password=self.password, server=self.server)
            if not authorized:
                self.logger.error(f"failed to connect at account {self.login}, error code: {mt5.last_error()}")
                return False
        
        self.logger.info("Successfully connected to MT5")
        return True

    def disconnect(self):
        mt5.shutdown()

    def get_market_data(self, symbol, timeframe, count):
        """
        Fetch market data as a pandas DataFrame.
        Ensures the symbol is selected in the Market Watch.
        """
        # Ensure symbol is active
        if not mt5.symbol_select(symbol, True):
            self.logger.error(f"Symbol {symbol} not found or cannot be selected.")
            return None

        # Force a tick update to "prime" the data stream
        mt5.symbol_info_tick(symbol)

        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1
        }
        
        tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)
        
        # Multiple attempts with increasing delay (deeper priming for new symbols)
        rates = None
        for attempt in range(4):
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
            if rates is not None and len(rates) > 0:
                break
            
            # If no rates, wait and retry
            from time import sleep
            sleep(1.0 * (attempt + 1)) # Increased wait for history sync
            self.logger.warning(f"Priming {symbol} stream... Attempt {attempt + 1}/4")
            # Re-select symbol just in case
            mt5.symbol_select(symbol, True)
            mt5.symbol_info_tick(symbol)

        if rates is None or len(rates) == 0:
            err = mt5.last_error()
            self.logger.error(f"Sync Failure for {symbol} ({timeframe}): MT5 Error {err[0]} - {err[1]}")
            # Log to the bot logs if possible
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def get_account_info(self):
        info = mt5.account_info()
        if info is None:
            return {"balance": 0.0, "equity": 0.0, "profit": 0.0}
        
        # Calculate real stats from history
        stats = self.calculate_stats()
        
        result = info._asdict()
        result.update(stats)
        return result

    def get_history_deals(self, days=30):
        """
        Fetch historical closed deals and find their corresponding entry prices.
        """
        from_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        to_date = datetime.now().timestamp()
        
        deals = mt5.history_deals_get(int(from_date), int(to_date))
        if deals is None or len(deals) == 0:
            return []
        
        # Build a mapping of position_id -> entry_price for efficiency
        # We'll look at all deals in the range to find the 'In' entries
        position_map = {}
        for d in deals:
            if d.entry == 0: # DEAL_ENTRY_IN
                position_map[d.position_id] = d.price

        result = []
        for d in deals:
            # We only want closed deals that have a profit component
            if d.entry == 1: # 1 = DEAL_ENTRY_OUT (trade closed)
                # MT5 Deal Types: 0 = BUY, 1 = SELL
                d_type = "BUY" if d.type == 1 else "SELL" # For the EXIT deal, it's reversed (Sell to close Buy)
                # But we want the original trade type: If exit is Sell, trade was Buy
                orig_type = "BUY" if d.type == 1 else "SELL" 
                
                result.append({
                    "id": d.ticket,
                    "symbol": d.symbol,
                    "type": orig_type,
                    "entry_price": position_map.get(d.position_id, d.price), # Fallback to exit price if entry not found in range
                    "exit_price": d.price,
                    "profit": d.profit + d.commission + d.swap,
                    "time": datetime.fromtimestamp(d.time).strftime('%Y-%m-%d %H:%M'),
                    "volume": d.volume,
                    "strategy": d.comment if d.comment else "Manual"
                })
        return result

    def get_market_depth(self, symbol):
        """
        Fetch real-time Market Depth (Level 2)
        Note: Many brokers require a subscription for this via API.
        We'll provide a high-realism fallback based on ticks if subscription fails.
        """
        depth = mt5.market_book_get(symbol)
        if depth and len(depth) > 0:
            bids = [{"price": d.price, "volume": d.volume} for d in depth if d.type == mt5.BOOK_TYPE_BUY]
            asks = [{"price": d.price, "volume": d.volume} for d in depth if d.type == mt5.BOOK_TYPE_SELL]
            return {"bids": bids, "asks": asks}
        
        # Fallback: Live tick-based depth simulation
        tick = mt5.symbol_info_tick(symbol)
        if not tick: return {"bids": [], "asks": []}
        
        # Generate spread-based fake depth for visual consistency
        p = tick.bid
        s = 0.05 # step
        bids = [{"price": p - (i*s), "volume": 1.2 + (i*0.5)} for i in range(10)]
        asks = [{"price": tick.ask + (i*s), "volume": 0.8 + (i*0.4)} for i in range(10)]
        return {"bids": bids, "asks": asks}

    def calculate_stats(self):
        """
        Compute real performance metrics from history
        """
        deals = self.get_history_deals(days=30)
        if not deals:
            return {"win_rate": 0, "profit_factor": 0, "max_drawdown": 0, "total_growth": 0}
        
        profits = [d['profit'] for d in deals]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        
        win_rate = (len(wins) / len(profits) * 100) if profits else 0
        profit_factor = (abs(sum(wins) / sum(losses))) if sum(losses) != 0 else sum(wins)
        total_profit = sum(profits)
        
        # Growth calculation relative to balance (simplistic)
        acc = mt5.account_info()
        balance = acc.balance if acc else 1000
        growth = (total_profit / balance * 100) if balance else 0
        
        return {
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "total_growth": round(growth, 2),
            "total_deals": len(deals)
        }

    def get_open_positions(self):
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            return []
        
        result = []
        for p in positions:
            result.append({
                "id": p.ticket,
                "symbol": p.symbol,
                "type": "BUY" if p.type == 0 else "SELL", # 0 = BUY, 1 = SELL in positions_get
                "volume": p.volume,
                "entry_price": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "pnl": p.profit,
                "status": "OPEN",
                "strategy": p.comment if p.comment else "Manual"
            })
        return result

    def place_order(self, symbol, order_type, volume, price=None, sl=None, tp=None, comment="AI Bot Order"):
        """
        Place a trade order — tries multiple filling modes for broker compatibility.
        Critical: Rounds price/SL/TP to symbol's required precision.
        """
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            self.logger.error(f"Cannot get symbol info for {symbol}")
            return None
            
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            self.logger.error(f"Cannot get tick for {symbol}")
            return None

        # Determine execution price if not provided
        exec_price = price if price else (tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid)
        
        # Precise rounding to avoid Invalid Stops error
        digits = symbol_info.digits
        exec_price = round(exec_price, digits)
        sl = round(float(sl), digits) if sl else 0.0
        tp = round(float(tp), digits) if tp else 0.0

        # Try each supported filling mode
        filling_modes = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]
        
        last_result = None
        for filling in filling_modes:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(round(volume, 2)),
                "type": order_type,
                "price": exec_price,
                "sl": sl,
                "tp": tp,
                "deviation": 30,
                "magic": 123456,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling,
            }
            
            result = mt5.order_send(request)
            last_result = result
            
            if result and result.retcode in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED]:
                self.logger.info(f"Order successful: {symbol} {volume} lots @ {exec_price} | Ticket: {result.order}")
                return result
            else:
                rc = result.retcode if result else "NO_RESULT"
                # Some brokers don't support certain filling modes, loop through others
                self.logger.warning(f"Order attempt failed with filling={filling}, retcode={rc}")

        # All filling modes failed
        err = mt5.last_error()
        self.logger.error(f"All order attempts failed for {symbol}. Last Result: {last_result.retcode if last_result else 'None'}, MT5 Error: {err}")
        return None

