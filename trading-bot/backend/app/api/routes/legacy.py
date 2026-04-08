from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.storage.db import get_db
from app.storage.models import BotState, Trade, SignalLog, User
from app.api.routes.bot import get_bot_status, start_bot, stop_bot
from app.api.routes.trades import get_recent_trades
from app.api.routes.risk import get_risk_settings, update_risk_settings
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class SettingsUpdate(BaseModel):
    symbol: Optional[str] = None
    active_symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    preferred_session: Optional[str] = None
    ai_confidence_threshold: Optional[float] = None

class SymbolSettingsUpdate(BaseModel):
    symbol: str
    manual_volume: Optional[float] = None

class StrategySettingsUpdate(BaseModel):
    strategy_id: str
    enabled: Optional[bool] = None
    ai_threshold: Optional[float] = None
    params: Optional[dict] = None

def map_trade(trade: Trade):
    return {
        "id": trade.id,
        "ticket_id": trade.ticket_id,
        "symbol": trade.symbol,
        "type": trade.type,
        "volume": trade.volume or 0.0,
        "initial_volume": trade.initial_volume or 0.0,
        "progress": round((1 - (trade.volume / trade.initial_volume)) * 100) if trade.initial_volume and trade.volume else 0,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "sl": trade.sl,
        "tp": trade.tp,
        "pnl": trade.profit or 0.0,
        "profit": trade.profit or 0.0,
        "status": trade.status,
        "time": trade.time.strftime("%Y-%m-%dT%H:%M:%S") if trade.time else None,
        "strategy": trade.strategy_name or "Manual",
        "strategy_name": trade.strategy_name,
        "rationale": trade.rationale or "Institutional Quant Analysis",
        "ai_score": trade.ai_score,
        "session": trade.session,
        "regime": trade.market_regime,
        "exit_reason": trade.exit_reason
    }

