import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from app.storage.db import DatabaseContext
from app.storage.models import NewsWindow

logger = logging.getLogger(__name__)

class NewsProvider(ABC):
    @abstractmethod
    def fetch_events(self) -> List[Dict[str, Any]]:
        """Fetch news events from an external source."""
        raise NotImplementedError

class DatabaseNewsProvider(NewsProvider):
    """
    Synchronizes news events from the internal 'news_windows' table.
    This allows manual entry via API or future sync jobs.
    """
    def fetch_events(self) -> List[Dict[str, Any]]:
        with DatabaseContext() as db:
            active_windows = db.query(NewsWindow).filter(NewsWindow.is_active == True).all()
            return [
                {
                    "event_name": n.event_name,
                    "currency": n.currency.upper(),
                    "impact": n.impact.upper(),
                    "start_time": n.start_time.replace(tzinfo=timezone.utc),
                    "end_time": n.end_time.replace(tzinfo=timezone.utc)
                }
                for n in active_windows
            ]

class NewsService:
    def __init__(self, provider: Optional[NewsProvider] = None):
        self.provider = provider or DatabaseNewsProvider()
        self.cached_events: List[Dict] = []
        self.last_fetch = datetime.min.replace(tzinfo=timezone.utc)

    def get_active_event(self, symbol: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Checks if there is an active or upcoming news event blocking trades.
        Returns the event dict if blocking, else None.
        """
        now = datetime.now(timezone.utc)
        
        # Sync every 5 minutes
        if (now - self.last_fetch).total_seconds() > 300:
            try:
                self.cached_events = self.provider.fetch_events()
                self.last_fetch = now
                logger.info(f"NewsService synced {len(self.cached_events)} events.")
            except Exception as e:
                logger.error(f"Failed to fetch news events: {e}")

        currency = self._get_currency_from_symbol(symbol)
        min_before = config.get("news_block_minutes_before", 20)
        min_after = config.get("news_block_minutes_after", 20)
        high_impact_only = config.get("high_impact_only", True)

        for event in self.cached_events:
            # Impact Filter
            if high_impact_only and event["impact"] != "HIGH":
                continue
            
            # Currency Filter (Symbol currency or USD)
            if event["currency"] == currency or event["currency"] == "USD":
                # Calculate the blocking window
                event_time = event["start_time"]
                block_start = event_time - timedelta(minutes=min_before)
                block_end = event_time + timedelta(minutes=min_after)
                
                if block_start <= now <= block_end:
                    # Enrich event with metadata for logging
                    event_info = event.copy()
                    event_info.update({
                        "current_time": now,
                        "block_window": f"-{min_before}m / +{min_after}m"
                    })
                    logger.warning(f"🚩 NEWS BLOCK ACTIVE: {event['event_name']} ({event['currency']})")
                    return event_info
        return None

    def is_news_active(self, symbol: str) -> bool:
        """Alias for backward compatibility or simple boolean checks."""
        return self.get_active_event(symbol, {
            "news_block_minutes_before": 20,
            "news_block_minutes_after": 20,
            "high_impact_only": True
        }) is not None

    def _get_currency_from_symbol(self, symbol: str) -> str:
        s = str(symbol).upper()
        if "XAU" in s or "GOLD" in s:
            return "USD" # Gold news is usually USD news
        return s[:3] if len(s) >= 3 else s

    def add_manual_event(self, event_name: str, currency: str, impact: str, start_time: datetime, duration_minutes: int = 30):
        """Helper for manual entry via DB."""
        with DatabaseContext() as db:
            new_window = NewsWindow(
                event_name=event_name,
                currency=currency.upper(),
                impact=impact.upper(),
                start_time=start_time,
                end_time=start_time + timedelta(minutes=duration_minutes),
                is_active=True
            )
            db.add(new_window)
            db.commit()
            logger.info(f"Added manual news window: {event_name}")
