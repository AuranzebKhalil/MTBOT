import time
import MetaTrader5 as mt5
from datetime import datetime, timezone
import pandas as pd
import logging

# Enable logging for demo
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Demo")

from app.market_data.mt5_client import MT5Client
from app.execution.executor import OrderExecutor
from app.storage.db import DatabaseContext
from app.storage.models import Trade, User, TradeEvent, SignalLog, ExecutionLog
from app.worker.bot_worker import BotWorker

def capture_trade():
    print("="*60)
    print("   COMPLETE TRADE CAPTURE & VERIFICATION DEMO")
    print("="*60)
    
    # Clear DB at start
    with DatabaseContext() as db:
        db.query(TradeEvent).delete()
        db.query(Trade).delete()
        db.query(SignalLog).delete()
        db.query(ExecutionLog).delete()
        db.commit()
    print("DB Cleared for fresh run.")
    
    mt5_client = MT5Client()
    if not mt5_client.connect():
        print("Failed to connect to MT5")
        return

    symbol = "EURUSD"
    if not mt5.symbol_select(symbol, True):
        symbol = "GBPUSD"
        mt5.symbol_select(symbol, True)
        
    print(f"\n[1] INITIALIZING: Using {symbol}")
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("No tick data")
        return
        
    bid = tick.bid
    ask = tick.ask
    spread = ask - bid
    
    # Set config for partial closes
    with DatabaseContext() as db:
        user = db.query(User).first()
        if not user:
            user = User(email="test@test.com", password_hash="hash")
            db.add(user)
            db.commit()
            user = db.query(User).first()
        
        user.partial_stage_1_trigger = 0.60
        user.partial_stage_1_close_pct = 0.50
        user.partial_stage_2_trigger = 0.80
        user.partial_stage_2_close_pct = 0.25
        db.commit()
        print(f"Config set: Stage 1 @ {user.partial_stage_1_trigger*100}% (Close 50%), Stage 2 @ {user.partial_stage_2_trigger*100}% (Close 25%)")

    print(f"\n[2] ENTRY EXECUTION")
    test_lot_size = 0.06
    sl_dist = 0.0050
    tp_dist = 0.0100
    
    sl = bid - sl_dist
    tp = ask + tp_dist
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": test_lot_size,
        "type": mt5.ORDER_TYPE_BUY,
        "price": ask,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 123456,
        "comment": "demo_capture",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        # Try without IOC
        request["type_filling"] = mt5.ORDER_FILLING_FOK
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order FAILED: {result.retcode}")
            return
            
    ticket = result.order
    filled_price = result.price
    print(f"   >>> Ticket: {ticket}")
    print(f"   >>> Requested: {ask} | Actual Fill: {filled_price}")

    # Create fake Signal class to use executor/save for DB
    class FakeSignal:
        def __init__(self):
            self.symbol = symbol
            self.strategy_name = "DEMO_STRATEGY"
            self.ai_confidence = 0.85
            self.side = "BUY"
            self.entry_price = ask
            self.structural_sl = sl
            # Targets for TP1 and TP2 - Ensure TP2 == TP (Rule 4)
            self.targets = [filled_price + 0.0040, tp] 

    signal = FakeSignal()
    
    # Store in DB via BotWorker
    worker = BotWorker()
    if not worker.mt5.connect():
        print("Worker failed to connect to MT5")
        return
        
    class ExecRes:
        def __init__(self, ticket, price, retcode):
            self.ticket = ticket
            self.price = price
            self.retcode = retcode
            self.success = retcode == mt5.TRADE_RETCODE_DONE
            self.order_type = "BUY"
            self.lot_size = test_lot_size
            self.sl = sl
            self.tp = tp
            self.latency_ms = 120

    ex = ExecRes(ticket, filled_price, result.retcode)
    
    tick_dict = {'bid': bid, 'ask': ask, 'spread': spread}
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    m15_df = pd.DataFrame(rates)
    if not m15_df.empty:
        m15_df['time'] = pd.to_datetime(m15_df['time'], unit='s')
        
    rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
    m1_df = pd.DataFrame(rates_m1)
    if not m1_df.empty:
        m1_df['time'] = pd.to_datetime(m1_df['time'], unit='s')

    worker._save_trade_enhanced(signal, ex, tick_dict, m15_df)
    
    # Show values at entry
    print("\n--- [3] STATE AT ENTRY ---")
    with DatabaseContext() as db:
        t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
        print(f"ticket: {t.ticket_id}")
        print(f"symbol: {t.symbol}")
        print(f"strategy: {t.strategy_name}")
        print(f"AI confidence: {t.ai_score}")
        print(f"bid: {t.bid_at_entry}")
        print(f"ask: {t.ask_at_entry}")
        print(f"spread: {t.spread_at_entry}")
        print(f"requested entry: {signal.entry_price}")
        print(f"actual fill: {t.entry_price}")
        print(f"original SL: {t.sl}")
        print(f"TP: {t.tp}")
        print(f"TP1: {t.tp1}")
        print(f"TP2: {t.tp2}")
        
        # Validation Check at Entry (Rule 4)
        if abs(t.tp - t.tp2) > 0.00001:
            print(f"[ERROR] TP CONSISTENCY FAILURE: TP ({t.tp}) != TP2 ({t.tp2})")
            return
        else:
            print(f"[OK] TP CONSISTENCY OK: TP == TP2")

        print(f"stage1_partial_done: {t.stage1_partial_done}")
        print(f"stage1_sl_done: {t.stage1_sl_done}")
        print(f"stage2_partial_done: {t.stage2_partial_done}")
        print(f"stage2_sl_done: {t.stage2_sl_done}")
        
    print("\n--- [4] DURING MANAGEMENT (SIMULATING PROGRESS) ---")
    
    # We will simulate price moves by manipulating the DB entry_price and tp1
    # while the worker uses the REAL current market bid for progress calculation.
    current_tick = mt5_client.get_latest_tick(symbol)
    current_bid = current_tick['bid']
    
    print(f"Current Market Bid: {current_bid}")
    
    # For Stage 1 (65%):
    # Bid 1.15226 - Entry 1.14856 = 0.0037
    # TP1 1.15356 - Entry 1.14856 = 0.0050
    # Progress = 0.0037 / 0.0050 = 0.74 ( > 0.60 trigger )
    
    fake_entry_1 = current_bid - 0.0037
    fake_tp1_1 = current_bid + 0.0013
    
    print(f"\n-> TRIGGERING STAGE 1: Simulating 65% progress...")
    print(f"   (Calculated Progress: (Bid {current_bid} - Entry {fake_entry_1:.5f}) / (TP1 {fake_tp1_1:.5f} - Entry {fake_entry_1:.5f}))")
    print(f"   Expected Progress: {(current_bid - fake_entry_1) / (fake_tp1_1 - fake_entry_1):.2%}")
    
    with DatabaseContext() as db:
        t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
        t.entry_price = fake_entry_1
        t.tp1 = fake_tp1_1
        # Also sync current SL to Trade object so worker sees it for monotonic check
        pos_list = mt5.positions_get(ticket=ticket)
        if pos_list: t.sl = pos_list[0].sl
        db.commit()

    worker._manage_open_positions(symbol, m1_df, m15_df)
    time.sleep(1) # Sync
    
    print("\n[VERIFYING STAGE 1]")
    with DatabaseContext() as db:
        db.expire_all()
        t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
        pos_list = mt5.positions_get(ticket=ticket)
        if pos_list:
            pos = pos_list[0]
            print(f"   Original Volume: {t.initial_volume}")
            print(f"   Current Bid: {current_bid:.5f}")
            print(f"   Stored Entry: {t.entry_price:.5f}")
            print(f"   Stored TP1: {t.tp1:.5f}")
            print(f"   MT5 Position Volume: {pos.volume}")
            print(f"   MT5 Position SL: {pos.sl:.5f}")
            sl_orig = float(sl)
            if pos.sl > sl_orig:
                print(f"   [OK] MONOTONIC CHECK: SL improved from {sl_orig:.5f} to {pos.sl:.5f}")
            else:
                print(f"   [FAIL] MONOTONIC FAILURE: SL {pos.sl:.5f} is not better than original {sl_orig:.5f}")
        else:
            print("   [FAIL] Position closed prematurely during Stage 1")

    # For Stage 2 (85%):
    # Bid 1.15226 - Entry 1.14776 = 0.0045
    # TP1 1.15276 - Entry 1.14776 = 0.0050
    # Progress = 0.0045 / 0.0050 = 0.90 ( > 0.80 trigger )
    
    fake_entry_2 = current_bid - 0.0045
    fake_tp1_2 = current_bid + 0.0005
    
    print(f"\n-> TRIGGERING STAGE 2: Simulating 85% progress...")
    print(f"   (Calculated Progress: (Bid {current_bid} - Entry {fake_entry_2:.5f}) / (TP1 {fake_tp1_2:.5f} - Entry {fake_entry_2:.5f}))")
    print(f"   Expected Progress: {(current_bid - fake_entry_2) / (fake_tp1_2 - fake_entry_2):.2%}")

    with DatabaseContext() as db:
        t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
        t.entry_price = fake_entry_2
        t.tp1 = fake_tp1_2
        db.commit()

    worker._manage_open_positions(symbol, m1_df, m15_df)
    time.sleep(1) # Sync
    
    print("\n[VERIFYING STAGE 2]")
    with DatabaseContext() as db:
        db.expire_all()
        t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
        pos_list = mt5.positions_get(ticket=ticket)
        if pos_list:
            pos = pos_list[0]
            print(f"   Current Bid: {current_bid:.5f}")
            print(f"   Stored Entry: {t.entry_price:.5f}")
            print(f"   Stored TP1: {t.tp1:.5f}")
            print(f"   Stored TP2 (Hard TP): {t.tp2:.5f}")
            print(f"   MT5 Position Volume: {pos.volume}")
            print(f"   MT5 Position SL: {pos.sl:.5f}")
            if pos.sl >= t.sl:
                print(f"   [OK] MONOTONIC CHECK: SL maintained or improved ({pos.sl:.5f} >= {t.sl:.5f})")
            else:
                print(f"   [FAIL] MONOTONIC FAILURE: SL degraded ({pos.sl:.5f} < {t.sl:.5f})")
            
            if pos.volume > 0:
                print(f"   [OK] RUNNER MAINTAINED: {pos.volume} units still open.")
            else:
                print(f"   [FAIL] RUNNER CLOSED: Position fully exited at Stage 2.")
        else:
             print("   [FAIL] Position closed fully (CLOSED_FULL) but should have remained open.")

    print("\n--- [5] AT EXIT ---")
    print("Closing remaining volume manually to finalize trade...")
    pos_list = mt5.positions_get(ticket=ticket)
    if pos_list:
        p = pos_list[0]
        exit_price = mt5.symbol_info_tick(symbol).bid
        req_close = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": p.volume,
            "type": mt5.ORDER_TYPE_SELL,
            "position": ticket,
            "price": exit_price,
            "deviation": 20,
            "magic": 123456,
            "comment": "manual_close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        r2 = mt5.order_send(req_close)
        if r2 and r2.retcode == mt5.TRADE_RETCODE_DONE:
             print(f"   Final exit price: {r2.price}")
             # mark exit in DB
             with DatabaseContext() as db:
                 t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
                 t.status = "CLOSED"
                 t.final_exit_reason = "USER_REQUEST_CLOSE"
                 db.commit()
    
    with DatabaseContext() as db:
         db.expire_all() # Ensure fresh data
         t = db.query(Trade).filter(Trade.ticket_id == ticket).first()
         print(f"   final_exit_status in DB: {t.status}")
         print(f"   final_exit_reason in DB: {t.final_exit_reason}")
         
    print("\n--- [6] FINAL VERIFICATION ---")
    print("Checking DB Trade Events for duplicate partials...")
    with DatabaseContext() as db:
        evs = db.query(TradeEvent).filter(TradeEvent.ticket_id == ticket).all()
        if not evs:
            print("   (No events found? Check if they were committed correctly)")
        for i, ev in enumerate(evs):
            print(f"   Event {i+1}: {ev.event_type} (Vol {ev.old_value} -> {ev.new_value})")

    # Restart-proof example
    print("\n" + "="*40)
    print("   [7] RESTART-PROOF TEST (Protection Gap)")
    print("="*40)
    
    lot_size2 = 0.04
    req2 = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size2,
        "type": mt5.ORDER_TYPE_BUY,
        "price": ask,
        "sl": ask - 0.0050,
        "tp": ask + 0.0050,
        "deviation": 20,
        "magic": 123456,
        "comment": "gap_test",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    print(f"Opening second trade for Gap Test...")
    # Fix ExecRes for this manual creation
    class ExecRes:
        def __init__(self, ticket, price, retcode):
            self.ticket = ticket
            self.price = price
            self.retcode = retcode
            self.success = retcode == mt5.TRADE_RETCODE_DONE
            self.order_type = "BUY"
            self.lot_size = lot_size2
            self.sl = ask - 0.0050
            self.tp = ask + 0.0050

    r3_raw = mt5.order_send(req2)
    if not r3_raw or r3_raw.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to open second trade for gap test. Retcode: {getattr(r3_raw, 'retcode', 'None')}")
    else:
        ticket2 = r3_raw.order
        print(f"Opened Trade #{ticket2} for Gap Test")
        r3 = ExecRes(ticket2, r3_raw.price, r3_raw.retcode)
        
        # Manually set DB state to simulate: Partial already happened, but SL didn't
        with DatabaseContext() as db:
            trade2 = Trade(
                ticket_id=ticket2,
                symbol=symbol,
                type="BUY",
                volume=lot_size2,
                initial_volume=lot_size2,
                entry_price=r3.price,
                sl=req2["sl"],
                tp=req2["tp"],
                tp1=r3.price + 0.0040,
                status="OPEN",
                stage1_partial_done=True,   # SIMULATE ALREADY DONE
                stage1_sl_done=False        # SIMULATE FAILED/INTERRUPTED
            )
            db.add(trade2)
            db.commit()
            
        print(f"Set DB: stage1_partial_done=True, stage1_sl_done=False")
        
        # Trigger manager to see if it retries ONLY the SL
        print("Calling _manage_open_positions to trigger retry...")
        
        # Update entry/tp1 to make sure it's in the trigger zone (65%)
        # Actually it's already past progress because stage1_partial_done is True
        # but the code checks `progress >= trigger and not stage1_executed`
        # and `stage1_executed` is (stage1_partial_done AND stage1_sl_done).
        # So it should trigger the SL part.
        
        with DatabaseContext() as db:
            t2 = db.query(Trade).filter(Trade.ticket_id == ticket2).first()
            current_bid_2 = mt5_client.get_latest_tick(symbol)['bid']
            # Entry 0.0040 below bid = 0.0040 / 0.0050 = 80% progress
            t2.entry_price = current_bid_2 - 0.0040
            t2.tp1 = current_bid_2 + 0.0010
            db.commit()

        worker._manage_open_positions(symbol, m1_df, m15_df)
        time.sleep(1)
        
        with DatabaseContext() as db:
            t2 = db.query(Trade).filter(Trade.ticket_id == ticket2).first()
            print(f"RESULT:")
            print(f"   DB stage1_partial_done: {t2.stage1_partial_done}")
            print(f"   DB stage1_sl_done: {t2.stage1_sl_done} (Should be True now)")
            
            # Verify MT5 SL
            pos_list = mt5.positions_get(ticket=ticket2)
            if pos_list:
                pos2 = pos_list[0]
                print(f"   MT5 SL: {pos2.sl} (Requested security SL)")
                print(f"   MT5 Vol: {pos2.volume} (Should still be {lot_size2}, no second partial sent)")
                
                # Cleanup
                req_close_2 = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos2.volume,
                    "type": mt5.ORDER_TYPE_SELL,
                    "position": ticket2,
                    "price": mt5.symbol_info_tick(symbol).bid,
                    "deviation": 20,
                    "magic": 123456,
                    "comment": "cleanup",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_FOK,
                }
                mt5.order_send(req_close_2)

    mt5_client.disconnect()
    print("\n--- DEMO COMPLETE ---")

if __name__ == '__main__':
    capture_trade()
