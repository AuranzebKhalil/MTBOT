import sqlite3
import json
import os

dbs = ['alertli.db', 'trading_bot.db']
symbols = ['GOLD']

for db_file in dbs:
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 1. Update existing bot_state
            cursor.execute("UPDATE bot_state SET active_symbols = ?", (json.dumps(symbols),))
            
            # 2. Add 'GOLD' back to live_logs for visual confirmation
            cursor.execute("SELECT live_logs FROM bot_state")
            row = cursor.fetchone()
            logs = json.loads(row[0]) if row and row[0] else []
            msg = "DB SYNC: Fixed Active Symbols to [GOLD]"
            if msg not in logs:
                logs.insert(0, msg)
                cursor.execute("UPDATE bot_state SET live_logs = ?", (json.dumps(logs[:50]),))
            
            conn.commit()
            conn.close()
            print(f"Successfully synced {db_file}")
        except Exception as e:
            print(f"Error syncing {db_file}: {e}")
    else:
        print(f"DB {db_file} not found")
