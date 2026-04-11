import logging
from supabase import create_client, Client
from app.core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = f"https://{settings.SUPABASE_PROJECT_ID}.supabase.co"
            key = settings.SUPABASE_KEY # This should be the Service Role Key for backend access
            
            if not settings.SUPABASE_PROJECT_ID or not settings.SUPABASE_KEY:
                logger.warning("⚠️ Supabase credentials missing. Client not initialized.")
                return None
            
            cls._instance = create_client(url, key)
            logger.info(f"🚀 Supabase Client initialized for project: {settings.SUPABASE_PROJECT_ID}")
            
        return cls._instance

# Helper for easy access
def get_supabase() -> Client:
    return SupabaseClient.get_client()
