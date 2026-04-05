import requests
import datetime
import logging
import threading
import time

logger = logging.getLogger("NewsProvider")

class NewsProvider:
    """
    Fetches high-impact economic news events to prevent trading during 'Red Folder' volatility.
    """
    def __init__(self, check_interval_minutes=60):
        self.events = []
        self.last_check = None
        self.check_interval = check_interval_minutes * 60
        self.is_running = False
        self._lock = threading.Lock()
        
    def start_monitoring(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._update_loop, daemon=True)
            self.thread.start()
            logger.info("News monitoring started.")

    def _update_loop(self):
        while self.is_running:
            self.fetch_events()
            time.sleep(self.check_interval)

    def fetch_events(self):
        """
        Fetches today's high-impact events. 
        Note: Real-world implementation would use Finnhub, ForexFactory, or similar API.
        This mock/demo implementation simulates the structure.
        """
        logger.info("Syncing high-impact news events...")
        try:
            # Placeholder for actual API call, e.g., Finnhub or a scraper
            # For now, we simulate detecting a 'Red Folder' if it's a specific time
            # or we could use a free RSS feed.
            
            with self._lock:
                # Real-world: self.events = requests.get(API_URL).json()
                # For now, we clear any stale events or placeholders
                self.events = []
                self.last_check = datetime.datetime.now()
            logger.info(f"News sync complete. {len(self.events)} events found.")
        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")

    def is_news_active(self, buffer_minutes=15):
        """
        Returns True if a high-impact news event is happening now or within the buffer.
        """
        now = datetime.datetime.now()
        with self._lock:
            for event in self.events:
                if event['impact'] != "HIGH":
                    continue
                
                event_time = event['time']
                start_block = event_time - datetime.timedelta(minutes=buffer_minutes)
                end_block = event_time + datetime.timedelta(minutes=buffer_minutes)
                
                if start_block <= now <= end_block:
                    return True, event['name']
        return False, ""

# Singleton instance
news_manager = NewsProvider()
