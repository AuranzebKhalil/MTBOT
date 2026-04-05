import sqlite3
import os

db_path = "trading_bot.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    new_cols = [
        ("stage1_partial_done", "BOOLEAN DEFAULT 0"),
        ("stage1_sl_done", "BOOLEAN DEFAULT 0"),
        ("stage2_partial_done", "BOOLEAN DEFAULT 0"),
        ("stage2_sl_done", "BOOLEAN DEFAULT 0")
    ]
    
    for col_name, col_type in new_cols:
        try:
            cursor.execute(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} to trades table.")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
