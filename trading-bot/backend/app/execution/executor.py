import time
import logging
import MetaTrader5 as mt5
from typing import Dict, Optional
from app.market_data.mt5_client import MT5Client
from app.core.datatypes import TradeSignal, OrderSide
from app.execution.models import ExecutionResult

logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self, mt5_client: MT5Client):
        self.client = mt5_client

    def execute(self, signal: TradeSignal, lot_size: float, rr_ratio: float = 1.5, eval_id: str = "N/A") -> ExecutionResult:
        start_time = time.time()
        logger.info(f"[{eval_id}] [EXECUTION] Preparing order for {signal.symbol} | Side={signal.side.name} | Lot={lot_size}")
        # Resolve symbol name (e.g. XAUUSD -> GOLD)
        mt5_symbol = self.client.resolve_symbol(signal.symbol)
        if not mt5_symbol:
            return ExecutionResult(success=False, retcode=-1, comment=f"Symbol {signal.symbol} not found or could not be resolved")

        symbol_info = mt5.symbol_info(mt5_symbol)
        if not symbol_info:
            return ExecutionResult(success=False, retcode=-1, comment=f"Symbol {mt5_symbol} (original: {signal.symbol}) info fetch failed")

        if not symbol_info.visible:
            if not mt5.symbol_select(mt5_symbol, True):
                return ExecutionResult(success=False, retcode=-1, comment=f"Symbol {mt5_symbol} could not be selected")

        # Get latest tick for fresh prices
        tick = mt5.symbol_info_tick(mt5_symbol)
        if not tick:
            return ExecutionResult(success=False, retcode=-1, comment=f"Could not get tick for {mt5_symbol}")

        # DIRECT EXECUTION LOGIC: Follow Strategy (BUY -> BUY, SELL -> SELL)
        if signal.side == OrderSide.BUY:
            # Strategy says BUY? We BUY.
            price = tick.ask
            order_type = mt5.ORDER_TYPE_BUY
            
            digits = symbol_info.digits
            # Use structural SL from signal
            sl_val = signal.structural_sl if signal.structural_sl else (price - 0.0020)
            
            # Priority: Signal Targets -> Fixed RR
            if signal.targets and len(signal.targets) > 0:
                tp_val = signal.targets[-1] # ALWAYS use the furthest target for the hard MT5 order
            else:
                risk_dist = abs(price - sl_val)
                tp_val = price + (risk_dist * rr_ratio)
        else:
            # Strategy says SELL? We SELL.
            price = tick.bid
            order_type = mt5.ORDER_TYPE_SELL
            
            digits = symbol_info.digits
            # Use structural SL from signal
            sl_val = signal.structural_sl if signal.structural_sl else (price + 0.0020)
            
            # Priority: Signal Targets -> Fixed RR
            if signal.targets and len(signal.targets) > 0:
                tp_val = signal.targets[-1] # ALWAYS use the furthest target for the hard MT5 order
            else:
                risk_dist = abs(price - sl_val)
                tp_val = price - (risk_dist * rr_ratio)
        
        # Rounding price/SL/TP to symbol's required precision
        price = round(price, digits)
        sl = round(sl_val, digits)
        tp = round(tp_val, digits)

        # 1. Stop Level Validation
        stop_level = symbol_info.trade_stops_level * symbol_info.point
        spread = tick.ask - tick.bid
        
        if order_type == mt5.ORDER_TYPE_BUY:
            if sl >= price: sl = price - (stop_level + spread + symbol_info.point * 10)
            if tp > 0 and tp <= price: tp = price + (stop_level + spread + symbol_info.point * 10)
            
            if abs(price - sl) < stop_level:
                sl = price - (stop_level + symbol_info.point)
            if tp > 0 and abs(tp - price) < stop_level:
                tp = price + (stop_level + symbol_info.point)
        else:
            if sl <= price: sl = price + (stop_level + spread + symbol_info.point * 10)
            if tp > 0 and tp >= price: tp = price - (stop_level + spread + symbol_info.point * 10)
            
            if abs(sl - price) < stop_level:
                sl = price + (stop_level + symbol_info.point)
            if tp > 0 and abs(price - tp) < stop_level:
                tp = price - (stop_level + symbol_info.point)

        import math
        if math.isnan(price) or math.isnan(sl) or math.isnan(tp) or math.isnan(lot_size):
            return ExecutionResult(success=False, retcode=-1, comment=f"SafeGuard: NaN value detected (price={price}, sl={sl}, tp={tp}, lot_size={lot_size})")

        # 2. Order Check
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": mt5_symbol,
            "volume": float(lot_size),
            "type": order_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 202401,
            "comment": signal.strategy_name[:15] if signal.strategy_name else "BotTrade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        check_res = self.client.check_order(request)
        logger.info(f"[{eval_id}] [EXECUTION] MT5 Order Check: Retcode={check_res.get('retcode')} | Comment={check_res.get('comment')}")
        
        if check_res.get('retcode') != 0:
            latency = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False, 
                retcode=check_res.get('retcode'), 
                comment=f"Order check failed: {check_res.get('comment')} (Stops: SL={sl}, TP={tp}, Price={price})",
                latency_ms=latency
            )

        # 3. Order Send
        logger.info(f"[{eval_id}] [EXECUTION] Sending Request: Action=DEAL, Type={order_type}, Price={price}, SL={sl}, TP={tp}")
        result = self.client.send_order(request)
        latency = (time.time() - start_time) * 1000
        
        success = result.get('retcode') in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED]
        logger.info(f"[{eval_id}] [EXECUTION] MT5 Order Send: Success={success} | Retcode={result.get('retcode')} | Ticket={result.get('order')} | Fill={result.get('price')}")
        
        return ExecutionResult(
            success=success,
            ticket=result.get('order'),
            price=result.get('price'),
            sl=float(sl),
            tp=float(tp),
            order_type="BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL",
            retcode=result.get('retcode'),
            comment=result.get('comment', 'Success' if success else 'Failed'),
            lot_size=float(lot_size) if success else 0.0,
            latency_ms=latency
        )
