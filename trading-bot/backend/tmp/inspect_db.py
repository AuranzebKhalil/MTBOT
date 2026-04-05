import sqlite3
import os

db_path = "trading_bot.db"

def inspect_db():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["trades"]
    for table in tables:
        print(f"\n--- {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        for col in cols:
            print(f"{col[1]} ({col[2]})")

    conn.close()

if __name__ == "__main__":
    inspect_db()
