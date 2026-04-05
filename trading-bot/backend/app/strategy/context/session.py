from datetime import datetime, timezone
from typing import Dict, Tuple, List
from app.core.datatypes import TradingSession

class SessionManager:
    def __init__(self, config: Dict[TradingSession, Tuple[int, int]]):
        self.windows = config

    def get_current_session(self, dt: datetime = None) -> List[str]:
        if not dt: dt = datetime.now(timezone.utc)
        hour = dt.hour
        sessions = []
        
        # UTC Session Hours (Standard)
        if 0 <= hour < 9: sessions.append("ASIA")
        if 8 <= hour < 16: sessions.append("LONDON")
        if 13 <= hour < 21: sessions.append("NEW YORK")
        
        # Detect Overlap (London + New York)
        if 13 <= hour < 16: sessions.append("OVERLAP")
        
        return sessions if sessions else ["DEAD_ZONE"]

    def is_liquid_session(self, session: str) -> bool:
        return session in ["LONDON", "NEW_YORK", "OVERLAP"]
