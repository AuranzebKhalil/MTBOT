import logging
import MetaTrader5 as mt5
from typing import List, Dict
from app.market_data.mt5_client import MT5Client
from app.storage.db import DatabaseContext
from app.storage.models import Trade
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TradeSynchronizer:
    def __init__(self, mt5_client: MT5Client):
        self.client = mt5_client

    def sync_open_trades(self):
        """Syncs local database with actual MT5 positions."""
        mt5_positions = self.client.get_positions()
        mt5_tickets = {p['ticket']: p for p in mt5_positions}

        with DatabaseContext() as db:
            # 1. Update existing OPEN trades in DB
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            # Check against ALL tickets in DB to prevent IntegrityError on re-import
            db_tickets = {t[0] for t in db.query(Trade.ticket_id).all()}
            
            for trade in open_trades:
                if trade.ticket_id in mt5_tickets:
                    pos = mt5_tickets[trade.ticket_id]
                    # Update metrics for OPEN trades
                    trade.volume = float(pos.get('volume', trade.volume))
                    if not trade.initial_volume or trade.initial_volume == 0:
                        trade.initial_volume = trade.volume
                    trade.profit = float(pos.get('profit', 0.0))
                    trade.commission = float(pos.get('commission', 0.0))
                    trade.swap = float(pos.get('swap', 0.0))
                    # Sync stops to ensure UI matches MT5 exactly
                    trade.sl = float(pos.get('sl', 0.0))
                    trade.tp = float(pos.get('tp', 0.0))
                    trade.type = "BUY" if pos.get('type') == 0 else "SELL"
                    # Ensure entry price is correct from position
                    if not trade.entry_price:
                        trade.entry_price = float(pos.get('price_open', 0.0))
                else:
                    # Position no longer exists in MT5 -> It was CLOSED (or cancelled)
                    logger.info(f"Trade {trade.ticket_id} no longer in MT5 positions. Marking as CLOSED.")
                    trade.status = "CLOSED"
                    trade.exit_time = datetime.now(timezone.utc)
                    # Try to fetch deal history to get final profit/exit price
                    self._fill_closed_trade_details(trade)
            
            # 2. Import manual/external trades NOT in DB
            for ticket, pos in mt5_tickets.items():
                if ticket not in db_tickets:
                    logger.info(f"Importing external trade {ticket} ({pos.get('symbol')}) to DB")
                    new_trade = Trade(
                        ticket_id=ticket,
                        symbol=pos.get('symbol'),
                        type="BUY" if pos.get('type') == 0 else "SELL", # POSITION_TYPE_BUY = 0
                        volume=float(pos.get('volume', 0.0)),
                        initial_volume=float(pos.get('volume', 0.0)),
                        entry_price=float(pos.get('price_open', 0.0)),
                        sl=float(pos.get('sl', 0.0)),
                        tp=float(pos.get('tp', 0.0)),
                        profit=float(pos.get('profit', 0.0)),
                        status="OPEN",
                        strategy_name="Manual/External",
                        rationale="Trade detected on MT5 account (External/Manual)"
                    )
                    db.add(new_trade)
            
            db.commit()

    def sync_history(self):
        """Repairs CLOSED trades in DB that have 0 profit/volume by searching MT5 history."""
        with DatabaseContext() as db:
            incomplete_trades = db.query(Trade).filter(
                Trade.status == "CLOSED",
                (Trade.profit == 0.0) | (Trade.volume == 0.0)
            ).all()

            if not incomplete_trades:
                return

            logger.info(f"Attempting to repair {len(incomplete_trades)} historical trades...")
            for trade in incomplete_trades:
                self._fill_closed_trade_details(trade)
            
            db.commit()

    def _fill_closed_trade_details(self, trade: Trade):
        """Fetches final deal details from MT5 history for a closed position."""
        import time
        deals = mt5.history_deals_get(position=trade.ticket_id)
        
        if deals:
            # We want the 'OUT' deal (closing deal) to get the final exit price and profit
            # Note: A single position ticket can have multiple deals (In, Out, Swaps)
            exit_deal = None
            total_profit = 0.0
            total_commission = 0.0
            total_swap = 0.0
            volume = 0.0

            for deal in deals:
                d = deal._asdict()
                total_profit += d.get('profit', 0.0)
                total_commission += d.get('commission', 0.0)
                total_swap += d.get('swap', 0.0)
                
                # Update volume from the deal (could be partial, but we want the max or the 'IN' volume)
                if d.get('entry') == 0: # DEAL_ENTRY_IN
                    volume = d.get('volume', volume)
                
                if d.get('entry') == 1: # DEAL_ENTRY_OUT
                    exit_deal = d

            if exit_deal:
                trade.exit_price = exit_deal.get('price')
                trade.profit = total_profit
                trade.commission = total_commission
                trade.swap = total_swap
                trade.volume = volume
                trade.exit_time = datetime.fromtimestamp(exit_deal.get('time'), tz=timezone.utc) if exit_deal.get('time') else datetime.now(timezone.utc)
                
                # Determine Exit Reason if not already set by worker
                if not trade.final_exit_reason:
                    reason_id = exit_deal.get('reason')
                    if reason_id == 4: # DEAL_REASON_TP
                        trade.final_exit_reason = "TP2_HIT"
                    elif reason_id == 3: # DEAL_REASON_SL
                        # Check if it was a Break-even exit
                        # (Price is near entry + small buffer)
                        entry = trade.entry_price
                        exit_p = trade.exit_price
                        is_buy = trade.type == "BUY"
                        
                        # Use 5 points as comparison tolerance
                        point = 0.0001 # TODO: Fetch real point
                        diff = (exit_p - entry) if is_buy else (entry - exit_p)
                        
                        if trade.stage1_executed and diff >= 0 and diff <= (point * 50): # Within 5 pips of BE
                            trade.final_exit_reason = "BREAKEVEN_EXIT"
                        else:
                            trade.final_exit_reason = "TRAILING_STOP_HIT"
                    elif reason_id == 5:
                        trade.final_exit_reason = "STOP_OUT"
                    else:
                        trade.final_exit_reason = "MANUAL_EXIT"
            else:
                # If no clear OUT deal, use totals found so far
                trade.profit = total_profit
                trade.volume = volume or trade.volume
        else:
            # Prevent infinite sync loops if deals are missing in MT5 history
            if trade.profit == 0.0: trade.profit = 0.00001
            if trade.volume == 0.0: trade.volume = 0.01
        
        if not trade.exit_price:
            # Fallback if history search fails or still empty
            trade.exit_price = trade.entry_price or 0.0

    def get_daily_pnl(self) -> float:
        """Calculates realized profit for today."""
        now = datetime.now()
        start_of_day = datetime(now.year, now.month, now.day)
        
        deals = mt5.history_deals_get(start_of_day, now)
        if not deals:
            return 0.0
            
        total_pnl = 0.0
        for deal in deals:
            if deal is None: continue
            d = deal._asdict() if hasattr(deal, '_asdict') else {}
            total_pnl += float(d.get('profit', 0.0))
            total_pnl += float(d.get('commission', 0.0))
            total_pnl += float(d.get('swap', 0.0))
            
        return total_pnl
