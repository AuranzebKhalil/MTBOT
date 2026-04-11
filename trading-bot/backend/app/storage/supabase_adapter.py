from typing import List, Dict, Any, Optional
from app.storage.supabase_client import get_supabase
import logging

logger = logging.getLogger("SupabaseAdapter")

class SupabaseAdapter:
    """
    Standardizes database operations (GET, POST, PUT, DELETE) 
    using the Supabase Python SDK for the trading bot history and settings.
    """

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None

    @staticmethod
    def get_trades(status: str = "OPEN", limit: int = 50) -> List[Dict[str, Any]]:
        supabase = get_supabase()
        query = supabase.table("trades").select("*").order("time", desc=True).limit(limit)
        if status.upper() != "ALL":
            query = query.eq("status", status.upper())
        res = query.execute()
        return res.data

    @staticmethod
    def create_trade(trade_data: Dict[str, Any]) -> Dict[str, Any]:
        supabase = get_supabase()
        res = supabase.table("trades").insert(trade_data).execute()
        return res.data[0] if res.data else {}

    @staticmethod
    def update_trade(ticket_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        supabase = get_supabase()
        res = supabase.table("trades").update(updates).eq("ticket_id", ticket_id).execute()
        return res.data[0] if res.data else {}

    @staticmethod
    def log_signal(signal_data: Dict[str, Any]):
        supabase = get_supabase()
        supabase.table("signal_logs").insert(signal_data).execute()

    @staticmethod
    def get_bot_state() -> Dict[str, Any]:
        supabase = get_supabase()
        res = supabase.table("bot_state").select("*").limit(1).execute()
        return res.data[0] if res.data else {}

    @staticmethod
    def update_bot_status(is_running: Optional[bool], message: Optional[str], action: Optional[str]):
        supabase = get_supabase()
        updates = {"updated_at": "now()"}
        if is_running is not None: updates["is_running"] = is_running
        if message is not None: updates["status_message"] = message
        if action is not None: updates["current_action"] = action
        
        supabase.table("bot_state").update(updates).eq("id", 1).execute()

    @staticmethod
    def get_risk_settings(user_email: str) -> Dict[str, Any]:
        user = SupabaseAdapter.get_user_by_email(user_email)
        if not user: return {}
        return {
            "risk_per_trade": user.get("risk_per_trade", 0.01),
            "max_trades": user.get("max_trades", 2),
            "daily_loss_limit": user.get("daily_loss_limit", 0.1),
            "news_filter_enabled": user.get("news_filter_enabled", True)
        }
