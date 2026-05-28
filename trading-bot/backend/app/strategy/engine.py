import hashlib
import logging
import pandas as pd
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
import math
from app.core.datatypes import (
    TradeSignal, SignalStatus, RawSetup, SetupScore, 
    StrategyDecision, OrderSide, EntryMode, StrategyContext
)
from app.strategy.context import ContextEvaluator
from app.strategy.scorer import ConfluenceScorer
from app.strategy.selector import CandidateSelector
from app.strategy.annotations import AnnotationBuilder
from app.core.config import settings

logger = logging.getLogger("StrategyEngine")

class StrategyEngine:
    """
    Central Orchestrator of the Strategy Pipeline. 
    Handles Context -> Detection -> Scoring -> Selection -> Signal.
    """
    
    def __init__(self, ai_predictor, strategies: List[Any]):
        self.ai = ai_predictor
        self.strategies = strategies
        self.context_eval = ContextEvaluator()
        self.scorer = ConfluenceScorer()
        self.selector = CandidateSelector()
        self.anno_builder = AnnotationBuilder()
        self.ai_threshold: float = 0.48
        # Structure gate is intentionally conservative: it filters low-context setups
        # without replacing existing strategy or risk logic.
        self.structure_gate_min_score: float = 0.45
        self.diagnose_gates: bool = False
        self.gate_profile: str = "strict" # strict, balanced, research
        self.ai_mode: str = "live_model" # disabled, fallback, live_model
        self._gate_diagnostics = {
            "structure_scores": [],
            "ai_confidences": [],
            "traced_signals": [],
            "funnel": {
                "raw_signals": 0,
                "after_strategy_filter": 0,
                "after_structure_gate": 0,
                "after_ai_gate": 0,
                "after_trade_grading": 0,
                "after_risk_manager": 0,
                "executed": 0
            },
            "strategy_funnels": {} # strategy_id -> funnel dict
        }

    def evaluate(self, symbol: str, dataframes: Dict[str, Any], strategy_settings: Optional[Dict[str, Any]] = None) -> Tuple[List[TradeSignal], List[TradeSignal], Dict[str, Any]]:
        """
        Refactored Analyze Flow with Stats Tracking:
        1. Contextualize Market (M1/M5/M15).
        2. Filter strategies based on user settings.
        3. Detect valid setups across enabled families.
        4. Appraise setups via weighted confluence scoring.
        5. Select the 'Best-of-Breed' candidate.
        6. Build a structured TradeSignal.
        """
        stats = {
            "evaluations": 0,
            "is_tradable": True,
            "rejections": {},
            "strategy_stats": {},
            "silent_skips": {
                "no_raw_setup": 0,
                "neutral_m15_bias": 0,
                "failed_mtf_alignment": 0,
                "missing_structure_context": 0,
                "missing_indicator_data": 0,
                "strategy_condition_not_met": 0
            },
            "gate_diagnostics": self._gate_diagnostics if self.diagnose_gates else None
        }
        
        # 1. Build Multi-Timeframe Context
        _rejected = []
        context = self.context_eval.evaluate(
            dataframes['M1'], dataframes['M5'], dataframes['M15'], symbol
        )
        
        logger.debug(f"[{symbol}] Context: Session={context.session}, Regime={context.regime}, Tradable={context.is_tradable}")
        
        if not context.is_tradable:
            logger.debug(f"[{symbol}] Market not tradable. Skipping.")
            stats["is_tradable"] = False
            return [], [], stats

        # 2. Gather Candidates from all Enabled Strategy Families
        candidates = []
        strategy_settings = strategy_settings or {}
        
        for strategy in self.strategies:
            sid = getattr(strategy, "strategy_id", "UNKNOWN")
            stats["strategy_stats"][sid] = stats["strategy_stats"].get(sid, {
                "evaluations": 0,
                "raw_setups_found": 0,
                "skipped_no_setup": 0,
                "skipped_neutral_bias": 0,
                "sent_to_risk_manager": 0,
                "rejected_by_risk_manager": 0,
                "approved": 0
            })
            stats["strategy_stats"][sid]["evaluations"] += 1
            stats["evaluations"] += 1

            # Fallback to current engine-wide threshold if not specified in strategy settings
            base_thr = float(getattr(self, "ai_threshold", 0.48))
            s_set = strategy_settings.get(sid, {"enabled": True, "ai_threshold": base_thr})
            
            if not s_set.get("enabled", True):
                continue

            # Neutral Bias Skip Check
            if context.m15_bias == 0:
                stats["silent_skips"]["neutral_m15_bias"] += 1
                stats["strategy_stats"][sid]["skipped_neutral_bias"] += 1

            setup = strategy.detect_setup(dataframes, context)
            if not setup:
                skip_reason = getattr(strategy, "last_skip_reason", None)
                if skip_reason:
                    stats["silent_skips"][skip_reason] = stats["silent_skips"].get(skip_reason, 0) + 1
                else:
                    stats["silent_skips"]["no_raw_setup"] += 1
                stats["strategy_stats"][sid]["skipped_no_setup"] += 1
                continue
            # Track raw signals in funnel
            self._update_strategy_funnel(sid, "raw_signals")
            
            # PHASE 0.5: Strategy Filter Gate (Senior context validation)
            is_valid, reject_rule = strategy.validate_setup(setup, dataframes, context)
            if not is_valid:
                rej_sig = self._setup_to_signal(setup, context, sid)
                rej_sig.metadata["rejection_stage"] = "strategy_filter"
                rej_sig.metadata["rejection_rule"] = reject_rule or "CONTEXT_REJECT"
                rej_sig.metadata["rejection_reason"] = f"Strategy-specific context filter: {reject_rule}"
                _rejected.append(rej_sig)
                stats["rejections"]["strategy_filter"] = stats["rejections"].get("strategy_filter", 0) + 1
                continue

            self._update_strategy_funnel(sid, "after_strategy_filter")
            stats["strategy_stats"][sid]["raw_setups_found"] += 1
            # 3. Apply Scoring Logic
            score = strategy.score_setup(setup, context)
            logger.info(f"[{symbol}] Candidate Detected: {sid} | Direction={setup.direction.name} | BaseScore={score.total_score}")
            candidates.append((setup, score, s_set, sid))

        # 4. Selection (Ranking & Tie-breaking)
        # Decision logic remains same but passes settings along if needed
        decision = self.selector.select([(r, s) for r, s, _set, _sid in candidates])
        
        if not decision.is_triggered or not decision.best_setup:
            return [], _rejected, stats

        # 5. Signal Construction for the Winner
        best = decision.best_setup
        best_candidate = next(c for c in candidates if c[0] == best)
        best_score = best_candidate[1]
        best_settings = best_candidate[2]
        best_strategy_id = best_candidate[3]
        
        if self.diagnose_gates:
            self._gate_diagnostics["funnel"]["after_strategy_filter"] += 1
            self._update_strategy_funnel(best_strategy_id, "after_strategy_filter") # Redundant but ensures winner tracking
        
        # Build Metadata for Execution & Charting
        best.chart_annotations = self.anno_builder.build(best)
        
        # PHASE 1: Unified market-structure analysis (read-only)
        # This does NOT execute orders. It enriches signal context and can reject weak
        # setups before they are sent to the risk layer.
        structure_ctx = self._build_market_structure_context(
            symbol=symbol,
            dataframes=dataframes,
            context=context,
            setup=best,
            strategy_id=best_strategy_id,
            strategy_settings=best_settings,
        )
        best.metadata = {**(best.metadata or {}), "market_structure": structure_ctx}
        
        # Use resolved thresholds based on profile
        req_struct_score, req_ai_conf = self._resolve_gate_thresholds(best_strategy_id)
        strategy_ai_thr = req_ai_conf # Use the resolved value
        
        ai_context = self._build_ai_context(
            symbol=symbol,
            setup=best,
            context=context,
            dataframes=dataframes,
            structure_ctx=structure_ctx
        )
        ai_raw = self.ai.predict(
            dataframes["M1"],
            confidence_threshold=strategy_ai_thr,
            context=ai_context
        )
        if self.diagnose_gates:
            conf = ai_raw.get("confidence", 0.0)
            self._gate_diagnostics["ai_confidences"].append({
                "value": conf,
                "strategy": best_strategy_id,
                "required": strategy_ai_thr,
                "is_fallback": ai_raw.get("decision") == "FALLBACK_APPROVE"
            })
        ai_pass, ai_conf, ai_reason, ai_decision, ai_strong, ai_weak = self._parse_ai_result(ai_raw)
        
        # Handle AI Gate Override Modes
        if self.ai_mode == "disabled":
            ai_pass = True
            ai_reason = "AI Gate Disabled (Backtest Mode)"
            ai_decision = "DISABLED_PASS"
        elif self.ai_mode == "fallback":
            # In fallback mode, we use a very permissive threshold
            if ai_conf < 0.45:
                ai_pass = False
                ai_reason = f"Fallback AI Reject (conf={ai_conf:.2f} < 0.45)"
            else:
                ai_pass = True
                ai_reason = f"Fallback AI Pass (conf={ai_conf:.2f} >= 0.45)"
        
        logger.info(f"[{symbol}] AI Prediction: Confidence={ai_conf:.2f} (Threshold={strategy_ai_thr}) | Mode={self.ai_mode} | Pass={ai_pass} | Reason={ai_reason}")
        
        # 0. Candle Quality Filter (Trigger Candle Range vs ATR)
        trigger_candle = dataframes["M1"].iloc[-1]
        candle_range = abs(trigger_candle['high'] - trigger_candle['low'])
        atr = ai_context.get("atr", 0.0)
        if candle_range > (atr * settings.MAX_CANDLE_ATR_RATIO) and atr > 0:
            ai_pass = False
            ai_reason = f"Trigger candle too large ({candle_range:.5f} > {atr*settings.MAX_CANDLE_ATR_RATIO:.5f})"
            ai_decision = "CANDLE_QUALITY_REJECT"
            ai_weak.append("oversized_trigger_candle")

        # Fingerprint generation
        fingerprint = self._generate_fingerprint(symbol, best)
        
        signal = TradeSignal(
            idempotency_key=f"{fingerprint}_{int(pd.to_datetime(best.setup_candle_timestamp).timestamp())}",
            signal_fingerprint=fingerprint,
            strategy_name=best.family.name if hasattr(best.family, "name") else str(best.family),
            symbol=symbol,
            timeframe="M1",
            side=best.direction,
            regime=context.regime,
            session=context.session,
            setup_score=best_score,
            ai_confidence=ai_conf,
            ai_threshold_used=strategy_ai_thr,
            entry_mode=EntryMode.MARKET_IMMEDIATE,
            entry_price=best.entry_price,
            structural_sl=best.stop_loss,
            volatility_buffer=0.0005,
            targets=best.targets,
            estimated_rr=2.0,
            setup_candle_timestamp=best.setup_candle_timestamp,
            chart_annotations=best.chart_annotations,
            metadata={
                **best.metadata,
                "strategy_id": best_strategy_id,
                "selector_reason": decision.selection_reason,
                "ai_confidence": ai_conf,
                "ai_decision": ai_decision,
                "ai_reason": ai_reason,
                "ai_strong_factors": ai_strong,
                "ai_weak_factors": ai_weak,
                # Phase 3 defaults: always present for backward-compatible consumers.
                "trade_grade": "UNGRADED",
                "trade_grade_score": 0.0,
                "trade_grade_reason": "Not graded yet",
                "trade_grade_breakdown": {},
                "grading_reason": "",
                # Phase 4 defaults: structured rejection payload (safe for JSON storage)
                "rejection_stage": None,
                "rejection_rule": None,
                "rejection_reason": None,
                "rejection_details": {},
                "current_value": None,
                "required_value": None,
                "current_ai_confidence": ai_conf,
                "required_ai_confidence": strategy_ai_thr,
                "current_structure_score": structure_ctx.get("score", 0.0),
                "required_structure_score": req_struct_score,
            }
        )

        # Structural gate before risk management hand-off.
        struct_current = float(structure_ctx.get("score", 0.0) or 0.0)
        if self.diagnose_gates:
            self._gate_diagnostics["structure_scores"].append({
                "value": struct_current,
                "strategy": best_strategy_id,
                "required": req_struct_score,
                "breakdown": structure_ctx.get("score_breakdown", {})
            })

        if struct_current < req_struct_score:
            signal.status = SignalStatus.AI_REJECTED
            failing_factors = structure_ctx.get("failing_factors", [])
            fail_txt = ", ".join(failing_factors) if failing_factors else "insufficient confluence"
            reason = (
                f"Rejected at structure gate. Score {struct_current:.2f} is below required {req_struct_score:.2f} for {best_strategy_id}. "
                f"Weak factors: {fail_txt}."
            )
            self._set_rejection_metadata(
                signal,
                stage="structure_gate",
                rule="STRUCTURE_SCORE_MIN",
                reason=reason,
                details={"weak_factors": failing_factors, "strategy_id": best_strategy_id},
                current_value=struct_current,
                required_value=req_struct_score,
            )
            # Update stats
            stats["strategy_stats"][best_strategy_id]["rejected_by_risk_manager"] += 1
            stats["rejections"]["structure_gate"] = stats["rejections"].get("structure_gate", 0) + 1
            
            # Tracing for diagnosis
            if self.diagnose_gates and len(self._gate_diagnostics["traced_signals"]) < 5:
                self._gate_diagnostics["traced_signals"].append({
                    "type": "STRUCTURE_REJECT",
                    "timestamp": best.setup_candle_timestamp,
                    "strategy": best_strategy_id,
                    "score": struct_current,
                    "required": req_struct_score,
                    "breakdown": structure_ctx.get("score_breakdown", {}),
                    "failing": failing_factors
                })

            # Backward compatible: keep a simple ai_reason too (many callers still read it)
            signal.metadata["ai_reason"] = signal.metadata.get("ai_reason") or reason
            logger.info(f"[{symbol}] {reason}")
            return [], _rejected + [signal], stats

        if self.diagnose_gates:
            self._gate_diagnostics["funnel"]["after_structure_gate"] += 1
            self._update_strategy_funnel(best_strategy_id, "after_structure_gate")

        if not ai_pass:
             signal.status = SignalStatus.AI_REJECTED
             current = float(ai_conf or 0.0)
             required = float(strategy_ai_thr)
             weak_txt = ", ".join(ai_weak or []) if ai_weak else "insufficient evidence"
             
             stage = "ai_gate"
             rule = "AI_CONFIDENCE_MIN"
             if ai_decision == "CANDLE_QUALITY_REJECT":
                 stage = "candle_quality"
                 rule = "MAX_ATR_RATIO"
                 
             reason = (
                 f"Rejected at {stage}. {ai_reason if ai_decision == 'CANDLE_QUALITY_REJECT' else f'Confidence {current:.2f} is below required {required:.2f}'}. "
                 f"Weak factors: {weak_txt}."
             )
             self._set_rejection_metadata(
                 signal,
                 stage=stage,
                 rule=rule,
                 reason=reason,
                 details={"ai_decision": ai_decision, "ai_weak_factors": ai_weak, "ai_strong_factors": ai_strong},
                 current_value=current,
                 required_value=required,
             )
             # Update stats
             stats["strategy_stats"][best_strategy_id]["rejected_by_risk_manager"] += 1
             stats["rejections"][stage] = stats["rejections"].get(stage, 0) + 1
             
             if self.diagnose_gates and len(self._gate_diagnostics["traced_signals"]) < 10:
                self._gate_diagnostics["traced_signals"].append({
                    "type": "AI_REJECT",
                    "timestamp": best.setup_candle_timestamp,
                    "strategy": best_strategy_id,
                    "confidence": current,
                    "required": required,
                    "reason": ai_reason,
                    "weak": ai_weak
                })
             
             return [], _rejected + [signal], stats

        if self.diagnose_gates:
            self._gate_diagnostics["funnel"]["after_ai_gate"] += 1
            self._update_strategy_funnel(best_strategy_id, "after_ai_gate")

        # PHASE 3: Trade grading gate (after AI, before risk pipeline).
        # Only A+ and A continue. B/C are rejected here.
        grade = self._grade_trade_signal(
            signal=signal,
            context=context,
            structure_ctx=structure_ctx,
            ai_context=ai_context,
        )
        signal.metadata["trade_grade"] = grade["grade"]
        signal.metadata["trade_grade_score"] = grade["score"]
        signal.metadata["trade_grade_reason"] = grade["reason"]
        signal.metadata["trade_grade_breakdown"] = grade["breakdown"]
        signal.metadata["grading_reason"] = grade["reason"]

        if not grade["pass"]:
            signal.status = SignalStatus.AI_REJECTED
            # Structured grading rejection without overwriting ai_reason.
            g = str(grade.get("grade", "C"))
            g_score = float(grade.get("score", 0.0) or 0.0)
            weak = grade.get("weak_factors", []) or []
            weak_txt = ", ".join(weak) if weak else "insufficient confluence"
            reason = (
                f"Rejected by trade grading. Grade {g} with score {g_score:.2f} is below required grade B "
                f"(B>=0.60). Weak factors: {weak_txt}."
            )
            self._set_rejection_metadata(
                signal,
                stage="trade_grading",
                rule="TRADE_GRADE_MIN_B",
                reason=reason,
                details={
                    "trade_grade": g,
                    "trade_grade_score": g_score,
                    "trade_grade_breakdown": grade.get("breakdown", {}),
                    "weak_factors": weak,
                },
                current_value=g_score,
                required_value=0.70 if self.gate_profile == "strict" else 0.60,
            )
            # Update stats
            stats["strategy_stats"][best_strategy_id]["rejected_by_risk_manager"] += 1
            stats["rejections"]["trade_grading"] = stats["rejections"].get("trade_grading", 0) + 1

            logger.info(
                f"[{symbol}] {reason}"
            )
            return [], _rejected + [signal], stats
        
        signal.status = SignalStatus.APPROVED
        stats["strategy_stats"][best_strategy_id]["approved"] += 1
        if self.diagnose_gates:
            self._gate_diagnostics["funnel"]["after_trade_grading"] += 1
            self._update_strategy_funnel(best_strategy_id, "after_trade_grading")
        return [signal], _rejected, stats

    def _generate_fingerprint(self, symbol: str, setup: RawSetup) -> str:
        raw_str = f"{symbol}_{setup.family.name}_{setup.setup_candle_timestamp}_{setup.direction.value}"
        return hashlib.md5(raw_str.encode()).hexdigest()

    def _build_market_structure_context(
        self,
        symbol: str,
        dataframes: Dict[str, Any],
        context: Any,
        setup: RawSetup,
        strategy_id: str,
        strategy_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a normalized, strategy-agnostic structure snapshot used by all signals.
        Keeps output backward-compatible by storing details in metadata only.
        """
        m1 = dataframes.get("M1")
        m5 = dataframes.get("M5")
        m15 = dataframes.get("M15")

        side = setup.direction
        entry = float(setup.entry_price)

        bos_choch = self._analyze_bos_choch(m1, m15, side)
        liquidity = self._analyze_liquidity_sweep(m1, m15, side)
        fvg = self._analyze_fvg(m1, m15, side, entry)
        ob = self._analyze_order_block_validity(m1, m15, side, entry)
        eqh_eql = self._analyze_equal_highs_lows(m15)
        pd_zone = self._analyze_premium_discount_zone(m15, side, entry)
        htf_align = self._analyze_higher_timeframe_alignment(m15, context, side)

        # Strategy-specific weight override:
        # expected shape:
        # strategy_settings = {
        #   "enabled": true,
        #   "params": {
        #       "structure_weights": {"bos": 0.2, "choch": 0.1, ...}
        #   }
        # }
        # Falls back to conservative defaults when missing/invalid.
        raw_weights = ((strategy_settings or {}).get("params") or {}).get("structure_weights", {})
        weights = self._resolve_structure_weights(raw_weights, strategy_id=strategy_id)

        # Extract strategy-specific confluence factors from metadata (if present)
        vol_ratio = setup.metadata.get("volume_ratio", 0.0)
        vol_strength = 1.0 if vol_ratio >= 1.2 else (vol_ratio / 1.2 if vol_ratio > 0 else 0.0)
        
        poc_dist = setup.metadata.get("distance_to_poc_percent", 1.0)
        # Proximity score: 1.0 at 0 dist, 0.0 at 0.05% dist
        poc_proximity = max(0.0, 1.0 - (poc_dist / 0.05)) if poc_dist <= 0.05 else 0.0

        score, score_breakdown = self._compute_structure_score(
            bos_choch=bos_choch,
            liquidity=liquidity,
            fvg=fvg,
            ob=ob,
            eqh_eql=eqh_eql,
            pd_zone=pd_zone,
            htf_align=htf_align,
            volume_strength=vol_strength,
            poc_proximity=poc_proximity,
            weights=weights,
        )
        failing_factors = [k for k, v in score_breakdown.items() if k != "final" and v <= 0.0]

        structure = {
            "symbol": symbol,
            "strategy_id": strategy_id,
            "score": round(score, 4),
            "gate_pass": score >= self.structure_gate_min_score,
            "weights_used": weights,
            "score_breakdown": score_breakdown,
            "failing_factors": failing_factors,
            "break_of_structure": bos_choch.get("bos", {}),
            "change_of_character": bos_choch.get("choch", {}),
            "liquidity_sweep": liquidity,
            "fair_value_gap": fvg,
            "order_block_validity": ob,
            "equal_highs_lows": eqh_eql,
            "premium_discount_zone": pd_zone,
            "higher_timeframe_alignment": htf_align,
        }
        # Explicit factor-level debug logs for calibration and audits.
        logger.info(
            f"[{symbol}] [STRUCTURE] strategy={strategy_id} "
            f"BOS={score_breakdown['bos']:.2f} CHOCH={score_breakdown['choch']:.2f} "
            f"LIQ_SWEEP={score_breakdown['liquidity_sweep']:.2f} FVG={score_breakdown['fvg']:.2f} "
            f"ORDER_BLOCK={score_breakdown['order_block']:.2f} EQH_EQL={score_breakdown['equal_highs_lows']:.2f} "
            f"PREM_DISC={score_breakdown['premium_discount']:.2f} HTF_ALIGN={score_breakdown['htf_alignment']:.2f} "
            f"FINAL={score_breakdown['final']:.2f} gate={structure['gate_pass']}"
        )
        return structure

    def _analyze_bos_choch(self, m1: Any, m15: Any, side: OrderSide) -> Dict[str, Any]:
        bos_m1 = self._recent_directional_count(m1, "bos", bars=20)
        bos_m15 = self._recent_directional_count(m15, "bos", bars=20)
        choch_m1 = self._recent_directional_count(m1, "choch", bars=20)
        choch_m15 = self._recent_directional_count(m15, "choch", bars=20)

        target_sign = 1 if side == OrderSide.BUY else -1
        bos_aligned = (bos_m1["last"] == target_sign) or (bos_m15["last"] == target_sign)
        choch_aligned = (choch_m1["last"] == target_sign) or (choch_m15["last"] == target_sign)

        return {
            "bos": {
                "m1_last": bos_m1["last"],
                "m15_last": bos_m15["last"],
                "m1_counts": bos_m1["counts"],
                "m15_counts": bos_m15["counts"],
                "aligned_with_side": bos_aligned,
            },
            "choch": {
                "m1_last": choch_m1["last"],
                "m15_last": choch_m15["last"],
                "m1_counts": choch_m1["counts"],
                "m15_counts": choch_m15["counts"],
                "aligned_with_side": choch_aligned,
            }
        }

    def _analyze_liquidity_sweep(self, m1: Any, m15: Any, side: OrderSide) -> Dict[str, Any]:
        sweep_m1 = self._recent_directional_count(m1, "sweep", bars=30)
        sweep_m15 = self._recent_directional_count(m15, "sweep", bars=30)
        target_sign = 1 if side == OrderSide.BUY else -1
        aligned = (sweep_m1["last"] == target_sign) or (sweep_m15["last"] == target_sign)
        return {
            "m1_last": sweep_m1["last"],
            "m15_last": sweep_m15["last"],
            "m1_counts": sweep_m1["counts"],
            "m15_counts": sweep_m15["counts"],
            "aligned_with_side": aligned,
        }

    def _analyze_fvg(self, m1: Any, m15: Any, side: OrderSide, entry: float) -> Dict[str, Any]:
        target_bull = side == OrderSide.BUY
        source = m1 if m1 is not None else m15
        if source is None:
            return {"exists": False, "aligned_with_side": False}

        bull_col = "fvg_bullish"
        bear_col = "fvg_bearish"
        mitigated_col = "fvg_mitigated"
        top_col = "fvg_top"
        bottom_col = "fvg_bottom"

        required = {bull_col, bear_col, mitigated_col, top_col, bottom_col}
        if not required.issubset(set(source.columns)):
            return {"exists": False, "aligned_with_side": False}

        recent = source.tail(80)
        if target_bull:
            cands = recent[(recent[bull_col] == True) & (recent[mitigated_col] == False)]  # noqa: E712
        else:
            cands = recent[(recent[bear_col] == True) & (recent[mitigated_col] == False)]  # noqa: E712

        if cands.empty:
            return {"exists": False, "aligned_with_side": False}

        last = cands.iloc[-1]
        top = self._safe_float(last.get(top_col))
        bottom = self._safe_float(last.get(bottom_col))
        zone_mid = (top + bottom) / 2.0 if top is not None and bottom is not None else None
        distance_to_zone = abs(entry - zone_mid) if zone_mid is not None else None
        return {
            "exists": True,
            "aligned_with_side": True,
            "top": top,
            "bottom": bottom,
            "zone_mid": zone_mid,
            "distance_to_entry": distance_to_zone,
            "unmitigated_recent_count": int(len(cands)),
        }

    def _analyze_order_block_validity(self, m1: Any, m15: Any, side: OrderSide, entry: float) -> Dict[str, Any]:
        source = m1 if m1 is not None else m15
        if source is None or "order_block" not in source.columns:
            return {"valid": False, "aligned_with_side": False}

        target_sign = 1 if side == OrderSide.BUY else -1
        recent = source.tail(100)
        cands = recent[recent["order_block"] == target_sign]
        if cands.empty:
            return {"valid": False, "aligned_with_side": False}

        last = cands.iloc[-1]
        ob_low = self._safe_float(last.get("low"))
        ob_high = self._safe_float(last.get("high"))
        in_zone = False
        if ob_low is not None and ob_high is not None:
            lo = min(ob_low, ob_high)
            hi = max(ob_low, ob_high)
            in_zone = lo <= entry <= hi
        return {
            "valid": True,
            "aligned_with_side": True,
            "zone_low": ob_low,
            "zone_high": ob_high,
            "entry_inside_zone": in_zone,
            "recent_same_side_count": int(len(cands)),
        }

    def _analyze_equal_highs_lows(self, m15: Any) -> Dict[str, Any]:
        if m15 is None or len(m15) < 30:
            return {"equal_highs": False, "equal_lows": False, "tolerance": None}

        recent = m15.tail(30)
        highs = recent["high"].tail(10).astype(float)
        lows = recent["low"].tail(10).astype(float)
        full_range = float(recent["high"].max() - recent["low"].min()) if len(recent) else 0.0
        tol = max(full_range * 0.0025, 1e-6)

        equal_highs = self._has_close_cluster(highs.tolist(), tol)
        equal_lows = self._has_close_cluster(lows.tolist(), tol)
        return {
            "equal_highs": equal_highs,
            "equal_lows": equal_lows,
            "tolerance": tol,
        }

    def _analyze_premium_discount_zone(self, m15: Any, side: OrderSide, entry: float) -> Dict[str, Any]:
        if m15 is None or len(m15) < 20:
            return {"zone": "UNKNOWN", "aligned_with_side": False}

        recent = m15.tail(50)
        swing_high = float(recent["high"].max())
        swing_low = float(recent["low"].min())
        eq = (swing_high + swing_low) / 2.0

        if entry < eq:
            zone = "DISCOUNT"
        elif entry > eq:
            zone = "PREMIUM"
        else:
            zone = "EQUILIBRIUM"

        aligned = (side == OrderSide.BUY and zone in {"DISCOUNT", "EQUILIBRIUM"}) or (
            side == OrderSide.SELL and zone in {"PREMIUM", "EQUILIBRIUM"}
        )
        return {
            "zone": zone,
            "equilibrium": eq,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "aligned_with_side": aligned,
        }

    def _analyze_higher_timeframe_alignment(self, m15: Any, context: Any, side: OrderSide) -> Dict[str, Any]:
        trend = "NEUTRAL"
        ema_fast = None
        ema_slow = None
        slope = None

        if m15 is not None and len(m15) >= 55:
            closes = m15["close"].astype(float)
            ema_fast_series = closes.ewm(span=20, adjust=False).mean()
            ema_slow_series = closes.ewm(span=50, adjust=False).mean()
            ema_fast = float(ema_fast_series.iloc[-1])
            ema_slow = float(ema_slow_series.iloc[-1])
            slope = float(ema_fast_series.iloc[-1] - ema_fast_series.iloc[-5])

            if ema_fast > ema_slow and slope > 0:
                trend = "BULLISH"
            elif ema_fast < ema_slow and slope < 0:
                trend = "BEARISH"

        # Context fallback for compatibility with existing context evaluator.
        if trend == "NEUTRAL":
            bias = getattr(context, "m15_bias", 0)
            if bias == 1:
                trend = "BULLISH"
            elif bias == -1:
                trend = "BEARISH"

        aligned = trend == "NEUTRAL" or (
            side == OrderSide.BUY and trend == "BULLISH"
        ) or (
            side == OrderSide.SELL and trend == "BEARISH"
        )
        return {
            "trend": trend,
            "aligned_with_side": aligned,
            "ema20": ema_fast,
            "ema50": ema_slow,
            "ema20_slope_5": slope,
        }

    def _compute_structure_score(self, **sections: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Weighted structure confidence score in [0, 1].
        We keep weights modest so existing strategy selection remains primary.
        """
        weights = sections.get("weights") or self._resolve_structure_weights({})

        bos_choch = sections.get("bos_choch", {})
        bos_score = 1.0 if bos_choch.get("bos", {}).get("aligned_with_side") else 0.0
        choch_score = 1.0 if bos_choch.get("choch", {}).get("aligned_with_side") else 0.0

        liq_score = 1.0 if sections.get("liquidity", {}).get("aligned_with_side") else 0.0
        fvg_score = 1.0 if sections.get("fvg", {}).get("aligned_with_side") else 0.0
        ob_score = 1.0 if sections.get("ob", {}).get("aligned_with_side") else 0.0
        pd_score = 1.0 if sections.get("pd_zone", {}).get("aligned_with_side") else 0.0
        htf_score = 1.0 if sections.get("htf_align", {}).get("aligned_with_side") else 0.0
        vol_score = float(sections.get("volume_strength", 0.0))
        poc_score = float(sections.get("poc_proximity", 0.0))

        eq_section = sections.get("eqh_eql", {})
        eq_score = 1.0 if (eq_section.get("equal_highs") or eq_section.get("equal_lows")) else 0.0

        raw_score = (
            (bos_score * weights.get("bos", 0)) +
            (choch_score * weights.get("choch", 0)) +
            (liq_score * weights.get("liquidity_sweep", 0)) +
            (fvg_score * weights.get("fvg", 0)) +
            (ob_score * weights.get("order_block", 0)) +
            (eq_score * weights.get("equal_highs_lows", 0)) +
            (pd_score * weights.get("premium_discount", 0)) +
            (htf_score * weights.get("htf_alignment", 0)) +
            (vol_score * weights.get("volume_strength", 0)) +
            (poc_score * weights.get("poc_proximity", 0))
        )
        final_score = max(0.0, min(1.0, float(raw_score)))
        breakdown = {
            "bos": round(bos_score, 4),
            "choch": round(choch_score, 4),
            "liquidity_sweep": round(liq_score, 4),
            "fvg": round(fvg_score, 4),
            "order_block": round(ob_score, 4),
            "equal_highs_lows": round(eq_score, 4),
            "premium_discount": round(pd_score, 4),
            "htf_alignment": round(htf_score, 4),
            "volume_strength": round(vol_score, 4),
            "poc_proximity": round(poc_score, 4),
            "final": round(final_score, 4),
        }
        return final_score, breakdown

    def _resolve_structure_weights(self, candidate: Any, strategy_id: str = "DEFAULT") -> Dict[str, float]:
        """
        Resolve and sanitize structure weights.
        Supports per-strategy overrides while preserving safe defaults.
        """
        defaults = {
            "bos": 0.14,
            "choch": 0.08,
            "liquidity_sweep": 0.14,
            "fvg": 0.14,
            "order_block": 0.16,
            "equal_highs_lows": 0.10,
            "premium_discount": 0.10,
            "htf_alignment": 0.14,
            "volume_strength": 0.0,  # Only used by specific strategies
            "poc_proximity": 0.0,     # Only used by specific strategies
        }
        
        # SMC_VOLUME Specialized Scoring Profile (Reversal/Absorption)
        if strategy_id == "SMC_VOLUME":
            defaults.update({
                "poc_proximity": 0.20,
                "volume_strength": 0.15,
                "liquidity_sweep": 0.15,
                "order_block": 0.10,
                "fvg": 0.10,
                "premium_discount": 0.10,
                "htf_alignment": 0.05,
                "bos": 0.05,
                "choch": 0.05,
                "equal_highs_lows": 0.05
            })

        if not isinstance(candidate, dict):
            return defaults

        merged: Dict[str, float] = {}
        for key, default_val in defaults.items():
            raw_val = candidate.get(key, default_val)
            try:
                value = float(raw_val)
                if not math.isfinite(value) or value < 0:
                    value = default_val
            except Exception:
                value = default_val
            merged[key] = value

        # Normalize sum to 1.0 so users can pass intuitive values safely.
        total = sum(merged.values())
        if total <= 0:
            return defaults
        for key in list(merged.keys()):
            merged[key] = merged[key] / total
        return merged

    def _recent_directional_count(self, df: Any, column: str, bars: int = 20) -> Dict[str, Any]:
        if df is None or column not in df.columns:
            return {"last": 0, "counts": {"bullish": 0, "bearish": 0}}
        recent = df[column].tail(bars).fillna(0)
        try:
            vals = recent.astype(int)
        except Exception:
            vals = recent
        last = int(vals.iloc[-1]) if len(vals) else 0
        bullish = int((vals == 1).sum())
        bearish = int((vals == -1).sum())
        return {"last": last, "counts": {"bullish": bullish, "bearish": bearish}}

    def _has_close_cluster(self, values: List[float], tolerance: float) -> bool:
        if len(values) < 3:
            return False
        sorted_vals = sorted(v for v in values if self._is_finite(v))
        for i in range(len(sorted_vals) - 1):
            if abs(sorted_vals[i + 1] - sorted_vals[i]) <= tolerance:
                return True
        return False

    def _safe_float(self, value: Any) -> Optional[float]:
        try:
            v = float(value)
            if not math.isfinite(v):
                return None
            return v
        except Exception:
            return None

    def _is_finite(self, value: Any) -> bool:
        try:
            return math.isfinite(float(value))
        except Exception:
            return False

    def _build_ai_context(
        self,
        symbol: str,
        setup: RawSetup,
        context: Any,
        dataframes: Dict[str, Any],
        structure_ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build rich context payload for AI filtering.
        Missing values are tolerated and filled with safe defaults.
        """
        side = setup.direction.name if hasattr(setup.direction, "name") else str(setup.direction)
        entry = self._safe_float(setup.entry_price) or 0.0
        sl = self._safe_float(setup.stop_loss) or 0.0
        target = self._safe_float((setup.targets or [0.0])[0]) or 0.0
        risk = abs(entry - sl)
        reward = abs(target - entry)
        rr_quality = (reward / risk) if risk > 0 else 0.0

        m1 = dataframes.get("M1")
        m15 = dataframes.get("M15")
        spread_ratio = self._safe_float(getattr(context, "spread_v_atr", None))
        spread_condition = "UNKNOWN"
        if spread_ratio is not None:
            if spread_ratio <= 0.25:
                spread_condition = "GOOD"
            elif spread_ratio <= 0.60:
                spread_condition = "ELEVATED"
            else:
                spread_condition = "HIGH"

        candle_momentum = self._estimate_candle_momentum(m1)
        htf = (structure_ctx.get("higher_timeframe_alignment") or {}).get("trend", "NEUTRAL")

        nearest_liq_dist = self._distance_to_nearest_liquidity(m15, entry, side)
        nearby_sr = self._nearest_support_resistance(m15, entry)
        prev_failed_zones = list((setup.metadata or {}).get("failed_setup_zones", []))

        return {
            "symbol": symbol,
            "setup_type": setup.family.name if hasattr(setup.family, "name") else str(setup.family),
            "setup_side": side,
            "setup_score": self._safe_float((setup.metadata or {}).get("score")) or 0.0,
            "session_name": getattr(context, "session", ""),
            "spread_condition": spread_condition,
            "spread_ratio": spread_ratio,
            "candle_momentum": candle_momentum,
            "htf_trend": htf,
            "distance_from_liquidity": nearest_liq_dist,
            "nearby_support_resistance": nearby_sr,
            "rr_quality": rr_quality,
            "previous_failed_setup_zones": prev_failed_zones,
            "market_structure": {
                "final_score": structure_ctx.get("score", 0.0),
                "score_breakdown": structure_ctx.get("score_breakdown", {}),
                "failing_factors": structure_ctx.get("failing_factors", []),
            }
        }

    def _parse_ai_result(self, ai_raw: Any) -> Tuple[bool, float, str, str, List[str], List[str]]:
        """
        Backward-compatible AI result parsing.
        Supports:
          - dict (new)
          - tuple(bool, conf, reason) (legacy)
          - tuple(bool, conf) (very old)
        Fail-closed on malformed output.
        """
        try:
            if isinstance(ai_raw, dict):
                passed = bool(ai_raw.get("pass", ai_raw.get("ai_pass", False)))
                conf = float(ai_raw.get("confidence", ai_raw.get("ai_confidence", 0.0)))
                reason = str(ai_raw.get("reason", ai_raw.get("ai_reason", "AI response missing reason")))
                decision = str(ai_raw.get("decision", "APPROVE" if passed else "REJECT"))
                strong = list(ai_raw.get("strong_factors", []))
                weak = list(ai_raw.get("weak_factors", []))
                return passed, conf, reason, decision, strong, weak

            if isinstance(ai_raw, tuple):
                if len(ai_raw) >= 3:
                    passed = bool(ai_raw[0])
                    conf = float(ai_raw[1])
                    reason = str(ai_raw[2])
                    decision = "APPROVE" if passed else "REJECT"
                    return passed, conf, reason, decision, [], []
                if len(ai_raw) == 2:
                    passed = bool(ai_raw[0])
                    conf = float(ai_raw[1])
                    reason = "Legacy AI output without reason"
                    decision = "APPROVE" if passed else "REJECT"
                    return passed, conf, reason, decision, [], []

            # Unknown AI format -> fail closed
            return False, 0.0, "Malformed AI response (rejected safely)", "REJECT", [], ["malformed_ai_response"]
        except Exception as e:
            return False, 0.0, f"AI parse failure: {e}", "REJECT", [], ["ai_parse_failure"]

    def _estimate_candle_momentum(self, m1: Any) -> Optional[float]:
        if m1 is None or len(m1) < 25:
            return None
        try:
            recent = m1.tail(25).copy()
            body = (recent["close"] - recent["open"]).abs()
            last_body = float(body.iloc[-1])
            avg_body = float(body.iloc[:-1].mean()) if len(body) > 1 else 0.0
            if avg_body <= 0:
                return None
            return last_body / avg_body
        except Exception:
            return None

    def _distance_to_nearest_liquidity(self, m15: Any, entry: float, side: str) -> Optional[float]:
        if m15 is None or len(m15) < 20:
            return None
        try:
            if side == "BUY":
                if "swing_high" in m15.columns:
                    highs = m15[m15["swing_high"] == True]["high"]  # noqa: E712
                else:
                    highs = m15["high"]
                above = highs[highs > entry]
                if above.empty:
                    return None
                return float(abs(float(above.min()) - entry))
            else:
                if "swing_low" in m15.columns:
                    lows = m15[m15["swing_low"] == True]["low"]  # noqa: E712
                else:
                    lows = m15["low"]
                below = lows[lows < entry]
                if below.empty:
                    return None
                return float(abs(entry - float(below.max())))
        except Exception:
            return None

    def _nearest_support_resistance(self, m15: Any, entry: float) -> Dict[str, Optional[float]]:
        if m15 is None or len(m15) < 20:
            return {"support": None, "resistance": None}
        try:
            highs = m15["high"].tail(50).astype(float)
            lows = m15["low"].tail(50).astype(float)
            res_cands = highs[highs > entry]
            sup_cands = lows[lows < entry]
            resistance = float(res_cands.min()) if not res_cands.empty else None
            support = float(sup_cands.max()) if not sup_cands.empty else None
            return {"support": support, "resistance": resistance}
        except Exception:
            return {"support": None, "resistance": None}

    def _grade_trade_signal(
        self,
        signal: TradeSignal,
        context: Any,
        structure_ctx: Dict[str, Any],
        ai_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Grade quality in [0,1] with strict thresholds:
          A+ >= 0.80, A >= 0.70, B >= 0.60, else C
        Gate: only A+ and A pass.
        Missing values are handled safely and noted in reason.
        """
        ms_score = self._safe_float(structure_ctx.get("score")) or 0.0
        sb = structure_ctx.get("score_breakdown", {}) or {}

        setup_total = self._safe_float(getattr(signal.setup_score, "total_score", None))
        setup_norm = min(1.0, max(0.0, (setup_total or 0.0) / 100.0))

        ai_conf = self._safe_float(signal.metadata.get("ai_confidence"))
        ai_norm = min(1.0, max(0.0, ai_conf or 0.0))

        htf = self._safe_float(sb.get("htf_alignment"))
        liq = self._safe_float(sb.get("liquidity_sweep"))
        fvg = self._safe_float(sb.get("fvg"))
        ob = self._safe_float(sb.get("order_block"))

        rr_quality = self._safe_float(ai_context.get("rr_quality"))
        rr_norm = None
        if rr_quality is not None:
            rr_norm = max(0.0, min(1.0, rr_quality / 2.0))  # 2.0R -> 1.0 normalized

        spread_state = str(ai_context.get("spread_condition", "UNKNOWN")).upper()
        spread_norm_map = {"GOOD": 1.0, "ELEVATED": 0.55, "HIGH": 0.20, "UNKNOWN": 0.50}
        spread_norm = spread_norm_map.get(spread_state, 0.50)

        session_quality = self._session_quality_score(str(getattr(context, "session", "")))

        sr_block_norm = self._support_resistance_target_clearance(signal, ai_context)

        # Weighted blend for trade-grade score (base weights).
        # IMPORTANT: Missing factors are NOT penalized:
        # we exclude missing factors from weight normalization.
        base_weights = {
            "setup_score": 0.18,
            "ai_confidence": 0.16,
            "market_structure": 0.20,
            "htf_alignment": 0.10,
            "liquidity_sweep": 0.07,
            "fvg": 0.07,
            "order_block": 0.08,
            "rr_quality": 0.07,
            "spread_condition": 0.04,
            "session_quality": 0.02,
            "sr_clearance": 0.01,
        }

        factor_values: Dict[str, Optional[float]] = {
            "setup_score": setup_norm if setup_total is not None else None,
            "ai_confidence": ai_norm if ai_conf is not None else None,
            "market_structure": ms_score,  # always available (safe default)
            "htf_alignment": htf,
            "liquidity_sweep": liq,
            "fvg": fvg,
            "order_block": ob,
            "rr_quality": rr_norm,
            "spread_condition": spread_norm if spread_state != "" else None,
            "session_quality": session_quality,
            "sr_clearance": sr_block_norm,
        }

        missing_factors = [k for k, v in factor_values.items() if v is None]
        present_factors = {k: v for k, v in factor_values.items() if v is not None}

        total_w = sum(base_weights[k] for k in present_factors.keys()) or 1.0
        normalized_weights = {k: (base_weights[k] / total_w) for k in present_factors.keys()}
        contributions = {k: float(present_factors[k]) * float(normalized_weights[k]) for k in present_factors.keys()}
        final_score = max(0.0, min(1.0, float(sum(contributions.values()))))

        if final_score >= 0.80:
            grade = "A+"
        elif final_score >= 0.70:
            grade = "A"
        elif final_score >= 0.60:
            grade = "B"
        else:
            grade = "C"

        weak_factors = []
        threshold_notes: List[str] = []

        # Threshold expectations (used for clear reasons).
        # These are grading thresholds only (not risk rules).
        REQ_HTF = 0.60
        REQ_RR = 2.0
        REQ_MS = 0.60
        REQ_OB = 0.60  # interpreted as 1.0/0.0 currently; future continuous scoring can refine
        REQ_FVG = 0.60
        REQ_LIQ = 0.60

        # Weak factor tagging with actual values vs expected thresholds
        if htf is not None and htf < REQ_HTF:
            weak_factors.append("weak HTF alignment")
            threshold_notes.append(f"HTF alignment score {htf:.2f} below required {REQ_HTF:.2f}")
        if rr_quality is not None and rr_quality < REQ_RR:
            weak_factors.append("low RR quality")
            threshold_notes.append(f"RR quality {rr_quality:.2f} below required {REQ_RR:.2f}")
        if ms_score < REQ_MS:
            weak_factors.append("weak market structure")
            threshold_notes.append(f"Market structure score {ms_score:.2f} below required {REQ_MS:.2f}")

        if liq is not None and liq < REQ_LIQ:
            weak_factors.append("weak liquidity sweep context")
            threshold_notes.append(f"Liquidity sweep score {liq:.2f} below required {REQ_LIQ:.2f}")
        if fvg is not None and fvg < REQ_FVG:
            weak_factors.append("weak FVG context")
            threshold_notes.append(f"FVG score {fvg:.2f} below required {REQ_FVG:.2f}")
        if ob is not None and ob < REQ_OB:
            weak_factors.append("weak order block context")
            threshold_notes.append(f"Order block score {ob:.2f} below required {REQ_OB:.2f}")

        if spread_state == "HIGH":
            weak_factors.append("high spread condition")
            threshold_notes.append(f"Spread condition {spread_state} is below required GOOD/ELEVATED")
        if sr_block_norm < 0.5:
            weak_factors.append("nearby resistance/support blocks target room")
            threshold_notes.append(f"SR clearance score {sr_block_norm:.2f} below required 0.50")

        reason_parts = [f"grade {grade}, score {final_score:.2f} (A+>=0.80, A>=0.70, B>=0.60)"]
        if threshold_notes:
            reason_parts.append("threshold checks: " + "; ".join(threshold_notes))
        if missing_factors:
            reason_parts.append(f"missing_factors: {', '.join(missing_factors)}")
        reason = ". ".join(reason_parts)

        return {
            "grade": grade,
            "score": round(final_score, 4),
            "pass": grade in {"A+", "A"} if self.gate_profile == "strict" else grade in {"A+", "A", "B"},
            "reason": reason,
            "weak_factors": weak_factors,
            "breakdown": {
                # Fully traceable grading output:
                "final_weighted_score": round(final_score, 4),
                "grade_thresholds": {"A+": 0.80, "A": 0.70, "B": 0.60},
                "missing_factors": missing_factors,
                "factors": {
                    # Each factor includes raw score, whether it was missing, base weight, normalized weight, and contribution.
                    k: {
                        "score": (None if factor_values.get(k) is None else round(float(factor_values[k]), 4)),
                        "missing": factor_values.get(k) is None,
                        "base_weight": round(float(base_weights[k]), 4),
                        "normalized_weight": (None if k not in normalized_weights else round(float(normalized_weights[k]), 6)),
                        "contribution": (None if k not in contributions else round(float(contributions[k]), 6)),
                    }
                    for k in base_weights.keys()
                },
            },
        }

    def _session_quality_score(self, session_name: str) -> float:
        s = (session_name or "").upper()
        if "OVERLAP" in s:
            return 1.0
        if "LONDON" in s or "NEW YORK" in s:
            return 0.8
        if "ASIA" in s or "ASIAN" in s:
            return 0.55
        return 0.5

    def _support_resistance_target_clearance(self, signal: TradeSignal, ai_context: Dict[str, Any]) -> float:
        """
        Score whether nearby S/R is likely to block the first target path.
        1.0 = clear, 0.0 = likely blocked.
        """
        try:
            entry = float(signal.entry_price)
            sl = float(signal.structural_sl)
            risk = abs(entry - sl)
            if risk <= 0:
                return 0.5

            sr = ai_context.get("nearby_support_resistance") or {}
            support = self._safe_float(sr.get("support"))
            resistance = self._safe_float(sr.get("resistance"))

            if signal.side == OrderSide.BUY:
                if resistance is None or resistance <= entry:
                    return 1.0
                dist = resistance - entry
            else:
                if support is None or support >= entry:
                    return 1.0
                dist = entry - support

            # If room to nearby level is below ~1.1R, likely blocked.
            if dist < (risk * 1.1):
                return 0.2
            if dist < (risk * 1.5):
                return 0.6
            return 1.0
        except Exception:
            return 0.5

    def _resolve_gate_thresholds(self, strategy_id: str) -> Tuple[float, float]:
        """Resolves structure and AI thresholds based on the active Gate Profile."""
        # 1. Start with config defaults
        base_struct = settings.STRUCTURE_THRESHOLDS.get(strategy_id, settings.STRUCTURE_THRESHOLDS.get("DEFAULT", 0.45))
        base_ai = settings.AI_THRESHOLDS.get(strategy_id, settings.AI_THRESHOLDS.get("DEFAULT", 0.52))
        
        # Use the most restrictive between global slider and config-driven threshold for AI
        global_ai_thr = float(getattr(self, "ai_threshold", 0.48))
        base_ai = max(global_ai_thr, base_ai)

        if self.gate_profile == "strict":
            return base_struct, base_ai
        
        elif self.gate_profile == "balanced":
            # Balanced Profile: Slightly more permissive for backtesting
            if strategy_id == "SMC_VOLUME":
                struct_thr = 0.52 # Specialized for SMC_VOLUME reaction
            else:
                struct_thr = max(0.45, base_struct * 0.9) # 10% reduction for others
            
            ai_thr = 0.48 # Standardized lower threshold for balanced research
            return struct_thr, ai_thr
            
        elif self.gate_profile == "research":
            # Research Profile: Low barriers for diagnostic data collection
            return 0.35, 0.45
            
        return base_struct, base_ai

    def _set_rejection_metadata(
        self,
        signal: TradeSignal,
        stage: str,
        rule: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
        current_value: Any = None,
        required_value: Any = None,
    ) -> None:
        """
        Standardizes rejection metadata fields across strategy/AI/grading stages.
        Uses `metadata` only (no schema changes).
        """
        md = signal.metadata or {}
        md["rejection_stage"] = stage
        md["rejection_rule"] = rule
        md["rejection_reason"] = reason
        md["rejection_details"] = details or {}
        md["current_value"] = current_value
        md["required_value"] = required_value
        signal.metadata = md
    def _update_strategy_funnel(self, strategy_id: str, stage: str):
        if not self.diagnose_gates: return
        if strategy_id not in self._gate_diagnostics["strategy_funnels"]:
            self._gate_diagnostics["strategy_funnels"][strategy_id] = {
                "raw_signals": 0, "after_strategy_filter": 0, "after_structure_gate": 0,
                "after_ai_gate": 0, "after_trade_grading": 0, "after_risk_manager": 0,
                "after_entry_model": 0, "executed": 0
            }
        self._gate_diagnostics["strategy_funnels"][strategy_id][stage] += 1

    def _setup_to_signal(self, setup: RawSetup, context: StrategyContext, strategy_id: str) -> TradeSignal:
        """Helper to convert a RawSetup to a full TradeSignal."""
        fingerprint = self._generate_fingerprint(setup.symbol, setup)
        return TradeSignal(
            idempotency_key=f"{fingerprint}_{int(pd.to_datetime(setup.setup_candle_timestamp).timestamp())}",
            signal_fingerprint=fingerprint,
            strategy_name=setup.family.name if hasattr(setup.family, "name") else str(setup.family),
            symbol=setup.symbol,
            timeframe="M1",
            side=setup.direction,
            regime=context.regime,
            session=context.session,
            setup_score=0.0,
            ai_confidence=0.0,
            ai_threshold_used=0.0,
            entry_mode=EntryMode.MARKET_IMMEDIATE,
            entry_price=setup.entry_price,
            structural_sl=setup.stop_loss,
            volatility_buffer=0.0005,
            targets=setup.targets,
            estimated_rr=2.0,
            setup_candle_timestamp=setup.setup_candle_timestamp,
            chart_annotations=[],
            metadata={
                **(setup.metadata or {}),
                "strategy_id": strategy_id,
                "rejection_stage": None,
                "rejection_rule": None,
                "rejection_reason": None,
            }
        )
