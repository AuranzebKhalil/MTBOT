from datetime import datetime, timezone

class ExecutionFeatures:
    """
    Extracts features related to the execution climate.
    Important for Execution Risk model.
    """
    
    @staticmethod
    def extract_features(execution_data: dict) -> dict:
        """
        Parses live execution parameters: spread, average vs historical slippage.
        """
        if execution_data is None:
            return {"current_spread": 0.0, "tick_volume": 0.0, "is_london": 0, "is_new_york": 0}
            
        current_spread = execution_data.get("spread", 0.0)
        tick_volume = execution_data.get("tick_volume", 0.0)
        
        # Session time derivation
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour
        
        is_london = 1 if 7 <= hour < 11 else 0
        is_new_york = 1 if 13 <= hour < 16 else 0
        
        return {
            "current_spread": round(current_spread, 2),
            "tick_volume": tick_volume,
            "is_london": is_london,
            "is_new_york": is_new_york,
        }
        
    @staticmethod
    def extract_all(execution_data: dict) -> dict:
        """Returns compiled execution dictionary."""
        return ExecutionFeatures.extract_features(execution_data)
