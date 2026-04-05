import sqlite3
import os

dbs = ['alertli.db', 'trading_bot.db']
for db_file in dbs:
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"DB: {db_file} Tables: {tables}")
        if 'bot_state' in tables:
            cursor.execute("SELECT active_symbols FROM bot_state")
            symbols = cursor.fetchone()
            print(f"Active Symbols in {db_file}: {symbols}")
        conn.close()
    else:
        print(f"DB {db_file} not found")
