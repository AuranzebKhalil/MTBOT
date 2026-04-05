
import sqlite3
import os

db_path = r'c:\Users\Auranzeb Khalil\OneDrive\Desktop\My project\trading-bot\backend\alertli.db'

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- LAST 10 TRADES ---")
    try:
        cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading trades: {e}")
        
    print("\n--- USERS ---")
    try:
        cursor.execute("SELECT id, email, preferred_symbol, preferred_timeframe FROM users")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading users: {e}")
        
    conn.close()