@router.get("/multi-status")
def multi_status(db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    if not state:
        return {"status": {}, "symbols": {}}

    metrics_data = state.current_metrics or {}
    active_symbols = state.active_symbols or ["GOLD"]
    
    # Calculate real stats from history
    total_trades = db.query(Trade).filter(Trade.status == "CLOSED").count()
    winning_trades = db.query(Trade).filter(Trade.status == "CLOSED", Trade.profit > 0).count()
    win_rate = round((winning_trades / total_trades * 100), 1) if total_trades > 0 else 0
    
    # Simple Growth Calculation
    total_profit = db.query(func.sum(Trade.profit)).filter(Trade.status == "CLOSED").scalar() or 0.0
    initial_balance = metrics_data.get("balance", 1000) - total_profit
    growth = round(float(total_profit / initial_balance * 100), 2) if initial_balance > 0 else 0.0
    
    bot_status = {
        "is_running": state.is_running,
        "status_message": state.status_message or "Bot is Idle",
        "current_action": state.current_action or "None",
        "balance": metrics_data.get("balance", 0),
        "equity": metrics_data.get("equity", 0),
        "daily_pnl": metrics_data.get("daily_pnl", 0),
        "active_trades": metrics_data.get("active_trades", 0),
        "win_rate": win_rate,
        "profit_factor": 1.85, # Logic for PF can be added here
        "total_growth": growth,
        "symbol": active_symbols[0] if active_symbols else "GOLD",
        "active_symbols": active_symbols,
        "timeframe": "M1",
        "market_open": True,
        "logs": state.live_logs or ["Bot Engine Operational"],
        "recent_rejections": state.recent_rejections or [],
        "ai_confidence_threshold": float(getattr(state, "ai_confidence_threshold", None) or metrics_data.get("ai_confidence_threshold", 0.48)),
        "filter_status": state.filter_status or {},
        "active_cooldowns": state.active_cooldowns or [],
        "strategy_analytics": state.strategy_analytics or {},
    }

    live_charts = state.live_charts or {}
    results = {}
    for sym in active_symbols:
        data = live_charts.get(sym, {})
        # Ensure data is a dict before calling get()
        chart_data = []
        overlay_data = {"fvg_zones":[], "order_blocks":[], "sweeps":[], "bos_markers":[], "support_resistance":[]}
        
        if isinstance(data, dict):
            chart_data = data.get("chart", [])
            overlay_data = data.get("overlays", overlay_data)
        else:
            chart_data = data # Fallback for old list format
        
        results[sym] = {
            "chart": chart_data,
            "overlays": overlay_data,
            "last_decision": {"direction": "WAIT", "strategy": "Monitoring", "reason": "Scanning...", "score": 0, "flow": []}
        }
    
    return {
        "status": bot_status,
        "symbols": results,
        "depth": metrics_data.get("depth", {"bids": [], "asks": []})
    }

@router.get("/status")
def legacy_status(db: Session = Depends(get_db)):
    res = multi_status(db)
    return res["status"]

@router.get("/chart")
def legacy_chart(symbol: str = "GOLD", db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    if not state or not state.live_charts:
        return []
    return state.live_charts.get(symbol.upper(), [])

@router.get("/trades")
def legacy_trades(db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(Trade.status == "OPEN").all()
    return [map_trade(t) for t in trades]

@router.get("/history")
def legacy_history(db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(Trade.status == "CLOSED").order_by(Trade.time.desc()).all()
    return [map_trade(t) for t in trades]

@router.get("/news")
def legacy_news():
    from app.market_data.mt5_client import MT5Client
    client = MT5Client()
    if client.connect():
        try:
            events = client.get_calendar_events()
            # Transform for frontend: importance (1,2,3) -> impact (LOW, MEDIUM, HIGH)
            impact_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}
            return [{
                "symbol": e.get("currency", "???"),
                "name": e.get("event", "Economic Event"),
                "time": e["time"].split("T")[1][:5] if "T" in e.get("time", "") else e.get("time", "00:00"),
                "impact": impact_map.get(e.get("importance", 1), "LOW")
            } for e in events]
        except Exception as e:
            from logging import getLogger
            getLogger("legacy").error(f"News transformation error: {e}")
            return []
    return []

@router.get("/depth")
def legacy_depth(symbol: str = "GOLD"):
    from app.market_data.mt5_client import MT5Client
    client = MT5Client()
    if client.connect():
        return client.get_market_depth(symbol.upper())
    return {"bids": [], "asks": []}

@router.get("/strategies")
def legacy_strategies():
    return []

@router.get("/risk")
def legacy_get_risk(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        return {
            "risk_per_trade": 0.01,
            "max_trades": 2,
            "max_daily_trades": 20,
            "daily_loss_limit": 0.10
        }
    return {
        "risk_per_trade": user.risk_per_trade,
        "max_trades": user.max_trades,
        "max_daily_trades": 20,
        "daily_loss_limit": user.daily_loss_limit,
        "preferred_session": user.preferred_session or "ALL"
    }

@router.post("/risk")
def legacy_update_risk(settings: dict, db: Session = Depends(get_db)):
    from app.api.routes.risk import RiskSettings
    
    # We fetch the current user to get the existing preferred_session if it's not sent
    user = db.query(User).first()
    curr_session = user.preferred_session if user and getattr(user, "preferred_session", None) else "ALL"
    
    risk_data = {
        "risk_per_trade": settings.get("risk_per_trade", getattr(user, "risk_per_trade", 0.01)),
        "max_trades": settings.get("max_trades", getattr(user, "max_trades", 2)),
        "daily_loss_limit": settings.get("daily_loss_limit", getattr(user, "daily_loss_limit", 0.1)),
        "preferred_session": settings.get("preferred_session", curr_session),
        "risk_reward_ratio": settings.get("risk_reward_ratio", getattr(user, "preferred_rr_ratio", 1.5)),
        # Add missing fields to satisfy RiskSettings Pydantic model
        "partial_execution_enabled": settings.get("partial_execution_enabled", getattr(user, "partial_execution_enabled", True)),
        "partial_stage_1_trigger": settings.get("partial_stage_1_trigger", getattr(user, "partial_stage_1_trigger", 0.6)),
        "partial_stage_1_close_pct": settings.get("partial_stage_1_close_pct", getattr(user, "partial_stage_1_close_pct", 0.5)),
        "partial_stage_2_trigger": settings.get("partial_stage_2_trigger", getattr(user, "partial_stage_2_trigger", 0.8)),
        "partial_stage_2_close_pct": settings.get("partial_stage_2_close_pct", getattr(user, "partial_stage_2_close_pct", 0.25)),
    }
    return update_risk_settings(RiskSettings(**risk_data), db)

@router.post("/settings")
def legacy_update_settings(settings: SettingsUpdate, db: Session = Depends(get_db)):
    state = db.query(BotState).first()
    if not state:
        state = BotState(is_running=False, active_symbols=["GOLD"])
        db.add(state)
    
    if settings.active_symbols:
        state.active_symbols = [s.upper() for s in settings.active_symbols]

    if settings.timeframe:
        state.timeframe = settings.timeframe

    if settings.preferred_session:
        user = db.query(User).first()
        if user:
            user.preferred_session = settings.preferred_session

    if settings.ai_confidence_threshold is not None:
        v = float(settings.ai_confidence_threshold)
        state.ai_confidence_threshold = max(0.15, min(1.0, v))
        cm = dict(state.current_metrics or {})
        cm["ai_confidence_threshold"] = state.ai_confidence_threshold
        state.current_metrics = cm
    
    db.commit()
    return {"status": "Settings updated", "data": {}}

@router.post("/start")
def legacy_start(db: Session = Depends(get_db)):
    return start_bot(db)

@router.post("/stop")
def legacy_stop(db: Session = Depends(get_db)):
    return stop_bot(db)

@router.post("/reset/history")
def legacy_reset_history(db: Session = Depends(get_db)):
    db.query(Trade).delete()
    db.commit()
    return {"message": "Success"}

@router.delete("/history/{trade_id}")
def delete_history_item(trade_id: str, db: Session = Depends(get_db)):
    # Try by internal DB ID first
    try:
        db_id = int(trade_id)
        trade = db.query(Trade).filter(Trade.id == db_id).first()
    except ValueError:
        trade = None

    # Fallback: Try by MT5 Ticket ID
    if not trade:
        try:
            ticket = int(trade_id)
            trade = db.query(Trade).filter(Trade.ticket_id == ticket).first()
        except ValueError:
            trade = None
            
    if not trade:
        # Final check: search symbol or other string-based IDs if needed
        raise HTTPException(status_code=404, detail=f"Trade record {trade_id} not found in Alpha database.")
        
    db.delete(trade)
    db.commit()
    return {"status": "deleted", "id": trade_id}

@router.post("/reset/risk")
def legacy_reset_risk(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if user:
        user.risk_per_trade = 0.01
        user.max_trades = 2
        user.daily_loss_limit = 0.05
        db.commit()
    return {"message": "Success", "data": {"risk_per_trade": 0.01, "max_trades": 2, "daily_loss_limit": 0.05}}

@router.post("/settings/symbol")
def update_symbol_settings(update: SymbolSettingsUpdate, db: Session = Depends(get_db)):
    """Updates manual volume override for a specific symbol."""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings_dict = dict(user.symbol_settings or {})
    
    # Save under the direct name provided by the frontend
    main_sym = update.symbol.upper()
    if update.manual_volume is not None:
        if main_sym not in settings_dict:
            settings_dict[main_sym] = {}
        settings_dict[main_sym]["manual_volume"] = update.manual_volume
        
        # Also try to resolve and save under the resolved name for RiskManager
        from app.market_data.mt5_client import MT5Client
        client = MT5Client()
        if client.connect():
            resolved = client.resolve_symbol(main_sym)
            if resolved and resolved != main_sym:
                if resolved not in settings_dict:
                    settings_dict[resolved] = {}
                settings_dict[resolved]["manual_volume"] = update.manual_volume
    else:
        # If None, remove the override
        if main_sym in settings_dict:
            settings_dict[main_sym].pop("manual_volume", None)
            
    user.symbol_settings = settings_dict
    db.commit()
    
    from logging import getLogger
    logger = getLogger("legacy")
    logger.info(f"Volume Saved: {main_sym} -> {update.manual_volume}")
    
    return {"message": f"Updated settings for {main_sym}", "settings": settings_dict.get(main_sym, {})}

@router.post("/settings/strategy")
def update_strategy_settings(update: StrategySettingsUpdate, db: Session = Depends(get_db)):
    """Updates toggle or params for a specific strategy."""
    user = db.query(User).first()
    state = db.query(BotState).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    settings_dict = dict(user.strategy_settings or {})
    if update.strategy_id not in settings_dict:
        settings_dict[update.strategy_id] = {"enabled": True, "ai_threshold": 0.7, "params": {}}
    
    if update.enabled is not None:
        settings_dict[update.strategy_id]["enabled"] = update.enabled
    if update.ai_threshold is not None:
        settings_dict[update.strategy_id]["ai_threshold"] = update.ai_threshold
    if update.params is not None:
        settings_dict[update.strategy_id]["params"].update(update.params)
        
    user.strategy_settings = settings_dict
    if state:
        state.strategy_settings = settings_dict
        
    db.commit()
    return {"message": f"Updated strategy {update.strategy_id}", "settings": settings_dict[update.strategy_id]}

@router.get("/settings/strategy")
def get_strategy_settings(db: Session = Depends(get_db)):
    """Returns all current strategy settings."""
    user = db.query(User).first()
    if not user:
        return {}
    
    # Default set if empty
    defaults = {
        "SMC_SWEEP": {"name": "BOS + Liquidity Sweep", "enabled": True, "ai_threshold": 0.7},
        "SMC_REVERSAL": {"name": "FVG + OB Reversal", "enabled": True, "ai_threshold": 0.7},
        "SMC_MSS": {"name": "Market Structure Shift (MSS)", "enabled": False, "ai_threshold": 0.75},
        "SMC_BREAKER": {"name": "Breaker Block (BB)", "enabled": False, "ai_threshold": 0.8},
        "SMC_VOLUME": {"name": "Volume Profile & Order Flow", "enabled": False, "ai_threshold": 0.7},
        "SMC_TREND": {"name": "MTF Trend Continuation", "enabled": True, "ai_threshold": 0.65},
        "SMC_MITIGATION": {"name": "First Touch Mitigation", "enabled": True, "ai_threshold": 0.7},
        "SMC_VSA": {"name": "Absorption Shift", "enabled": True, "ai_threshold": 0.7},
        "HYBRID_MASTER": {"name": "Hybrid Master Switcher (Auto-Regime)", "enabled": True, "ai_threshold": 0.5},
        "HYBRID_REVERSION": {"name": "Mean Reversion (BB/RSI)", "enabled": True, "ai_threshold": 0.7},
        "HYBRID_SR": {"name": "Advanced S/R Reversal", "enabled": True, "ai_threshold": 0.7},
        "HYBRID_BREAKOUT": {"name": "Momentum Breakout", "enabled": True, "ai_threshold": 0.7},
        "MAD_TREND_LOOP": {"name": "MAD - Trend Loop (Lyro RS)", "enabled": True, "ai_threshold": 0.5},
    }
    
    current = user.strategy_settings or {}
    for k, v in defaults.items():
        if k not in current:
            current[k] = v
            
    return current

@router.get("/symbols/engine-config")
def get_symbol_engine_config(db: Session = Depends(get_db)):
    """Returns symbol specifications collected by the worker."""
    state = db.query(BotState).first()
    user = db.query(User).first()
    if not state or not state.current_metrics or not user:
        return {}
    
    specs = state.current_metrics.get("symbol_specs", {})
    user_settings = user.symbol_settings or {}
    
    # Combined specs with user settings
    response = {}
    aliases = {
        "GOLD": ["XAUUSD", "XAUUSD.", "XAUUSD.raw", "XAUUSD.m", "XAUUSD.i", "XAUUSD.pro"],
        "XAUUSD": ["GOLD", "GOLD.", "GOLD.raw", "GOLD.m", "GOLD.i", "GOLD.pro"],
        "EURUSD": ["EURUSD.", "EURUSD.raw", "EURUSD.m", "EURUSD.pro"],
        "GBPUSD": ["GBPUSD.", "GBPUSD.raw", "GBPUSD.m", "GBPUSD.pro"],
    }

    for symbol, spec in specs.items():
        sym_upper = symbol.upper()
        # 1. Direct match
        vol = user_settings.get(sym_upper, {}).get("manual_volume")
        
        # 2. Try variations (removing dots/suffixes)
        if vol is None:
            base_sym = sym_upper.split(".")[0]
            vol = user_settings.get(base_sym, {}).get("manual_volume")

        # 3. Try hardcoded aliases
        if vol is None:
            for main, alternates in aliases.items():
                if sym_upper == main or sym_upper in alternates:
                    # Look for any of the alternates in user_settings
                    for alt in [main] + alternates:
                        if alt in user_settings:
                            vol = user_settings[alt].get("manual_volume")
                            if vol is not None: break
                if vol is not None: break

        response[symbol] = {
            **spec,
            "manual_volume": float(vol) if vol is not None else None
        }
    return response

@router.get("/symbols/search")
def search_symbols(q: str = ""):
    """Search for symbols across the broker's entire asset list."""
    from app.market_data.mt5_client import MT5Client
    client = MT5Client()
    if client.connect():
        all_syms = client.get_all_symbols()
        if not q:
            # Return first 50 if no query
            return all_syms[:50]
        
        q = q.upper()
        matches = [s for s in all_syms if q in s["name"].upper() or q in s["description"].upper()]
        return matches[:30] # Limit results
    return []

@router.delete("/risk/events")
def legacy_clear_risk_events(db: Session = Depends(get_db)):
    from app.storage.models import RiskEvent
    db.query(RiskEvent).delete()
    db.commit()
    return {"message": "All risk events cleared"}
