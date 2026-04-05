import sys
import os
import random
import logging
import time
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5
from app.market_data.mt5_client import MT5Client
from app.execution.executor import OrderExecutor
from app.core.datatypes import TradeSignal, OrderSide, EntryMode, SetupScore, SignalStatus
from app.storage.db import DatabaseContext, init_db
from app.storage.models import BotState, User

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RandomTest")

def run_test(num_trades=1):
    init_db()
    mt5_client = MT5Client()
    if not mt5_client.connect():
        logger.error("MT5 connection failed")
        return

    executor = OrderExecutor(mt5_client)
    
    # Get active symbols from DB
    with DatabaseContext() as db:
        state = db.query(BotState).first()
        active_symbols = list(state.active_symbols) if state and state.active_symbols else ["GOLD", "USDJPY", "EURUSD", "SOLUSD"]
        user = db.query(User).first()
        rr_ratio = getattr(user, "preferred_rr_ratio", 1.5) if user else 1.5

    logger.info(f"Starting test with {num_trades} random trades on symbols: {active_symbols}")

    for i in range(num_trades):
        symbol = random.choice(active_symbols)
        side = random.choice([OrderSide.BUY, OrderSide.SELL])
        
        # Get Symbol Info for constraints
        info = mt5.symbol_info(symbol)
        if not info:
            logger.warning(f"Symbol {symbol} info not found, skipping")
            continue
            
        if not info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5_client.get_latest_tick(symbol)
        if not tick:
            logger.warning(f"Could not get tick for {symbol}, trying a different symbol...")
            continue
            
        price = tick['ask'] if side == OrderSide.BUY else tick['bid']
        
        # Calculate a safe SL/TP
        # For Crypto like SOL, 0.5% is a lot. For Gold, it's also a lot.
        # Let's use 50-100 pips/points as a baseline
        point = info.point
        offset_points = 1000 # 1000 points
        
        sl = price - (offset_points * point) if side == OrderSide.BUY else price + (offset_points * point)
        tp = price + (offset_points * point * rr_ratio) if side == OrderSide.BUY else price - (offset_points * point * rr_ratio)

        # Lot size: respect Volume Min
        lot_size = info.volume_min
        if lot_size < 0.01: lot_size = 0.01

        # Create a dummy signal
        signal = TradeSignal(
            idempotency_key=f"test_{int(time.time())}_{i}",
            signal_fingerprint=f"fp_{i}",
            strategy_name="RandomTestStrategy",
            symbol=symbol,
            timeframe="M1",
            side=side,
            regime="TRENDING",
            session="LONDON",
            setup_score=SetupScore(total_score=0.9, is_qualified=True),
            ai_confidence=0.85,
            ai_threshold_used=0.15,
            entry_mode=EntryMode.MARKET_IMMEDIATE,
            entry_price=price,
            structural_sl=sl,
            volatility_buffer=0.0002,
            targets=[tp],
            estimated_rr=rr_ratio,
            setup_candle_timestamp=datetime.now(),
            status=SignalStatus.APPROVED
        )
        
        logger.info(f"Test Trade {i+1}/{num_trades}: {side} {symbol} (Vol: {lot_size})")
        logger.info(f"  Price: {price}, SL: {sl:.5f}, TP: {tp:.5f}")
        
        # Execute
        res = executor.execute(signal, lot_size=lot_size, rr_ratio=rr_ratio)
        
        if res.success:
            logger.info(f"✅ Success: Ticket #{res.ticket}, Filled: {res.price}")
        else:
            logger.error(f"❌ Failed: {res.comment}")
        
        if i < num_trades - 1:
            logger.info("Waiting 2 seconds before next trade...")
            time.sleep(2)

if __name__ == "__main__":
    count = 1
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    
    run_test(count)
