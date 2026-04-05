import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
from app.core.datatypes import (
    TradeSignal, SignalStatus, RawSetup, SetupScore, 
    StrategyDecision, OrderSide, EntryMode
)
from app.strategy.context import ContextEvaluator
from app.strategy.scorer import ConfluenceScorer
from app.strategy.selector import CandidateSelector
from app.strategy.annotations import AnnotationBuilder

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

    def evaluate(self, symbol: str, dataframes: Dict[str, Any], strategy_settings: Optional[Dict[str, Any]] = None) -> Tuple[List[TradeSignal], List[TradeSignal]]:
        """
        Refactored Analyze Flow:
        1. Contextualize Market (M1/M5/M15).
        2. Filter strategies based on user settings.
        3. Detect valid setups across enabled families.
        4. Appraise setups via weighted confluence scoring.
        5. Select the 'Best-of-Breed' candidate.
        6. Build a structured TradeSignal.
        """
        # 1. Build Multi-Timeframe Context
        context = self.context_eval.evaluate(
            dataframes['M1'], dataframes['M5'], dataframes['M15'], symbol
        )
        
        logger.info(f"[{symbol}] Context: Session={context.session}, Regime={context.regime}, Tradable={context.is_tradable}")
        
        if not context.is_tradable:
            logger.info(f"[{symbol}] Market not tradable. Skipping.")
            return [], []

        # 2. Gather Candidates from all Enabled Strategy Families
        candidates = []
        strategy_settings = strategy_settings or {}
        
        for strategy in self.strategies:
            # Check for mapping to settings ID
            # Assuming strategy.strategy_id is defined in individual classes
            sid = getattr(strategy, "strategy_id", "UNKNOWN")
            # Fallback to current engine-wide threshold if not specified in strategy settings
            base_thr = float(getattr(self, "ai_threshold", 0.48))
            s_set = strategy_settings.get(sid, {"enabled": True, "ai_threshold": base_thr})
            
            if not s_set.get("enabled", True):
                continue

            raw = strategy.detect_setup(dataframes, context)
            if raw:
                # 3. Apply Scoring Logic
                score = strategy.score_setup(raw, context)
                logger.info(f"[{symbol}] Candidate Detected: {sid} | Direction={raw.direction.name} | BaseScore={score.total_score}")
                candidates.append((raw, score, s_set))

        # 4. Selection (Ranking & Tie-breaking)
        # Decision logic remains same but passes settings along if needed
        decision = self.selector.select([(r, s) for r, s, set in candidates])
        
        if not decision.is_triggered or not decision.best_setup:
            return [], []

        # 5. Signal Construction for the Winner
        best = decision.best_setup
        best_candidate = next(c for c in candidates if c[0] == best)
        best_score = best_candidate[1]
        best_settings = best_candidate[2]
        
        # Build Metadata for Execution & Charting
        best.chart_annotations = self.anno_builder.build(best)
        
        # AI Gate: Prioritize Global Slider (self.ai_threshold)
        # This ensures that when the user sets 20% in the UI, the bot actually uses 0.20
        # instead of the hidden strategy defaults (like 0.70).
        global_thr = float(getattr(self, "ai_threshold", 0.48))
        
        # We use the global threshold as the master gate. 
        # Strategy-specific thresholds are ignored if the global one has been tuned.
        strategy_ai_thr = global_thr
        
        ai_pass, ai_conf, ai_reason = self.ai.predict(
            dataframes["M1"], confidence_threshold=strategy_ai_thr
        )
        
        logger.info(f"[{symbol}] AI Prediction: Confidence={ai_conf:.2f} (Threshold={strategy_ai_thr}) | Pass={ai_pass} | Reason={ai_reason}")
        
        # Fingerprint generation
        fingerprint = self._generate_fingerprint(symbol, best)
        
        signal = TradeSignal(
            idempotency_key=f"{fingerprint}_{int(datetime.now(timezone.utc).timestamp())}",
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
            metadata={**best.metadata, "selector_reason": decision.selection_reason, "ai_reason": ai_reason}
        )

        if not ai_pass:
             signal.status = SignalStatus.AI_REJECTED
             return [], [signal]
        
        signal.status = SignalStatus.APPROVED
        return [signal], []

    def _generate_fingerprint(self, symbol: str, setup: RawSetup) -> str:
        raw_str = f"{symbol}_{setup.family.name}_{setup.setup_candle_timestamp}_{setup.direction.value}"
        return hashlib.md5(raw_str.encode()).hexdigest()
