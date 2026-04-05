import sqlite3
import os

db_path = "trading_bot.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def add_column(table, column, type):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [c[1] for c in cursor.fetchall()]
        if column not in columns:
            print(f"Adding {column} to {table} table...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        else:
            print(f"{column} already exists in {table} table.")

    try:
        # User table
        add_column("users", "strategy_settings", "JSON")
        add_column("users", "preferred_session", "TEXT")
        add_column("users", "session_filter_enabled", "BOOLEAN")
        add_column("users", "news_filter_enabled", "BOOLEAN")
        add_column("users", "cooldown_candles", "INTEGER")
        add_column("users", "same_zone_threshold_points", "INTEGER")
        add_column("users", "min_reward_to_level_points", "INTEGER")
        add_column("users", "late_entry_threshold", "FLOAT")
        add_column("users", "min_rr_filter", "FLOAT")
        add_column("users", "max_spread_points", "FLOAT")

        # Bot State table
        add_column("bot_state", "strategy_settings", "JSON")
        add_column("bot_state", "filter_status", "JSON")
        add_column("bot_state", "active_cooldowns", "JSON")
        add_column("bot_state", "strategy_analytics", "JSON")
        add_column("bot_state", "recent_rejections", "JSON")

        # Trades table
        add_column("trades", "market_regime", "TEXT")
        add_column("trades", "session", "TEXT")
        add_column("trades", "ai_score", "FLOAT")
        add_column("trades", "bid_at_entry", "FLOAT")
        add_column("trades", "ask_at_entry", "FLOAT")
        add_column("trades", "spread_at_entry", "FLOAT")
        add_column("trades", "exit_time", "DATETIME")
        add_column("trades", "exit_reason", "TEXT")
        add_column("trades", "final_exit_reason", "TEXT")

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
