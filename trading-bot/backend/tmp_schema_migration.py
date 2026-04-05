import sqlite3
import os

db_path = "c:/Users/Auranzeb Khalil/OneDrive/Desktop/My project/trading-bot/backend/trading_bot.db"

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Update 'users' table
    user_columns = [
        ("partial_execution_enabled", "BOOLEAN DEFAULT 1"),
        ("partial_stage_1_trigger", "FLOAT DEFAULT 0.6"),
        ("partial_stage_1_close_pct", "FLOAT DEFAULT 0.5"),
        ("partial_stage_2_trigger", "FLOAT DEFAULT 0.8"),
        ("partial_stage_2_close_pct", "FLOAT DEFAULT 0.25"),
        ("max_spread_points", "INTEGER DEFAULT 50"),
        ("max_consecutive_losses", "INTEGER DEFAULT 3"),
        ("late_entry_threshold", "FLOAT DEFAULT 0.7"),
        ("cooldown_minutes", "INTEGER DEFAULT 60"),
        ("max_daily_loss_pct", "FLOAT DEFAULT 0.03")
    ]
    
    current_user_cols = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    for col_name, col_type in user_columns:
        if col_name not in current_user_cols:
            print(f"Adding {col_name} to users")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            
    # 2. Update 'trades' table
    trade_columns = [
        ("initial_volume", "FLOAT"),
        ("tp1", "FLOAT"),
        ("tp2", "FLOAT"),
        ("bid_at_entry", "FLOAT"),
        ("ask_at_entry", "FLOAT"),
        ("spread_at_entry", "FLOAT"),
        ("slippage_points", "FLOAT"),
        ("session", "STRING"),
        ("market_regime", "STRING"),
        ("ai_score", "FLOAT"),
        ("final_exit_reason", "STRING"),
        ("stage1_executed", "BOOLEAN DEFAULT 0"),
        ("stage1_trigger_time", "DATETIME"),
        ("stage2_executed", "BOOLEAN DEFAULT 0"),
        ("stage2_trigger_time", "DATETIME"),
        ("breakeven_done", "BOOLEAN DEFAULT 0")
    ]
    
    current_trade_cols = [row[1] for row in cursor.execute("PRAGMA table_info(trades)").fetchall()]
    for col_name, col_type in trade_columns:
        if col_name not in current_trade_cols:
            print(f"Adding {col_name} to trades")
            cursor.execute(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}")

    # 3. Update 'signal_logs' table
    signal_columns = [
        ("ai_score", "FLOAT"),
        ("session", "STRING"),
        ("market_regime", "STRING"),
        ("bid", "FLOAT"),
        ("ask", "FLOAT"),
        ("spread", "FLOAT")
    ]
    
    current_signal_cols = [row[1] for row in cursor.execute("PRAGMA table_info(signal_logs)").fetchall()]
    for col_name, col_type in signal_columns:
        if col_name not in current_signal_cols:
            print(f"Adding {col_name} to signal_logs")
            cursor.execute(f"ALTER TABLE signal_logs ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
