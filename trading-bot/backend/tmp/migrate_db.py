import sqlite3
import os

db_path = "trading_bot.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Columns to add to 'users' table
    users_columns = [
        ("cooldown_candles", "INTEGER DEFAULT 120"),
        ("same_zone_threshold_points", "INTEGER DEFAULT 100"),
        ("min_reward_to_level_points", "INTEGER DEFAULT 50"),
        ("news_filter_enabled", "BOOLEAN DEFAULT 1"),
        ("session_filter_enabled", "BOOLEAN DEFAULT 1")
    ]

    # Columns to add to 'trades' table
    trades_columns = [
        ("ai_score", "FLOAT"),
        ("session", "TEXT"),
        ("market_regime", "TEXT"),
        ("exit_reason", "TEXT"),
        ("final_exit_reason", "TEXT")
    ]

    # Columns to add to 'bot_state' table
    bot_state_columns = [
        ("recent_rejections", "JSON DEFAULT '[]'"),
        ("filter_status", "JSON DEFAULT '{}'"),
        ("active_cooldowns", "JSON DEFAULT '[]'"),
        ("strategy_analytics", "JSON DEFAULT '{}'")
    ]

    def add_columns(table, columns):
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        for col_name, col_type in columns:
            if col_name not in existing_cols:
                print(f"Adding column {col_name} to {table}...")
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"Error adding {col_name} to {table}: {e}")
            else:
                print(f"Column {col_name} already exists in {table}.")

    add_columns("users", users_columns)
    add_columns("trades", trades_columns)
    add_columns("bot_state", bot_state_columns)

    # Tables to create
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_windows (
        id INTEGER PRIMARY KEY,
        event_name TEXT,
        currency TEXT,
        impact TEXT,
        start_time DATETIME,
        end_time DATETIME,
        is_active BOOLEAN DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocked_zones (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        direction TEXT,
        price_level FLOAT,
        range_points INTEGER,
        expiry DATETIME,
        reason TEXT,
        created_at DATETIME
    )
    """)

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
