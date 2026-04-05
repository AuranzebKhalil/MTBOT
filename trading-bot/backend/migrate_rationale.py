import sqlite3
import os

db_path = "c:\\Users\\Auranzeb Khalil\\OneDrive\\Desktop\\My project\\trading-bot\\backend\\alertli.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN rationale TEXT")
        conn.commit()
        print("Successfully added rationale column to trades table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Rationale column already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
