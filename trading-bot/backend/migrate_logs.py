import sqlite3
import os

db_path = "trading_bot.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"DB {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. execution_logs
    columns_execution = [
        ("bid", "FLOAT"),
        ("ask", "FLOAT"),
        ("spread", "FLOAT"),
        ("error_message", "TEXT")
    ]
    
    for col_name, col_type in columns_execution:
        try:
            cursor.execute(f"ALTER TABLE execution_logs ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} to execution_logs")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists in execution_logs")

    # 2. signal_logs
    columns_signal = [
        ("ai_score", "FLOAT"),
        ("session", "TEXT"),
        ("market_regime", "TEXT"),
        ("bid", "FLOAT"),
        ("ask", "FLOAT"),
        ("spread", "FLOAT")
    ]
    
    for col_name, col_type in columns_signal:
        try:
            cursor.execute(f"ALTER TABLE signal_logs ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} to signal_logs")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists in signal_logs")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
