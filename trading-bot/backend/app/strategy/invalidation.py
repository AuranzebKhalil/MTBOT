from datetime import datetime
from typing import Dict, Any, Optional
from app.core.datatypes import RawSetup, InvalidationRule, OrderSide

class InvalidationService:
    """Post-Detection Integrity Monitor."""
    
    def is_invalid(self, setup: RawSetup, rules: InvalidationRule, current_data: Dict[str, Any]) -> bool:
        """Checks if a pending/detected setup is now stale or invalidated by structure."""
        
        # 1. Expiry Check (Bar Count)
        if (current_data.get('bar_count', 0) - setup.metadata.get('bar_index', 0)) > rules.expiry_bars:
            return True
            
        # 2. Structural Anchor Check (Was our low swept before entry?)
        price = current_data['ticker']['close']
        if setup.direction == OrderSide.BUY and price < rules.structure_anchor:
            return True
        if setup.direction == OrderSide.SELL and price > rules.structure_anchor:
            return True
            
        # 3. Session End Guard
        if rules.cancel_on_session_change and current_data.get('session_changed', False):
            return True
            
        # 4. Regime Shift Guard
        if rules.cancel_on_regime_flip and current_data.get('current_regime') != setup.metadata.get('regime_at_detect'):
            return True
            
        # 5. Live Flow Spread Spike Check
        if current_data['ticker'].get('spread', 0) > current_data.get('max_allowed_spread', 999):
            return True
            
        return False
        
    def generate_default_rules(self, setup: RawSetup) -> InvalidationRule:
        """Returns standard institutional invalidation rules based on family."""
        
        # Default anchors are the SL levels for most families
        rules = InvalidationRule(
            setup_id=setup.metadata.get('id', 'unknown'),
            expiry_bars=5 if setup.family.name == "VSA_SHIFT" else 15,
            structure_anchor=setup.stop_loss
        )
        return rules
