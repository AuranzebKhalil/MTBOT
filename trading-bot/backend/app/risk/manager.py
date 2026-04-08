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

    def validate_signal(self, signal: TradeSignal, account_info: Dict, open_positions: List[Dict], daily_pnl: float, symbol_settings: Optional[Dict] = None, symbol_spec: Optional[Dict] = None, context: Optional[Dict] = None) -> RiskDecision:
        """
        Comprehensive risk validation for a signal.
        """
        user_settings = symbol_settings or {}
        context = context or {}
        eval_id = context.get("eval_id", "N/A")

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
                reason = (
                    f"REJECTED_SESSION_FILTER: Strategy={signal.strategy_name} not allowed in {current_sessions}. "
                    f"Allowed sessions: {pref_info}. Direction={signal.side.name}"
                )
                return RiskDecision(is_approved=False, reason=reason, lot_size=0.0)

        # 2. News Filter
        if user_settings.get("news_filter_enabled", True):
            news_event = context.get("active_news_event") # Expects Dict from NewsService
            logger.info(f"[{eval_id}] [RISK] News Check: Active={news_event is not None} -> {'FAIL' if news_event else 'PASS'}")
            if news_event:
                event_name = news_event.get("event_name", "Unknown Event")
                event_curr = news_event.get("currency", "N/A")
                event_time = news_event.get("start_time").strftime("%H:%M:%S")
                block_win = news_event.get("block_window", "N/A")
                reason = (
                    f"REJECTED_NEWS_WINDOW: {event_name} ({event_curr}) at {event_time} UTC. "
                    f"Block window: {block_win}. Strategy={signal.strategy_name}, Direction={signal.side.name}"
                )
                return RiskDecision(is_approved=False, reason=reason, lot_size=0.0)

        # 3. Max Open Trades (Total)
        max_t = self.max_trades if self.max_trades is not None else 2
        total_trades_pass = len(open_positions) < max_t
        logger.info(f"[{eval_id}] [RISK] Total Trades Check: Open={len(open_positions)}, Max={max_t} -> {'PASS' if total_trades_pass else 'FAIL'}")
        if not total_trades_pass:
            return RiskDecision(is_approved=False, reason=f"Max total open trades ({max_t}) reached", lot_size=0.0)

        # 4. Max Open Trades Per Symbol
        symbol_positions = [p for p in open_positions if p.get('symbol') == signal.symbol]
        max_sym_t = user_settings.get("max_trades_per_symbol", 1)
        sym_trades_pass = len(symbol_positions) < max_sym_t
        logger.info(f"[{eval_id}] [RISK] Symbol Trades Check: {signal.symbol} Open={len(symbol_positions)}, Max={max_sym_t} -> {'PASS' if sym_trades_pass else 'FAIL'}")
        if not sym_trades_pass:
            return RiskDecision(is_approved=False, reason=f"Max trades for {signal.symbol} ({max_sym_t}) reached", lot_size=0.0)

        # 5. Cooldown Check
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
                    rem = (expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 60
                    bars_rem = max(0, int(rem))
                break
        logger.info(f"[{eval_id}] [RISK] Cooldown Check: Blocked={cooldown_block} -> {'FAIL' if cooldown_block else 'PASS'}")
        if cooldown_block:
            return RiskDecision(is_approved=False, reason=f"REJECTED_COOLDOWN: Blocked until {expiry_info} for {signal.symbol} {signal.side.name} ({bars_rem} bars left)", lot_size=0.0)

        # 6. Same-Zone Re-entry Block
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

        # 7. Daily Loss Limit
        balance = account_info.get('balance', 0)
        limit = self.daily_loss_limit if self.daily_loss_limit is not None else 0.02
        daily_loss_pass = daily_pnl > -(balance * limit)
        logger.info(f"[{eval_id}] [RISK] Daily Loss Check: PnL={daily_pnl}, Limit={limit*100}% -> {'PASS' if daily_loss_pass else 'FAIL'}")
        if not daily_loss_pass:
            return RiskDecision(is_approved=False, reason=f"Daily account loss limit ({limit*100}%) reached", lot_size=0.0)

        # 8. Spread Protection
        current_tick = signal.metadata.get("current_tick")
        if not current_tick:
            return RiskDecision(is_approved=False, reason="REJECTED_SPREAD: Live tick data missing", lot_size=0.0)

        tick_time = current_tick.get("time", 0)
        current_ts = int(time.time())
        latency = current_ts - tick_time
        if latency > 10:
            return RiskDecision(is_approved=False, reason=f"REJECTED_STALE_TICK: Tick data stale ({latency}s old)", lot_size=0.0)

        spread = current_tick.get("ask", 0) - current_tick.get("bid", 0)
        point = symbol_spec.get("point", 0.0001) if symbol_spec else 0.0001
        if point > 0:
            spread_points = spread / point
            max_spread = user_settings.get("max_spread_points", 50)
            if spread_points > max_spread:
                return RiskDecision(is_approved=False, reason=f"REJECTED_SPREAD: {spread_points:.1f} pts (Max: {max_spread})", lot_size=0.0)

        # 9. Late Entry & RR Filter
        exec_price = current_tick.get("ask") if signal.side == OrderSide.BUY else current_tick.get("bid")
        entry_signal = signal.entry_price
        sl = signal.structural_sl or signal.sl
        tp = signal.targets[0] if (signal.targets and len(signal.targets) > 0) else 0
        
        if tp != 0:
            total_move = abs(tp - entry_signal)
            current_move = abs(exec_price - entry_signal)
            if total_move > 0:
                move_pct = current_move / total_move
                threshold = user_settings.get("late_entry_threshold", 0.7)
                if move_pct > threshold:
                    return RiskDecision(is_approved=False, reason=f"REJECTED_LATE_ENTRY: {move_pct:.1%} move gone (Limit: {threshold})", lot_size=0.0)
            
            risk = abs(exec_price - sl)
            reward = abs(tp - exec_price)
            if risk > 0:
                current_rr = reward / risk
                min_rr = user_settings.get("min_rr_filter", 1.0)
                if current_rr < min_rr:
                    return RiskDecision(is_approved=False, reason=f"REJECTED_RR_FILTER: {current_rr:.2f} (Min: {min_rr})", lot_size=0.0)

        # 10. HTF Trend Alignment Filter (SENTINEL)
        if user_settings.get("enable_htf_filter", True):
            market_bias = context.get("market_bias") # Expected: "BULLISH", "BEARISH", "NEUTRAL"
            signal_dir = "BULLISH" if signal.side == OrderSide.BUY else "BEARISH"
            
            logger.info(f"[{eval_id}] [RISK] Trend Check: HTF Bias={market_bias}, Signal={signal_dir} -> {'PASS' if market_bias == signal_dir or market_bias == 'NEUTRAL' else 'FAIL'}")
            
            if market_bias != "NEUTRAL" and market_bias != signal_dir:
                reason = f"REJECTED_HTF_ALIGNMENT: Signal {signal_dir} is against HTF Bias ({market_bias}). Win probability too low."
                return RiskDecision(is_approved=False, reason=reason, lot_size=0.0)

        # 11. Volatility Buffer Check (ATR Protection)
        if user_settings.get("enable_volatility_filter", True):
            atr = context.get("atr", 0.0)
            if atr > 0:
                point = symbol_spec.get("point", 0.0001) if symbol_spec else 0.0001
                sl_dist = abs(exec_price - sl)
                # If SL is tighter than 0.5 * ATR, it's likely to be hunted by noise
                min_sl_atr = user_settings.get("min_sl_atr_multiplier", 0.5)
                if sl_dist < (atr * min_sl_atr):
                    reason = f"REJECTED_VOLATILITY_NOISE: SL dist ({sl_dist/point:.1f}pts) is too tight for current ATR ({atr/point:.1f}pts). Exposure to hunt is high."
                    return RiskDecision(is_approved=False, reason=reason, lot_size=0.0)

        # 12. Do-not-trade-into-level Filter
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
                        reason = (
                            f"REJECTED_NEAR_LEVEL: {getattr(signal, 'strategy_name', 'Unknown')} - Room to level poor. "
                            f"Level: {nearest_level:.5f} ({nearest_level_data.get('tf')}), RR to level: {reward_rr:.2f} < {min_rr_to_level}"
                        )
                        return RiskDecision(is_approved=False, reason=reason, lot_size=0.0)

        # 11. Lot Size Calculation
        manual_vol = self._get_manual_volume(signal.symbol, user_settings)
        if manual_vol is not None:
            lot_size = float(manual_vol)
        else:
            lot_size = self._calculate_lot_size(balance, exec_price, sl, signal.symbol, symbol_spec)
        
        if lot_size <= 0:
            return RiskDecision(is_approved=False, reason="Invalid lot size calculation", lot_size=0.0)

        return RiskDecision(
            is_approved=True, 
            reason="Risk approved", 
            lot_size=lot_size,
            risk_pct=self.risk_per_trade
        )

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

    def _calculate_lot_size(self, balance: float, entry: float, sl: float, symbol: str, spec: Optional[Dict] = None) -> float:
        risk_amount = balance * self.risk_per_trade
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
