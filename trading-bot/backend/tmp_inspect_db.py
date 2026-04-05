import sqlite3
import json

db_file = 'trading_bot.db'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables in {db_file}: {tables}")

if 'bot_state' in tables:
    cursor.execute("SELECT active_symbols, live_logs FROM bot_state")
    row = cursor.fetchone()
    if row:
        print(f"Active Symbols: {row[0]}")
        print(f"Live Logs Count: {len(json.loads(row[1]) if row[1] else [])}")
        print(f"Recent Logs: {json.loads(row[1])[:3] if row[1] else 'None'}")
    else:
        print("BotState table is empty")

conn.close()
