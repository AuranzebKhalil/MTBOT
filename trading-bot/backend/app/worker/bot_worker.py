import time
import logging
import threading
import uuid
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from app.core.config import settings
from app.market_data.mt5_client import MT5Client
from app.strategy.engine import StrategyEngine
from app.ai.predictor import MarketPredictor
from app.risk.manager import RiskManager
from app.execution.executor import OrderExecutor
from app.execution.synchronizer import TradeSynchronizer
from app.storage.db import DatabaseContext
from app.storage.models import BotState, Trade, SignalLog, ExecutionLog, LatencyLog, User, TradeAnnotation, TradeEvent, BlockedZone
from app.telemetry.metrics import metrics
from indicators import SMCIndicators

from app.core.datatypes import TradingSession, MarketRegime, TradeSignal, SignalStatus, OrderSide
from app.strategy.context.regime import RegimeDetector
from app.strategy.context.session import SessionManager
from app.strategy.smc import (
    SMCSweepReclaimStrategy, SMCVsaShiftStrategy, SMCContinuationRetestStrategy,
    SMCFirstTouchMitigationStrategy, SMCExhaustionReversalStrategy,
    SMCMSSStrategy, SMCBreakerStrategy, SMCVolumeFlowStrategy
)
from app.strategy.hybrid_strategies import (
    MeanReversionStrategy, SupportResistanceStrategy,
    BreakoutStrategy, HybridSwitcherStrategy, MadTrendLoopStrategy
)

logger = logging.getLogger("BotWorker")

