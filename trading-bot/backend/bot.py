import time
import logging
import MetaTrader5 as mt5
from data_layer.mt5_connector import MT5Connector
from strategy import SMCStrategy
from ai_model import MarketPredictor
from risk_engine.risk_manager import RiskManager
from data_layer.news_provider import news_manager
from indicators import SMCIndicators
from api import run_api, BOT_DATA
import threading
import pandas as pd
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TradingBot")

TRADE_COOLDOWN_SECONDS = 300  # 5 minutes between trades

class TradingBot:
    """
    Revised Main Loop: Uses the 5-Family Strategy + Consolidated AI Brain.
    Supports 3-class logic (BUY/SELL/NO TRADE) and net profit expectancy.
    """
    def __init__(self):
        self.mt5 = MT5Connector()
        self.strategy = SMCStrategy()
        self.indicators = SMCIndicators()
        self.predictor = MarketPredictor()
        self.risk_manager = RiskManager()
        self.running = False
        self.last_trade_time = 0

    def _add_log(self, msg):
        logger.info(msg)
        if "logs" not in BOT_DATA["status"]:
            BOT_DATA["status"]["logs"] = []
        if not BOT_DATA["status"]["logs"] or BOT_DATA["status"]["logs"][-1] != msg:
            BOT_DATA["status"]["logs"].append(msg)
            if len(BOT_DATA["status"]["logs"]) > 20:
                BOT_DATA["status"]["logs"].pop(0)

    def _is_market_open(self, symbol):
        # Crypto always open
        if any(c in symbol.upper() for c in ["BTC", "ETH", "SOL", "CRYPTO"]):
            return True
        now = datetime.datetime.now(datetime.timezone.utc)
        if now.weekday() == 5: return False # Sat
        if now.weekday() == 6 and now.hour < 21: return False # Sun
        if now.weekday() == 4 and now.hour >= 22: return False # Fri
        return True

    def start(self):
        if not self.mt5.connect():
            logger.error("Failed to connect to MT5")
            return
        
        self.running = True
        logger.info("Consolidated AI Engine started...")
        
        # Start background syncers
        news_manager.start_monitoring()
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        
        time.sleep(2)
        self._add_log("[SYS] Initializing Quant Engine...")
        self._add_log(f"[SYS] Session: {self._get_session_name()} | Preferred: {BOT_DATA['status'].get('preferred_session', 'ALL')}")
        self._add_log("[SYS] Engine ONLINE — Scanning for institutional setups...")
        
        while self.running:
            try:
                # 1. Sync State from Dashboard
                active_symbols = BOT_DATA["status"].get("active_symbols", ["GOLD"])
                is_engine_on = BOT_DATA["status"].get("is_running", False)
                risk_cfg = BOT_DATA.get("risk", {})
                
                # Update Risk Manager with live settings
                self.risk_manager.risk_per_trade = risk_cfg.get("risk_per_trade", 0.005)
                self.risk_manager.max_trades = risk_cfg.get("max_trades", 2)
                self.risk_manager.max_daily_losses = risk_cfg.get("max_daily_trades", 5) 
                self.risk_manager.daily_loss_limit = risk_cfg.get("daily_loss_limit", 0.10)
                
                # 2. Sync Real-time Global Account Data
                acc_info = self.mt5.get_account_info()
                open_trades = self.mt5.get_open_positions()
                history_deals = self.mt5.get_history_deals(days=30)
                
                BOT_DATA["status"].update({
                    "balance": acc_info.get('balance', 0),
                    "equity": acc_info.get('equity', 0),
                    "active_trades": len(open_trades),
                    "session": self._get_session_name()
                })
                BOT_DATA["trades"] = open_trades
                BOT_DATA["history"] = history_deals
                
                # Sync News for Frontend (Global)
                BOT_DATA["news"] = [
                    {
                        "name": e["name"],
                        "time": e["time"].strftime("%H:%M") if isinstance(e["time"], datetime.datetime) else e["time"],
                        "impact": e["impact"],
                        "symbol": e["symbol"]
                    } for e in news_manager.events
                ]

                # Decision Logic Gate
                if not is_engine_on:
                    time.sleep(5)
                    continue

                # --- MULTI-SYMBOL PROCESSING LOOP ---
                for current_symbol in active_symbols:
                    try:
                        if not self._is_market_open(current_symbol):
                            continue

                        # Ensure symbol exists in memory
                        if current_symbol not in BOT_DATA["symbols"]:
                            BOT_DATA["symbols"][current_symbol] = {
                                "chart": [], "overlays": {"fvg_zones":[], "order_blocks":[], "sweeps":[], "bos_markers":[], "support_resistance":[]},
                                "last_decision": {"direction": "WAIT", "strategy": "Monitoring", "reason": "Syncing...", "score": 0, "flow": []}
                            }

                        # Fetch MTF Bars (Lean lookback for speed)
                        data_m1 = self.mt5.get_market_data(current_symbol, "M1", 500)
                        data_m5 = self.mt5.get_market_data(current_symbol, "M5", 600)
                        data_m15 = self.mt5.get_market_data(current_symbol, "M15", 300)

                        if any(d is None for d in [data_m1, data_m5, data_m15]):
                            continue

                        # --- SYNC CHART DATA & OVERLAYS ---
                        CHART_DISPLAY_CANDLES = 500  
                        processed_df = self.strategy._preprocess(data_m1)
                        chart_df = processed_df.tail(CHART_DISPLAY_CANDLES).copy()

                        def _safe_ts(t):
                            return int(t.timestamp()) if hasattr(t, 'timestamp') else int(t)

                        chart_records = [
                            {"time": _safe_ts(t), "open": float(o), "high": float(h), "low": float(l), "close": float(c)}
                            for t, o, h, l, c in zip(chart_df['time'], chart_df['open'], chart_df['high'], chart_df['low'], chart_df['close'])
                        ]

                        overlays = {"fvg_zones": [], "order_blocks": [], "sweeps": [], "bos_markers": [], "support_resistance": []}
                        valid_fvgs = processed_df[(processed_df['fvg_bullish'] | processed_df['fvg_bearish']) & ~processed_df['fvg_mitigated'].fillna(False)]
                        valid_obs = processed_df[processed_df['order_block'] != 0].dropna(subset=['order_block'])
                        valid_sweeps = processed_df[processed_df['sweep'] != 0].dropna(subset=['sweep'])
                        valid_bos = processed_df[processed_df['bos'] != 0].dropna(subset=['bos'])

                        for t, top, bot, is_bull in zip(valid_fvgs['time'], valid_fvgs['fvg_top'], valid_fvgs['fvg_bottom'], valid_fvgs['fvg_bullish']):
                            overlays["fvg_zones"].append({"time": _safe_ts(t), "top": float(top), "bottom": float(bot), "type": "bullish" if is_bull else "bearish"})
                        for t, h, l, ob in zip(valid_obs['time'], valid_obs['high'], valid_obs['low'], valid_obs['order_block']):
                            overlays["order_blocks"].append({"time": _safe_ts(t), "top": float(h), "bottom": float(l), "type": "bullish" if ob == 1 else "bearish"})
                        for t, l, h, sw in zip(valid_sweeps['time'], valid_sweeps['low'], valid_sweeps['high'], valid_sweeps['sweep']):
                            overlays["sweeps"].append({"time": _safe_ts(t), "price": float(l) if sw == 1 else float(h), "type": "bullish" if sw == 1 else "bearish"})
                        for t, l, h, bos in zip(valid_bos['time'], valid_bos['low'], valid_bos['high'], valid_bos['bos']):
                            overlays["bos_markers"].append({"time": _safe_ts(t), "price": float(h) if bos == 1 else float(l), "type": "bullish" if bos == 1 else "bearish"})
                        
                        sr_levels = self.indicators.detect_sr_levels(data_m1)
                        for level in sr_levels:
                            overlays["support_resistance"].append({"price": float(level['price']), "type": level['type'].lower(), "time": _safe_ts(level['time'])})

                        BOT_DATA["symbols"][current_symbol]["chart"] = chart_records
                        BOT_DATA["symbols"][current_symbol]["overlays"] = overlays
                        
                        # News Defense
                        is_news, event_name = news_manager.is_news_active()
                        if is_news:
                            continue

                        # Active Position Management
                        self._manage_open_positions(current_symbol, data_m1)

                        # Strategy Analysis
                        signal, price, name, details = self.strategy.analyze(data_m1, data_m5, data_m15)
                        
                        decision = {
                            "direction": signal if signal != "WAIT" else "NONE",
                            "strategy": name if name else "Monitoring",
                            "reason": details.get("reason", name if name else "Searching..."),
                            "score": details.get("mcs_score", 0) * 15 + 10 if signal != "WAIT" else 0,
                            "flow": ["SMC analysis active"]
                        }

                        if signal != "WAIT":
                            decision["flow"] = ["SMC setup identified", f"Pattern: {name}"]
                            
                            # AI Engine Confirmation
                            ai_choice, ai_conf = self.predictor.predict(data_m1)
                            ai_confirmed = (signal == "BUY" and ai_choice == 1) or (signal == "SELL" and ai_choice == 2)
                            
                            if not ai_confirmed:
                                decision["flow"].append("AI Brain divergence detected")
                                decision["score"] = 0
                            else:
                                decision["flow"].append(f"AI Brain confirmed ({ai_conf*100:.1f}%)")
                                decision["score"] = round(ai_conf * 100, 1)
                                # Risk Engine Analysis
                                tick = mt5.symbol_info_tick(current_symbol)
                                current_spread = (tick.ask - tick.bid) / (mt5.symbol_info(current_symbol).point) if tick else 0
                                
                                is_safe, reason = self.risk_manager.is_risk_acceptable(
                                    open_trades, history_deals, acc_info.get('balance', 0), 
                                    symbol=current_symbol, spread=current_spread
                                )

                                if not is_safe:
                                    decision["flow"].append(f"Risk Block: {reason}")
                                else:
                                    decision["flow"].append("Risk parameters validated")
                                    # Execution
                                    direction = 1 if signal == "BUY" else -1
                                    sl, tp = self.risk_manager.calculate_sl_tp(price, direction)
                                    symbol_info = mt5.symbol_info(current_symbol)
                                    lot_size = self.risk_manager.calculate_lot_size(acc_info.get('balance', 0), price, sl, symbol_info)
                                    
                                    now_ts = time.time()
                                    if now_ts - self.last_trade_time > TRADE_COOLDOWN_SECONDS:
                                        self._add_log(f"🚀 EXECUTE: {name} {signal} on {current_symbol} @ {price:.4f}")
                                        order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL
                                        res = self.mt5.place_order(current_symbol, order_type, lot_size, sl=sl, tp=tp, comment=name[:15])
                                        if res:
                                            self.last_trade_time = time.time()
                                            self._add_log(f"   ↳ ✅ Ticket: #{res.order}")
                                            BOT_DATA["rationales"][res.order] = f"{name} (MCS: {details.get('mcs_score', 0)})"
                                            decision["flow"].append("Order executed")
                                            decision["order_id"] = res.order
                        
                        # Update per-symbol memory
                        BOT_DATA["symbols"][current_symbol]["last_decision"] = decision
                        
                    except Exception as sym_err:
                        logger.error(f"Error processing {current_symbol}: {sym_err}")
                        continue
                
                # Global sync of last decision
                BOT_DATA["last_decision"] = decision

                time.sleep(2) # Snappier loop (from 10s -> 2s)
            except Exception as e:
                logger.error(f"Bot loop error: {e}")
                time.sleep(5)

    def _get_session_name(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        h = now.hour
        if 7 <= h < 11: return "LONDON"
        if 13 <= h < 16: return "NEW YORK"
        if 11 <= h < 13: return "LON/NY GAP"
        return "ASIAN/AFTER"

    def _manage_open_positions(self, symbol, df):
        """ Institutional Position Manager: Trails SL to BE and beyond. """
        positions = mt5.positions_get(symbol=symbol)
        if not positions: return

        atr = self.indicators.calculate_atr(df)
        
        for pos in positions:
            tick = mt5.symbol_info_tick(symbol)
            if not tick: continue
            
            direction = 1 if pos.type == mt5.POSITION_TYPE_BUY else -1
            current_price = tick.bid if direction == 1 else tick.ask
            
            new_sl = self.risk_manager.calculate_trailing_stop(
                current_price, pos.price_open, pos.sl, direction, atr
            )
            
            if abs(new_sl - pos.sl) > 0.0001: # Small threshold to avoid redundant updates
                self._add_log(f"🛡️ PROFIT GUARD: Trailing SL for #{pos.ticket} -> {new_sl:.4f}")
                self.mt5.place_order(
                    symbol, pos.type, pos.volume, sl=new_sl, tp=pos.tp,
                    request_type=mt5.TRADE_ACTION_SLTP, position_id=pos.ticket
                )

    def stop(self):
        self.running = False
        self.mt5.disconnect()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    bot = TradingBot()
    bot.start()
