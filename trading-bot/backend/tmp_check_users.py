import sqlite3

db_file = 'trading_bot.db'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print(f"Columns in users: {[c[1] for c in columns]}")

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
print(f"Number of users: {len(rows)}")

conn.close()
