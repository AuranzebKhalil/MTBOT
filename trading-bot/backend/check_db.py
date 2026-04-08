import sqlite3
import os

db_path = "trading_bot.db"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- User Table Schema ---")
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[1]} | Type: {col[2]}")
    except Exception as e:
        print(f"Error reading users: {e}")
        
    print("\n--- Support Ticket Table ---")
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets'")
        if cursor.fetchone():
            print("support_tickets table exists.")
        else:
            print("support_tickets table MISSING.")
    except Exception as e:
        print(f"Error checking tickets: {e}")
        
    conn.close()
