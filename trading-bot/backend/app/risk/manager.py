import logging
import datetime
import time
from typing import List, Dict, Optional
from app.core.config import settings
from app.core.datatypes import TradeSignal
from app.risk.models import RiskDecision
from app.core.enums import OrderSide

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, settings_override: Optional[Dict] = None):
        self.risk_per_trade = settings_override.get('risk_per_trade', settings.RISK_PER_TRADE) if settings_override else settings.RISK_PER_TRADE
        self.max_trades = settings_override.get('max_trades', settings.MAX_TRADES) if settings_override else settings.MAX_TRADES
        self.daily_loss_limit = settings_override.get('daily_loss_limit', settings.DAILY_LOSS_LIMIT) if settings_override else settings.DAILY_LOSS_LIMIT
        
        # Phase 2 persistence
        self.strategy_status = {} # {strategy_name: "HEALTHY" / "DEGRADED"}
        self.strategy_degraded_count = 0
        self.strategy_recovered_count = 0
        self.rejected_by_cooldown = 0
        self.rejected_by_clustering = 0
        self.rejected_by_strategy_health = 0

    def _get_closed_trades(self, strategy_name: str, symbol: str, context: Dict) -> List[Dict]:
        is_backtest = context.get("is_backtest", False)
        standardized = []
        if is_backtest:
            closed_list = context.get("closed_trades", [])
            for t in closed_list:
                if t.get("strategy") == strategy_name:
                    if not context.get("per_symbol_cooldown", True) or t.get("symbol") == symbol:
                        standardized.append({
                            "profit": t.get("realized_pnl", 0.0),
                            "market_regime": t.get("market_regime", "N/A"),
                            "exit_time": t.get("exit_time"),
                            "ai_score": t.get("ai_conf", 0.5),
                            "setup_score": t.get("structure", 0.5),
                            "entry_time": t.get("entry_time"),
                            "entry_price": t.get("entry_price"),
                            "direction": t.get("direction") or t.get("side")
                        })
        else:
            from app.storage.db import DatabaseContext
            from app.storage.models import Trade
            try:
                with DatabaseContext() as db:
                    query = db.query(Trade).filter(
                        Trade.status == "CLOSED",
                        Trade.strategy_name == strategy_name
                    )
                    if context.get("per_symbol_cooldown", True):
                        query = query.filter(Trade.symbol == symbol)
                    db_trades = query.order_by(Trade.exit_time.desc()).limit(20).all()
                    for t in db_trades:
                        standardized.append({
                            "profit": t.profit - (t.commission or 0.0),
                            "market_regime": t.market_regime or "N/A",
                            "exit_time": t.exit_time,
                            "ai_score": t.ai_score or 0.5,
                            "setup_score": t.setup_score or 0.5,
                            "entry_time": t.time,
                            "entry_price": t.entry_price,
                            "direction": t.type
                        })
            except Exception as e:
                logger.error(f"Error querying closed trades: {e}")
                
        # Sort by exit time descending so index 0 is most recent
        def get_exit_timestamp(t):
            et = t.get("exit_time")
            if not et: return 0
            if isinstance(et, (int, float)): return et
            if isinstance(et, str):
                try:
                    return datetime.datetime.fromisoformat(et.replace("Z", "+00:00")).timestamp()
                except:
                    return 0
            if isinstance(et, datetime.datetime):
                return et.timestamp()
            return 0
            
        standardized.sort(key=get_exit_timestamp, reverse=True)
        return standardized

    def validate_signal(self, signal: TradeSignal, account_info: Dict, open_positions: List[Dict], daily_pnl: float, symbol_settings: Optional[Dict] = None, symbol_spec: Optional[Dict] = None, context: Optional[Dict] = None, gate_profile: str = "balanced") -> RiskDecision:
        """
        Comprehensive risk validation for a signal.
        """
        user_settings = symbol_settings or {}
        context = context or {}
        eval_id = context.get("eval_id", "N/A")
        is_backtest = context.get("is_backtest", False)
        tick_time = context.get("tick_time", 0)
        
        def reject(stage: str, rule: str, category: str, current_value, required_value, short_reason: str, legacy_prefix: str) -> RiskDecision:
            """
            Phase 4: normalized rejection payload with backward-compatible reason string.
            """
            msg = (
                f"{legacy_prefix}: Rejected by risk manager. "
                f"{short_reason} (stage={stage}, rule={rule}, category={category}, "
                f"current={current_value}, required={required_value})"
            )
            return RiskDecision(
                is_approved=False,
                reason=msg,
                lot_size=0.0,
                metadata={
                    "rejection_stage": stage,
                    "rejection_rule": rule,
                    "rejection_reason": msg,
                    "rejection_details": {"category": category},
                    "current_value": current_value,
                    "required_value": required_value,
                },
            )

        # Parse current reference time
        current_time_ref = datetime.datetime.fromtimestamp(tick_time, datetime.timezone.utc) if tick_time > 0 else datetime.datetime.now(datetime.timezone.utc)

        # Phase 2 configurations
        cooldown_after_losses = user_settings.get("cooldown_after_losses", settings.COOLDOWN_AFTER_LOSSES)
        cooldown_minutes = user_settings.get("cooldown_minutes", settings.COOLDOWN_MINUTES)
        per_strategy_cooldown = user_settings.get("per_strategy_cooldown", settings.PER_STRATEGY_COOLDOWN)
        per_symbol_cooldown = user_settings.get("per_symbol_cooldown", settings.PER_SYMBOL_COOLDOWN)
        
        min_candles = user_settings.get("min_candles_between_same_strategy_entries", settings.MIN_CANDLES_BETWEEN_SAME_STRATEGY_ENTRIES)
        min_atr_mult = user_settings.get("min_price_distance_atr_multiplier", settings.MIN_PRICE_DISTANCE_ATR_MULTIPLIER)
        
        min_win_rate = user_settings.get("min_rolling_win_rate", settings.MIN_ROLLING_WIN_RATE)
        min_pf = user_settings.get("min_rolling_profit_factor", settings.MIN_ROLLING_PROFIT_FACTOR)

        # Parse open positions with strategy names mapped
        open_strategy_trades = []
        for pos in open_positions:
            ticket = pos.get("ticket")
            if is_backtest:
                open_strategy_trades.append({
                    "strategy": pos.get("strategy"),
                    "symbol": pos.get("symbol"),
                    "direction": pos.get("direction") or pos.get("side"),
                    "entry_price": pos.get("entry_price"),
                    "entry_time": pos.get("entry_time")
                })
            else:
                from app.storage.db import DatabaseContext
                from app.storage.models import Trade
                try:
                    with DatabaseContext() as db:
                        trade = db.query(Trade).filter(Trade.ticket_id == ticket).first()
                        if trade:
                            open_strategy_trades.append({
                                "strategy": trade.strategy_name,
                                "symbol": trade.symbol,
                                "direction": trade.type,
                                "entry_price": trade.entry_price,
                                "entry_time": trade.time
                            })
                except Exception as e:
                    logger.error(f"Error matching open position ticket {ticket}: {e}")

        # Fetch closed trades
        s_closed = self._get_closed_trades(signal.strategy_name, signal.symbol, context)

        # --- STRATEGY HEALTH GATE ---
        health_window = 10
        recent_trades = s_closed[:health_window]
        
        is_degraded = False
        win_rate = 100.0
        profit_factor = 10.0
        
        if len(recent_trades) >= 5:
            wins = [t for t in recent_trades if t["profit"] > 0]
            losses = [t for t in recent_trades if t["profit"] <= 0]
            
            win_rate = (len(wins) / len(recent_trades)) * 100
            
            gross_profit = sum(t["profit"] for t in wins)
            gross_loss = abs(sum(t["profit"] for t in losses))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 10.0
            
            is_degraded = (win_rate < min_win_rate) or (profit_factor < min_pf)

        # Transition status
        current_status = self.strategy_status.get(signal.strategy_name, "HEALTHY")
        if is_degraded:
            if current_status == "HEALTHY":
                self.strategy_status[signal.strategy_name] = "DEGRADED"
                self.strategy_degraded_count += 1
                logger.warning(f"[HEALTH] Strategy {signal.strategy_name} marked DEGRADED! Win Rate={win_rate:.1f}%, PF={profit_factor:.2f}")
            
            self.rejected_by_strategy_health += 1
            return reject(
                stage="strategy_health",
                rule="STRATEGY_DEGRADED",
                category="health",
                current_value=f"win_rate={win_rate:.1f}%, pf={profit_factor:.2f}",
                required_value=f"win_rate>={min_win_rate}%, pf>={min_pf}",
                short_reason=f"Strategy health degraded: Win Rate={win_rate:.1f}% (Req: {min_win_rate}%), PF={profit_factor:.2f} (Req: {min_pf})",
                legacy_prefix="REJECTED_STRATEGY_HEALTH"
            )
        else:
            if current_status == "DEGRADED":
                self.strategy_status[signal.strategy_name] = "HEALTHY"
                self.strategy_recovered_count += 1
                logger.info(f"[HEALTH] Strategy {signal.strategy_name} recovered to HEALTHY! Win Rate={win_rate:.1f}%, PF={profit_factor:.2f}")

        # --- TRADE SEQUENCING & COOLDOWN GATE ---
        consec_losses = 0
        loss_regimes = []
        for t in s_closed[:5]:
            if t["profit"] < 0:
                consec_losses += 1
                loss_regimes.append(t["market_regime"])
            else:
                break
                
        if consec_losses >= cooldown_after_losses:
            recent_loss_regimes = loss_regimes[:cooldown_after_losses]
            # check if they are all from the same regime
            if len(set(recent_loss_regimes)) == 1 and recent_loss_regimes[0] != "N/A":
                offending_regime = recent_loss_regimes[0]
                last_loss = s_closed[0]
                last_exit = last_loss["exit_time"]
                if isinstance(last_exit, str):
                    last_exit = datetime.datetime.fromisoformat(last_exit.replace("Z", "+00:00"))
                if last_exit.tzinfo is None:
                    last_exit = last_exit.replace(tzinfo=datetime.timezone.utc)
                
                elapsed = (current_time_ref - last_exit).total_seconds() / 60.0
                if elapsed < cooldown_minutes:
                    # Let's check if the current market regime matches the offending regime
                    current_regime = context.get("market_regime", "N/A")
                    if current_regime == offending_regime or current_regime in offending_regime:
                        self.rejected_by_cooldown += 1
                        return reject(
                            stage="cooldown",
                            rule="STRATEGY_REGIME_COOLDOWN",
                            category="cooldown",
                            current_value=f"{elapsed:.1f} mins elapsed in regime {current_regime}",
                            required_value=f">{cooldown_minutes} mins elapsed",
                            short_reason=f"Regime Cooldown active for {signal.strategy_name} due to {cooldown_after_losses} consecutive losses in {offending_regime}",
                            legacy_prefix="REJECTED_COOLDOWN"
                        )

        # --- TRADE CLUSTERING PROTECTION GATE ---
        # 1. Max 1 active trade per strategy per symbol
        same_strat_active = [p for p in open_strategy_trades if p.get("strategy") == signal.strategy_name and p.get("symbol") == signal.symbol]
        if len(same_strat_active) >= 1:
            self.rejected_by_clustering += 1
            return reject(
                stage="clustering_protection",
                rule="MAX_ACTIVE_PER_STRATEGY",
                category="clustering",
                current_value=len(same_strat_active),
                required_value="0",
                short_reason=f"Active trade already open for strategy {signal.strategy_name} on {signal.symbol}",
                legacy_prefix="REJECTED_CLUSTERING"
            )
            
        # 2. Max 1 same-direction trade within min_candles_between_same_strategy_entries (in minutes)
        all_recent_trades = []
        for p in open_strategy_trades:
            if p.get("symbol") == signal.symbol and p.get("strategy") == signal.strategy_name:
                all_recent_trades.append(p)
        for t in s_closed:
            all_recent_trades.append(t)
            
        for t in all_recent_trades:
            t_entry = t.get("entry_time") or t.get("time")
            if t_entry:
                if isinstance(t_entry, str):
                    t_entry = datetime.datetime.fromisoformat(t_entry.replace("Z", "+00:00"))
                if t_entry.tzinfo is None:
                    t_entry = t_entry.replace(tzinfo=datetime.timezone.utc)
                
                t_dir = t.get("direction") or t.get("side") or t.get("type")
                if t_dir:
                    t_dir_str = "BUY" if "BUY" in str(t_dir).upper() else "SELL"
                    sig_dir_str = "BUY" if signal.side == OrderSide.BUY else "SELL"
                    if t_dir_str == sig_dir_str:
                        elapsed_entry = (current_time_ref - t_entry).total_seconds() / 60.0
                        if elapsed_entry < min_candles:
                            self.rejected_by_clustering += 1
                            return reject(
                                stage="clustering_protection",
                                rule="MIN_CANDLES_WINDOW",
                                category="clustering",
                                current_value=f"{elapsed_entry:.1f} mins since entry",
                                required_value=f">{min_candles} mins",
                                short_reason=f"Same direction entry too close in time for {signal.strategy_name} ({elapsed_entry:.1f} mins < {min_candles} mins)",
                                legacy_prefix="REJECTED_CLUSTERING"
                            )
                            
        # 3. Block repeated entries near the same price zone (if price hasn't moved enough since last trade)
        atr = context.get("atr", 0.0)
        point = symbol_spec.get("point", 0.0001) if symbol_spec else 0.0001
        if atr > 0:
            min_dist = atr * min_atr_mult
            for t in all_recent_trades:
                t_entry_price = t.get("entry_price")
                if t_entry_price:
                    dist = abs(signal.entry_price - t_entry_price)
                    if dist < min_dist:
                        self.rejected_by_clustering += 1
                        return reject(
                            stage="clustering_protection",
                            rule="MIN_PRICE_DISTANCE_ATR",
                            category="clustering",
                            current_value=f"{dist/point:.1f} pts",
                            required_value=f">{min_dist/point:.1f} pts",
                            short_reason=f"Entry price {signal.entry_price:.5f} too close to previous trade entry {t_entry_price:.5f} (distance {dist/point:.1f} pts < required {min_dist/point:.1f} pts)",
                            legacy_prefix="REJECTED_CLUSTERING"
                        )

        # 1. Session Filter
        if user_settings.get("session_filter_enabled", True):
            current_sessions = context.get("current_session", []) # Now a list
            mapping = user_settings.get("strategy_session_mapping", {})
            
            # Use strategy-specific allowed sessions if configured, else fallback to global preferred_session
            allowed_sessions = mapping.get(signal.strategy_name)
            if allowed_sessions:
                # If specific mapping exists, at least one current session must be in the allowed list
                session_pass = any(s in allowed_sessions for s in current_sessions)
                pref_info = f"Strategy specific: {allowed_sessions}"
            else:
                preferred_session = user_settings.get("preferred_session", "ALL")
                session_pass = preferred_session == "ALL" or any(preferred_session == s for s in current_sessions)
                pref_info = f"Global: {preferred_session}"

            logger.info(f"[{eval_id}] [RISK] Session Check: Current={current_sessions}, Allowed={pref_info} -> {'PASS' if session_pass else 'FAIL'}")
            if not session_pass:
                return reject(
                    stage="session_filter",
                    rule="SESSION_ALLOWED",
                    category="session",
                    current_value=str(current_sessions),
                    required_value=pref_info,
                    short_reason=f"Session {current_sessions} not allowed. Allowed={pref_info}. Direction={signal.side.name}",
                    legacy_prefix="REJECTED_SESSION_FILTER",
                )

        # 2. News Filter
        if user_settings.get("news_filter_enabled", True):
            news_event = context.get("active_news_event") # Expects Dict from NewsService
            logger.info(f"[{eval_id}] [RISK] News Check: Active={news_event is not None} -> {'FAIL' if news_event else 'PASS'}")
            if news_event:
                event_name = news_event.get("event_name", "Unknown Event")
                event_curr = news_event.get("currency", "N/A")
                event_time = news_event.get("start_time").strftime("%H:%M:%S")
                block_win = news_event.get("block_window", "N/A")
                return reject(
                    stage="news_filter",
                    rule="NEWS_WINDOW_CLEAR",
                    category="news",
                    current_value=f"{event_name} {event_curr} {event_time}UTC",
                    required_value=f"clear window ({block_win})",
                    short_reason=f"News window active: {event_name} ({event_curr}) at {event_time} UTC. Block={block_win}",
                    legacy_prefix="REJECTED_NEWS_WINDOW",
                )

        # 3. Signal Quality Gate
        setup_score = float(getattr(signal.setup_score, "total_score", 0.0) if getattr(signal, "setup_score", None) else 0.0)
        min_setup_score = float(user_settings.get("min_setup_score", 70.0))
        if setup_score < min_setup_score:
            return reject(
                stage="quality_gate",
                rule="SETUP_SCORE_MIN",
                category="quality",
                current_value=round(setup_score, 2),
                required_value=round(min_setup_score, 2),
                short_reason=f"Setup score {setup_score:.1f} below required {min_setup_score:.1f}",
                legacy_prefix="REJECTED_SETUP_SCORE",
            )

        min_ai_conf = float(user_settings.get("min_ai_confidence", 0.45))
        ai_conf = float(getattr(signal, "ai_confidence", 0.0))
        if ai_conf < min_ai_conf:
            return reject(
                stage="quality_gate",
                rule="AI_CONFIDENCE_MIN",
                category="quality",
                current_value=round(ai_conf, 3),
                required_value=round(min_ai_conf, 3),
                short_reason=f"AI confidence {ai_conf:.2f} below required {min_ai_conf:.2f}",
                legacy_prefix="REJECTED_AI_CONFIDENCE",
            )

        # 4. Max Open Trades (Total)
        max_t = self.max_trades if self.max_trades is not None else 2
        total_trades_pass = len(open_positions) < max_t
        logger.info(f"[{eval_id}] [RISK] Total Trades Check: Open={len(open_positions)}, Max={max_t} -> {'PASS' if total_trades_pass else 'FAIL'}")
        if not total_trades_pass:
            return reject(
                stage="position_limits",
                rule="MAX_TOTAL_TRADES",
                category="limits",
                current_value=len(open_positions),
                required_value=max_t,
                short_reason=f"Open trades {len(open_positions)} >= max allowed {max_t}",
                legacy_prefix="REJECTED_MAX_TRADES",
            )

        # 5. Max Open Trades Per Symbol
        symbol_positions = [p for p in open_positions if p.get('symbol') == signal.symbol]
        max_sym_t = user_settings.get("max_trades_per_symbol", 1)
        sym_trades_pass = len(symbol_positions) < max_sym_t
        logger.info(f"[{eval_id}] [RISK] Symbol Trades Check: {signal.symbol} Open={len(symbol_positions)}, Max={max_sym_t} -> {'PASS' if sym_trades_pass else 'FAIL'}")
        if not sym_trades_pass:
            return reject(
                stage="position_limits",
                rule="MAX_TRADES_PER_SYMBOL",
                category="limits",
                current_value=len(symbol_positions),
                required_value=max_sym_t,
                short_reason=f"{signal.symbol} open trades {len(symbol_positions)} >= max allowed {max_sym_t}",
                legacy_prefix="REJECTED_MAX_TRADES_SYMBOL",
            )

        # 6. Cooldown Check
        active_cooldowns = context.get("active_cooldowns", [])
        cooldown_block = False
        expiry_info = ""
        bars_rem = 0
        for cd in active_cooldowns:
            if cd.get("symbol") == signal.symbol and cd.get("direction") == signal.side.name:
                cooldown_block = True
                expiry = cd.get("expiry")
                if expiry:
                    if isinstance(expiry, str):
                        expiry = datetime.datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    
                    expiry_info = expiry.strftime("%H:%M:%S")
                    
                    # Use tick-based time for deterministic backtesting
                    current_time_ref = datetime.datetime.fromtimestamp(tick_time, datetime.timezone.utc) if tick_time > 0 else datetime.datetime.now(datetime.timezone.utc)
                    rem = (expiry - current_time_ref).total_seconds() / 60
                    bars_rem = max(0, int(rem))
                break
        logger.info(f"[{eval_id}] [RISK] Cooldown Check: Blocked={cooldown_block} -> {'FAIL' if cooldown_block else 'PASS'}")
        if cooldown_block:
            return reject(
                stage="cooldown",
                rule="POST_LOSS_COOLDOWN",
                category="cooldown",
                current_value=f"{bars_rem} bars remaining",
                required_value="0 bars remaining",
                short_reason=f"Cooldown active until {expiry_info} for {signal.symbol} {signal.side.name}",
                legacy_prefix="REJECTED_COOLDOWN",
            )

        # 7. Same-Zone Re-entry Block
        if user_settings.get("enable_same_zone_block", True):
            blocked_zones = context.get("blocked_zones", [])
            atr = context.get("atr", 0.0)
            for zone in blocked_zones:
                if zone.get("symbol") == signal.symbol and zone.get("direction") == signal.side.name:
                    dist = abs(signal.entry_price - zone.get("price"))
                    point = symbol_spec.get("point", 0.0001) if symbol_spec else 0.0001
                    atr_mult = user_settings.get("same_zone_distance_atr_multiplier", 0.25)
                    threshold = (atr * atr_mult) if atr > 0 else (user_settings.get("same_zone_threshold_points", 100) * point)
                    
                    if dist < threshold:
                        setup_time = signal.metadata.get("setup_time")
                        zone_created = zone.get("created_at")
                        is_fresh = False
                        if setup_time and zone_created:
                            if setup_time.tzinfo is None: setup_time = setup_time.replace(tzinfo=datetime.timezone.utc)
                            if zone_created.tzinfo is None: zone_created = zone_created.replace(tzinfo=datetime.timezone.utc)
                            is_fresh = setup_time > zone_created
                        
                        if not is_fresh:
                            logger.info(f"[{eval_id}] [RISK] Same-Zone Check: FAIL (Dist: {dist/point:.1f}pts < Thresh: {threshold/point:.1f}pts)")
                            return RiskDecision(is_approved=False, reason=f"REJECTED_SAME_ZONE: Price {signal.entry_price:.5f} near Failed Zone {zone.get('price'):.5f}. No fresh structure since last SL.", lot_size=0.0)
                            # NOTE: unreachable due to return above kept for safety

        # 8. Daily Loss Limit
        balance = account_info.get('balance', 0)
        limit = self.daily_loss_limit if self.daily_loss_limit is not None else 0.02
        daily_loss_pass = daily_pnl > -(balance * limit)
        logger.info(f"[{eval_id}] [RISK] Daily Loss Check: PnL={daily_pnl}, Limit={limit*100}% -> {'PASS' if daily_loss_pass else 'FAIL'}")
        if not daily_loss_pass:
            return reject(
                stage="daily_loss_limit",
                rule="DAILY_LOSS_LIMIT",
                category="account",
                current_value=float(daily_pnl),
                required_value=f">{-(balance * limit):.2f}",
                short_reason=f"Daily PnL {daily_pnl:.2f} breached loss limit {limit*100:.1f}%",
                legacy_prefix="REJECTED_DAILY_LOSS_LIMIT",
            )

        # 9. Spread Protection
        current_tick = signal.metadata.get("current_tick")
        if not current_tick:
            return reject(
                stage="spread_protection",
                rule="LIVE_TICK_REQUIRED",
                category="market_data",
                current_value=None,
                required_value="tick present",
                short_reason="Live tick data missing",
                legacy_prefix="REJECTED_SPREAD",
            )

        tick_time = current_tick.get("time", 0)
        current_ts = tick_time if is_backtest else int(time.time())
        latency = current_ts - tick_time
        
        if not is_backtest and latency > 10:
            return reject(
                stage="spread_protection",
                rule="TICK_FRESHNESS_MAX_SEC",
                category="market_data",
                current_value=latency,
                required_value="<=10s",
                short_reason=f"Tick data stale ({latency}s old)",
                legacy_prefix="REJECTED_STALE_TICK",
            )
        elif is_backtest and latency > 10:
            logger.info(f"[{eval_id}] [RISK] Backtest mode: Skipping tick freshness check (Latency: {latency}s)")
            # We don't return here, we just continue to other checks.
            # We can't easily add to a metadata that doesn't exist yet (approved decision is created at the end).
            # So I'll just rely on the fact that if it passes, it was skipped if latency > 10.
            pass

        spread = current_tick.get("ask", 0) - current_tick.get("bid", 0)
        point = symbol_spec.get("point", 0.0001) if symbol_spec else 0.0001
        if point > 0:
            spread_points = spread / point
            max_spread = user_settings.get("max_spread_points", 50)
            if spread_points > max_spread:
                return reject(
                    stage="spread_protection",
                    rule="MAX_SPREAD_POINTS",
                    category="spread",
                    current_value=round(float(spread_points), 2),
                    required_value=float(max_spread),
                    short_reason=f"Spread {spread_points:.1f} points is above max allowed {max_spread}",
                    legacy_prefix="REJECTED_SPREAD",
                )

            # 10. Late Entry & RR Filter
            exec_price = current_tick.get("ask") if signal.side == OrderSide.BUY else current_tick.get("bid")
            entry_signal = signal.entry_price
            sl = signal.structural_sl or signal.sl
            tp = signal.targets[0] if (signal.targets and len(signal.targets) > 0) else 0
            
            # Geometry Validation
            if tp == 0 or sl == 0:
                 return reject("risk_manager", "INVALID_RR_GEOMETRY", "geometry", 0, "non-zero", "SL or TP is zero", "REJECTED_GEOMETRY")
            
            if signal.side == OrderSide.BUY:
                if sl >= exec_price:
                    return reject("risk_manager", "INVALID_RR_GEOMETRY", "geometry", sl, f"<{exec_price}", "SL above entry for BUY", "REJECTED_GEOMETRY")
                if tp <= exec_price:
                    return reject("risk_manager", "INVALID_RR_GEOMETRY", "geometry", tp, f">{exec_price}", "TP below entry for BUY", "REJECTED_GEOMETRY")
            else:
                if sl <= exec_price:
                    return reject("risk_manager", "INVALID_RR_GEOMETRY", "geometry", sl, f">{exec_price}", "SL below entry for SELL", "REJECTED_GEOMETRY")
                if tp >= exec_price:
                    return reject("risk_manager", "INVALID_RR_GEOMETRY", "geometry", tp, f"<{exec_price}", "TP above entry for SELL", "REJECTED_GEOMETRY")

            risk = abs(exec_price - sl)
            reward = abs(tp - exec_price)
            
            if risk <= 0:
                return reject("risk_manager", "INVALID_RR", "rr", risk, ">0", "Risk distance is zero", "REJECTED_RR")
            
            current_rr = reward / risk
            
            # Resolve Minimum RR by Profile
            min_rr = 1.2 # Balanced default
            if gate_profile == "strict": min_rr = 1.5
            elif gate_profile == "research": min_rr = 0.1
            
            # Manual override from settings if present
            min_rr = user_settings.get("min_rr_filter", min_rr)

            if current_rr < min_rr:
                # In research mode, we allow it but mark it
                if gate_profile == "research":
                    logger.info(f"[RISK] Research Mode: Allowing low RR trade ({current_rr:.2f})")
                else:
                    return reject(
                        stage="risk_manager",
                        rule="RR_TOO_LOW",
                        category="rr",
                        current_value=round(float(current_rr), 3),
                        required_value=float(min_rr),
                        short_reason=f"RR quality {current_rr:.2f} is below minimum {min_rr}",
                        legacy_prefix="REJECTED_RR_FILTER",
                    )
            
            # Late Entry Check
            total_move = abs(tp - entry_signal)
            current_move = abs(exec_price - entry_signal)
            if total_move > 0:
                move_pct = current_move / total_move
                threshold = user_settings.get("late_entry_threshold", 0.7)
                if move_pct > threshold:
                    return reject(
                        stage="late_entry",
                        rule="LATE_ENTRY_MAX_PCT",
                        category="timing",
                        current_value=round(float(move_pct), 4),
                        required_value=float(threshold),
                        short_reason=f"Late entry: {move_pct:.1%} move gone is above limit {threshold:.1%}",
                        legacy_prefix="REJECTED_LATE_ENTRY",
                    )

        # 11. HTF Trend Alignment Filter (SENTINEL)
        if user_settings.get("enable_htf_filter", True):
            market_bias = context.get("market_bias") # Expected: "BULLISH", "BEARISH", "NEUTRAL"
            signal_dir = "BULLISH" if signal.side == OrderSide.BUY else "BEARISH"
            
            logger.info(f"[{eval_id}] [RISK] Trend Check: HTF Bias={market_bias}, Signal={signal_dir} -> {'PASS' if market_bias == signal_dir or market_bias == 'NEUTRAL' else 'FAIL'}")
            
            if market_bias != "NEUTRAL" and market_bias != signal_dir:
                return reject(
                    stage="htf_alignment",
                    rule="HTF_BIAS_MATCH",
                    category="trend",
                    current_value=str(signal_dir),
                    required_value=str(market_bias),
                    short_reason=f"Signal {signal_dir} is against HTF Bias ({market_bias})",
                    legacy_prefix="REJECTED_HTF_ALIGNMENT",
                )

        # 12. Volatility Buffer Check (ATR Protection)
        if user_settings.get("enable_volatility_filter", True):
            atr = context.get("atr", 0.0)
            if atr > 0:
                point = symbol_spec.get("point", 0.0001) if symbol_spec else 0.0001
                sl_dist = abs(exec_price - sl)
                # If SL is tighter than 0.5 * ATR, it's likely to be hunted by noise
                min_sl_atr = user_settings.get("min_sl_atr_multiplier", 0.5)
                if sl_dist < (atr * min_sl_atr):
                    return reject(
                        stage="volatility_filter",
                        rule="MIN_SL_ATR_MULTIPLIER",
                        category="volatility",
                        current_value=round(float(sl_dist / point), 2),
                        required_value=round(float((atr * min_sl_atr) / point), 2),
                        short_reason=f"SL distance {sl_dist/point:.1f}pts is too tight for ATR requirement {min_sl_atr}x",
                        legacy_prefix="REJECTED_VOLATILITY_NOISE",
                    )

        # 13. Do-not-trade-into-level Filter
        if user_settings.get("enable_level_distance_filter", True):
            nearest_level_data = context.get("nearest_level") # Dict: {"price", "type", "tf"}
            if nearest_level_data:
                nearest_level = nearest_level_data.get("price")
                is_buy = signal.side == OrderSide.BUY
                dist_to_level = (nearest_level - exec_price) if is_buy else (exec_price - nearest_level)
                risk_dist = abs(exec_price - sl)
                
                if risk_dist > 0:
                    reward_rr = dist_to_level / risk_dist
                    min_rr_to_level = user_settings.get("min_reward_to_nearest_level_rr", 1.2)
                    in_front = (is_buy and nearest_level > exec_price) or (not is_buy and nearest_level < exec_price)
                    
                    if in_front and reward_rr < min_rr_to_level:
                        return reject(
                            stage="level_distance_filter",
                            rule="MIN_RR_TO_NEAREST_LEVEL",
                            category="levels",
                            current_value=round(float(reward_rr), 3),
                            required_value=float(min_rr_to_level),
                            short_reason=f"Room to level poor. RR to level {reward_rr:.2f} < {min_rr_to_level}. Level={nearest_level:.5f} ({nearest_level_data.get('tf')})",
                            legacy_prefix="REJECTED_NEAR_LEVEL",
                        )

        # 14. Lot Size Calculation (Adaptive)
        effective_risk_pct = self._compute_effective_risk_pct(signal, user_settings)
        manual_vol = self._get_manual_volume(signal.symbol, user_settings)
        if manual_vol is not None:
            lot_size = float(manual_vol)
        else:
            lot_size = self._calculate_lot_size(balance, exec_price, sl, signal.symbol, symbol_spec, risk_pct=effective_risk_pct)
        
        if lot_size <= 0:
            return reject(
                stage="lot_sizing",
                rule="LOT_SIZE_POSITIVE",
                category="sizing",
                current_value=float(lot_size),
                required_value=">0",
                short_reason="Invalid lot size calculation",
                legacy_prefix="REJECTED_LOT_SIZE",
            )

        return RiskDecision(
            is_approved=True, 
            reason="Risk approved", 
            lot_size=lot_size,
            risk_pct=effective_risk_pct
        )

    def _compute_effective_risk_pct(self, signal: TradeSignal, settings_dict: Dict) -> float:
        """Scale risk down for borderline-quality signals and keep full risk for high-quality setups."""
        base_risk = float(settings_dict.get("risk_per_trade", self.risk_per_trade))
        min_risk = float(settings_dict.get("min_risk_per_trade", 0.003))
        max_risk = float(settings_dict.get("max_risk_per_trade", base_risk))

        setup_score = float(getattr(signal.setup_score, "total_score", 0.0) if getattr(signal, "setup_score", None) else 0.0)
        ai_conf = float(getattr(signal, "ai_confidence", 0.0))

        score_factor = max(0.0, min(1.0, (setup_score - 70.0) / 30.0))
        ai_factor = max(0.0, min(1.0, (ai_conf - 0.5) / 0.5))
        quality_factor = (score_factor * 0.6) + (ai_factor * 0.4)

        dynamic_risk = min_risk + (base_risk - min_risk) * quality_factor
        return max(min_risk, min(max_risk, dynamic_risk))

    def _get_manual_volume(self, symbol: str, settings_dict: Dict) -> Optional[float]:
        # 1. Check if the value is directly in the dict (flat settings passed from loop)
        if "manual_volume" in settings_dict:
            return settings_dict["manual_volume"]

        sym_upper = symbol.upper()
        # 2. Check for exact symbol match as a key
        if sym_upper in settings_dict and isinstance(settings_dict[sym_upper], dict):
            return settings_dict[sym_upper].get("manual_volume")
            
        # aliases
        base_sym = sym_upper.split(".")[0]
        aliases = {
            "GOLD": ["XAUUSD", "XAUUSD.", "XAUUSD.raw", "XAUUSD.m", "XAUUSD.pro"],
            "XAUUSD": ["GOLD", "GOLD.", "GOLD.raw", "GOLD.m", "GOLD.pro"],
        }
        
        for main, alts in aliases.items():
            if sym_upper == main or sym_upper in alts:
                for s in [main] + alts:
                    if s in settings_dict and "manual_volume" in settings_dict[s]:
                        return settings_dict[s]["manual_volume"]
        return None

    def _calculate_lot_size(self, balance: float, entry: float, sl: float, symbol: str, spec: Optional[Dict] = None, risk_pct: Optional[float] = None) -> float:
        applied_risk = self.risk_per_trade if risk_pct is None else max(0.0, float(risk_pct))
        risk_amount = balance * applied_risk
        stop_loss_diff = abs(entry - sl)
        
        if stop_loss_diff == 0:
            return 0.0
            
        # Logic based on symbol type and contract size
        multiplier = 100000 # Default for Forex
        if "GOLD" in symbol.upper() or "XAU" in symbol.upper():
            multiplier = 100
        elif "JPY" in symbol.upper():
            multiplier = 1000
        elif spec and "contract_size" in spec:
            multiplier = spec["contract_size"]
        
        lots = risk_amount / (stop_loss_diff * multiplier)
            
        # Refine by symbol step
        min_v = 0.01
        step = 0.01
        if spec:
            min_v = spec.get("min_volume", 0.01)
            step = spec.get("volume_step", 0.01)

        final_lots = max(min_v, round(round(lots / (step or 0.01)) * (step or 0.01), 2))
        return final_lots