class BotWorker:
    def __init__(self):
        self.mt5 = MT5Client()
        self.predictor = MarketPredictor()
        
        # Initialize new StrategyEngine architecture dependencies
        self.regime_detector = RegimeDetector()
        self.session_manager = SessionManager({
            TradingSession.ASIA: (0, 8),
            TradingSession.LONDON: (8, 16),
            TradingSession.NEW_YORK: (13, 21),
            TradingSession.OVERLAP: (12, 13)
        })
        self.indicators = SMCIndicators()
        
        # Register ALL Families
        self.strategies = [
            SMCSweepReclaimStrategy(self.indicators),
            SMCVsaShiftStrategy(self.indicators),
            SMCContinuationRetestStrategy(self.indicators),
            SMCFirstTouchMitigationStrategy(self.indicators),
            SMCExhaustionReversalStrategy(self.indicators),
            SMCMSSStrategy(self.indicators),
            SMCBreakerStrategy(self.indicators),
            SMCVolumeFlowStrategy(self.indicators),
            MeanReversionStrategy(self.indicators),
            SupportResistanceStrategy(self.indicators),
            BreakoutStrategy(self.indicators),
            HybridSwitcherStrategy(self.indicators),
            MadTrendLoopStrategy(self.indicators)
        ]
        
        self.strategy = StrategyEngine(
            ai_predictor=self.predictor,
            strategies=self.strategies
        )
        self.risk = RiskManager()
        self.executor = OrderExecutor(self.mt5)
        self.synchronizer = TradeSynchronizer(self.mt5)
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
        # Smart Context Cache: {symbol: {tf: analyzed_df, "last_update": timestamp}}
        self.structural_cache = {} 
        self._last_heartbeat = 0
        self._config_printed = False
        
        from app.services.news_service import NewsService
        self.news_service = NewsService()
        self.loop_cooldowns = []
        self.loop_blocked_zones = []
        self.last_analytics_update = datetime.min.replace(tzinfo=timezone.utc)
        
        logger.info("🤖 BotWorker initialized with enhanced filters.")

    def _update_bot_status(self, is_running: Optional[bool] = None, message: Optional[str] = None, action: Optional[str] = None):
        """Internal helper to sync bot health/activity to the database for the dashboard."""
        try:
            with DatabaseContext() as db:
                state = db.query(BotState).first()
                if state:
                    if is_running is not None: state.is_running = is_running
                    if message is not None: state.status_message = message
                    if action is not None: state.current_action = action
                    state.last_loop_at = datetime.now(timezone.utc)
                    db.commit()
        except Exception as e:
            logger.error(f"Failed to update bot status in DB: {e}")

    def start(self):
        if self.running: return
        self.running = True
        thread = threading.Thread(target=self._loop, daemon=True)
        self._thread = thread
        thread.start()
        logger.info("Bot Worker started")

    def stop(self):
        self.running = False
        thread = self._thread
        if thread is not None:
            thread.join(timeout=5)
        self.mt5.disconnect()
        logger.info("Bot Worker stopped")

    def _log_activity(self, tag: str, message: str):
        """Helper to push a system log to the live_logs array."""
        try:
            with DatabaseContext() as db:
                state = db.query(BotState).first()
                if state:
                    logs = list(state.live_logs or [])
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    msg = f"{timestamp} - [{tag}] {message}"
                    # Check if last log is same to avoid spamming
                    if not logs or logs[0] != msg:
                        logs.insert(0, msg)
                        state.live_logs = logs[:200] # Increase to 200 for better history
                        db.commit()
        except Exception as e:
            logger.error(f"Failed to update live logs: {e}")

    def _loop(self):
        self._update_bot_status(is_running=True, message="Initializing MT5 Connection...", action="Connecting")
        if not self.mt5.connect():
            self._update_bot_status(is_running=False, message="Stopped: MT5 Connection Failed", action="Offline")
            self._log_activity("HEALTH", "❌ CRITICAL: MT5 Connection Failed. Engine Stopped.")
            logger.error("Failed to connect to MT5, stopping worker")
            self.running = False
            return
        
        self._log_activity("HEALTH", "✅ MT5 Terminal Connected. AI Engine Synced.")

        while self.running:
            try:
                start_cycle = time.time()
                self._update_bot_status(message="Scanning Market...", action="Data Sync")
                
                # HEARTBEAT & STARTUP CONFIG
                current_time = time.time()
                if not self._config_printed:
                    with DatabaseContext() as db:
                        user = db.query(User).first()
                        if user:
                            print("\n" + "="*40)
                            print("LIVE ALPHA DEPLOYMENT ACTIVE")
                            print(f"Max Spread Points: 55")
                            print(f"Late Entry Threshold: {user.late_entry_threshold}")
                            print(f"Stage 1 Trigger: {user.partial_stage_1_trigger * 100}%")
                            print(f"Stage 2 Trigger: {user.partial_stage_2_trigger * 100}%")
                            print("="*40 + "\n")
                    self._config_printed = True

                if (current_time - float(self._last_heartbeat)) > 60:
                    self._log_activity("HEALTH", f"Pulse: Engine active. LIVE MODE: Multi-asset scan active.")
                    self._last_heartbeat = current_time

                self._process_cycle()
                
                duration = (time.time() - start_cycle) * 1000
                metrics.record_latency("full_cycle", duration)
                
                interval = settings.BOT_LOOP_INTERVAL
                sleep_time = max(0.1, interval - (duration / 1000))
                
                self._update_bot_status(
                    message=f"Cycle Complete ({duration:.0f}ms)", 
                    action=f"Sleeping {sleep_time:.1f}s"
                )
                time.sleep(sleep_time)
            except Exception as e:
                self._update_bot_status(message=f"Critical Error: {str(e)[:50]}", action="Error Recovery")
                self._log_activity("ERROR", f"Loop Exception: {str(e)[:100]}")
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(5)
        
        # Mark as stopped when loop exits normally
        self._update_bot_status(is_running=False, message="Bot Service Terminated", action="Stopped")

    def _process_cycle(self):
        # 1. Sync State/Config from DB (Short lived)
        with DatabaseContext() as db:
            state = db.query(BotState).first()
            if not state:
                state = BotState(is_running=False, active_symbols=settings.ACTIVE_SYMBOLS)
                db.add(state)
                db.commit()
            active_symbols = list(state.active_symbols)

        # 2. Sync account and trades (External calls)
        acc_info = self.mt5.get_account_info()
        positions = self.mt5.get_positions()
        
        # These methods have their own DatabaseContext
        self.synchronizer.sync_open_trades()
        self.synchronizer.sync_history()
        daily_pnl = self.synchronizer.get_daily_pnl()
        
        # 3. Update Metrics (Short lived)
        with DatabaseContext() as db:
            state = db.query(BotState).first()
            user = db.query(User).first()
            preferred_session = user.preferred_session if user else "ALL"
            current_session = self._get_current_session()
            
            # Fetch active cooldowns/blocked zones for metrics & risk context
            self._sync_and_cleanup_cooldowns(db)
            
            # Update metrics and filter status for the dashboard
            user_news_config = {
                "news_block_minutes_before": getattr(user, "news_block_minutes_before", 20),
                "news_block_minutes_after": getattr(user, "news_block_minutes_after", 20),
                "high_impact_only": getattr(user, "high_impact_only", True)
            }
            state.filter_status = {
                "news": self.news_service.get_active_event("XAUUSD", user_news_config) is not None,
                "session": preferred_session == "ALL" or preferred_session in current_session,
                "cooldowns_active": len(self.loop_cooldowns) > 0,
                "zones_blocked": len(self.loop_blocked_zones) > 0
            }
            
            ai_thr = float(getattr(state, "ai_confidence_threshold", None) or 0.48)
            state.current_metrics = {
                "balance": acc_info.get("balance", 0),
                "equity": acc_info.get("equity", 0),
                "daily_pnl": daily_pnl,
                "active_trades": len(positions),
                "preferred_session": preferred_session,
                "current_session": current_session[0] if current_session else "ASIAN",
                "ai_confidence_threshold": ai_thr,
                "filter_status": state.filter_status,
                "trading_mode": "LIVE"
            }
            state.active_cooldowns = self.loop_cooldowns
            state.active_blocked_zones = self.loop_blocked_zones
            state.last_loop_at = datetime.now(timezone.utc)
            
            # Periodically update analytics
            if (datetime.now(timezone.utc) - self.last_analytics_update).total_seconds() > 3600:
                self._update_strategy_analytics(db, state)
                self.last_analytics_update = datetime.now(timezone.utc)
                
            db.commit()
        
        # 3. Process each symbol
        symbol_specs = {}
        with DatabaseContext() as db:
            user = db.query(User).first()
            user_settings = {}
            strategy_settings = {}
            global_risk_settings = {
                "risk_per_trade": 0.01,
                "max_trades": 1,
                "daily_loss_limit": 0.03,
                "preferred_session": "ALL",
                "session_filter_enabled": True,
                "news_filter_enabled": True,
                "enable_post_sl_cooldown": True,
                "cooldown_bars_after_sl": 5,
                "same_zone_threshold_points": 100,
                "enable_same_zone_block": True,
                "same_zone_distance_atr_multiplier": 0.25,
                "enable_level_distance_filter": True,
                "min_reward_to_nearest_level_rr": 1.2,
                "min_reward_to_level_points": 50
            }

            if user:
                # Eagerly load settings into dictionary to avoid session detachment
                user_settings = dict(user.symbol_settings) if user.symbol_settings else {}
                strategy_settings = dict(user.strategy_settings) if user.strategy_settings else {}
                
                global_risk_settings.update({
                    "risk_per_trade": user.risk_per_trade,
                    "max_trades": user.max_trades,
                    "daily_loss_limit": user.daily_loss_limit,
                    "preferred_session": user.preferred_session,
                    "session_filter_enabled": getattr(user, "session_filter_enabled", True),
                    "news_filter_enabled": getattr(user, "news_filter_enabled", True),
                    "enable_post_sl_cooldown": getattr(user, "enable_post_sl_cooldown", True),
                    "cooldown_bars_after_sl": getattr(user, "cooldown_bars_after_sl", 5),
                    "same_zone_threshold_points": getattr(user, "same_zone_threshold_points", 100),
                    "enable_same_zone_block": getattr(user, "enable_same_zone_block", True),
                    "same_zone_distance_atr_multiplier": getattr(user, "same_zone_distance_atr_multiplier", 0.25),
                    "enable_level_distance_filter": getattr(user, "enable_level_distance_filter", True),
                    "min_reward_to_nearest_level_rr": getattr(user, "min_reward_to_nearest_level_rr", 1.2),
                    "min_reward_to_level_points": getattr(user, "min_reward_to_level_points", 50)
                })
            
            # --- LIVE EXECUTION ACTIVE ---
            # Check for protective stops gap on open trades
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            has_gap = any(
                (t.stage1_partial_done and not t.stage1_sl_done) or 
                (t.stage2_partial_done and not t.stage2_sl_done) 
                for t in open_trades
            )
            if has_gap:
                self._update_bot_status(action="Halted: Protection Gap", message="Gap found. Fixing SL before new entries.")
                logger.warning("🚫 NEW ENTRIES HALTED: Protection gap detected on an open trade.")
            
            # Multi-Symbol scan list is already captured in the beginning of the cycle as 'active_symbols'

        for symbol in active_symbols:
            eval_id = uuid.uuid4().hex[:6].upper()
            # Collect specs for frontend Engine Settings popup
            mt5_symbol = self.mt5.resolve_symbol(symbol)
            info = mt5.symbol_info(mt5_symbol) if mt5_symbol else None
            
            logger.info(f"[{eval_id}] >>> STARTED EVALUATION: {symbol} <<<")
            
            if info:
                tick = self.mt5.get_latest_tick(symbol)
                symbol_specs[symbol] = {
                    "min_volume": info.volume_min,
                    "volume_step": info.volume_step,
                    "last_price": tick["ask"] if tick else 0,
                    "point": info.point,
                    "contract_size": info.trade_contract_size,
                    "currency": info.currency_profit
                }

            # Merge settings for this symbol
            sym_specific = user_settings.get(symbol, {})
            merged_settings = {**global_risk_settings, **sym_specific}
            
            self._update_bot_status(action=f"Analyzing {symbol}")
            self._process_symbol(symbol, acc_info, positions, preferred_session, merged_settings, strategy_settings, symbol_specs.get(symbol), eval_id=eval_id)
        
        # Update specs in metrics for API access
        with DatabaseContext() as db:
            state = db.query(BotState).first()
            if state:
                metrics_copy = dict(state.current_metrics or {})
                metrics_copy["symbol_specs"] = symbol_specs
                state.current_metrics = metrics_copy
                db.commit()

        self._update_bot_status(action="Cycle Complete - Sleeping")

    def _get_current_session(self) -> list:
        """
        Determines the current active trading sessions in UTC.
        Labels overlaps for specifically targeted strategies.
        """
        h = datetime.now(timezone.utc).hour
        sessions = []
        
        # 1. Base Sessions
        is_asian = (h >= 23 or h < 8)
        is_london = (8 <= h < 16)
        is_ny = (13 <= h < 21)
        
        if is_asian: sessions.append("ASIAN")
        if is_london: sessions.append("LONDON")
        if is_ny: sessions.append("NEW YORK")
        
        # 2. Overlap Synthesis
        if is_london and is_ny:
            sessions.append("LONDON/NY OVERLAP")
        if is_asian and is_london:
            sessions.append("ASIAN/LONDON OVERLAP") # Small window usually
            
        if not sessions:
            sessions.append("ASIAN") # Deep night fallback
            
        return sessions

    def _sync_and_cleanup_cooldowns(self, db):
        """Removes expired cooldowns and loads active ones into memory."""
        now = datetime.now(timezone.utc)
        
        # 1. Cooldowns (Time-based blocks)
        # We store these in state for fast access. Ensure strings are converted back for comparison.
        cleaned = []
        for cd in self.loop_cooldowns:
            expiry = cd.get("expiry")
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            
            if expiry > now:
                cleaned.append(cd)
        self.loop_cooldowns = cleaned
        
        # 2. Blocked Zones (Price-based blocks)
        from app.storage.models import BlockedZone
        active_zones = db.query(BlockedZone).filter(BlockedZone.expiry > now).all()
        self.loop_blocked_zones = [
            {"symbol": z.symbol, "direction": z.direction, "price": z.price_level}
            for z in active_zones
        ]

    def _find_nearest_structural_level(self, symbol: str, m15_df: pd.DataFrame, direction: OrderSide) -> Optional[Dict[str, Any]]:
        """Finds the nearest swing high/low that might act as immediate resistance."""
        latest_price = m15_df['close'].iloc[-1]
        if direction == OrderSide.BUY:
            # Look for recent swing highs above current price
            highs = m15_df[m15_df['swing_high'] == True].tail(10) # Look at last 10 highs
            above = highs[highs['high'] > latest_price]
            if not above.empty:
                level = float(above['high'].min()) # Nearest one
                return {"price": level, "type": "Swing High", "tf": "M15"}
            return None
        else:
            # Look for recent swing lows below current price
            lows = m15_df[m15_df['swing_low'] == True].tail(10) # Look at last 10 lows
            below = lows[lows['low'] < latest_price]
            if not below.empty:
                level = float(below['low'].max()) # Nearest one
                return {"price": level, "type": "Swing Low", "tf": "M15"}
            return None

    def _handle_sl_hit(self, trade: Trade, db):
        """Triggers cooldown and blocks the zone after a loss."""
        now = datetime.now(timezone.utc)
        
        # 1. Add Cooldown (Time-based)
        from app.storage.models import User
        user = db.query(User).first()
        
        enabled = getattr(user, "enable_post_sl_cooldown", True)
        if not enabled:
            return

        cooldown_bars = getattr(user, "cooldown_bars_after_sl", 5)
        # Use a safe buffer of 1 minute per bar on M1
        expiry = now + timedelta(minutes=cooldown_bars)
        
        self.loop_cooldowns.append({
            "symbol": trade.symbol,
            "direction": trade.type,
            "strategy": trade.strategy_name,
            "sl_time": now.isoformat(),
            "expiry": expiry.isoformat()
        })
        
        # 2. Add Blocked Zone (Price-based)
        from app.storage.models import BlockedZone
        new_zone = BlockedZone(
            symbol=trade.symbol,
            direction=trade.type,
            price_level=trade.entry_price,
            range_points=100, # Legacy field, we now use ATR-based distance in RiskManager
            expiry=now + timedelta(minutes=getattr(user, "same_zone_block_minutes", 120)),
            reason="SL_HIT"
        )
        db.add(new_zone)
        logger.warning(f"🛡️ [COOLDOWN] SL HIT detected for {trade.symbol} {trade.type}. Block active for {cooldown_bars} bars until {expiry.strftime('%H:%M:%S')}")

    def _update_strategy_analytics(self, db, state):
        """Calculates performance per strategy for the dashboard using real trade and signal data."""
        from sqlalchemy import func
        from app.storage.models import Trade, SignalLog
        
        stats = {}
        # 1. Fetch all closed trades for performance metrics
        all_closed = db.query(Trade).filter(Trade.status == "CLOSED").all()
        # 2. Fetch all signal logs for rejection metrics
        all_signals = db.query(SignalLog).all()
        
        # Determine all strategies from both sources (Trades + Signals)
        strategies = set([t.strategy_name for t in all_closed if t.strategy_name] + 
                         [s.strategy for s in all_signals if s.strategy])
        
        for s in strategies:
            if not s or s == "Unknown": continue
            
            # TRADE PERFORMANCE
            s_trades = [t for t in all_closed if t.strategy_name == s]
            total = len(s_trades)
            wins = [t for t in s_trades if t.profit > (t.commission or 0)]
            losses = [t for t in s_trades if t.profit <= (t.commission or 0)]
            
            # SL/TP Diagnostics
            sl_hits = len([t for t in s_trades if t.final_exit_reason in ["TRAILING_STOP_HIT", "STOP_OUT"]])
            tp1_hits = len([t for t in s_trades if t.stage1_executed])
            tp2_hits = len([t for t in s_trades if t.final_exit_reason in ["TP2_HIT", "STAGE_2_CLOSED_FULL"]])
            
            hold_times = []
            rr_ratios = []
            ai_scores = []
            session_stats = {}
            symbol_stats = {}

            for t in s_trades:
                # Sessions & Symbols
                sess = t.session[0] if isinstance(t.session, list) and t.session else str(t.session)
                session_stats[sess] = session_stats.get(sess, 0) + t.profit
                symbol_stats[t.symbol] = symbol_stats.get(t.symbol, 0) + t.profit
                
                # AI Score
                if t.ai_score is not None:
                    ai_scores.append(t.ai_score)

                # Hold Time
                if t.exit_time and t.time:
                    hold_times.append((t.exit_time - t.time).total_seconds() / 60)
                
                # RR Ratio (Calculated at Entry)
                risk = abs(t.entry_price - (t.sl or t.entry_price))
                reward = abs((t.tp or t.entry_price) - t.entry_price)
                if risk > 0:
                    rr_ratios.append(reward / risk)

            # REJECTION ANALYTICS (From SignalLog)
            s_signals = [sig for sig in all_signals if sig.strategy == s]
            rejections = [sig for sig in s_signals if sig.status in ["REJECTED", "REJECTED_RISK", "IGNORED"]]
            rej_reasons = {}
            for r in rejections:
                r_type = r.rejection_reason.split(":")[0] if r.rejection_reason else "Unknown"
                rej_reasons[r_type] = rej_reasons.get(r_type, 0) + 1

            stats[s] = {
                "performance": {
                    "total_trades": total,
                    "wins": len(wins),
                    "losses": len(losses),
                    "win_rate": round(len(wins)/total * 100, 1) if total > 0 else 0,
                    "avg_profit": round(sum(t.profit for t in s_trades)/total, 2) if total > 0 else 0,
                    "avg_win": round(sum(t.profit for t in wins)/len(wins), 2) if wins else 0,
                    "avg_loss": round(sum(t.profit for t in losses)/len(losses), 2) if losses else 0,
                    "avg_rr": round(sum(rr_ratios)/len(rr_ratios), 2) if rr_ratios else 0,
                    "avg_hold_time_min": round(sum(hold_times)/len(hold_times), 1) if hold_times else 0,
                },
                "diagnostics": {
                    "sl_hit_count": sl_hits,
                    "tp1_hit_count": tp1_hits,
                    "tp2_hit_count": tp2_hits,
                    "stage1_hit_rate": round(tp1_hits/total * 100, 1) if total > 0 else 0,
                    "stage2_hit_rate": round(tp2_hits/total * 100, 1) if total > 0 else 0,
                    "avg_ai_score": round(sum(ai_scores)/len(ai_scores), 2) if ai_scores else 0,
                },
                "rejections": {
                    "total_rejected": len(rejections),
                    "reasons_breakdown": rej_reasons
                },
                "breakdowns": {
                    "sessions": session_stats,
                    "symbols": symbol_stats
                }
            }
        state.strategy_analytics = stats

    def _process_symbol(self, symbol, acc_info, positions, preferred_session, symbol_settings, strategy_settings=None, spec=None, eval_id=None):
        # A. SMART Tiered Fetching
        t_start = time.time()
        m1_bars = self.mt5.get_bars(symbol, "M1", 500, include_current=True)
        if m1_bars is None:
            logger.error(f"[{eval_id}] [{symbol}] Failed to fetch M1 data.")
            return
        data = {"M1": m1_bars}
        
        if symbol not in self.structural_cache:
            self.structural_cache[symbol] = {"m15_df": None, "m15_last": 0.0, "m5_df": None, "m5_last": 0.0}
            
        now = time.time()
        cache = self.structural_cache[symbol]
        
        if cache["m15_df"] is None or (now - cache["m15_last"] > 300):
            data["M15"] = self.mt5.get_bars(symbol, "M15", 2000)
            cache["m15_df"] = data["M15"]
            cache["m15_last"] = now
            m15_source = "FRESH"
        else:
            data["M15"] = cache["m15_df"]
            m15_source = "CACHE"

        if cache["m5_df"] is None or (now - cache["m5_last"] > 60):
            data["M5"] = self.mt5.get_bars(symbol, "M5", 1000)
            cache["m5_df"] = data["M5"]
            cache["m5_last"] = now
            m5_source = "FRESH"
        else:
            data["M5"] = cache["m5_df"]
            m5_source = "CACHE"
        
        if any(v is None for v in data.values()): 
             logger.warning(f"[{eval_id}] [{symbol}] Missing dataframes for evaluation. M15={m15_source}, M5={m5_source}")
             return

        # Prepare data for strategy (closed candles for signal confirmation)
        data_strategy = {
            "M1": data["M1"].iloc[:-1].copy(),
            "M5": data["M5"].copy(),
            "M15": data["M15"].copy()
        }
        
        last_closed_m1 = data_strategy["M1"].index[-1] if not data_strategy["M1"].empty else "N/A"
        logger.info(f"[{eval_id}] [{symbol}] Data Loaded: M1={len(data['M1'])}, M5={len(data['M5'])} ({m5_source}), M15={len(data['M15'])} ({m15_source})")
        logger.info(f"[{eval_id}] [{symbol}] Latest Strategy Candle (M1 Closed): {last_closed_m1}")

        # Run Preprocessing
        if self.strategies:
            family = self.strategies[0].logic_family
            data_strategy["M1"] = family.preprocess(data_strategy["M1"])
            data_strategy["M5"] = family.preprocess(data_strategy["M5"])
            data_strategy["M15"] = family.preprocess(data_strategy["M15"])

        # Save Live Chart Data
        self._sync_charts(symbol, data["M1"], data_strategy["M1"])

        # Check for open positions to prevent double entry
        mt5_symbol = self.mt5.resolve_symbol(symbol)
        has_pos = any(p.get('symbol') == mt5_symbol for p in positions) if mt5_symbol else False
        if has_pos:
            logger.debug(f"[{eval_id}] [{symbol}] Active position detected on {mt5_symbol}. Managing only.")
            self._manage_open_positions(symbol, data["M1"], data_strategy["M15"])
            # In demo mode, if a trade is open, we don't process new signals.
            # This is handled by the _process_cycle logic now.
            # If we reach here, it means _process_cycle allowed processing this symbol
            # but we still need to manage existing positions.
            # The following signal evaluation should only happen if no trade is open.
            with DatabaseContext() as db:
                open_trade_count = db.query(Trade).filter(Trade.status == "OPEN").count()
                if open_trade_count >= 1:
                    logger.debug(f"Demo Mode: Skipping signal evaluation for {symbol} due to existing open trade.")
                    return

        # B. Strategy Evaluation
        try:
            with DatabaseContext() as db:
                state = db.query(BotState).first()
                # Force demo threshold to 0.48
                self.strategy.ai_threshold = 0.48 
        except: pass

        approved, rejected = self.strategy.evaluate(symbol, data_strategy, strategy_settings=strategy_settings)
        
        for rej in rejected:
            reason = rej.metadata.get("ai_reason", "Low Score")
            logger.info(f"[{eval_id}] [{symbol}] STRATEGY REJECTED: {rej.strategy_name} | Direction={rej.side.name} | AI Score={rej.ai_confidence:.2f} (Required: {rej.ai_threshold_used}) | Reason={reason}")
            self._log_signal(rej, "REJECTED", reason)

        if not approved: 
             logger.info(f"[{eval_id}] [{symbol}] No strategies approved for this cycle.")
             return

        # Get latest tick for live validation (Spread, Late Entry)
        tick = self.mt5.get_latest_tick(symbol)
        if not tick: 
             logger.error(f"[{eval_id}] [{symbol}] Could not fetch latest tick for risk validation.")
             return
        
        for signal in approved:
            logger.info(f"[{eval_id}] [{symbol}] STRATEGY APPROVED: {signal.strategy_name} | Direction={signal.side.name} | AI Score={signal.ai_confidence:.2f} | Entry={signal.entry_price:.5f}")
            # Inject live tick into signal for Risk Manager
            signal.metadata["current_tick"] = tick
            
            daily_pnl = acc_info.get("daily_pnl", 0.0)
            
            # --- DEMO PROTECTION GAP CHECK ---
            with DatabaseContext() as db:
                open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
                has_gap = any(
                    (t.stage1_partial_done and not t.stage1_sl_done) or 
                    (t.stage2_partial_done and not t.stage2_sl_done) 
                    for t in open_trades
                )
                if has_gap: 
                    logger.warning(f"[{eval_id}] [{symbol}] 🚫 Signal IGNORED: Active protection gap on unmanaged trade.")
                    continue

            # --- DEMO SPREAD OVERRIDE ---
            if symbol == "XAUUSD":
                # Ensure we have a dict for the symbol to keep RiskManager happy
                if "XAUUSD" not in symbol_settings:
                    symbol_settings["XAUUSD"] = {}
                symbol_settings["max_spread_points"] = 55
                # Also set at root in case RiskManager doesn't handle nesting correctly yet
                symbol_settings["max_spread_points"] = 55

            # 1. Higher-Timeframe Context Detection (SENTINEL)
            m15_regime = self.regime_detector.identify(data_strategy["M15"])
            m15_bias = m15_regime.metrics.get("market_bias", "NEUTRAL")
            m15_atr = m15_regime.metrics.get("atr", 0.0)
            
            logger.info(f"[{eval_id}] [{symbol}] HTF Context Analysis (M15): Regime={m15_regime.regime.name}, Bias={m15_bias}, ATR={m15_atr:.5f}")

            # 2. Context for Risk Manager
            risk_context = {
                "active_cooldowns": self.loop_cooldowns,
                "blocked_zones": self.loop_blocked_zones,
                "active_news_event": self.news_service.get_active_event(symbol, symbol_settings),
                "current_session": self._get_current_session(),
                "nearest_level": self._find_nearest_structural_level(symbol, data_strategy["M15"], signal.side),
                "market_bias": m15_bias,
                "atr": m15_atr,
                "eval_id": eval_id
            }

            decision = self.risk.validate_signal(signal, acc_info, positions, daily_pnl, symbol_settings=symbol_settings, symbol_spec=spec, context=risk_context)
            
            if not decision.is_approved:
                # Log detailed rejection reason for frontend visibility
                logger.info(f"[{eval_id}] [{symbol}] RISK REJECTED: {decision.reason}")
                self._log_signal(signal, "REJECTED_RISK", decision.reason)
                continue

            # Log the final risk outcome
            logger.info(f"[{eval_id}] [{symbol}] ✅ RISK APPROVED: Lot={decision.lot_size} | Risk={decision.risk_pct*100}% | Executing signal...")

            # Execution logic
            self._log_signal(signal, "APPROVED", f"Executing with live tick: Bid={tick['bid']}, Ask={tick['ask']}")
            
            rr = 1.5
            try:
                with DatabaseContext() as db:
                    u = db.query(User).first()
                    if u: rr = u.preferred_rr_ratio
            except: pass

            logger.info(f"[{eval_id}] [{symbol}] Sending EXECUTION request to MetaTrader 5...")
            exec_res = self.executor.execute(signal, decision.lot_size, rr_ratio=rr, eval_id=eval_id)
            
            if exec_res.success:
                logger.info(f"[{eval_id}] [{symbol}] 🚀 EXECUTION SUCCESS: Ticket=#{exec_res.ticket} | Fill={exec_res.price}")
                self._save_trade_enhanced(signal, exec_res, tick, data_strategy["M15"])
            else:
                logger.error(f"[{eval_id}] [{symbol}] ❌ EXECUTION FAILED: {exec_res.comment}")
                self._log_execution_failure(signal, exec_res)

        # C. Post-Execution Position Management
        self._manage_open_positions(symbol, data["M1"], data_strategy["M15"])

    def _manage_open_positions(self, symbol: str, m1_raw: pd.DataFrame, m15_strat: pd.DataFrame):
        """Enhanced Position Management with Staged Closes and Structural Trailing."""
        mt5_symbol = self.mt5.resolve_symbol(symbol)
        if not mt5_symbol: return

        positions = self.mt5.get_positions()
        symbol_positions = [p for p in positions if p.get('symbol') == mt5_symbol]
        if not symbol_positions: return

        mt5_symbol = self.mt5.resolve_symbol(symbol)
        tick = self.mt5.get_latest_tick(symbol)
        if not tick or not mt5_symbol: return

        with DatabaseContext() as db:
            user = db.query(User).first()
            if not user: return
            
            for pos in symbol_positions:
                ticket = pos.get('ticket')
                trade = db.query(Trade).filter(Trade.ticket_id == ticket).first()
                if not trade: continue

                # 0: BUY, 1: SELL
                order_type = pos.get('type')
                is_buy = order_type == 0
                current_price = tick['bid'] if is_buy else tick['ask']
                
                entry = float(trade.entry_price)
                tp1 = float(trade.tp1 or trade.tp) # Fallback to order TP
                current_sl = float(pos.get('sl', 0))
                volume = float(pos.get('volume', 0))
                
                if tp1 == 0 or entry == tp1: continue

                # RESTORED CALCULATION
                total_move_tp1 = abs(tp1 - entry)
                dist_moved = (current_price - entry) if is_buy else (entry - current_price)
                progress = dist_moved / total_move_tp1 if total_move_tp1 > 0 else 0
                
                new_sl = current_sl
                state_changed = False

                # STAGE 1: 60% Progress
                if progress >= user.partial_stage_1_trigger and not trade.stage1_executed:
                    # Case 1: Partial not done yet
                    if not trade.stage1_partial_done:
                        close_vol = (trade.initial_volume or volume) * user.partial_stage_1_close_pct
                        res = self.executor.client.partial_close(ticket, close_vol, mt5_symbol)
                        status = res.get("status", "FAILED")
                        
                        if status != "FAILED":
                            # LOGGING REQUIREMENTS
                            logger.info(f"📊 VOLUME LOG [Stage 1] #{ticket}:")
                            logger.info(f"   Original: {trade.initial_volume} | Before: {res.get('current')}")
                            logger.info(f"   Requested: {res.get('requested'):.3f} | Rounded: {res.get('rounded')}")
                            logger.info(f"   Forced Full: {res.get('forced_full')} (Min: {res.get('min_lot')})")
                            logger.info(f"   Projected Remainder: {res.get('remainder')}")

                            if status == "CLOSED_FULL":
                                trade.stage1_partial_done = True
                                trade.stage1_sl_done = True
                                trade.stage1_executed = True # Map to completed
                                trade.status = "CLOSED"
                                trade.final_exit_reason = "STAGE_1_CLOSED_FULL"
                                db.add(TradeEvent(ticket_id=ticket, event_type="STAGE_1_CLOSED_FULL", old_value=volume, new_value=0.0))
                                db.commit()
                                logger.info(f"🎯 STAGE 1 CLOSED_FULL: {symbol} #{ticket}")
                                continue
                            
                            # Success or Skipped Lot Size
                            trade.stage1_partial_done = True
                            db.add(TradeEvent(ticket_id=ticket, event_type=f"STAGE_1_{status}", 
                                           old_value=volume, 
                                           new_value=res.get("remainder", volume)))
                            db.commit() # Immediate lock before SL attempt
                    
                    # Case 2: Partial is done (or skipped), try to secure SL
                    if trade.stage1_partial_done and not trade.stage1_sl_done:
                        sym_info = self.mt5.get_symbol_info(symbol)
                        point = sym_info.point if sym_info else 0.0001
                        buffer = max(tick['spread'] * 1.5, point * 10)
                        target_sl = entry + buffer if is_buy else entry - buffer
                        
                        # MONOTONIC GUARD: Reject if it makes the risk worse
                        is_worse = (is_buy and target_sl < current_sl) or (not is_buy and current_sl != 0 and target_sl > current_sl)
                        if is_worse:
                            logger.error(f"🛑 SL GUARD: Rejected Stage 1 SL update for #{ticket}. Proposed {target_sl:.5f} is worse than current {current_sl:.5f}")
                            trade_state = "PARTIAL_DONE_SL_PENDING"
                        elif self.executor.client.update_sl(ticket, mt5_symbol, target_sl, tp=trade.tp):
                            trade.stage1_sl_done = True
                            trade.stage1_executed = True # Completed
                            trade.stage1_trigger_time = datetime.now(timezone.utc)
                            trade.sl = target_sl
                            db.commit()
                            logger.info(f"🎯 STAGE 1 LOG: [ticket=#{ticket}] stage1_partial_done=T, stage1_sl_done=T, stage1_executed=T")
                            logger.info(f"🎯 SL Secured at {target_sl:.5f}")
                            continue
                        else:
                            trade_state = "PARTIAL_DONE_SL_PENDING"
                            logger.warning(f"🚨 PROTECTION GAP (Stage 1): #{ticket} Partial EXIT succeeded but SL move FAILED. Retrying...")

                # STAGE 2: 80% Progress
                elif progress >= user.partial_stage_2_trigger and not trade.stage2_executed:
                    # Case 1: Partial not done yet
                    if not trade.stage2_partial_done:
                        close_vol = (trade.initial_volume or volume) * user.partial_stage_2_close_pct
                        res = self.executor.client.partial_close(ticket, close_vol, mt5_symbol)
                        status = res.get("status", "FAILED")
                        
                        if status != "FAILED":
                            # LOGGING REQUIREMENTS
                            logger.info(f"📊 VOLUME LOG [Stage 2] #{ticket}:")
                            logger.info(f"   Original: {trade.initial_volume} | Before: {res.get('current')}")
                            logger.info(f"   Requested: {res.get('requested'):.3f} | Rounded: {res.get('rounded')}")
                            logger.info(f"   Forced Full: {res.get('forced_full')} (Min: {res.get('min_lot')})")
                            logger.info(f"   Projected Remainder: {res.get('remainder')}")

                            if status == "CLOSED_FULL":
                                trade.stage2_partial_done = True
                                trade.stage2_sl_done = True
                                trade.stage2_executed = True
                                trade.status = "CLOSED"
                                trade.final_exit_reason = "STAGE_2_CLOSED_FULL"
                                db.add(TradeEvent(ticket_id=ticket, event_type="STAGE_2_CLOSED_FULL", old_value=volume, new_value=0.0))
                                db.commit()
                                logger.info(f"🚀 STAGE 2 CLOSED_FULL: {symbol} #{ticket}")
                                continue
                            
                            trade.stage2_partial_done = True
                            db.add(TradeEvent(ticket_id=ticket, event_type=f"STAGE_2_{status}", 
                                           old_value=volume, 
                                           new_value=res.get("remainder", volume)))
                            db.commit()
                            
                    # Case 2: Partial done, try to lock SL
                    if trade.stage2_partial_done and not trade.stage2_sl_done:
                        stage1_tgt = entry + (total_move_tp1 * user.partial_stage_1_trigger) if is_buy else entry - (total_move_tp1 * user.partial_stage_1_trigger)
                        
                        # MONOTONIC GUARD: SL must only move in favor of protection
                        is_worse = (is_buy and stage1_tgt < current_sl) or (not is_buy and current_sl != 0 and stage1_tgt > current_sl)
                        if is_worse:
                            logger.error(f"🛑 SL GUARD: Rejected Stage 2 SL update for #{ticket}. Proposed {stage1_tgt:.5f} is worse than current {current_sl:.5f}")
                        elif self.executor.client.update_sl(ticket, mt5_symbol, stage1_tgt, tp=trade.tp):
                            trade.stage2_sl_done = True
                            trade.stage2_executed = True
                            trade.stage2_trigger_time = datetime.now(timezone.utc)
                            trade.sl = stage1_tgt
                            db.commit()
                            logger.info(f"🚀 STAGE 2 LOG: [ticket=#{ticket}] stage2_partial_done=T, stage2_sl_done=T, stage2_executed=T")
                            logger.info(f"🚀 SL Advanced to {stage1_tgt:.5f}")
                            continue
                        else:
                            logger.warning(f"🚨 PROTECTION GAP (Stage 2): #{ticket} Partial EXIT succeeded but SL move FAILED. Retrying...")

                # STRUCTURAL TRAILING (Only if past Stage 1)
                elif trade.stage1_executed and 'swing_low' in m1_raw.columns:
                    recent_hl = m1_raw[m1_raw['swing_low']].tail(1)
                    recent_lh = m1_raw[m1_raw['swing_high']].tail(1)
                    
                    point = 0.0001
                    trail_buffer = max(tick['spread'] * 1.5, point * 5)
                    
                    if is_buy and not recent_hl.empty:
                        target_sl = float(recent_hl.iloc[0]['low']) - trail_buffer
                        if target_sl > new_sl and target_sl < current_price:
                            new_sl = target_sl
                    elif not is_buy and not recent_lh.empty:
                        target_sl = float(recent_lh.iloc[0]['high']) + trail_buffer
                        if (new_sl == 0 or target_sl < new_sl) and target_sl > current_price:
                            new_sl = target_sl

                # Immediate Persistence for SL/State
                if state_changed or (new_sl != current_sl and new_sl != 0):
                    # Defensive: Never move SL backwards
                    is_backwards = (is_buy and new_sl < current_sl) or (not is_buy and current_sl != 0 and new_sl > current_sl)
                    if not is_backwards:
                        if self.executor.client.update_sl(ticket, new_sl):
                            trade.sl = new_sl
                            logger.info(f"🛡️ SL Updated: {symbol} #{ticket} -> {new_sl:.5f}")
                    db.commit() # IMMEDIATE Persistence

            # Post-management: Check for SL hits (to trigger cooldowns)
            just_closed_sl = db.query(Trade).filter(
                Trade.status == "CLOSED",
                Trade.final_exit_reason.in_(["TRAILING_STOP_HIT", "STOP_OUT"]),
                Trade.exit_time > datetime.now(timezone.utc) - timedelta(minutes=5)
            ).all()
            for t in just_closed_sl:
                if not any(cd["symbol"] == t.symbol and cd["direction"] == t.type for cd in self.loop_cooldowns):
                    self._handle_sl_hit(t, db)
                    db.commit()

    def _save_trade_enhanced(self, signal, exec_res, tick, m15_df):
        """Deep analytics storage for each trade."""
        with DatabaseContext() as db:
            user = db.query(User).first()
            
            # Detect regime for analytics
            regime = self.regime_detector.identify(m15_df)
            
            trade = db.query(Trade).filter(Trade.ticket_id == exec_res.ticket).first()
            if not trade:
                trade = Trade(ticket_id=exec_res.ticket)
                db.add(trade)
            
            trade.symbol = signal.symbol
            trade.type = exec_res.order_type if hasattr(exec_res, 'order_type') else ("BUY" if signal.side == OrderSide.BUY else "SELL")
            trade.volume = exec_res.lot_size or 0.0
            trade.initial_volume = exec_res.lot_size or 0.0
            trade.entry_price = exec_res.price
            trade.sl = exec_res.sl if exec_res.sl else signal.structural_sl
            trade.tp = exec_res.tp if exec_res.tp else (signal.targets[0] if signal.targets else 0.0)
            trade.tp1 = signal.targets[0] if len(signal.targets) > 0 else (exec_res.tp or 0.0)
            trade.tp2 = signal.targets[1] if len(signal.targets) > 1 else (exec_res.tp or 0.0)
            
            # TP CONSISTENCY VALIDATION
            if abs(trade.tp - trade.tp2) > 0.00001:
                logger.error(f"❌ TP CONSISTENCY FAILURE: trade.tp ({trade.tp}) != trade.tp2 ({trade.tp2})")
                trade.status = "INVALID_TEST"
                trade.rationale = "TP consistency validation failed at entry"
            else:
                trade.status = "OPEN"
            
            trade.strategy_name = signal.strategy_name
            
            # New Analytics Fields
            trade.bid_at_entry = tick['bid']
            trade.ask_at_entry = tick['ask']
            trade.spread_at_entry = (tick['ask'] - tick['bid'])
            trade.session = ", ".join(self._get_current_session())
            trade.market_regime = regime.regime.name if hasattr(regime.regime, "name") else str(regime.regime)
            trade.ai_score = signal.ai_score if hasattr(signal, "ai_score") else signal.ai_confidence
            trade.user_id = user.id if user else None
            
            # Save Geometric Annotations
            if hasattr(signal, 'chart_annotations'):
                for ann_dict in signal.chart_annotations:
                    ann = TradeAnnotation(
                        id=ann_dict["id"],
                        ticket_id=exec_res.ticket,
                        symbol=signal.symbol,
                        concept_type=ann_dict["concept_type"],
                        shape=ann_dict["shape"],
                        style=ann_dict["style"],
                        time1=ann_dict["time1"],
                        time2=ann_dict.get("time2"),
                        price1=ann_dict["price1"],
                        price2=ann_dict.get("price2"),
                        text=ann_dict.get("text"),
                        layer_priority=ann_dict.get("layer_priority", 0),
                        is_active=True,
                        metadata_json=ann_dict.get("metadata_fields", {})
                    )
                    db.add(ann)

            ex_log = ExecutionLog(
                symbol=signal.symbol,
                requested_price=signal.entry_price,
                filled_price=exec_res.price,
                deviation=20,
                retcode=exec_res.retcode if hasattr(exec_res, 'retcode') else 0,
                latency_ms=exec_res.latency_ms if hasattr(exec_res, 'latency_ms') else 0
            )
            db.add(ex_log)
            db.commit()
            
            logger.info("\n" + "-"*30)
            logger.info(f"🆕 NEW TRADE CAPTURED: #{exec_res.ticket}")
            logger.info(f"   Symbol: {signal.symbol}")
            logger.info(f"   Bid/Ask: {tick['bid']}/{tick['ask']} (Spread: {(tick['ask']-tick['bid']):.5f})")
            logger.info(f"   Requested: {signal.entry_price} | Filled: {exec_res.price}")
            logger.info(f"   SL: {trade.sl} | TP1: {trade.tp1} | TP2: {trade.tp2}")
            logger.info(f"   Initial Stages: stage1_partial_done: {trade.stage1_partial_done}, stage1_sl_done: {trade.stage1_sl_done}")
            logger.info(f"   AI Conf: {trade.ai_score:.2f} (Threshold: 0.48)")
            logger.info("-"*30 + "\n")


    def _log_signal(self, signal: TradeSignal, status: str, reason: str):
        # Always attach real AI confidence + threshold when present
        conf = getattr(signal, "ai_confidence", None)
        thr = getattr(signal, "ai_threshold_used", None)
        if conf is not None and thr is not None:
            # Avoid duplicating if already formatted
            if "conf=" not in reason and "thr=" not in reason:
                reason = f"{reason} (conf={conf:.2f}, thr={thr:.2f})"

        strat_name = getattr(signal, "strategy_name", "Unknown")
        msg = f"[{signal.symbol}] {status}: {strat_name} - {reason}"
        logger.info(msg)
        with DatabaseContext() as db:
            log = SignalLog(
                symbol=signal.symbol,
                strategy=strat_name,
                direction=signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                entry=signal.entry_price,
                sl=signal.structural_sl,
                tp=signal.targets[0] if signal.targets else 0.0,
                score=signal.setup_score.total_score if hasattr(signal.setup_score, "total_score") else 0.0,
                reasons=str(signal.metadata.get("reasons", [])),
                status=status,
                rejection_reason=reason,
            )
            db.add(log)

            # Update live logs
            state = db.query(BotState).first()
            if state:
                # 1. Update live logs stream
                logs = list(state.live_logs or [])
                msg = f"{datetime.now().strftime('%H:%M:%S')} - [{signal.symbol}] {status}: {strat_name} - {reason}"
                logs.insert(0, msg)
                state.live_logs = logs[:200]
                
                # 2. Update recent rejections for structured UI display
                if status in ["REJECTED", "REJECTED_RISK", "IGNORED"]:
                    rejections = list(state.recent_rejections or [])
                    rejections.insert(0, {
                        "time": datetime.now(timezone.utc).isoformat(),
                        "symbol": signal.symbol,
                        "direction": signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                        "strategy": strat_name,
                        "reason": reason,
                        "score": getattr(signal, "ai_score", getattr(signal, "ai_confidence", 0.0))
                    })
                    state.recent_rejections = rejections[:20]
            db.commit()

    def _extract_overlays(self, df: pd.DataFrame) -> Dict:
        """Extract SMC indicators from dataframe for chart overlay."""
        overlays = {
            "fvg_zones": [],
            "order_blocks": [],
            "sweeps": [],
            "bos_markers": [],
            "support_resistance": [],
            "mss_markers": [],
            "breaker_markers": [],
            "volume_zones": []
        }
        
        # 1. FVGs
        if 'fvg_bullish' in df.columns:
            # We want recent unmitigated or very recent ones
            fvg_rows = df[(df['fvg_bullish'] | df['fvg_bearish'])].tail(10)
            for _, row in fvg_rows.iterrows():
                # Correctly access the 'time' column which is already a datetime
                # Convert to UNIX timestamp (int)
                t_val = int(row['time'].timestamp())
                overlays["fvg_zones"].append({
                    "time": t_val,
                    "top": float(row['fvg_top']),
                    "bottom": float(row['fvg_bottom']),
                    "type": "bullish" if row['fvg_bullish'] else "bearish"
                })

        # 2. Order Blocks
        if 'order_block' in df.columns:
            ob_rows = df[df['order_block'] != 0].tail(10)
            for _, row in ob_rows.iterrows():
                overlays["order_blocks"].append({
                    "time": int(row['time'].timestamp()),
                    "top": float(row['high']),
                    "bottom": float(row['low']),
                    "type": "bullish" if row['order_block'] == 1 else "bearish"
                })

        # 3. BOS/CHOCH
        if 'bos' in df.columns:
            bos_rows = df[df['bos'] != 0].tail(10)
            for _, row in bos_rows.iterrows():
                overlays["bos_markers"].append({
                    "time": int(row['time'].timestamp()),
                    "type": "bullish" if row['bos'] == 1 else "bearish",
                    "price": float(row['close'])
                })

        # 4. Sweeps
        if 'sweep' in df.columns:
            sweep_rows = df[df['sweep'] != 0].tail(10)
            for _, row in sweep_rows.iterrows():
                overlays["sweeps"].append({
                    "time": int(row['time'].timestamp()),
                    "type": "bullish" if row['sweep'] == 1 else "bearish"
                })

        # 5. MSS
        if 'mss' in df.columns:
            mss_rows = df[df['mss'] != 0].tail(10)
            for _, row in mss_rows.iterrows():
                if "mss_markers" in overlays:
                    overlays["mss_markers"].append({
                        "time": int(row['time'].timestamp()),
                        "type": "bullish" if row['mss'] == 1 else "bearish"
                    })

        # 6. Breakers
        if 'breaker_block' in df.columns:
            bb_rows = df[df['breaker_block'] != 0].tail(10)
            for _, row in bb_rows.iterrows():
                if "breaker_markers" in overlays:
                    overlays["breaker_markers"].append({
                        "time": int(row['time'].timestamp()),
                        "type": "bullish" if row['breaker_block'] == 1 else "bearish",
                        "top": float(row['high']),
                        "bottom": float(row['low'])
                    })

        # 7. Volume Profile (POC)
        if 'poc' in df.columns:
            last_poc = df[df['poc'] > 0].tail(3)
            for _, row in last_poc.iterrows():
                if "volume_zones" in overlays:
                    overlays["volume_zones"].append({
                        "time": int(row['time'].timestamp()),
                        "price": float(row['poc'])
                    })

        return overlays


    def _sync_charts(self, symbol, m1_raw, m1_strat):
        """Prepares and saves live chart data for the frontend."""
        try:
            with DatabaseContext() as db:
                state = db.query(BotState).first()
                if state is not None:
                    current_charts = dict(state.live_charts or {})
                    df_export = m1_raw.tail(500).copy()
                    df_export['time'] = df_export['time'].values.astype('datetime64[s]').astype('int64')
                    chart_records = df_export.to_dict('records')
                    
                    current_charts[symbol] = {
                        "chart": chart_records,
                        "overlays": self._extract_overlays(m1_strat)
                    }
                    state.live_charts = current_charts
                    db.commit()
        except Exception as e:
            logger.error(f"Failed to sync charts for {symbol}: {e}")


    def _log_execution_failure(self, signal, exec_res):
        with DatabaseContext() as db:
            ex_log = ExecutionLog(
                symbol=signal.symbol,
                requested_price=signal.entry_price,
                filled_price=None,
                deviation=20,
                retcode=exec_res.retcode,
                error_message=exec_res.comment,
                latency_ms=exec_res.latency_ms
            )
            db.add(ex_log)
            
            # Update SignalLog to reflect failure
            log = db.query(SignalLog).filter(
                SignalLog.symbol == signal.symbol,
                SignalLog.status == "APPROVED"
            ).order_by(SignalLog.timestamp.desc()).first()
            if log:
                log.status = "EXEC_FAILURE"
                log.rejection_reason = exec_res.comment
                
            db.commit()
