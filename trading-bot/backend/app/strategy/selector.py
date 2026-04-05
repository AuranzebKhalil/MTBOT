from typing import List, Optional, Tuple
from app.core.datatypes import RawSetup, SetupScore, StrategyDecision, OrderSide

class CandidateSelector:
    """Best-of-Breed Implementation: Compares and picks only high-prob setups."""
    
    def __init__(self, min_qualified_score: float = 70.0):
        self.threshold = min_qualified_score

    def select(self, candidates: List[Tuple[RawSetup, SetupScore]]) -> StrategyDecision:
        """
        Gathers all scored setups, filters out weak ones, compares them, 
        resolves ties, and returns the 'Best' candidate.
        """
        
        # 1. Filter out non-qualified candidates
        qualified = [c for c in candidates if c[1].is_qualified and c[1].total_score >= self.threshold]
        
        if not qualified:
            return StrategyDecision(
                is_triggered=False,
                action=OrderSide.WAIT,
                rejection_reason="No Candidates Passed High-Confluence Threshold (70+ points)"
            )
        
        # 2. Rank candidates (Score -> RR -> Family Priority)
        # We prefer VSA_SHIFT and SWEEP_RECLAIM over EXHAUSTION
        qualified.sort(key=lambda x: (x[1].total_score, self._calculate_rr(x[0]), self._get_family_rank(x[0])), reverse=True)
        
        best_cand = qualified[0]
        
        # 3. Resolve Tie-Cases (If scores equal, pick best RR)
        # Sort handles this via tuple-priority ordering
        
        return StrategyDecision(
            is_triggered=True,
            action=best_cand[0].direction,
            best_setup=best_cand[0],
            selection_reason=f"Top candidate: {best_cand[0].family.name} with score {best_cand[1].total_score:.2f}",
            all_candidates=[c[0] for c in qualified]
        )

    def _calculate_rr(self, setup: RawSetup) -> float:
        """Calculates Reward:Risk for comparison."""
        dist_sl = abs(setup.entry_price - setup.stop_loss)
        dist_tp = abs(setup.targets[0] - setup.entry_price)
        return dist_tp / dist_sl if dist_sl > 0 else 0

    def _get_family_rank(self, setup: RawSetup) -> int:
        """High frequency families get higher priority."""
        ranks = {
            "VSA_SHIFT": 10,
            "SWEEP_RECLAIM": 9,
            "CONTINUATION": 8,
            "MITIGATION": 7,
            "EXHAUSTION": 5
        }
        return ranks.get(setup.family.name, 0)
