import MetaTrader5 as mt5
from app.storage.db import DatabaseContext
from app.storage.models import Trade

def force_close():
    mt5.initialize()
    poses = mt5.positions_get()
    
    if not poses:
        print("No MT5 positions.")
        return
        
    for p in poses:
        tick = mt5.symbol_info_tick(p.symbol)
        order_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": order_type,
            "position": p.ticket,
            "price": price,
            "deviation": 20,
            "magic": 0,
            "comment": "Force close invalid",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(request)
        print("MT5 Close Res:", res)
        
        with DatabaseContext() as db:
            t = db.query(Trade).filter(Trade.ticket_id == str(p.ticket)).first()
            if t:
                t.status = "CLOSED"
                t.final_exit_reason = "INVALID_TEST_TRADE"
                db.commit()
                print("DB Updated.")

if __name__ == "__main__":
    force_close()
