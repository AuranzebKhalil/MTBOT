from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple

from app.storage.db import get_db
from app.storage.models import Trade

router = APIRouter()


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _planned_rr(entry: float, sl: Optional[float], tp: Optional[float]) -> float:
    if sl is None or tp is None:
        return 0.0
    risk = abs(entry - sl)
    if risk <= 0:
        return 0.0
    reward = abs(tp - entry)
    return reward / risk


def _max_drawdown_from_pnls(pnls: List[float]) -> float:
    peak = 0.0
    eq = 0.0
    max_dd = 0.0
    for p in pnls:
        eq += float(p)
        peak = max(peak, eq)
        dd = peak - eq
        max_dd = max(max_dd, dd)
    return float(max_dd)


def _suggested_status(win_rate: float, avg_rr: float) -> str:
    # Phase 6 rules
    if win_rate >= 55.0 and avg_rr >= 1.5:
        return "active"
    # pause dominates if either metric is below minimum
    if win_rate < 45.0 or avg_rr < 1.0:
        return "pause"
    return "reduce"


def _compute_group_stats(trades: List[Trade]) -> Dict[str, Any]:
    total = len(trades)
    wins = len([t for t in trades if _safe_float(t.profit, 0.0) > 0])
    losses = total - wins
    win_rate = (wins / total * 100.0) if total > 0 else 0.0

    rr_vals: List[float] = []
    pnl_vals: List[float] = []
    for t in trades:
        entry = _safe_float(t.entry_price, 0.0)
        sl = t.sl if t.sl not in (None, 0) else None
        tp = t.tp if t.tp not in (None, 0) else (t.tp1 if t.tp1 not in (None, 0) else (t.tp2 if t.tp2 not in (None, 0) else None))
        rr_vals.append(_planned_rr(entry, sl, tp))
        pnl_vals.append(_safe_float(t.profit, 0.0))

    avg_rr = (sum(rr_vals) / len(rr_vals)) if rr_vals else 0.0
    avg_profit = (sum(pnl_vals) / len(pnl_vals)) if pnl_vals else 0.0

    # drawdown from cumulative pnl sequence
    ordered = sorted(trades, key=lambda x: (x.exit_time or x.time))
    ordered_pnls = [_safe_float(t.profit, 0.0) for t in ordered]
    max_dd = _max_drawdown_from_pnls(ordered_pnls)

    last10 = ordered[-10:]
    last10_perf = [
        {
            "ticket_id": t.ticket_id,
            "time": (t.exit_time or t.time).isoformat() if (t.exit_time or t.time) else None,
            "pnl": _safe_float(t.profit, 0.0),
            "win": _safe_float(t.profit, 0.0) > 0,
            "rr": _planned_rr(_safe_float(t.entry_price, 0.0), t.sl, t.tp or t.tp1 or t.tp2),
        }
        for t in last10
    ]

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "average_rr": round(avg_rr, 3),
        "average_profit": round(avg_profit, 4),
        "max_drawdown": round(max_dd, 4),
        "last_10": last10_perf,
        "suggested_status": _suggested_status(win_rate, avg_rr),
    }


@router.get("/strategy-performance")
def strategy_performance(db: Session = Depends(get_db)):
    closed = db.query(Trade).filter(Trade.status == "CLOSED").all()

    # group by setup_type (= strategy_name)
    by_setup: Dict[str, List[Trade]] = {}
    by_session: Dict[str, List[Trade]] = {}
    by_symbol: Dict[str, List[Trade]] = {}

    for t in closed:
        setup = t.strategy_name or "Unknown"
        sess = t.session or "UNKNOWN"
        sym = t.symbol or "UNKNOWN"
        by_setup.setdefault(setup, []).append(t)
        by_session.setdefault(sess, []).append(t)
        by_symbol.setdefault(sym, []).append(t)

    setup_stats = {k: _compute_group_stats(v) for k, v in by_setup.items()}
    session_stats = {k: _compute_group_stats(v) for k, v in by_session.items()}
    symbol_stats = {k: _compute_group_stats(v) for k, v in by_symbol.items()}

    # best/worst sessions overall
    session_pnl = {k: sum(_safe_float(t.profit, 0.0) for t in v) for k, v in by_session.items()}
    best_session = max(session_pnl, key=session_pnl.get) if session_pnl else None
    worst_session = min(session_pnl, key=session_pnl.get) if session_pnl else None

    return {
        "totals": _compute_group_stats(closed),
        "by_setup_type": setup_stats,
        "by_session": session_stats,
        "by_symbol": symbol_stats,
        "best_session": best_session,
        "worst_session": worst_session,
        # Placeholder for future: strategy_id mapping if you persist it later
        "by_strategy_id": {},
    }

