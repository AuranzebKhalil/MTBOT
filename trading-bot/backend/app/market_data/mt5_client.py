import MetaTrader5 as mt5
import pandas as pd
import logging
from typing import Optional, List, Dict
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class MT5Client:
    def __init__(self):
        self._connected = False
        import os
        self.audit_logger = logging.getLogger("BrokerAudit")
        if not self.audit_logger.handlers:
            os.makedirs("logs", exist_ok=True)
            fh = logging.FileHandler("logs/broker_audit.log")
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.audit_logger.addHandler(fh)
            self.audit_logger.setLevel(logging.INFO)

    def connect(self) -> bool:
        if self._connected:
            return True
            
        path = settings.MT5_PATH
        if path:
            self._connected = mt5.initialize(path=path)
        else:
            self._connected = mt5.initialize()
            
        if not self._connected:
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
            
        # XM-DEMO SAFETY CHECK: REFUSE LIVE ACCOUNTS
        acc = mt5.account_info()
        if not acc:
            logger.error("Could not retrieve MT5 account info for safety check.")
            mt5.shutdown()
            self._connected = False
            return False
            
        if acc.trade_mode not in [mt5.ACCOUNT_TRADE_MODE_DEMO, mt5.ACCOUNT_TRADE_MODE_CONTEST]:
            msg = f"🛑 FATAL SAFETY BREACH: Non-demo account detected (#{acc.login} on {acc.server}). Bot shutdown."
            logger.critical(msg)
            mt5.shutdown()
            self._connected = False
            return False
            
        logger.info(f"✅ XM-DEMO VERIFIED: Account #{acc.login} ({acc.server})")
        self.audit_logger.info(f"STARTUP: Connected to account #{acc.login} (Mode: {acc.trade_mode})")
            
        # Optional Login
        if settings.MT5_LOGIN and settings.MT5_PASSWORD:
            authorized = mt5.login(
                login=settings.MT5_LOGIN,
                password=settings.MT5_PASSWORD,
                server=settings.MT5_SERVER or ""
            )
            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                return False
                
        logger.info("Successfully connected to MT5")
        return True

    def disconnect(self):
        mt5.shutdown()
        self._connected = False

    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """Resolves a symbol name to the one used by the broker (e.g. XAUUSD -> GOLD)."""
        if not self._connected:
            return None
            
        # Try direct selection first
        if mt5.symbol_select(symbol, True):
            return symbol
            
        # Then try uppercase
        mt5_symbol = symbol.upper()
        if mt5.symbol_select(mt5_symbol, True):
            return mt5_symbol
            
        # Try common mappings
        if mt5_symbol == "GOLD":
            mt5_symbol = "XAUUSD"
        elif mt5_symbol == "XAUUSD":
            mt5_symbol = "GOLD"
        
        if mt5.symbol_select(mt5_symbol, True):
            return mt5_symbol
            
        # Try finding similar names (e.g. XAUUSD.m, XAUUSD.raw)
        raw_symbols = mt5.symbols_get()
        if raw_symbols:
            all_names = [s.name for s in raw_symbols]
            # Look for exact match with any case or symbol with suffixes
            matches = [n for n in all_names if n.upper().startswith(symbol.upper())]
            if matches:
                resolved = matches[0]
                if mt5.symbol_select(resolved, True):
                    return resolved
                    
        return None

    def get_symbol_info(self, symbol: str):
        """Returns the raw symbol info object for a given symbol."""
        mt5_symbol = self.resolve_symbol(symbol)
        if not mt5_symbol:
            return None
        return mt5.symbol_info(mt5_symbol)

    def get_bars(self, symbol: str, timeframe: str, count: int, include_current: bool = False) -> Optional[pd.DataFrame]:
        """Fetch historical bars. By default returns CLOSED candles only."""
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1
        }
        
        mt5_symbol = self.resolve_symbol(symbol)
        if not mt5_symbol:
            logger.error(f"Symbol {symbol} resolve failed. Active Market Watch check failed.")
            return None
            
        # We fetch count + (0 if include_current else 1)
        fetch_count = count if include_current else count + 1
        # CRITICAL: Use the RESOLVED mt5_symbol here
        rates = mt5.copy_rates_from_pos(mt5_symbol, tf_map.get(timeframe, mt5.TIMEFRAME_M1), 0, fetch_count)
        
        if rates is None or len(rates) == 0:
            err = mt5.last_error()
            logger.error(f"Failed to fetch rates for {mt5_symbol} (original: {symbol}): {err}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # If we want closed only, we dropped the current one already for simplicity or can drop here
        if not include_current:
            df = df.iloc[:-1].copy()
        
        return df

    def get_latest_tick(self, symbol: str) -> Optional[Dict]:
        mt5_symbol = self.resolve_symbol(symbol)
        if not mt5_symbol:
            return None
        tick = mt5.symbol_info_tick(mt5_symbol)
        if not tick:
            return None
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "time": int(tick.time),
            "spread": (tick.ask - tick.bid)
        }

    def get_account_info(self) -> Dict:
        acc = mt5.account_info()
        if not acc:
            return {"balance": 0.0, "equity": 0.0}
        return {
            "balance": acc.balance,
            "equity": acc.equity,
            "margin": acc.margin,
            "margin_free": acc.margin_free,
            "leverage": acc.leverage
        }

    def get_positions(self) -> List[Dict]:
        pos = mt5.positions_get()
        if pos is None:
            return []
        return [p._asdict() for p in pos]

    def get_market_depth(self, symbol: str) -> Dict:
        """Fetch Level 2 / Depth of Market data."""
        mt5_symbol = self.resolve_symbol(symbol)
        if not mt5_symbol:
            return {"bids": [], "asks": []}
            
        ticks = mt5.symbol_info_tick(mt5_symbol)
        if not ticks:
            return {"bids": [], "asks": []}
        
        # Simulating depth based on tick spread for basic visualization
        # Real L2 requires mt5.market_book_add() which is complex for a simple API
        # We provide a 'synthetic' depth for the UI to feel alive
        spread = ticks.ask - ticks.bid
        bids = [{"price": ticks.bid - (i * 0.0001), "volume": 100 + (i * 50)} for i in range(10)]
        asks = [{"price": ticks.ask + (i * 0.0001), "volume": 100 + (i * 50)} for i in range(10)]
        return {"bids": bids, "asks": asks}

    def get_calendar_events(self) -> List[Dict]:
        """Fetch economic calendar events. Fallback to sample data if not available."""
        import datetime
        dt_from = datetime.datetime.now()
        dt_to = dt_from + datetime.timedelta(days=7)
        
        # Check if the method exists in this build of MetaTrader5
        if not hasattr(mt5, 'calendar_events_get'):
            logger.warning("MT5 calendar_events_get not found in this library version. Providing advisory fallback.")
            return self._get_fallback_events()

        try:
            events = mt5.calendar_events_get(date_from=dt_from, date_to=dt_to)
            if events is None or len(events) == 0:
                return self._get_fallback_events()
            
            # Sort and clean
            cleaned = []
            for e in events:
                try:
                    cleaned.append({
                        "id": str(e.id),
                        "event": e.event_name,
                        "currency": e.currency,
                        "importance": e.importance,
                        "time": datetime.datetime.fromtimestamp(e.time).isoformat()
                    })
                except Exception as inner_e:
                    logger.error(f"Error parsing event: {inner_e}")
                    continue
            return [cleaned[i] for i in range(min(30, len(cleaned)))]
        except Exception as e:
            logger.error(f"MT5 Calendar Error: {e}")
            return self._get_fallback_events()

    def _get_fallback_events(self) -> List[Dict]:
        """Advisory events for when MT5 data is unavailable."""
        import datetime
        now = datetime.datetime.now()
        return [
            {
                "id": "mock_1",
                "event": "FOMC Monetary Policy Advisory",
                "currency": "USD",
                "importance": 3,
                "time": (now + datetime.timedelta(hours=2)).isoformat()
            },
            {
                "id": "mock_2",
                "event": "ECB Press Conference",
                "currency": "EUR",
                "importance": 3,
                "time": (now + datetime.timedelta(hours=5)).isoformat()
            }
        ]

    def check_order(self, request: Dict) -> Dict:
        logger.info(f"DEBUG: MT5 client calling mt5.order_check with {request}")
        import time
        t1 = time.time()
        res = mt5.order_check(request)
        t2 = time.time()
        logger.info(f"DEBUG: MT5 client mt5.order_check returned in {t2-t1}s: {res}")
        if res is None:
            last_err = mt5.last_error()
            return {"retcode": last_err[0] if last_err else -1, "comment": f"order_check failed directly. Error: {last_err}"}
        return res._asdict()

    def send_order(self, request: Dict) -> Dict:
        """Sends an order with automated filling mode retries for XM Demo conditions."""
        action_type = request.get("action")
        symbol = request.get("symbol", "UNKNOWN")
        
        # 1. SL/TP updates don't use filling mode
        if action_type == mt5.TRADE_ACTION_SLTP:
            self.audit_logger.info(f"ORDER SLTP: ticket=#{request.get('position')} symbol={symbol} sl={request.get('sl')} tp={request.get('tp')}")
            res = mt5.order_send(request)
            if res:
                self.audit_logger.info(f"  RESULT SLTP: retcode={res.retcode} comment={res.comment}")
                return res._asdict()
            return {"retcode": -1, "comment": "mt5.order_send returned None"}

        # 2. For DEAL actions, try multiple filling modes (IOC -> RETURN -> FOK)
        # Sequential retry is safer across different broker symbols.
        potential_modes = [
            (mt5.ORDER_FILLING_IOC, "IOC"),
            (mt5.ORDER_FILLING_RETURN, "RETURN"),
            (mt5.ORDER_FILLING_FOK, "FOK")
        ]

        self.audit_logger.info(f"ORDER DEAL: action={action_type} symbol={symbol} vol={request.get('volume')} comment='{request.get('comment')}'")
        
        for mode, mode_name in potential_modes:
            request["type_filling"] = mode
            import time
            t1 = time.time()
            result = mt5.order_send(request)
            t2 = time.time()
            
            if result is None:
                continue
                
            self.audit_logger.info(f"  TRY FILLING {mode_name}: retcode={result.retcode} time={t2-t1:.3f}s comment={result.comment}")
            
            # retcode 10013=Invalid request, 10030=Unsupported filling, 10014=Invalid filling, 10031=No filling mode
            # Retrying on filling mode errors only
            if result.retcode in [10013, 10014, 10030, 10031]:
                continue
            
            # Success or legitimate trading error (e.g. 10009 SUCCESS or 10015 Invalid price, etc)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.audit_logger.info(f"  SUCCESS: #{result.order} filled via {mode_name}")
            return result._asdict()

        return {"retcode": -1, "comment": "All filling modes (IOC, RETURN, FOK) failed on XM Broker demo."}

    def update_sl(self, ticket: int, symbol: str, sl: float, tp: Optional[float] = None) -> bool:
        """Updates SL/TP with explicit symbol to avoid cache race conditions."""
        if tp is None:
            # Fallback to current TP if not provided
            positions = mt5.positions_get(ticket=ticket)
            if positions:
                tp = positions[0].tp
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": float(sl),
            "tp": float(tp) if tp is not None else 0.0
        }
        res = self.send_order(request)
        return res.get("retcode") in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED]

    def partial_close(self, ticket: int, volume: float, symbol: str) -> Dict:
        """
        Executes a partial close with strict volume validation.
        Returns a result dict with details for logging.
        """
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return {"status": "FAILED", "reason": "Position not found"}
        
        pos = pos[0]
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return {"status": "FAILED", "reason": "Symbol info not found"}
            
        step = symbol_info.volume_step
        min_vol = symbol_info.volume_min
        current_vol = float(pos.volume)
        
        # 1. Round requested volume to lot step
        import math
        rounded_vol = round(math.floor(volume / step) * step, 2)
        
        # 2. Validation
        if rounded_vol < min_vol:
            # If we requested e.g. 0.007 and min is 0.01, we skip instead of forcing full
            return {
                "status": "SKIPPED_LOT_SIZE",
                "requested": volume,
                "rounded": rounded_vol,
                "current": current_vol,
                "remainder": current_vol,
                "min_lot": min_vol
            }
            
        remainder = round(current_vol - rounded_vol, 4)
        
        # 3. Handle problematic remaining volume
        effective_vol = rounded_vol
        action_status = "SUCCESS"
        forced_full = False
        
        if remainder < (min_vol - 0.00001):
            # If remaining would be 0 or dust, we must close full
            effective_vol = current_vol
            action_status = "CLOSED_FULL"
            remainder = 0.0
            forced_full = True
            
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {"status": "FAILED", "reason": "Tick not found"}

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": float(effective_vol),
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask,
            "magic": pos.magic,
            "comment": "Bot Partial" if not forced_full else "Bot Full Exit",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        res = self.send_order(request)
        if res.get("retcode") in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED]:
            logger.info(f"DEBUG: Partial close SUCCESS for #{ticket} | Action: {action_status} | Remainder: {remainder}")
            return {
                "status": action_status,
                "requested": volume,
                "rounded": rounded_vol,
                "effective": effective_vol,
                "current": current_vol,
                "remainder": remainder,
                "forced_full": forced_full,
                "min_lot": min_vol,
                "ticket": res.get("order")
            }
        
        logger.error(f"DEBUG: Partial close FAILED for #{ticket}: {res.get('comment')}")
        return {"status": "FAILED", "reason": res.get("comment")}

    def get_all_symbols(self) -> List[Dict]:
        """Fetch all available symbols with basic info."""
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        
        results = []
        for s in symbols:
            results.append({
                "name": s.name,
                "path": s.path,
                "description": s.description,
                "digits": s.digits,
                "spread": s.spread,
                "last_price": s.lasttick.last if hasattr(s, 'lasttick') and s.lasttick else 0.0,
                "bid": s.bid,
                "ask": s.ask,
                "min_volume": s.volume_min,
                "max_volume": s.volume_max,
                "trade_mode": s.trade_mode
            })
        return results

    def get_last_error(self):
        return mt5.last_error()
